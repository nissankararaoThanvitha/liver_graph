"""
paper2_task5_transition_convergence.py
--------------------------------------
Paper 2, Task 5 addendum: do candidate drugs converge on the transition Paper 1
identified as molecularly important?

WHY THIS EXISTS
The plan asks, inside Task 5: "Also extend the MetaPath analysis using the
statistically supported stage-transition genes and the major fibrosis-associated
pathways/processes identified in Paper 1. In particular, test whether candidate
drugs converge on genes involved in the transitions identified as molecularly
important in Paper 1."

The first half was done -- MP7 restricts metapath targets to the 2,568 genes
with a substantial stage transition. The second half, the convergence test, was
not: `Largest_transition` appears nowhere in paper2_task5_metapaths.py. This
closes that.

WHICH TRANSITION IS "MOLECULARLY IMPORTANT"
Paper 1 Task 3: with every transition given equal statistical power, F3->F4
produced a median of 311 substantially changing genes against 0 to 2 for the
earlier ones, and roughly twice the typical effect size. The fall into cirrhosis
is the event. So the question is whether drugs concentrate on genes whose
largest change happens there.

THE TEST
Each fibrosis-associated gene carries the transition at which it moves most.
For each transition, compare the share of drug-connected genes against the
share of genes overall -- a hypergeometric test, BH-corrected across the four
transitions. Convergence would mean drugs reach F3->F4 genes more often than
their number alone predicts.

A null result is the expected one and is worth stating: drug annotation has no
reason to know when in a disease a gene moves.

Usage:
    uv run --with pandas --with numpy --with scipy python scripts/paper2_task5_transition_convergence.py
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables

PAPER1 = "Paper1_HighConfidence/11_final_all_3845_genes.csv"
ACTION = "Paper2_Results/Task7/task7_action_direction_evidence.csv"
CANDIDATES = "Paper2_Results/Task8/task8_leading_candidates.csv"
OUT_DIR = "Paper2_Results/Task5"


def main():
    sup = SupportingTables(OUT_DIR, "task5")
    p1 = pd.read_csv(PAPER1)
    act = pd.read_csv(ACTION)
    cand = pd.read_csv(CANDIDATES)

    genes = p1[["Ensembl_ID", "Gene", "Largest_transition", "Tier"]].dropna(
        subset=["Largest_transition"])
    drugged = set(act.Gene_ID)
    genes["drug_connected"] = genes.Ensembl_ID.isin(drugged)

    total, total_hit = len(genes), int(genes.drug_connected.sum())
    rows = []
    for tr, sub in genes.groupby("Largest_transition"):
        k, n = int(sub.drug_connected.sum()), len(sub)
        # P(>= k drug-connected among n draws) from the whole fibrosis set
        p = stats.hypergeom.sf(k - 1, total, total_hit, n)
        rows.append({"transition": tr, "genes": n,
                     "drug_connected": k,
                     "percent": round(100 * k / n, 1),
                     "overall_percent": round(100 * total_hit / total, 1),
                     "enrichment": round((k / n) / (total_hit / total), 3),
                     "hypergeom_p": p})
    t = pd.DataFrame(rows).sort_values("transition")
    t["q_BH"] = stats.false_discovery_control(t.hypergeom_p.values)
    t["converges"] = np.where((t.q_BH < 0.05) & (t.enrichment > 1), "yes", "no")
    t["hypergeom_p"] = t.hypergeom_p.map(lambda v: f"{v:.3f}")
    t["q_BH"] = t.q_BH.map(lambda v: f"{v:.3f}")
    t.to_csv(f"{OUT_DIR}/task5_transition_convergence.csv", index=False)

    # where the Task 8 leading candidates actually land
    tgt = genes[genes.Gene.isin(set(cand.best_target))]
    sup.add("candidate_targets_by_transition",
            tgt[["Gene", "Largest_transition", "Tier"]])
    sup.write()

    print("Do drugs converge on the transition Paper 1 found most important?")
    print("(Paper 1 Task 3: F3->F4, 311 genes under equal power vs 0-2)")
    print("")
    print(t.to_string(index=False))
    print("")
    print("targets of the Task 8 leading candidates:")
    print(tgt[["Gene", "Largest_transition"]].to_string(index=False))
    print(f"\nwrote {OUT_DIR}/task5_transition_convergence.csv")


if __name__ == "__main__":
    main()
