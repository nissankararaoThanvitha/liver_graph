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

TWO TESTS, ANSWERING TWO DIFFERENT QUESTIONS

TEST A -- direct connectivity, over all fibrosis-associated genes.
Each fibrosis-associated gene carries the transition at which it moves most.
For each transition, compare the share of drug-connected genes against the share
of genes overall -- a hypergeometric test, BH-corrected across the four
transitions. This asks whether drug ANNOTATION knows when in a disease a gene
moves. A null result is the expected one and is worth stating.

TEST B -- the question the plan actually asks.
"Test whether CANDIDATE DRUGS converge on genes involved in the transitions
identified as molecularly important in Paper 1." That needs three things Test A
does not have: a defined candidate set, the statistically supported transition
genes rather than every gene with a largest transition, and the requested graph
paths rather than direct edges.

  candidate set       the drugs Task 8 ranks, with the 30 leading candidates
                      reported separately
  transition genes    Paper 1 Task 3's genes with a SUBSTANTIAL transition,
                      the same 2,568 MP7 restricts to
  paths               MP7, Drug -> Gene -> Pathway <- transition gene, which is
                      the metapath the plan names
  null                the non-candidate ranked drugs, which reach the graph the
                      same way and differ only in not being candidates; a
                      permutation over which drugs are labelled candidates
                      preserves the degree distribution of the whole set

Convergence would mean candidate drugs reach F3->F4 transition genes through
the metapath more often than drugs that are not candidates.

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
TRANSITIONS = "Paper1_Results/Task3/task3_all_genes_all_transitions.csv"
MP7_PAIRS = "Paper2_Results/Task5/task5_mp7_pairs.csv"
DRUG_RANKING = "Paper2_Results/Task8/task8_final_drug_ranking.csv"
TARGET_TRANSITION = "F3→F4"   # Paper 1 writes transitions with an arrow
N_PERM = 2000
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

    # ---- TEST B: do candidate drugs converge, by metapath? -----------------
    pairs = pd.read_csv(MP7_PAIRS)
    trans = pd.read_csv(TRANSITIONS)
    trans = trans[trans.substantial.astype(str).str.lower() == "true"]
    big = set(trans[trans.transition.astype(str) == TARGET_TRANSITION].ensembl_id)
    supported = set(trans.ensembl_id)
    print(f"\nstatistically supported transition genes: {len(supported):,}, "
          f"of which {len(big):,} move most at {TARGET_TRANSITION}")

    ranked = pd.read_csv(DRUG_RANKING)
    candidate_ids = set(cand.Drug_ID)
    pairs = pairs[pairs.drug.isin(set(ranked.Drug_ID))]
    pairs["is_candidate"] = pairs.drug.isin(candidate_ids)
    pairs["hits_target_transition"] = pairs.target_gene.isin(big)

    per_drug = (pairs.groupby(["drug", "drug_name", "is_candidate"])
                     .agg(reach=("target_gene", "nunique"),
                          reach_target=("hits_target_transition",
                                        lambda v: pairs.loc[v.index][v]
                                        .target_gene.nunique()))
                     .reset_index())
    per_drug["share_at_target_transition"] = (
        per_drug.reach_target / per_drug.reach.replace(0, np.nan))
    per_drug = per_drug.dropna(subset=["share_at_target_transition"])

    obs_c = per_drug[per_drug.is_candidate].share_at_target_transition
    obs_n = per_drug[~per_drug.is_candidate].share_at_target_transition
    diff = float(obs_c.mean() - obs_n.mean())

    # permute WHICH drugs are candidates, keeping the number fixed, so the null
    # draws its label set from drugs with the same reach distribution
    rng = np.random.default_rng(42)
    vals = per_drug.share_at_target_transition.to_numpy()
    n_c = int(per_drug.is_candidate.sum())
    null = np.empty(N_PERM)
    for k in range(N_PERM):
        idx = rng.permutation(len(vals))
        null[k] = vals[idx[:n_c]].mean() - vals[idx[n_c:]].mean()
    centre = float(null.mean())
    extreme = int(np.sum(np.abs(null - centre) >= abs(diff - centre)))
    p_perm = (1 + extreme) / (N_PERM + 1)

    conv = pd.DataFrame([{
        "metapath": "MP7 Drug -> Gene -> Pathway <- transition gene",
        "target_transition": TARGET_TRANSITION,
        "candidate_drugs": n_c,
        "non_candidate_ranked_drugs": len(per_drug) - n_c,
        "candidate_mean_share": round(float(obs_c.mean()), 4),
        "non_candidate_mean_share": round(float(obs_n.mean()), 4),
        "difference": round(diff, 4),
        "permutation_null_mean": round(centre, 4),
        "permutation_p": round(p_perm, 5),
        "permutations": N_PERM,
        "converges": "yes" if (p_perm < 0.05 and diff > 0) else "no",
    }])
    conv.to_csv(f"{OUT_DIR}/task5_candidate_transition_convergence.csv",
                index=False)
    # The per-drug reach table IS the input to the permutation -- the test runs
    # on these shares and nothing else -- so shipping it makes Test B
    # reproducible from the delivered files. The 194,393-row MP7 pair table it
    # was derived from stays a local intermediate: 17 MB that nothing else
    # reads, regenerable by paper2_task5_metapaths.py in one run.
    per_drug.sort_values("share_at_target_transition", ascending=False).to_csv(
        f"{OUT_DIR}/task5_mp7_reach_per_drug.csv", index=False)
    print(f"wrote {OUT_DIR}/task5_mp7_reach_per_drug.csv "
          f"({len(per_drug):,} ranked drugs)")
    sup.add("candidate_convergence_per_drug",
            per_drug.sort_values("share_at_target_transition", ascending=False)
                    .head(100))
    sup.write()

    print("")
    print("TEST B -- do candidate drugs converge on the supported "
          f"{TARGET_TRANSITION} genes by metapath?")
    print(conv.to_string(index=False))

    print("Do drugs converge on the transition Paper 1 found most important?")
    print("(Paper 1 Task 3: F3->F4, 311 genes under equal power vs 0-2)")
    print("")
    print(t.to_string(index=False))
    print("")
    print("targets of the Task 8 leading candidates:")
    print(tgt[["Gene", "Largest_transition"]].to_string(index=False))
    print(f"\nwrote {OUT_DIR}/task5_transition_convergence.csv")
    print(f"wrote {OUT_DIR}/task5_candidate_transition_convergence.csv")


if __name__ == "__main__":
    main()
