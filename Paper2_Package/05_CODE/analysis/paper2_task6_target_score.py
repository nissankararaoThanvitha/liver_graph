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
DEGREES = "Paper2_Results/Task3/task3_gene_degrees.csv"
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

    # ---- K: two binary facts, no drug COUNT ------------------------------
    # K deliberately carries no count of drugs, so a gene with one
    # characterised inhibitor scores the same as one with forty. That is not
    # the same as being independent of annotation: a better-studied gene has
    # more chances to satisfy either binary condition, and K_degree_sensitivity
    # in the supporting workbook measures how much (Spearman 0.25 against
    # non-drug degree).
    #
    # "Has a therapeutic drug" must mean a drug, not a mineral salt. Task 7
    # carries the entity flag; honouring it removes K credit from the genes
    # whose only drug is zinc chloride, ATP or an unnamed accession.
    if "non_therapeutic_entity" in action.columns:
        usable = action[~action.non_therapeutic_entity.astype(bool)]
        dropped = action.Gene_ID.nunique() - usable.Gene_ID.nunique()
        print(f"K: {dropped} genes lose drug credit (non-therapeutic entities only)")
    else:
        raise SystemExit("Task 7 table has no non_therapeutic_entity column; "
                         "re-run paper2_task7_action_direction.py")
    has_drug = set(usable.Gene_ID)
    # Honour Task 7's trajectory rule where it exists. A relationship whose
    # association direction and stage endpoints disagree is held at ambiguous
    # there, and crediting it here would make that rule decorative.
    rc = ("reversal_class_with_trajectory"
          if "reversal_class_with_trajectory" in usable.columns
          else "reversal_class")
    consistent = set(usable.loc[usable[rc] == "reversal-consistent", "Gene_ID"])
    print(f"K: consistency read from {rc}")
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


STABLE_MIN_FREQUENCY = 0.80      # the stated definition of "stable core"
TIE_TOLERANCE = 1e-12            # scores this close are the same score


def top_set(s, n=TOP_N):
    """Indices in the top n BY SCORE, including everyone tied at the cutoff.

    `nlargest(n)` resolves ties by row order, so two genes with identical
    scores are separated by where they happen to sit in the file. At the
    equal-weight cutoff 105 shared genes carry the cutoff score and 47
    fibrosis-only genes do, so that choice is not a rounding detail: shuffling
    the rows moves top-50 membership. Admitting the whole tied band instead
    makes membership a property of the scores and nothing else, at the cost of
    a set that is sometimes larger than n -- which is the honest shape of the
    answer.
    """
    s = s.dropna()
    if not len(s):
        return set()
    if len(s) <= n:
        return set(s.index)
    cut = s.nlargest(n).iloc[-1]
    return set(s[s >= cut - TIE_TOLERANCE].index)


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
            top_base = top_set(base[i])
            top_abl = top_set(s[i])
            # A component that is constant inside a class carries no ordering
            # information there, so removing it CANNOT reorder the class. Any
            # movement reported for such a component is tie-breaking noise, not
            # an effect, and saying so is the point of the column.
            vals = g.loc[i, drop].dropna()
            constant = bool(len(vals)) and float(vals.max() - vals.min()) <= TIE_TOLERANCE
            rows.append({"component_removed": drop, "progression_class": cls,
                         "constant_within_class": "yes" if constant else "no",
                         "can_reorder_within_class": "no" if constant else "yes",
                         "spearman_vs_full": 1.0 if constant else round(float(rho), 3),
                         f"top{TOP_N}_band_full": len(top_base),
                         f"top{TOP_N}_band_ablated": len(top_abl),
                         f"top{TOP_N}_overlap": len(top_base & top_abl),
                         f"top{TOP_N}_overlap_pct":
                             round(100 * len(top_base & top_abl)
                                   / max(len(top_base), 1), 1)})
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
        top_base = top_set(b)
        rhos, overlaps = [], []
        for _ in range(N_WEIGHT_SAMPLES):
            w = dict(zip(COMPONENTS, rng.dirichlet(np.ones(len(COMPONENTS)))))
            s = score(g.loc[i], w)
            rhos.append(stats.spearmanr(b, s, nan_policy="omit").statistic)
            overlaps.append(len(top_base & top_set(s)))
        rows.append({"progression_class": cls, "genes": len(sub),
                     f"top{TOP_N}_band_at_equal_weights": len(top_base),
                     "median_spearman": round(float(np.median(rhos)), 3),
                     "spearman_5th_pct": round(float(np.percentile(rhos, 5)), 3),
                     f"median_top{TOP_N}_retained": int(np.median(overlaps)),
                     f"top{TOP_N}_retained_5th_pct":
                         int(np.percentile(overlaps, 5))})
    sens = pd.DataFrame(rows)
    sens.to_csv(f"{OUT_DIR}/task6_weight_sensitivity.csv", index=False)

    # ---- the stable core: genes in the top N under almost any weighting ---
    # The definition is a THRESHOLD, not a quota: a gene is in the stable core
    # when it reaches the top band under at least 80% of sampled weightings.
    # Taking the 25 highest frequencies per class instead would fill the file
    # to a fixed length whatever the frequencies were, so a class with no
    # stable genes would still appear to have 25 of them.
    #
    # It uses the same 2,000 weight samples as the sensitivity summary, so the
    # two tables describe the same experiment.
    rows, counts = [], []
    for cls, sub in g.groupby("progression_class"):
        i = sub.index
        hits = pd.Series(0, index=i)
        for _ in range(N_WEIGHT_SAMPLES):
            w = dict(zip(COMPONENTS, rng.dirichlet(np.ones(len(COMPONENTS)))))
            hits[list(top_set(score(g.loc[i], w)))] += 1
        frac = (hits / N_WEIGHT_SAMPLES).rename("top50_frequency")
        joined = g.loc[i].join(frac)
        core = (joined[joined.top50_frequency >= STABLE_MIN_FREQUENCY]
                .sort_values("top50_frequency", ascending=False)
                [["Gene", "progression_class", "TargetScore",
                  "top50_frequency"] + COMPONENTS])
        counts.append({"progression_class": cls,
                       "genes_in_class": len(sub),
                       "weight_samples": N_WEIGHT_SAMPLES,
                       "threshold": STABLE_MIN_FREQUENCY,
                       "genes_meeting_threshold": len(core),
                       "max_frequency": round(float(joined.top50_frequency.max()), 3)})
        rows.append(core)
    stable = pd.concat(rows, ignore_index=True)
    stable.to_csv(f"{OUT_DIR}/task6_stable_core.csv", index=False)
    core_counts = pd.DataFrame(counts)
    sup.add("stable_core_counts", core_counts)
    print("")
    print(f"STABLE CORE -- top-{TOP_N} band under >= "
          f"{STABLE_MIN_FREQUENCY:.0%} of {N_WEIGHT_SAMPLES:,} weightings")
    print(core_counts.to_string(index=False))

    # ---- K against annotation degree -------------------------------------
    # K carries no drug COUNT, which is what "degree-free" was meant to claim,
    # but it is not independent of how well studied a gene is: a gene with more
    # annotation has more chances to satisfy either of its two binary
    # conditions. Measured rather than asserted, against the same non-drug
    # degree Task 3 matched on.
    if os.path.exists(DEGREES):
        deg = pd.read_csv(DEGREES)[["Ensembl_ID", "nondrug_degree"]]
        kd = g[["Ensembl_ID", "K"]].merge(deg, on="Ensembl_ID", how="left") \
                                   .dropna(subset=["K", "nondrug_degree"])
        rho_k = stats.spearmanr(kd.K, kd.nondrug_degree)
        kd["degree_quintile"] = pd.qcut(
            kd.nondrug_degree.rank(method="first"), 5,
            labels=["Q1 least connected", "Q2", "Q3", "Q4",
                    "Q5 most connected"])
        ktab = (kd.groupby("degree_quintile", observed=True)
                  .agg(genes=("K", "size"),
                       mean_K=("K", "mean"),
                       percent_with_any_K=("K", lambda v: 100 * (v > 0).mean()),
                       median_nondrug_degree=("nondrug_degree", "median"))
                  .round(3).reset_index())
        ktab["spearman_K_vs_degree"] = round(float(rho_k.statistic), 3)
        ktab["spearman_p"] = f"{rho_k.pvalue:.2e}"
        sup.add("K_degree_sensitivity", ktab)
        print("")
        print("K vs annotation degree -- K is binary, not degree-free")
        print(ktab.to_string(index=False))

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
