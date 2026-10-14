"""
paper2_task8_final_ranking.py
-----------------------------
Paper 2, Task 8: final target and drug ranking, with a per-candidate evidence
summary.

WHAT THE PLAN ASKS FOR
"Final evidence chain: Fibrosis progression evidence + fibrosis specificity +
F0-F4 trajectory evidence + pathway/biological-process evidence +
knowledge-graph relationships + drug-target mechanism + transcriptomic
drug-reversal evidence -> prioritized therapeutic hypotheses.

The final prioritization should explicitly preserve the Paper 1 biological
hierarchy... For each leading candidate, provide an auditable evidence summary
showing which of these layers support or contradict the candidate and where
evidence is missing."

And: "Report how many final drug candidates are supported by the shortlist
versus only by broader progression evidence."

And, finally: "Unless supported by experimental or clinical validation, the
final output should be described as therapeutic hypotheses or prioritized
candidate relationships, not as proven anti-fibrotic treatments."

SIX LAYERS, NOT SEVEN
The mentor's instruction of 13 October 2026 -- "repurposing not reversal",
"focus only on the knowledge graph" -- puts the transcriptomic reversal layer
out of scope. It is carried in the evidence summary as a row that reads
"out of scope", because a layer the plan named and the paper did not use should
be visible rather than quietly dropped.

DRUGS ARE RANKED BY THEIR BEST TARGET, NOT BY HOW MANY THEY HIT
The obvious rule is to sum target scores over everything a drug touches. That
rewards promiscuity, and three tasks have already measured the damage: Task 4
found coverage NEGATIVELY correlated with coherence (rho = -0.268) and its raw
ranking led with zinc salts and one scattergun kinase inhibitor; Task 5 found
DWPC promoting proteasome and tubulin binders because complex subunits share
annotations.

So the primary key is the single best-supported target a drug has. A drug that
hits one excellent target outranks one that grazes forty mediocre ones. The
count is kept as a reported column, never as the sort key.

HOW CANDIDATES ARE SCOPED
To fibrosis-associated genes. The 2,377 inflammation-only genes are scored on
two components (Task 6) and carry no trajectory, pathway or tier evidence, so a
candidate resting on them is supported by strictly less than one resting on the
fibrosis set. They are reported separately rather than mixed in.

Usage:
    uv run --with pandas --with numpy --with openpyxl python scripts/paper2_task8_final_ranking.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables

SCORES = "Paper2_Results/Task6/task6_target_scores.csv"
STABLE = "Paper2_Results/Task6/task6_stable_core.csv"
ACTION = "Paper2_Results/Task7/task7_action_direction_evidence.csv"
COVERAGE = "Paper2_Results/Task4/task4_drug_coverage.csv"
PAPER1 = "Paper1_HighConfidence/11_final_all_3845_genes.csv"
SHORTLIST = "Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv"
OUT_DIR = "Paper2_Results/Task8"

TOP_CANDIDATES = 30

# The plan's evidence chain, in the hierarchy it specifies.
LAYERS = [
    ("L1 progression association", "P"),
    ("L2 fibrosis specificity", "F"),
    ("L3 trajectory / stage transition", "T"),
    ("L4 pathway / process context", "B"),
    ("L5 knowledge-graph relationship", "K"),
    ("L6 drug-target mechanism", None),       # from Task 7
    ("L7 transcriptomic reversal", None),     # out of scope, 13 Oct 2026
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sup = SupportingTables(OUT_DIR, "task8")

    scores = pd.read_csv(SCORES)
    action = pd.read_csv(ACTION)
    # ONE reversal column across the paper. Task 6's K reads Task 7's
    # trajectory-aware class, so this must read the same one: a relationship
    # whose association direction disagrees with its F4 - F0 endpoints is held
    # at ambiguous there and cannot count as supporting evidence here.
    REVERSAL = ("reversal_class_with_trajectory"
                if "reversal_class_with_trajectory" in action.columns
                else "reversal_class")
    action["reversal_class"] = action[REVERSAL]
    print(f"reversal evidence read from {REVERSAL}")
    cover = pd.read_csv(COVERAGE)
    p1 = pd.read_csv(PAPER1)
    shortlist = set(pd.read_csv(SHORTLIST).Gene.dropna())
    tier1 = set(p1.loc[p1.Tier.astype(str).str.startswith("Tier 1"), "Gene"])
    print(f"Paper 1 shortlist: {len(shortlist)} genes | Tier 1: {len(tier1)} genes")

    # ---- final TARGET ranking ---------------------------------------------
    stable = pd.read_csv(STABLE)[["Gene", "top50_frequency"]]
    targets = (scores.merge(stable, on="Gene", how="left")
                     .sort_values(["progression_class", "rank_in_class"]))
    targets["in_paper1_shortlist"] = targets.Gene.isin(shortlist)
    targets["in_paper1_tier1"] = targets.Gene.isin(tier1)
    # Task 6 found exact top-N indefensible; bands are what survives.
    targets["rank_band"] = pd.cut(
        targets.rank_in_class, [0, 25, 100, 500, np.inf],
        labels=["top 25", "26-100", "101-500", "500+"])
    targets.to_csv(f"{OUT_DIR}/task8_final_target_ranking.csv", index=False)

    # ---- final DRUG ranking -----------------------------------------------
    fib = scores[scores.in_fibrosis_starting_set].set_index("Gene")
    a = action[action.Gene.isin(fib.index)].copy()
    a["target_score"] = a.Gene.map(fib.TargetScore)

    best = (a.sort_values("target_score", ascending=False)
             .groupby(["Drug", "Drug_ID"], as_index=False)
             .agg(best_target=("Gene", "first"),
                  best_target_score=("target_score", "max"),
                  n_targets=("Gene", "nunique"),
                  n_tier1_targets=("Gene", lambda s: len(set(s) & tier1)),
                  n_shortlist_targets=("Gene", lambda s: len(set(s) & shortlist)),
                  n_mechanism_consistent=("reversal_class",
                                          lambda s: int((s == "reversal-consistent").sum())),
                  n_mechanism_inconsistent=("reversal_class",
                                            lambda s: int((s == "reversal-inconsistent").sum())),
                  n_mechanism_unknown=("reversal_class",
                                       lambda s: int((s == "unknown").sum()))))

    cov = cover.set_index("Drug")
    best["coherence"] = best.Drug.map(cov.dominant_class_fraction)
    best["specificity_lower95"] = best.Drug.map(cov.progression_fraction_lower95)
    # A drug absent from Task 4's coverage table has never been judged, and
    # defaulting it to "fine" would let an unassessed entity into the candidate
    # list unflagged. Every ranked drug reaches a progression gene, so every one
    # of them must be there; if that stops being true the run should say so.
    best["likely_non_therapeutic"] = best.Drug.map(cov.likely_non_therapeutic)
    unjudged = best[best.likely_non_therapeutic.isna()]
    if len(unjudged):
        raise SystemExit(
            f"{len(unjudged)} ranked drugs are missing from "
            f"{COVERAGE} and cannot be screened: "
            f"{', '.join(unjudged.Drug.head(5))}")
    best["likely_non_therapeutic"] = best.likely_non_therapeutic.astype(bool)

    # Primary key is the best target a drug has. 51 drugs tie at the maximum,
    # so the tie-break decides the whole top of the list and has to be chosen
    # as carefully as the key itself.
    #
    # An earlier version broke ties on the NUMBER of shortlist and Tier-1
    # targets, which put FOSTAMATINIB (82 targets, coherence 0.34) above
    # NINTEDANIB (6 targets, coherence 0.43) -- the promiscuity bias that
    # Tasks 4 and 5 measured, re-entering through the back door. Counts are
    # now reported and never sorted on.
    #
    # Ties break on quality instead: coherence, then the RATE at which a drug's
    # mechanism agrees with the direction of travel. Drugs sharing a
    # best_target_score are one BAND, and order within a band is weakly
    # determined -- Task 6 found exact ranks indefensible even with a single
    # continuous score.
    mech_total = best.n_mechanism_consistent + best.n_mechanism_inconsistent
    best["mechanism_consistent_rate"] = (
        best.n_mechanism_consistent / mech_total.replace(0, np.nan)).round(3)
    best = best.sort_values(
        ["best_target_score", "coherence", "mechanism_consistent_rate"],
        ascending=False, na_position="last").reset_index(drop=True)
    best.insert(0, "rank", np.arange(1, len(best) + 1))
    best.insert(1, "score_band",
                best.best_target_score.rank(method="dense", ascending=False)
                    .astype(int))
    best.to_csv(f"{OUT_DIR}/task8_final_drug_ranking.csv", index=False)

    candidates = best[~best.likely_non_therapeutic].head(TOP_CANDIDATES).copy()
    candidates.to_csv(f"{OUT_DIR}/task8_leading_candidates.csv", index=False)

    # ---- how much of the candidate list the tie-break decides -------------
    # Band 1 holds more drugs than the list has places, so the tie-break does
    # not merely order the top -- it chooses who is in it. Two defensible rules
    # exist and they disagree:
    #
    #   coherence           1.000 automatically for a one-target drug, so it
    #                       rewards a thin record (Task 4, limitation 9e)
    #   Wilson lower bound  tightens with the denominator, so it rewards a drug
    #                       with many targets -- the promiscuity Tasks 4 and 5
    #                       measured
    #
    # Neither is justified by anything this project measured, so both orderings
    # are reported and the overlap is stated rather than one being presented as
    # the answer. What is stable across them is the claim worth making.
    eligible = best[~best.likely_non_therapeutic]
    alt = eligible.sort_values(
        ["best_target_score", "specificity_lower95", "coherence"],
        ascending=False, na_position="last").head(TOP_CANDIDATES)
    overlap = len(set(candidates.Drug_ID) & set(alt.Drug_ID))
    band1 = int((best.score_band == 1).sum())
    band1_ok = int(((best.score_band == 1) & ~best.likely_non_therapeutic).sum())
    tie = pd.DataFrame([{
        "band_1_drugs": band1,
        "band_1_not_flagged": band1_ok,
        "places_in_candidate_list": TOP_CANDIDATES,
        "tie_break_decides_membership": "yes" if band1_ok > TOP_CANDIDATES else "no",
        "primary_tie_break": "coherence, then mechanism-consistent rate",
        "alternative_tie_break": "Wilson lower bound on progression fraction",
        "candidates_shared_by_both": overlap,
        "targets_primary": "; ".join(sorted(candidates.best_target.unique())),
        "targets_alternative": "; ".join(sorted(alt.best_target.unique())),
    }])
    tie.to_csv(f"{OUT_DIR}/task8_tiebreak_sensitivity.csv", index=False)
    sup.add("candidates_under_alternative_tiebreak",
            alt[["rank", "Drug", "best_target", "n_targets", "coherence",
                 "specificity_lower95", "mechanism_consistent_rate"]])
    print("")
    print(f"TIE-BREAK SENSITIVITY -- band 1 holds {band1_ok} eligible drugs for "
          f"{TOP_CANDIDATES} places")
    print(f"   the two orderings share {overlap} of {TOP_CANDIDATES} candidates")
    print(f"   targets reached are the same either way: "
          f"{', '.join(sorted(candidates.best_target.unique()))}")

    # ---- auditable evidence summary, per leading candidate ----------------
    rows = []
    for _, c in candidates.iterrows():
        g = c.best_target
        gs = fib.loc[g]
        pair = a[(a.Drug == c.Drug) & (a.Gene == g)]
        mech = pair.reversal_class.iloc[0] if len(pair) else "unknown"
        for layer, comp in LAYERS:
            if layer.startswith("L7"):
                verdict, detail = "out of scope", (
                    "transcriptomic reversal ruled out 13 Oct 2026 "
                    "(repurposing not reversal; knowledge graph only)")
            elif layer.startswith("L6"):
                # Any label starting "ambiguous" is ambiguous -- the
                # trajectory rule emits "ambiguous - rho and stage endpoints
                # disagree", and matching that on a literal key would send
                # contradictory evidence to "missing", which a reader takes as
                # "nothing recorded" rather than "the record disagrees".
                if str(mech).startswith("ambiguous"):
                    verdict = "ambiguous"
                else:
                    verdict = {"reversal-consistent": "supports",
                               "reversal-inconsistent": "contradicts",
                               }.get(mech, "missing")
                detail = f"{pair.Drug_action.iloc[0] if len(pair) else '?'} / {mech}"
            else:
                v = gs[comp]
                if pd.isna(v):
                    verdict, detail = "missing", "component undefined for this class"
                else:
                    verdict = ("supports" if v >= 0.75 else
                               "partial" if v > 0 else "does not support")
                    detail = f"{comp} = {v:.2f}"
            rows.append({"rank": c["rank"], "drug": c.Drug,
                         "best_target": g, "layer": layer,
                         "verdict": verdict, "detail": detail})
    evidence = pd.DataFrame(rows)
    evidence.to_csv(f"{OUT_DIR}/task8_evidence_summary.csv", index=False)
    # The summary has one block per candidate, but candidates collapse onto a
    # couple of targets, so L1-L5 repeat those targets' verdicts many times
    # over. Counting layer verdicts across 30 rows reads as 30 independent
    # evidence chains; it is not, and the file says how many distinct ones
    # there are.
    n_t = candidates.best_target.nunique()
    print(f"evidence summary: {len(candidates)} candidates, {n_t} distinct "
          f"targets -- layers L1-L5 describe the TARGET, so they carry "
          f"{n_t} distinct verdicts, not {len(candidates)}")

    # ---- shortlist support, which the plan asks for by name ---------------
    sup_rows = []
    for label, sel in [("all ranked drugs", best),
                       ("named drugs only", best[~best.likely_non_therapeutic]),
                       (f"top {TOP_CANDIDATES} candidates", candidates)]:
        sup_rows.append({
            "set": label, "drugs": len(sel),
            "supported_by_paper1_shortlist": int((sel.n_shortlist_targets > 0).sum()),
            "supported_by_tier1_only": int(((sel.n_shortlist_targets == 0)
                                            & (sel.n_tier1_targets > 0)).sum()),
            "broader_progression_evidence_only":
                int(((sel.n_shortlist_targets == 0)
                     & (sel.n_tier1_targets == 0)).sum()),
        })
    support = pd.DataFrame(sup_rows)
    support.to_csv(f"{OUT_DIR}/task8_shortlist_support.csv", index=False)

    sup.add("evidence_verdict_counts",
            evidence.pivot_table(index="layer", columns="verdict",
                                 values="drug", aggfunc="count",
                                 fill_value=0).reset_index())
    sup.add("inflammation_only_targets",
            targets[targets.progression_class == "inflammation-only"]
            .nsmallest(25, "rank_in_class")[
                ["Gene", "TargetScore", "rank_in_class", "P", "K"]])
    sup.write()

    # ---- report -------------------------------------------------------------
    print("")
    print(f"drugs ranked: {len(best):,}  ({int(best.likely_non_therapeutic.sum())} flagged)")
    print("")
    nb = int((best.score_band == 1).sum())
    print(f"TOP CANDIDATES -- {nb} drugs tie in band 1; "
          "within a band the order is weakly determined")
    print(candidates.head(15)[
        ["rank", "score_band", "Drug", "best_target", "best_target_score",
         "coherence", "mechanism_consistent_rate", "n_targets",
         "n_shortlist_targets"]
    ].to_string(index=False))
    print("")
    print("SHORTLIST SUPPORT (the plan asks for this explicitly)")
    print(support.to_string(index=False))
    print("")
    print("EVIDENCE LAYERS across the leading candidates")
    print(evidence.pivot_table(index="layer", columns="verdict", values="drug",
                               aggfunc="count", fill_value=0).to_string())
    for f in ["task8_final_target_ranking.csv", "task8_final_drug_ranking.csv",
              "task8_leading_candidates.csv", "task8_evidence_summary.csv",
              "task8_shortlist_support.csv", "task8_tiebreak_sensitivity.csv"]:
        print(f"wrote {OUT_DIR}/{f}")


if __name__ == "__main__":
    main()
