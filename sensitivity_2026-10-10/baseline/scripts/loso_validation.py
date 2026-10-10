# Corrected 2026-10-10: common biopsy policy and BH across all eligible
# genes within each omitted-study run. This is internal robustness of an
# already selected set, not independent clinical or predictive validation.
"""Internal leave-one-study-out robustness of the corrected Tier1 gene set.

Use the shared equal-stage mean/otherwise biopsy1 policy. Recompute per-study
Spearman on all14,794 eligible genes; omit one of five fibrosis-staged studies;
combine Fisher p and correct BH over the full eligible family per run. Report
Tier1 direction, significance and median|rho|>=.30 retention. Discovery and
prioritisation are not refit in nested held-out prediction; this is not external
clinical validation. Direction retention follows initial consistency.
"""
import glob
import pathlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
import sys
sys.path.insert(0, str(ROOT))
from biopsy_policy import select_biopsies, expression_directory
import argparse as _argparse
import sys as _sys

_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default=None,
                 help="folder for this script's own numbered outputs")
_ap.add_argument("--results", default=None,
                 help="Paper1_Results folder to read Task2/3/4 from")
_args, _rest = _ap.parse_known_args()
_sys.argv = [_sys.argv[0]] + _rest
# These scripts used to live inside the results folder, so HERE was
# both 'where the code is' and 'where results go'. They now live in
# scripts/, so the output location has to be named rather than
# inherited from the file's own position.
HERE = (pathlib.Path(_args.out).resolve() if _args.out
        else ROOT / "Paper1_HighConfidence")
HERE.mkdir(parents=True, exist_ok=True)
RESULTS = pathlib.Path(_args.results) if _args.results else ROOT / "Paper1_Results"


TIER1 = HERE / "09a_tier1_genes.csv"
CLINICAL = ROOT / "data/graph/nodes_sample_clinical.csv"
GRAPH = expression_directory(ROOT)

Q_CUT, RHO_CUT = 0.05, 0.30   # the same bars used in steps 3 and 8


def spearman_matrix(Y, y):
    """Spearman rho of every column of Y against y, plus its p-value."""
    ry = stats.rankdata(y)
    rY = np.apply_along_axis(stats.rankdata, 0, Y)
    ry = (ry - ry.mean()) / ry.std()
    rY = (rY - rY.mean(0)) / rY.std(0)
    n = len(y)
    rho = (rY * ry[:, None]).mean(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = rho * np.sqrt((n - 2) / (1 - rho ** 2))
    return rho, 2 * stats.t.sf(np.abs(t), df=n - 2)


t1 = pd.read_csv(TIER1)
report_genes = set(t1.ensembl_id)
core_nodes = pd.read_csv(GRAPH / "nodes_gene.csv")
keep = set(core_nodes.loc[core_nodes.n_datasets == 8, "ensembl_id"])
print(f"Tier 1 genes reported: {len(report_genes):,}; BH universe: {len(keep):,}")

lab = pd.read_csv(CLINICAL, low_memory=False)
lab = select_biopsies(lab)
lab = lab[lab.fibrosis_stage.notna()]

print("\nper-study Spearman (recomputed; find_progression_genes.py keeps only "
      "the median)")
per_study = {}
for path in sorted(glob.glob(str(GRAPH / "edges_GSE*.csv"))):
    gse = Path(path).stem[6:]
    l = lab[lab.dataset_id == gse]
    if l.empty:
        continue
    e = pd.concat(
        [ch[ch.ensembl_id.isin(keep) & ch.sample_id.isin(set(l.sample_id))]
         for ch in pd.read_csv(path, usecols=["sample_id", "ensembl_id",
                                              "value_z"], chunksize=2_000_000)],
        ignore_index=True)
    if e.empty:
        continue
    e = e.merge(l[["sample_id", "patient_id", "fibrosis_stage"]], on="sample_id")
    # one row per patient: repeat biopsies must not count twice
    e = (e.groupby(["patient_id", "ensembl_id"], as_index=False)
           .agg(value_z=("value_z", "mean"), y=("fibrosis_stage", "first")))
    wide = e.pivot(index="patient_id", columns="ensembl_id", values="value_z")
    y = e.drop_duplicates("patient_id").set_index("patient_id").y.reindex(wide.index)
    wide = wide.loc[:, wide.notna().all(axis=0)]
    rho, p = spearman_matrix(wide.to_numpy(float), y.to_numpy(float))
    per_study[gse] = pd.DataFrame({"rho": rho, "p": p}, index=wide.columns)
    print(f"  {gse}: {len(wide):>4} patients, {wide.shape[1]:,} genes")

studies = sorted(per_study)
RHO = pd.DataFrame({k: per_study[k].rho for k in studies})
PV = pd.DataFrame({k: per_study[k].p for k in studies})
print(f"\n{len(studies)} studies stage fibrosis -> {len(studies)} LOSO runs "
      f"(the brief asks for 8; three studies carry no F0-F4 labels)")

full_sign = np.sign(RHO.median(axis=1))
rows = []
for left_out in studies:
    kept = [s for s in studies if s != left_out]
    r, pv = RHO[kept], PV[kept]
    med = r.median(axis=1)
    chi = -2 * np.log(pv.clip(lower=1e-300)).sum(axis=1)
    comb = pd.Series(stats.chi2.sf(chi, df=2 * pv.notna().sum(axis=1)),
                     index=pv.index)
    ok = comb.notna()
    q = pd.Series(np.nan, index=comb.index)
    q[ok] = stats.false_discovery_control(comb[ok], method="bh")
    rows.append(pd.DataFrame({
        "ensembl_id": med.index, "left_out": left_out,
        "median_rho": med.round(4).to_numpy(), "q_value": q.to_numpy(),
        "direction_kept": (np.sign(med) == full_sign).to_numpy(),
        "still_significant": (q < Q_CUT).to_numpy(),
        "still_strong": (med.abs() >= RHO_CUT).to_numpy(),
    }))
runs = pd.concat(rows, ignore_index=True)
runs.to_csv(HERE / "10_loso_all_eligible_runs.csv", index=False)
runs = runs[runs.ensembl_id.isin(report_genes)].copy()
runs.to_csv(HERE / "10_loso_runs.csv", index=False)
RHO.join(PV, lsuffix="_rho", rsuffix="_p").to_csv(HERE / "10_loso_per_study_all_eligible.csv")

n = len(studies)
summ = (runs.groupby("ensembl_id")
        .agg(loso_direction_kept=("direction_kept", "sum"),
             loso_still_significant=("still_significant", "sum"),
             loso_still_strong=("still_strong", "sum"),
             loso_min_median_rho=("median_rho", lambda s: s.abs().min()),
             loso_max_q=("q_value", "max"))
        .reset_index())
for c in ("direction_kept", "still_significant", "still_strong"):
    summ[f"R_{c}"] = summ[f"loso_{c}"].astype(str) + f"/{n}"
summ = t1[["ensembl_id", "symbol", "cluster", "direction",
           "HighConfidenceScore"]].merge(summ, on="ensembl_id")
summ.to_csv(HERE / "10_loso_summary.csv", index=False)

print(f"\nof {len(summ):,} Tier 1 genes, how many of the {n} runs each "
      f"measure survives:")
for c, note in (("direction_kept", "  <- guaranteed; all 5 studies already agree"),
                ("still_significant", ""), ("still_strong", "")):
    vc = summ[f"loso_{c}"].value_counts().sort_index(ascending=False)
    print(f"  {c}{note}")
    for k, v in vc.items():
        print(f"      {k}/{n} runs: {v:>4,} genes")
print(f"\n-> {(HERE / '10_loso_summary.csv').relative_to(ROOT)}")
print(f"-> {(HERE / '10_loso_runs.csv').relative_to(ROOT)}")
