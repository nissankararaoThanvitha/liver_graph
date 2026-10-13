"""
paper2_task2_robustness.py
--------------------------
Stress-test the three soft spots in Task 2 before any of it is relied on.

1. DID THE LOADER LOSE MODE-OF-ACTION?
   load_knowledge_layer.cypher does `MERGE (d)-[r:ACTS_ON]->(g) SET r.action`,
   which keeps ONE edge per drug-gene pair. If the source listed a pair twice
   with different actions, the later row would silently overwrite the earlier
   one and the directional share would be understated. Checked directly against
   the source file now that it has been found in Paper1_Package/04_DATA.

2. IS THE RESULT AN ARTEFACT OF MY ACTION->DIRECTION MAPPING?
   The split of action values into "lowers" and "raises" is a judgement call,
   and a few of them are genuinely arguable: STABILISER, DEGRADER, MODULATOR,
   BINDING_AGENT. The whole reversal-consistency result rests on that table, so
   it is re-run under alternative mappings. If the conclusion only survives one
   of them, it is a property of the table and not of the data.

3. IS THE BINOMIAL TEST VALID?
   No. It assumes 1,005 independent observations; they are not independent --
   a drug can hit several genes and a gene is hit by several drugs, so the
   edges come in correlated blocks. Replaced with a permutation test that
   shuffles direction labels at the GENE level, so a gene's whole set of edges
   moves together and the clustering is preserved under the null. Every
   mapping variant gets its own test, because a variant that raises the
   percentage also shrinks n and widens its own null.

Usage:
    uv run --with pandas --with numpy --with scipy python scripts/paper2_task2_robustness.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables

EDGES = "Paper2_Results/Task2/task2_drug_gene_edges.csv"
SOURCE = "Paper1_Package/04_DATA/knowledge_layer/edges_drug_gene.csv"
OUT_DIR = "Paper2_Results/Task2"
SEED = 42
N_PERM = 10000

# The mapping used in Task 2, and the arguable members of it.
BASE_LOWERS = {"INHIBITOR", "ANTAGONIST", "BLOCKER",
               "NEGATIVE_ALLOSTERIC_MODULATOR", "NEGATIVE_MODULATOR",
               "INVERSE_AGONIST", "ALLOSTERIC_ANTAGONIST", "DEGRADER"}
BASE_RAISES = {"AGONIST", "PARTIAL_AGONIST", "ACTIVATOR",
               "POSITIVE_ALLOSTERIC_MODULATOR", "POSITIVE_MODULATOR",
               "OPENER", "RELEASING_AGENT", "STABILISER"}

# Alternatives. Each is (name, lowers, raises).
VARIANTS = [
    ("as published", BASE_LOWERS, BASE_RAISES),
    ("STABILISER dropped", BASE_LOWERS, BASE_RAISES - {"STABILISER"}),
    ("DEGRADER dropped", BASE_LOWERS - {"DEGRADER"}, BASE_RAISES),
    ("both arguable dropped",
     BASE_LOWERS - {"DEGRADER"}, BASE_RAISES - {"STABILISER"}),
    ("strict core only",
     {"INHIBITOR", "ANTAGONIST", "BLOCKER"}, {"AGONIST", "ACTIVATOR"}),
    ("INHIBITOR vs AGONIST only", {"INHIBITOR"}, {"AGONIST"}),
]


def consistency(e, lowers, raises):
    """Edges whose drug action opposes the gene's direction of travel."""
    d = e[e.Action_Mechanism.isin(lowers | raises) & e.gene_direction.notna()].copy()
    d["drug_lowers"] = d.Action_Mechanism.isin(lowers)
    d["gene_rises"] = d.gene_direction == "increasing"
    d["consistent"] = d.drug_lowers == d.gene_rises
    return d


def permutation_p(d, rng, n=N_PERM):
    """Shuffle direction at the GENE level, so each gene's edges move as a unit.

    Shuffling edge by edge would assume the edges are independent -- the very
    thing that makes the binomial test invalid here.
    """
    gene_dir = d.groupby("Gene_ID").gene_rises.first()
    genes = gene_dir.index.to_numpy()
    labels = gene_dir.to_numpy()
    edge_gene = d.Gene_ID.to_numpy()
    lowers = d.drug_lowers.to_numpy()
    pos = {g: i for i, g in enumerate(genes)}
    idx = np.array([pos[g] for g in edge_gene])

    observed = (lowers == labels[idx]).mean()
    null = np.empty(n)
    for i in range(n):
        null[i] = (lowers == rng.permutation(labels)[idx]).mean()
    # Two-sided, centred on the NULL mean rather than on 0.5. The null here
    # averages 55.9%, not 50%: 68% of directional drugs lower their target and
    # 68% of these genes rise, so the right-way pairing is common by accident.
    # Measuring deviation from 0.5 asks whether the result differs from a coin
    # flip, which is not the question -- the question is whether it differs
    # from what this vocabulary gives for free.
    centre = null.mean()
    p = (np.abs(null - centre) >= abs(observed - centre)).mean()
    return observed, null, p


def main():
    e = pd.read_csv(EDGES)
    sup = SupportingTables(OUT_DIR, "task2")
    rng = np.random.default_rng(SEED)
    lines = []

    # ---- 1. loader fidelity ----------------------------------------------
    src = pd.read_csv(SOURCE)
    pairs = src.groupby(["from_id", "to_id"]).size()
    lost = int((pairs - 1).clip(lower=0).sum())
    print("1. DID THE LOADER LOSE ACTIONS?")
    print(f"   source rows                    {len(src):,}")
    print(f"   distinct drug-gene pairs       {len(pairs):,}")
    print(f"   pairs with >1 action row       {int((pairs > 1).sum()):,}")
    print(f"   rows lost to MERGE overwrite   {lost:,}")
    print("   ->", "NO LOSS. The directional share is exact, not a floor."
          if lost == 0 else f"LOSS: {lost} actions overwritten.")
    lines.append({"check": "loader_action_loss", "value": lost,
                  "verdict": "no loss" if lost == 0 else "actions lost"})

    # ---- 2. mapping sensitivity ------------------------------------------
    print("\n2. DOES THE RESULT SURVIVE A DIFFERENT ACTION MAPPING?")
    # Every variant gets its own permutation test. A mapping that lifts the
    # percentage but not past its own null has not found anything -- restricting
    # to cleaner pharmacology also shrinks n, which widens the null.
    rows = []
    for name, lowers, raises in VARIANTS:
        d = consistency(e, lowers, raises)
        k, n = int(d.consistent.sum()), len(d)
        obs, null, p = permutation_p(d, np.random.default_rng(SEED))
        rows.append({"mapping": name, "edges": n, "consistent": k,
                     "inconsistent": n - k,
                     "percent_consistent": round(100 * k / n, 1) if n else None,
                     "null_mean_percent": round(100 * null.mean(), 1),
                     "permutation_p": round(float(p), 3),
                     "beats_chance": "no" if p >= 0.05 else "yes"})
        print(f"   {name:<28} {k:>4}/{n:<5} = {100*k/n:5.1f}%   "
              f"null {100*null.mean():4.1f}%   p = {p:.3f}")
    sens = pd.DataFrame(rows)
    sup.add("mapping_sensitivity", sens)

    spread = sens.percent_consistent.max() - sens.percent_consistent.min()
    print(f"   -> range across mappings: {sens.percent_consistent.min():.1f}% "
          f"to {sens.percent_consistent.max():.1f}% (spread {spread:.1f} pts)")

    # ---- 3. a test that respects the clustering --------------------------
    print("\n3. A TEST THAT DOES NOT ASSUME INDEPENDENT EDGES")
    d = consistency(e, BASE_LOWERS, BASE_RAISES)
    obs, null, p = permutation_p(d, rng)
    lo, hi = np.percentile(null, [2.5, 97.5])
    print(f"   observed consistent fraction   {100*obs:.1f}%")
    print(f"   null distribution (gene-level shuffle, {N_PERM:,} permutations)")
    print(f"     mean {100*null.mean():.1f}%, 95% range "
          f"{100*lo:.1f}% to {100*hi:.1f}%")
    print(f"   permutation p = {p:.3f}")
    print("   -> " + ("NOT distinguishable from chance."
                      if p >= 0.05 else "distinguishable from chance."))
    print(f"   (the binomial p = 0.088 reported earlier assumed {len(d):,} "
          "independent\n    observations; the largest drug alone contributes "
          f"{d.Drug_ID.value_counts().iloc[0]} edges)")

    perm = pd.DataFrame([{
        "test": "gene-level permutation", "n_edges": len(d),
        "n_genes": d.Gene_ID.nunique(), "n_drugs": d.Drug_ID.nunique(),
        "observed_percent_consistent": round(100 * obs, 1),
        "null_mean_percent": round(100 * null.mean(), 1),
        "null_95_low": round(100 * lo, 1), "null_95_high": round(100 * hi, 1),
        "permutations": N_PERM, "p_value": round(float(p), 4),
        "verdict": "not distinguishable from chance" if p >= 0.05
                   else "distinguishable from chance",
    }])
    sup.add("consistency_permutation_test", perm)
    sup.write()


if __name__ == "__main__":
    main()
