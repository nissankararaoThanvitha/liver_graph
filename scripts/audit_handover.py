"""Consistency audit of the files handed to the next group.

These lists will be built on by people who will not re-derive them, so the
failure that matters is not "the biology is arguable" but "the file says
something the pipeline did not compute". This checks the second kind: broken
joins, duplicate or missing genes, scores that do not add up, subsets that
are not subsets, symbols that disagree between files, and values outside
their allowed range.

Every check prints PASS or FAIL. A FAIL means the file is wrong and must not
be handed over until fixed.

Usage:
    python Paper1_HighConfidence/audit_handover.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

fails = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        fails.append(name)


s25 = pd.read_csv(HERE / "11_FINAL_shortlist_25_genes.csv")
t507 = pd.read_csv(HERE / "11_final_tier1_507_genes.csv")
all3645 = pd.read_csv(HERE / "11_final_all_3645_genes.csv")
prog = pd.read_csv(HERE / "00_all_4692_progression_genes.csv")
master = pd.read_csv(HERE / "01_master_table.csv")
loso = pd.read_csv(HERE / "10_loso_summary.csv")
stage = pd.read_csv(ROOT / "data/for_mentor/genes_by_fibrosis_stage.csv")
fibq = pd.read_csv(ROOT / "data/progression_full/progression_fibrosis.csv")

print("\n1. COUNTS")
check("shortlist is 25 genes", len(s25) == 25, f"{len(s25)}")
check("Tier 1 is 507 genes", len(t507) == 507, f"{len(t507)}")
check("full table is 3,645 genes", len(all3645) == 3645, f"{len(all3645)}")
check("progression list is 4,692", len(prog) == 4692, f"{len(prog)}")

print("\n2. NO DUPLICATES")
for nm, d in [("shortlist", s25), ("tier1", t507), ("all", all3645),
              ("progression", prog)]:
    col = "Ensembl_ID" if "Ensembl_ID" in d else "ensembl_id"
    check(f"{nm}: unique gene IDs", d[col].is_unique,
          f"{int(d[col].duplicated().sum())} duplicated")

print("\n3. NESTING -- each list must be a subset of the one above")
a, b, c = set(s25.Ensembl_ID), set(t507.Ensembl_ID), set(all3645.Ensembl_ID)
p = set(prog[prog.in_fibrosis_starting_set].ensembl_id)
check("25 inside 507", a <= b, f"{len(a - b)} outside")
check("507 inside 3,645", b <= c, f"{len(b - c)} outside")
check("3,645 == fibrosis starting set of the 4,692", c == p,
      f"{len(c ^ p)} differ")

print("\n4. SCORES ADD UP")
sc = all3645[["P", "T", "X", "F", "B"]].sum(axis=1)
check("P+T+X+F+B == Total_score", (sc == all3645.Total_score).all(),
      f"{int((sc != all3645.Total_score).sum())} rows wrong")
rng = {"P": 2, "T": 2, "X": 2, "F": 1, "B": 2}
for k, mx in rng.items():
    check(f"{k} within 0-{mx}", all3645[k].between(0, mx).all(),
          f"range {all3645[k].min()}-{all3645[k].max()}")
check("Total_score within 0-9", all3645.Total_score.between(0, 9).all())

print("\n5. TIERS MATCH THE SCORES")
exp = np.select([all3645.Total_score >= 7, all3645.Total_score >= 5],
                ["Tier 1 - high confidence", "Tier 2 - moderate confidence"],
                default="Tier 3")
check("tier label matches total", (exp == all3645.Tier).all(),
      f"{int((exp != all3645.Tier).sum())} mislabelled")
check("every Tier 1 row scores >= 7", (t507.Total_score >= 7).all(),
      f"min {t507.Total_score.min()}")
check("Tier 1 file == Tier 1 rows of full table",
      b == set(all3645[all3645.Tier.str.startswith("Tier 1")].Ensembl_ID))

print("\n6. SHORTLIST RULE -- 5 per cluster, highest scoring")
vc = s25.Cluster.value_counts()
check("5 genes from each of C1-C5", sorted(vc.index) == ["C1", "C2", "C3", "C4", "C5"]
      and (vc == 5).all(), vc.to_dict())
worst = []
for cl, g in s25.groupby("Cluster"):
    pool = t507[t507.Cluster == cl]
    cut = g.Total_score.min()
    better = pool[(pool.Total_score > cut)
                  & (~pool.Ensembl_ID.isin(a))]
    if len(better):
        worst.append(f"{cl}: {len(better)} higher-scoring gene(s) left out")
check("no higher-scoring gene was skipped within a cluster", not worst,
      "; ".join(worst))

print("\n7. VALUES AGREE WITH THE SOURCE FILES")
src = stage.set_index("ensembl_id")
m = all3645.set_index("Ensembl_ID")
common = m.index.intersection(src.index)
check("fibrosis_rho matches genes_by_fibrosis_stage.csv",
      np.allclose(m.loc[common, "Fibrosis_rho"],
                  src.loc[common, "fibrosis_rho"], atol=1e-6),
      f"{len(common):,} genes compared")
check("symbols match genes_by_fibrosis_stage.csv",
      (m.loc[common, "Gene"].fillna("")
       == src.loc[common, "symbol"].fillna("")).all())
for i in range(5):
    ok = np.allclose(m.loc[common, f"F{i}"], src.loc[common, f"stage_{i}"],
                     atol=1e-6, equal_nan=True)
    check(f"stage mean F{i} matches source", ok)

print("\n8. DIRECTION AND DERIVED COLUMNS")
check("Direction agrees with the sign of rho",
      ((all3645.Fibrosis_rho > 0) == (all3645.Direction == "increasing")).all())
check("Delta_F0_F4 == F4 - F0",
      np.allclose(all3645.Delta_F0_F4, (all3645.F4 - all3645.F0), atol=5e-3))
check("no 'upregulated'/'downregulated' wording anywhere",
      not all3645.astype(str).apply(
          lambda s: s.str.contains("regulated", case=False)).any().any())

print("\n9. NOTHING MISSING WHERE IT MATTERS")
must = ["Gene", "Ensembl_ID", "Fibrosis_rho", "Fibrosis_q_FDR", "Direction",
        "Cluster", "Total_score", "Tier"]
for col in must:
    check(f"{col}: no blanks in the shortlist", s25[col].notna().all())
check("shortlist has LOSO for every gene",
      s25["LOSO_still_significant_of_5"].notna().all())
check("LOSO counts are 0-5",
      s25["LOSO_still_significant_of_5"].between(0, 5).all())

print("\n10. ENTRY CRITERIA STILL HOLD")
check("every gene passes fibrosis FDR < 0.05",
      (all3645.Fibrosis_q_FDR < 0.05).all(),
      f"max q {all3645.Fibrosis_q_FDR.max():.4f}")
fq = fibq.set_index("ensembl_id")
cm = m.index.intersection(fq.index)
check("every gene had all studies agreeing on direction",
      (fq.loc[cm, "n_agree"] == fq.loc[cm, "n_studies"]).all())

print("\n" + "=" * 62)
if fails:
    print(f"{len(fails)} CHECK(S) FAILED -- do not hand these files over:")
    for f in fails:
        print(f"  - {f}")
else:
    print("ALL CHECKS PASSED -- the files are internally consistent and")
    print("agree with the pipeline outputs they were derived from.")
print("=" * 62)
