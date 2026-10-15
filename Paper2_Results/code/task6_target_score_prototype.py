"""Paper 2 Task 6 — target-score design test (equal weights).

Equal weights (0.2 each), used to test that the framework in
Paper2_Results/Task6/target_score_framework.md runs end to end, and to exercise the
ablation and weight-sensitivity analyses. After Paper 1 was confirmed final, the final
ranking (Paper2_Results/Final_ranking/, code/final_ranking.py) froze equal weights;
quote final results from there.

    TargetScore(g) = w1*P + w2*F + w3*T + w4*K + w5*B      (every component in [0, 1])

Inputs: Paper 2 Tasks 1, 2, 4, 5 outputs, Paper 1 active files, and read-only Neo4j
(gene -> fibrosis-spectrum disease association scores). Password from NEO4J_PASSWORD.

    python Paper2_Results/code/task6_target_score_prototype.py
"""
import base64
import getpass
import json
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Paper2_Results" / "Task6"
OUT.mkdir(parents=True, exist_ok=True)
TAG = "equal_weights"

GENES = ROOT / "Paper2_Results/Task1/Paper2_progression_genes.csv"
ALL = ROOT / "Paper1_HighConfidence/00_all_progression_genes.csv"
MASTER = ROOT / "Paper1_HighConfidence/01_master_table.csv"
LOSO = ROOT / "Paper1_HighConfidence/10_loso_all_eligible_runs.csv"
EDGES = ROOT / "Paper2_Results/Task2/drug_gene_edges.csv"
DRUG_SCORES = ROOT / "Paper2_Results/Task5/metapath_drug_scores.csv"
TERM_GENES = ROOT / "Paper2_Results/Task5/prep/paper1_term_genes_long.csv"
LIVER = ROOT / "Paper2_Results/Task4/liver_disease_set.csv"

PK = ["ENZYME", "TRANSPORTER", "CARRIER"]
FIB_SPECTRUM = r"fatty liver|steatohepatitis|cirrhosis|fibrosis|portal hypertension|liver failure"
LAMBDA_INFL = 0.5           # P scale for inflammation-only genes (sensitivity: 0, 0.5, 1)
F_LEVELS = {"fibrosis_only": 1.0, "shared": 2 / 3, "shared_discordant": 1 / 3, "inflammation_only": 0.0}
COMPONENTS = ["P", "F", "T", "K", "B"]
EQUAL = dict.fromkeys(COMPONENTS, 0.2)
TOP_N, N_DRAWS, SEED = 50, 1000, 42


def pct(s):
    """Percentile rank in [0, 1] (average ties); NaN stays NaN."""
    return s.rank(pct=True, method="average")


def pct_pos(s):
    """Percentile rank among positive values; zeros stay 0 (no evidence = no credit)."""
    out = pd.Series(0.0, index=s.index)
    pos = s > 0
    out[pos] = s[pos].rank(pct=True, method="average")
    return out


# ------------------------------------------------------------------ gene table
g = pd.read_csv(GENES).set_index("ensembl_id")
a = pd.read_csv(ALL).set_index("ensembl_id")
m = pd.read_csv(MASTER).set_index("ensembl_id")
fib = g.progression_class != "inflammation_only"
infl = ~fib

# ------------------------------------------------------------------ P: progression evidence
loso = pd.read_csv(LOSO)
loso_sig = loso.groupby("ensembl_id").still_significant.mean()          # share of 5 leave-one-study-out runs
loso_dir = loso.groupby("ensembl_id").direction_kept.mean()
sign_fib = (np.sign(a.fibrosis_min_rho) == np.sign(a.fibrosis_max_rho)).astype(float)
sign_inf = (np.sign(a.inflammation_min_rho) == np.sign(a.inflammation_max_rho)).astype(float)

P = pd.Series(0.0, index=g.index)
D_fib = 0.5 * (0.5 + 0.5 * sign_fib[fib]) + 0.5 * (0.5 * loso_sig.reindex(g.index[fib]).fillna(0)
                                                  + 0.5 * loso_dir.reindex(g.index[fib]).fillna(0))
P[fib] = (0.5 * pct(g.fibrosis_rho[fib].abs()) + 0.2 * pct(-np.log10(g.fibrosis_q[fib])) + 0.3 * D_fib)
D_inf = 0.5 + 0.5 * sign_inf[infl]
P[infl] = LAMBDA_INFL * (0.5 * pct(g.inflammation_rho[infl].abs()) + 0.2 * pct(-np.log10(g.inflammation_q[infl]))
                         + 0.3 * D_inf)

# ------------------------------------------------------------------ F: fibrosis specificity
cls = g.progression_class.where(~g.paper1_group.str.startswith("shared_discordant"), "shared_discordant")
F = cls.map(F_LEVELS).astype(float)

# ------------------------------------------------------------------ T: trajectory + stage transition
T = pd.Series(0.0, index=g.index)                                   # structural 0 for inflammation-only
mf = m.reindex(g.index[fib])
T1 = pct(mf.delta_F0_F4.abs()) * mf.delta_agrees.astype(float)       # endpoint travel, direction-coherent
T2 = mf.membership_confidence                                        # bootstrap cluster stability
T3 = pct(-np.log10(mf.transition_q)) * mf.matched_frac_reproducible  # largest stage jump: significance x reproducibility
T[fib] = (T1 + T2 + T3) / 3

# ------------------------------------------------------------------ K: knowledge-graph evidence
e = pd.read_csv(EDGES)
pe = e[~e.Action_raw.isin(PK)].copy()
pe["clinical"] = (pe.max_phase >= 2) & ~pe.withdrawn.astype("boolean").fillna(False)
k = pd.DataFrame(index=g.index)
k["n_pharm_drugs"] = pe.groupby("Gene_ID").Drug_ID.nunique()
k["n_clinical_drugs"] = pe[pe.clinical].groupby("Gene_ID").Drug_ID.nunique()
k["multi_source"] = pe.groupby("Gene_ID").evidence_level.agg(lambda s: (s == "multi-source").any())
k["directional_drug"] = pe.groupby("Gene_ID").Action_direction.agg(lambda s: s.isin(["up", "down"]).any())
ds = pd.read_csv(DRUG_SCORES).set_index("Drug_ID")
m1f_pct = pct_pos(ds["M1f Drug→Gene→FibrosisSpectrumDisease_dns"])
pe["drug_m1f"] = pe.Drug_ID.map(m1f_pct)
k["best_drug_metapath"] = pe.groupby("Gene_ID").drug_m1f.max()

pw = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password: ")
liver = pd.read_csv(LIVER)
fib_ids = liver.loc[~liver.excluded_non_hepatic & liver.disease_name.str.contains(FIB_SPECTRUM, case=False), "disease_id"].tolist()
h = {"Authorization": "Basic " + base64.b64encode(f"neo4j:{pw}".encode()).decode(),
     "Content-Type": "application/json", "Accept": "application/json"}
body = json.dumps({"statement": """MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(x:Disease)
WHERE g.ensembl_id IN $ids AND x.node_id IN $fib
RETURN g.ensembl_id AS gene, max(r.score) AS max_score, count(x) AS n_diseases""",
                   "parameters": {"ids": g.index.tolist(), "fib": fib_ids}, "accessMode": "Read"}).encode()
res = json.load(urllib.request.urlopen(urllib.request.Request(
    "http://127.0.0.1:7474/db/neo4j/query/v2", data=body, headers=h, method="POST"), timeout=300))
assoc = pd.DataFrame(res["data"]["values"], columns=res["data"]["fields"]).set_index("gene")
k["fib_disease_assoc"] = assoc.max_score                              # OptimusKG score, already 0-1
k["n_fib_diseases"] = assoc.n_diseases
k = k.fillna(0)
K_parts = pd.DataFrame({
    "K1_drugs": pct_pos(np.log1p(k.n_pharm_drugs)),
    "K2_clinical": pct_pos(np.log1p(k.n_clinical_drugs)),
    "K3_multisource": k.multi_source.astype(float),
    "K4_directional": k.directional_drug.astype(float),
    "K5_fib_disease": k.fib_disease_assoc.clip(0, 1),
    "K6_drug_metapath": k.best_drug_metapath,
})
K = K_parts.mean(axis=1)

# ------------------------------------------------------------------ B: Paper 1 pathway / process evidence
tg = pd.read_csv(TERM_GENES)
tg = tg[~tg.group.str.startswith("inflammation_only")].dropna(subset=["ensembl_id"])
n_db = tg.groupby("ensembl_id").database.nunique().reindex(g.index).fillna(0)
n_terms = tg.groupby("ensembl_id").term.nunique().reindex(g.index).fillna(0)
B = 0.5 * n_db / 4 + 0.5 * pct_pos(np.log1p(n_terms))
paper1_ndb = m.n_databases.reindex(g.index[fib])
b_agree = float((n_db[fib] == paper1_ndb).mean())

comp = pd.DataFrame({"P": P, "F": F, "T": T, "K": K, "B": B})
assert comp.notna().all().all() and comp.min().min() >= 0 and comp.max().max() <= 1
# Component definitions are fixed by the framework; only the weights were left open.
# The final ranking (Final_ranking/) reads these components.
(g[["Gene", "progression_class", "paper1_group", "trajectory_cluster", "fibrosis_direction",
    "inflammation_direction", "Tier", "in_shortlist"]].join(comp.round(6)).join(K_parts.round(6))
 .to_csv(OUT / "target_components.csv"))


def score(c, w):
    return sum(c[x] * w[x] for x in COMPONENTS) / sum(w.values())


def ranks(s):
    return s.rank(ascending=False, method="min")


full = score(comp, EQUAL)
r_full = ranks(full)
top_full = set(r_full.nsmallest(TOP_N).index)
shortlist = set(g.index[g.in_shortlist])

# ------------------------------------------------------------------ ablation (drop one component, renormalise)
abl = []
for drop in [None] + COMPONENTS + ["K and B (knowledge-free)"]:
    if drop is None:
        w, label = EQUAL, "full (equal weights)"
    elif drop.startswith("K and B"):
        w, label = {x: (0.0 if x in "KB" else 1 / 3) for x in COMPONENTS}, "without K and B"
    else:
        w, label = {x: (0.0 if x == drop else 0.25) for x in COMPONENTS}, f"without {drop}"
    s = score(comp, w)
    r = ranks(s)
    abl.append({"variant": label, "spearman_vs_full": round(spearmanr(r_full, r)[0], 4),
                "kendall_vs_full": round(kendalltau(r_full, r)[0], 4),
                f"top{TOP_N}_overlap": len(top_full & set(r.nsmallest(TOP_N).index)),
                "median_abs_rank_shift": float((r - r_full).abs().median()),
                "shortlist_median_rank": float(r[list(shortlist)].median()),
                "shortlist_in_top_500": int((r[list(shortlist)] <= 500).sum())})
abl = pd.DataFrame(abl)
abl.to_csv(OUT / f"ablation_{TAG}.csv", index=False)

# ------------------------------------------------------------------ Dirichlet weight sensitivity
rng = np.random.default_rng(SEED)
C = comp[COMPONENTS].values
sens_rows = []
summ = {}
for alpha in (1.0, 10.0):
    W = rng.dirichlet([alpha] * 5, size=N_DRAWS)
    R = np.empty((N_DRAWS, len(comp)))
    rho = np.empty(N_DRAWS)
    ov = np.empty(N_DRAWS)
    for i, w in enumerate(W):
        r = pd.Series(C @ w, index=comp.index).rank(ascending=False, method="min")
        R[i] = r.values
        rho[i] = spearmanr(r_full, r)[0]
        ov[i] = len(top_full & set(r.nsmallest(TOP_N).index))
    p_top = (R <= TOP_N).mean(axis=0)
    summ[alpha] = pd.DataFrame({f"median_rank_a{alpha:g}": np.median(R, axis=0),
                                f"rank_p05_a{alpha:g}": np.percentile(R, 5, axis=0),
                                f"rank_p95_a{alpha:g}": np.percentile(R, 95, axis=0),
                                f"p_top{TOP_N}_a{alpha:g}": p_top}, index=comp.index)
    sens_rows.append({"dirichlet_alpha": alpha, "draws": N_DRAWS,
                      "median_spearman_vs_equal": round(float(np.median(rho)), 4),
                      "p05_spearman_vs_equal": round(float(np.percentile(rho, 5)), 4),
                      f"median_top{TOP_N}_overlap": float(np.median(ov)),
                      f"genes_in_top{TOP_N}_in_>=80%_of_draws": int((p_top >= 0.8).sum()),
                      f"genes_ever_in_top{TOP_N}": int((p_top > 0).sum())})
sens = pd.DataFrame(sens_rows)
sens.to_csv(OUT / f"weight_sensitivity_{TAG}.csv", index=False)

# lambda sensitivity for inflammation-only P
lam_rows = []
for lam in (0.0, 0.5, 1.0):
    P2 = P.copy()
    P2[infl] = P[infl] / LAMBDA_INFL * lam
    r = ranks(score(comp.assign(P=P2), EQUAL))
    lam_rows.append({"lambda_inflammation_only": lam, "spearman_vs_full": round(spearmanr(r_full, r)[0], 4),
                     f"top{TOP_N}_overlap": len(top_full & set(r.nsmallest(TOP_N).index)),
                     f"inflammation_only_in_top{TOP_N}": int(infl[r.nsmallest(TOP_N).index].sum())})
pd.DataFrame(lam_rows).to_csv(OUT / f"lambda_sensitivity_{TAG}.csv", index=False)

# ------------------------------------------------------------------ outputs
out = g[["Gene", "progression_class", "paper1_group", "trajectory_cluster", "Tier", "in_shortlist"]].join(comp)
out = out.join(K_parts.round(4)).join(k[["n_pharm_drugs", "n_clinical_drugs", "n_fib_diseases"]])
out["TargetScore_equal_weights"] = full.round(4)
out["rank_equal_weights"] = r_full.astype(int)
out = out.join(summ[1.0].round(1))
out["paper1_HighConfidenceScore"] = m.HighConfidenceScore.reindex(out.index)
out = out.sort_values("rank_equal_weights")
out.insert(0, "STATUS", "Task 6 design test (equal weights); final ranking: Final_ranking/")
out.to_csv(OUT / f"target_scores_{TAG}.csv")

corr = comp.corr(method="spearman").round(3)
corr.to_csv(OUT / f"component_correlations_{TAG}.csv")
p1_rho = spearmanr(full[fib], m.HighConfidenceScore.reindex(g.index[fib]))[0]


def md(df, idx=False):
    d = df.reset_index() if idx else df
    lines = ["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * d.shape[1]]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in d.values]
    return "\n".join(lines)


desc = comp.describe().T[["mean", "50%", "min", "max"]].round(3)
desc["share of genes = 0"] = (comp == 0).mean().round(3)
top10 = out.head(10)[["Gene", "progression_class", "trajectory_cluster", "P", "F", "T", "K", "B", "TargetScore_equal_weights"]].round(3)
report = f"""# Task 6 design test run (equal weights)

> **Design test with equal weights (0.2 each).** After Paper 1 was confirmed final, equal weights were frozen for the final ranking; the final, stability-checked results are in `Final_ranking/`.

Gene set: corrected Paper 1 union of **{len(g):,} genes** (the plan's 4,692 was the pre-correction count). Script: `Paper2_Results/code/task6_target_score_prototype.py`.

## Did it run?
Yes. All five components are in [0, 1] for all {len(g):,} genes, with no missing values after the documented rules. Paper 1 `n_databases` is reproduced for {100 * b_agree:.1f}% of fibrosis genes by the B input (from the Task 5 prep term lists).

## Component distributions
{md(desc, idx=True)}

## Component correlations (Spearman)
{md(corr, idx=True)}

## Ablation (drop one component; remaining weights renormalised)
{md(abl)}

## Weight sensitivity (Dirichlet, {N_DRAWS:,} draws, seed {SEED})
{md(sens)}

α = 1: weights anywhere on the simplex (stress test). α = 10: weights near equal (plausible range).

## λ sensitivity (P scale for inflammation-only genes)
{md(pd.DataFrame(lam_rows))}

## Sanity check against Paper 1
Spearman between this prototype score and Paper 1's HighConfidenceScore (fibrosis genes): **{p1_rho:.3f}**. Expected to be positive but not 1: P, T and B reuse Paper 1 evidence (partly circular), while K is new and F is graded differently.

## First 10 genes under equal weights (design test; see Final_ranking/ for the final lists)
{md(top10)}
"""
(OUT / "design_test_report.md").write_text(report, encoding="utf-8")
print(report)
