"""
paper2_task6_target_score.py
----------------------------
Paper 2, Task 6: the target-prioritisation framework.

WHAT THE PLAN ASKS FOR
"Paper 2 should first rank therapeutic targets and only then rank drugs. Define
a transparent target-scoring framework now...

    TargetScore(g) = w1*P(g) + w2*F(g) + w3*T(g) + w4*K(g) + w5*B(g)

...P should incorporate fibrosis association strength/significance and
direction; F should distinguish fibrosis-only from shared/inflammation-only
genes; T should incorporate the F0-F4 trajectory cluster and, where
appropriate, stage-transition evidence; B should incorporate the Paper 1
GO/KEGG/Reactome/Hallmark results. This keeps the score traceable to the
biological analyses already performed in Paper 1."

Required outputs: a mathematical definition of every component; a plan for
normalisation and missing values; a plan for weight sensitivity. The plan also
asks for an ablation showing how rankings move when a component is removed, and
rank stability across weight perturbations, before the score is applied to
final candidates.

FOUR OF THE FIVE COMPONENTS ALREADY EXIST
Paper 1's high-confidence scoring computes P, T, X, F and B per gene, frozen as
named constants before any ranked list was inspected, with published
sensitivity. Those are reused rather than re-derived: re-deriving them would
produce a second, differently-calibrated version of work that has already been
validated, and would break the traceability the plan asks for. Only K, the
knowledge-graph component, is new to Paper 2.

K IS DELIBERATELY DEGREE-FREE
The obvious K is "how many drugs act on this gene". That is raw degree, and
every task so far has found degree misleading: Task 3 killed an apparently
significant druggability result once connectivity was matched, Task 4 found
coverage NEGATIVELY correlated with coherence, and Task 5 found raw path counts
disagreeing with DWPC at rho = 0.45 and DWPC itself promoting drugs that hit
protein complexes. So K uses two binary facts and no counts:

    K(g) = 0.5 * [a therapeutic drug acts on g]
         + 0.5 * [that drug's action opposes g's direction of travel]

A gene with one well-characterised inhibitor scores the same as one with forty.

THE MISSING-DATA PROBLEM, WHICH IS THE REAL DESIGN DECISION
Paper 1's trajectory, transition, pathway and tier work covers only the 3,845
fibrosis-associated genes. The 2,377 inflammation-only genes have none of it.
A score containing T and B therefore ranks those 2,377 last for MISSING DATA
rather than biology -- while the plan separately forbids collapsing the three
classes into one "progression" category.

Three options were available:
  (a) impute the missing components      -- rejected: invents evidence
  (b) score 0 for missing components     -- rejected: that IS the penalty above
  (c) score within class, renormalising the weights over the components that
      exist for that class

(c) is used. Each class is scored and ranked on its own, the weights are
renormalised so every class's score stays on [0,1], and the three lists are
never merged into one ranking. A gene is compared only with genes that had the
same evidence available to them.

NORMALISATION IS RANK-BASED, NOT MIN-MAX
Continuous inputs are converted to within-class percentiles. Min-max scaling
would let a single extreme rho compress everything else into the bottom of the
range, and the rho distributions are skewed.

WEIGHTS ARE NOT TUNED
Equal weights are the default, because nothing in Paper 1 or Paper 2 justifies
preferring one component over another yet, and the plan explicitly warns
against "selecting arbitrary weights solely to obtain a desired ranking". The
sensitivity analysis below is what makes that defensible: if the ranking only
holds at one weight vector, it is not a ranking.

Usage:
    uv run --with pandas --with numpy --with scipy --with openpyxl python scripts/paper2_task6_target_score.py
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables

MASTER = "Paper2_Results/Task1/Paper2_progression_genes.csv"
PAPER1 = "Paper1_HighConfidence/11_final_all_3845_genes.csv"
ACTION = "Paper2_Results/Task7/task7_action_direction_evidence.csv"
OUT_DIR = "Paper2_Results/Task6"

COMPONENTS = ["P", "F", "T", "K", "B"]
DEFAULT_W = {c: 0.2 for c in COMPONENTS}      # equal; see docstring
N_WEIGHT_SAMPLES = 2000
TOP_N = 50
SEED = 42


def pct(s):
    """Within-class percentile in [0,1]. NaN stays NaN."""
    return s.rank(pct=True, na_option="keep")


def build(master, p1, action):
    g = master.copy()

    # ---- K: two binary facts, no degree ----------------------------------
    has_drug = set(action.Gene_ID)
    consistent = set(action.loc[action.reversal_class == "reversal-consistent",
                                "Gene_ID"])
    g["K"] = 0.5 * g.Ensembl_ID.isin(has_drug) + 0.5 * g.Ensembl_ID.isin(consistent)

    # ---- P, F, T, B: Paper 1's frozen components where they exist --------
    p1 = p1.set_index("Ensembl_ID")
    g["p1_P"] = g.Ensembl_ID.map(p1.P)
    g["p1_F"] = g.Ensembl_ID.map(p1.F)
    g["p1_T"] = g.Ensembl_ID.map(p1["T"])
    g["p1_X"] = g.Ensembl_ID.map(p1.X)
    g["p1_B"] = g.Ensembl_ID.map(p1.B)

    fib = g.in_fibrosis_starting_set

    # P -- progression strength. Paper 1's P for the fibrosis set; for the
    # inflammation-only genes the same quantity on their own ladder, since they
    # have no fibrosis association to score.
    g["P"] = np.where(fib, g.p1_P / 2.0, np.nan)
    infl = ~fib
    g.loc[infl, "P"] = pct(g.loc[infl, "inflammation_rho"].abs())

    # F -- fibrosis specificity. Paper 1 scores fibrosis-only 1 and shared 0;
    # inflammation-only genes are 0 by definition, not by absence.
    g["F"] = np.where(fib, g.p1_F, 0.0)

    # T -- trajectory AND stage transition, as the plan asks. Undefined off the
    # fibrosis set: Paper 1 never clustered those genes.
    g["T"] = np.where(fib, (g.p1_T + g.p1_X) / 4.0, np.nan)

    # B -- biological/pathway evidence from Paper 1's four databases. Same.
    g["B"] = np.where(fib, g.p1_B / 2.0, np.nan)
    return g


def score(g, weights):
    """Weighted sum, with weights renormalised over the components a gene has.

    A gene is never penalised for a component its class could not have. The
    renormalisation keeps every class's score on the same [0,1] scale so the
    numbers are readable, but genes are only ever RANKED within their class.
    """
    vals = g[COMPONENTS]
    w = pd.Series(weights)[COMPONENTS]
    present = vals.notna()
    wsum = present.mul(w, axis=1).sum(axis=1)
    return vals.fillna(0).mul(w, axis=1).sum(axis=1) / wsum.replace(0, np.nan)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sup = SupportingTables(OUT_DIR, "task6")
    rng = np.random.default_rng(SEED)

    master = pd.read_csv(MASTER)
    p1 = pd.read_csv(PAPER1)
    action = pd.read_csv(ACTION)
    g = build(master, p1, action)

    # ---- component availability, the thing that drives the design ---------
    avail = (g.groupby("progression_class")[COMPONENTS]
               .apply(lambda d: d.notna().mean().round(3)).reset_index())
    print("fraction of genes with each component defined, by class:")
    print(avail.to_string(index=False))

    g["TargetScore"] = score(g, DEFAULT_W)
    g["rank_in_class"] = (g.groupby("progression_class").TargetScore
                           .rank(ascending=False, method="min"))
    out_cols = (["Gene", "Ensembl_ID", "progression_class",
                 "in_fibrosis_starting_set"] + COMPONENTS
                + ["TargetScore", "rank_in_class", "fibrosis_rho",
                   "inflammation_rho", "fibrosis_direction"])
    g.sort_values(["progression_class", "rank_in_class"])[out_cols].to_csv(
        f"{OUT_DIR}/task6_target_scores.csv", index=False)

    # ---- ablation: drop one component at a time ---------------------------
    rows = []
    base = g.TargetScore
    for drop in COMPONENTS:
        w = {c: (0.0 if c == drop else DEFAULT_W[c]) for c in COMPONENTS}
        s = score(g, w)
        for cls, sub in g.groupby("progression_class"):
            i = sub.index
            if s[i].notna().sum() < 10 or base[i].notna().sum() < 10:
                continue
            rho = stats.spearmanr(base[i], s[i], nan_policy="omit").statistic
            top_base = set(base[i].nlargest(TOP_N).index)
            top_abl = set(s[i].nlargest(TOP_N).index)
            rows.append({"component_removed": drop, "progression_class": cls,
                         "spearman_vs_full": round(float(rho), 3),
                         f"top{TOP_N}_overlap": len(top_base & top_abl),
                         f"top{TOP_N}_overlap_pct":
                             round(100 * len(top_base & top_abl) / TOP_N, 1)})
    ablation = pd.DataFrame(rows)
    ablation.to_csv(f"{OUT_DIR}/task6_ablation.csv", index=False)

    # ---- weight sensitivity: Dirichlet over the simplex -------------------
    # Sampling the whole weight simplex rather than nudging one weight at a
    # time: the question is whether the ranking survives ANY reasonable
    # weighting, not whether it survives a small perturbation of this one.
    rows = []
    for cls, sub in g.groupby("progression_class"):
        i = sub.index
        b = base[i]
        top_base = set(b.nlargest(TOP_N).index)
        rhos, overlaps = [], []
        for _ in range(N_WEIGHT_SAMPLES):
            w = dict(zip(COMPONENTS, rng.dirichlet(np.ones(len(COMPONENTS)))))
            s = score(g.loc[i], w)
            rhos.append(stats.spearmanr(b, s, nan_policy="omit").statistic)
            overlaps.append(len(top_base & set(s.nlargest(TOP_N).index)))
        rows.append({"progression_class": cls, "genes": len(sub),
                     "median_spearman": round(float(np.median(rhos)), 3),
                     "spearman_5th_pct": round(float(np.percentile(rhos, 5)), 3),
                     f"median_top{TOP_N}_retained": int(np.median(overlaps)),
                     f"top{TOP_N}_retained_5th_pct":
                         int(np.percentile(overlaps, 5))})
    sens = pd.DataFrame(rows)
    sens.to_csv(f"{OUT_DIR}/task6_weight_sensitivity.csv", index=False)

    # ---- the stable core: genes in the top N under almost any weighting ---
    rows = []
    for cls, sub in g.groupby("progression_class"):
        i = sub.index
        hits = pd.Series(0, index=i)
        for _ in range(500):
            w = dict(zip(COMPONENTS, rng.dirichlet(np.ones(len(COMPONENTS)))))
            s = score(g.loc[i], w)
            hits[s.nlargest(TOP_N).index] += 1
        frac = (hits / 500).rename("top50_frequency")
        core = (g.loc[i].join(frac).nlargest(25, "top50_frequency")
                 [["Gene", "progression_class", "TargetScore",
                   "top50_frequency"] + COMPONENTS])
        rows.append(core)
    stable = pd.concat(rows, ignore_index=True)
    stable.to_csv(f"{OUT_DIR}/task6_stable_core.csv", index=False)

    sup.add("component_availability", avail)
    sup.add("component_correlations",
            g[COMPONENTS].corr(method="spearman").round(3).reset_index())
    sup.write()

    print("")
    print("ABLATION -- how far the ranking moves when a component is removed")
    print(ablation.to_string(index=False))
    print("")
    print("WEIGHT SENSITIVITY -- 2,000 random weightings from the simplex")
    print(sens.to_string(index=False))
    print("")
    print("Top 10 fibrosis-only targets at equal weights:")
    fo = g[g.progression_class == "fibrosis-only"].nlargest(10, "TargetScore")
    print(fo[["Gene", "P", "F", "T", "K", "B", "TargetScore"]].to_string(index=False))
    for f in ["task6_target_scores.csv", "task6_ablation.csv",
              "task6_weight_sensitivity.csv", "task6_stable_core.csv"]:
        print(f"wrote {OUT_DIR}/{f}")


if __name__ == "__main__":
    main()
