"""
paper2_task7_action_direction.py
--------------------------------
Paper 2, Task 7: the drug action / direction evidence table.

WHAT THE PLAN ASKS FOR
"For candidate drug-target relationships, determine whether the drug is
reported as an inhibitor, antagonist, agonist, activator, binder, or has
unknown/mixed action. Preserve the source and evidence level...

Progression direction must be kept separate from drug mechanism. For example,
an F0-to-F4 increasing gene that is inhibited by a drug may be mechanistically
interesting, but this alone does not prove that the drug is anti-fibrotic.

Use the actual Paper 1 direction and trajectory evidence... Classify each
relationship as reversal-consistent, reversal-inconsistent, ambiguous, or
unknown... this remains a hypothesis until independently validated."

Required outputs: the table; a summary of known versus unknown action
direction; and mechanism consistency broken down by Paper 1 group and by
trajectory cluster.

THE FOUR-WAY CLASSIFICATION, STATED EXACTLY
A relationship is reversal-consistent only when the drug's action opposes the
direction the gene travels as disease worsens:

  gene rises with disease  + drug lowers it      reversal-consistent
  gene falls with disease  + drug raises it      reversal-consistent
  gene rises               + drug raises         reversal-inconsistent
  gene falls               + drug lowers         reversal-inconsistent
  action is binder or mixed (BINDING_AGENT,
    MODULATOR, TARGET-with-no-direction)         unknown
  gene direction is itself contradictory         ambiguous

The last row matters. Task 1 found 30 shared genes that fall with fibrosis and
rise with inflammation. A gene that travels both ways cannot be given one
direction, so a relationship touching it is ambiguous by construction, not
unknown -- the drug's action is known perfectly well; it is the gene that is
not resolvable.

PHARMACOKINETIC EDGES ARE NOT DRUG-TARGET RELATIONSHIPS
The plan scopes this to "candidate drug-target relationships". ENZYME,
TRANSPORTER, CARRIER and SUBSTRATE mean the gene metabolises or transports the
drug -- there is no mechanism to be consistent or inconsistent with. They are
excluded from the table and counted separately, so their absence is a stated
decision rather than a silent filter.

EVIDENCE LEVEL CANNOT BE SUPPLIED
The plan asks to "preserve the source and evidence level". ACTS_ON carries one
property, `action`. There is no evidence level, no reference, no assay, no
confidence anywhere on the edge -- load_knowledge_layer.cypher sets
r.action = row.rel_type and nothing else. Both columns are emitted with an
explicit statement of that rather than left blank, because a blank reads as
"none found" instead of "never recorded".

WHAT THIS TABLE IS NOT
Task 2 established that reversal consistency across these relationships sits at
52.7% against a null of 55.9%, permutation p = 0.78 -- indistinguishable from
chance, and robust to six different action-to-direction mappings. So a
reversal-consistent label here marks a relationship worth a look, not a
relationship that works. The plan says it first: this remains a hypothesis
until independently validated.

Usage:
    uv run --with pandas --with numpy --with openpyxl python scripts/paper2_task7_action_direction.py
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables
from paper2_drug_filters import flag_entities

EDGES = "Paper2_Results/Task2/task2_drug_gene_edges.csv"
MASTER = "Paper2_Results/Task1/Paper2_progression_genes.csv"
OUT_DIR = "Paper2_Results/Task7"

PK = {"ENZYME", "TRANSPORTER", "CARRIER", "SUBSTRATE"}
LOWERS = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE_ALLOSTERIC_MODULATOR",
          "NEGATIVE_MODULATOR", "INVERSE_AGONIST", "ALLOSTERIC_ANTAGONIST",
          "DEGRADER"}
RAISES = {"AGONIST", "PARTIAL_AGONIST", "ACTIVATOR",
          "POSITIVE_ALLOSTERIC_MODULATOR", "POSITIVE_MODULATOR", "OPENER",
          "RELEASING_AGENT", "STABILISER"}
BINDER_OR_MIXED = {"BINDING_AGENT", "MODULATOR"}

SOURCE = "OptimusKG (Harvard Dataverse DOI 10.7910/DVN/IYNGEV)"
EVIDENCE_LEVEL = "not recorded - ACTS_ON carries `action` only"


def action_direction(a):
    """The plan's vocabulary: inhibitor / antagonist / agonist / activator /
    binder / unknown-or-mixed, reduced to what it means for the gene."""
    if a in LOWERS:
        return "lowers"
    if a in RAISES:
        return "raises"
    if a in BINDER_OR_MIXED:
        return "binder or mixed"
    return "unknown"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sup = SupportingTables(OUT_DIR, "task7")

    e = pd.read_csv(EDGES)
    master = pd.read_csv(MASTER)
    n_all = len(e)

    pk = e[e.Action_Mechanism.isin(PK)]
    e = e[~e.Action_Mechanism.isin(PK)].copy()
    print(f"all drug-gene edges            {n_all:,}")
    print(f"  pharmacokinetic, excluded    {len(pk):,}")
    print(f"  drug-target relationships    {len(e):,}\n")

    e["drug_action_direction"] = e.Action_Mechanism.map(action_direction)

    # Paper 1's direction per gene, and whether it is resolvable at all
    direc = master.set_index("Ensembl_ID")
    both = (direc.fibrosis_direction.notna() & direc.inflammation_direction.notna())
    contradictory = set(direc[both & (direc.fibrosis_direction
                                      != direc.inflammation_direction)].index)
    e["gene_direction_contradictory"] = e.Gene_ID.isin(contradictory)

    def classify(r):
        if r.gene_direction_contradictory:
            return "ambiguous"
        if r.drug_action_direction in ("binder or mixed", "unknown"):
            return "unknown"
        if pd.isna(r.gene_direction):
            return "ambiguous"
        rises = r.gene_direction == "increasing"
        lowers = r.drug_action_direction == "lowers"
        return "reversal-consistent" if lowers == rises else "reversal-inconsistent"

    e["reversal_class"] = e.apply(classify, axis=1)
    e["Evidence_Source"] = SOURCE
    e["Evidence_Level"] = EVIDENCE_LEVEL

    # ENTITY FLAG, added 13 October after review of Task 3.
    # This table is read by Task 6 to decide whether a gene "has a therapeutic
    # drug". Without the flag, 175 genes earn that credit from zinc salts, ATP
    # and unnamed accessions alone. The flag travels with the row so every
    # consumer can apply it; Task 7's own summaries deliberately do NOT filter,
    # because the question there is what the vocabulary says, not what is
    # prescribable.
    names = dict(zip(e.Drug_ID, e.Drug))
    targets = e.groupby("Drug_ID").Gene_ID.apply(set).to_dict()
    flags = flag_entities(names, targets)
    e["non_therapeutic_entity"] = e.Drug_ID.map(
        lambda d: flags[d]["non_therapeutic"])
    print(f"relationships involving a non-therapeutic entity: "
          f"{int(e.non_therapeutic_entity.sum()):,} of {len(e):,}")

    # ---- the required table ------------------------------------------------
    cols = ["Drug", "Drug_ID", "Gene", "Gene_ID", "gene_direction",
            "fibrosis_rho", "inflammation_rho", "progression_class",
            "Cluster", "Cluster_pattern", "Largest_transition", "Tier",
            "Action_Mechanism", "drug_action_direction",
            "Evidence_Source", "Evidence_Level", "reversal_class",
            "non_therapeutic_entity"]
    out = e[cols].rename(columns={"gene_direction": "Gene_progression_direction",
                                  "Action_Mechanism": "Drug_action"})
    out = out.sort_values(["reversal_class", "Drug", "Gene"])
    out.to_csv(f"{OUT_DIR}/task7_action_direction_evidence.csv", index=False)

    # ---- known versus unknown action direction -----------------------------
    known = e.drug_action_direction.isin(["lowers", "raises"])
    kv = pd.DataFrame([
        ("drug-target relationships", len(e), 100.0),
        ("  action direction KNOWN (lowers or raises)", int(known.sum()),
         round(100 * known.mean(), 1)),
        ("    ...lowers the gene", int((e.drug_action_direction == "lowers").sum()),
         round(100 * (e.drug_action_direction == "lowers").mean(), 1)),
        ("    ...raises the gene", int((e.drug_action_direction == "raises").sum()),
         round(100 * (e.drug_action_direction == "raises").mean(), 1)),
        ("  action direction UNKNOWN or MIXED", int((~known).sum()),
         round(100 * (~known).mean(), 1)),
        ("    ...binder or mixed action",
         int((e.drug_action_direction == "binder or mixed").sum()),
         round(100 * (e.drug_action_direction == "binder or mixed").mean(), 1)),
        ("    ...no direction recorded",
         int((e.drug_action_direction == "unknown").sum()),
         round(100 * (e.drug_action_direction == "unknown").mean(), 1)),
        ("pharmacokinetic edges (excluded, not drug-target)", len(pk), None),
    ], columns=["measure", "relationships", "percent_of_drug_target"])
    kv.to_csv(f"{OUT_DIR}/task7_known_vs_unknown_direction.csv", index=False)

    # ---- consistency by Paper 1 group --------------------------------------
    def grp(r):
        cls = "shared" if r.progression_class == "both" else r.progression_class
        if r.gene_direction_contradictory or pd.isna(r.gene_direction):
            return f"{cls} / contradictory"
        d = "positive" if r.gene_direction == "increasing" else "negative"
        return f"{cls} / {d}"
    e["paper1_group"] = e.apply(grp, axis=1)

    by_group = (e.pivot_table(index="paper1_group", columns="reversal_class",
                              values="Drug_ID", aggfunc="size", fill_value=0)
                  .reset_index())
    by_group["total"] = by_group.select_dtypes("number").sum(axis=1)
    by_group.to_csv(f"{OUT_DIR}/task7_consistency_by_group.csv", index=False)

    # ---- consistency by trajectory cluster ---------------------------------
    clus = e[e.Cluster.notna()].copy()
    by_cluster = (clus.pivot_table(index=["Cluster", "Cluster_pattern"],
                                   columns="reversal_class", values="Drug_ID",
                                   aggfunc="size", fill_value=0).reset_index())
    by_cluster["total"] = by_cluster.select_dtypes("number").sum(axis=1)
    by_cluster.to_csv(f"{OUT_DIR}/task7_consistency_by_cluster.csv", index=False)

    # ---- is any group more reversal-consistent than the vocabulary allows? --
    # 68% of directional drugs LOWER their target, so a rising gene is
    # consistent 67.6% of the time by chance and a falling gene only 32.4%.
    # Comparing a group against 50% would therefore invent a result; the
    # baseline is the vocabulary's own mix.
    #
    # The per-edge binomial against that baseline is reported, and then tested
    # again by permuting the gene -> group assignment at GENE level, because
    # edges on the same gene are not independent -- the error Task 2 had to
    # correct.
    dd = e[e.reversal_class.isin(["reversal-consistent",
                                  "reversal-inconsistent"])].copy()
    p_lower = (dd.drug_action_direction == "lowers").mean()
    rng = np.random.default_rng(42)
    gene_group = dd.groupby("Gene_ID").paper1_group.first()
    genes = gene_group.index.to_numpy()
    labels = gene_group.to_numpy()
    pos = {g: i for i, g in enumerate(genes)}
    idx = np.array([pos[g] for g in dd.Gene_ID])
    consistent = (dd.reversal_class == "reversal-consistent").to_numpy()

    rows_t = []
    for g, s in dd.groupby("paper1_group"):
        k, n = int((s.reversal_class == "reversal-consistent").sum()), len(s)
        expected = p_lower if g.endswith("positive") else 1 - p_lower
        p_binom = stats.binomtest(k, n, expected).pvalue
        obs = k / n
        null = np.empty(2000)
        for i in range(2000):
            lab = rng.permutation(labels)[idx]
            m = lab == g
            null[i] = consistent[m].mean() if m.any() else np.nan
        p_perm = float(np.nanmean(np.abs(null - np.nanmean(null))
                                  >= abs(obs - np.nanmean(null))))
        rows_t.append({"paper1_group": g, "relationships": n, "consistent": k,
                       "observed_percent": round(100 * obs, 1),
                       "expected_from_vocabulary": round(100 * expected, 1),
                       "binomial_p": p_binom,
                       "gene_permutation_null": round(100 * float(np.nanmean(null)), 1),
                       "gene_permutation_p": round(p_perm, 4)})
    tests = pd.DataFrame(rows_t)
    tests["binomial_q_BH"] = stats.false_discovery_control(tests.binomial_p.values)
    tests["binomial_p"] = tests.binomial_p.map(lambda v: f"{v:.2e}")
    tests["binomial_q_BH"] = tests.binomial_q_BH.map(lambda v: f"{v:.2e}")
    tests["survives_gene_permutation"] = np.where(
        (tests.observed_percent > tests.expected_from_vocabulary)
        & (tests.gene_permutation_p < 0.05), "yes", "no")
    tests.to_csv(f"{OUT_DIR}/task7_consistency_significance.csv", index=False)

    # ---- supporting ---------------------------------------------------------
    sup.add("action_vocabulary",
            e.groupby(["drug_action_direction", "Action_Mechanism"])
             .size().reset_index(name="relationships")
             .sort_values(["drug_action_direction", "relationships"],
                          ascending=[True, False]))
    sup.add("by_largest_transition",
            clus.pivot_table(index="Largest_transition", columns="reversal_class",
                             values="Drug_ID", aggfunc="size", fill_value=0)
                .reset_index())
    cons = e[e.reversal_class == "reversal-consistent"]
    sup.add("consistent_by_tier",
            cons[cons.Tier.notna()].groupby("Tier")
                .agg(relationships=("Drug_ID", "size"),
                     drugs=("Drug_ID", "nunique"),
                     genes=("Gene_ID", "nunique")).reset_index())
    sup.add("top_consistent_tier1",
            cons[cons.Tier.astype(str).str.startswith("Tier 1")]
                .sort_values("fibrosis_rho", key=abs, ascending=False)
                [["Drug", "Gene", "Gene_progression_direction"
                  if "Gene_progression_direction" in cons.columns
                  else "gene_direction",
                  "Action_Mechanism", "fibrosis_rho", "Cluster_pattern"]]
                .head(40))
    sup.write()

    # ---- report -------------------------------------------------------------
    print(kv.to_string(index=False))
    print("\nreversal classification, all drug-target relationships:")
    print(e.reversal_class.value_counts().to_string())
    print("\nby Paper 1 group:")
    print(by_group.to_string(index=False))
    print("\nby trajectory cluster:")
    print(by_cluster.to_string(index=False))
    print("")
    print("is any group more consistent than the drug vocabulary allows?")
    print(tests[["paper1_group", "relationships", "observed_percent",
                 "expected_from_vocabulary", "binomial_q_BH",
                 "gene_permutation_null", "gene_permutation_p",
                 "survives_gene_permutation"]].to_string(index=False))
    for f in ["task7_action_direction_evidence.csv",
              "task7_consistency_significance.csv",
              "task7_known_vs_unknown_direction.csv",
              "task7_consistency_by_group.csv",
              "task7_consistency_by_cluster.csv"]:
        print(f"wrote {OUT_DIR}/{f}")


if __name__ == "__main__":
    main()
