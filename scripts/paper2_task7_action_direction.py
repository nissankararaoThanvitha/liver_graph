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
52.7% against a null of 55.9%, permutation p = 0.553 -- indistinguishable from
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
N_PERM = 2000
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

    # TWO INDEPENDENT REASONS A ROW CANNOT BE CLASSIFIED, kept as separate
    # flags because they are separate facts and a reader needs to know which
    # applies. Every one of the eight rows that cannot be resolved by gene
    # direction ALSO has an unrecorded drug direction (all eight are `TARGET`),
    # so a single "ambiguous" label hid the fact that the drug side was unknown
    # too.
    e["drug_direction_known"] = e.drug_action_direction.isin(["lowers", "raises"])
    e["gene_direction_conflict"] = (e.gene_direction_contradictory
                                    | e.gene_direction.isna())

    # PRECEDENCE: the drug side is tested first, which is the order Task 2
    # uses. A row with no recorded drug direction is `unknown` there, so it is
    # `unknown` here, and the gene-side flag travels beside it rather than
    # overriding it. The previous order made the same eight rows `ambiguous`
    # in this table and `unknown` in Task 2's.
    def classify(r):
        if not r.drug_direction_known:
            return "unknown"
        if r.gene_direction_conflict:
            return "ambiguous"
        rises = r.gene_direction == "increasing"
        lowers = r.drug_action_direction == "lowers"
        return "reversal-consistent" if lowers == rises else "reversal-inconsistent"

    e["reversal_class"] = e.apply(classify, axis=1)
    print(f"unclassifiable: {int((~e.drug_direction_known).sum()):,} with no "
          f"recorded drug direction, "
          f"{int(e.gene_direction_conflict.sum()):,} with no usable gene "
          f"direction, "
          f"{int((~e.drug_direction_known & e.gene_direction_conflict).sum()):,} "
          f"with both")
    # PER-EDGE PROVENANCE, carried from Task 2's table rather than stamped on
    # as a constant. Task 2 reads the recovered properties straight off the
    # ACTS_ON edge, so a plain re-run of this script rebuilds them; the
    # dataset-level string is only a fallback for an edge that carries none.
    e["Evidence_Source"] = np.where(
        e.get("sources_direct", pd.Series(index=e.index, dtype=object)).notna(),
        "OptimusKG: " + e.get("sources_direct",
                              pd.Series(index=e.index, dtype=object)).astype(str),
        SOURCE)
    if "n_sources" in e.columns:
        # n_sources counts DISTINCT asserting databases, not assertions.
        e["Evidence_Level"] = np.where(e.n_sources.fillna(0) >= 2,
                                       "multi-source", "single-source")
    else:
        e["Evidence_Level"] = EVIDENCE_LEVEL
    n_prov = int(e.get("sources_direct",
                       pd.Series(index=e.index, dtype=object)).notna().sum())
    print(f"per-edge provenance present on {n_prov:,} of {len(e):,} "
          f"relationships")

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

    # ---- item 33: trajectory evidence that actually bears on the label -----
    # Cluster and transition were attached and never consulted, so "trajectory
    # evidence" meant "a trajectory is on file". The reversal label uses the
    # association direction (the sign of rho); the stage means carry a second,
    # independent statement of which way the gene moves, namely the sign of
    # F4 - F0. Where the two agree, the trajectory supports the label; where
    # they disagree, the label rests on rho alone and the row says so.
    stage = master.set_index("Ensembl_ID")
    e["F0"] = e.Gene_ID.map(stage.F0)
    e["F4"] = e.Gene_ID.map(stage.F4)
    delta = e.F4 - e.F0
    e["trajectory_direction"] = np.where(delta > 0, "increasing",
                                         np.where(delta < 0, "decreasing", None))

    # ONLY WHERE A FIBROSIS TRAJECTORY EXISTS.
    # F0-F4 are fibrosis-stage means and Paper 1 fitted a trajectory cluster to
    # the 3,845 fibrosis-associated genes alone. An inflammation-only gene has
    # stage means in the table but no fibrosis trajectory, and its
    # gene_direction comes from the disease-group ladder -- a different
    # contrast, on 216 patients rather than 610. Comparing the two is a
    # category error, not a disagreement: without this guard the rule fires on
    # 364 relationships, every one of them inflammation-only, and withholds 84
    # reversal labels on the strength of it.
    has_cluster = e.Cluster.notna()
    both_known = e.trajectory_direction.notna() & e.gene_direction.notna()
    has_traj = has_cluster & both_known
    agrees = e.trajectory_direction == e.gene_direction
    e["trajectory_support"] = np.where(
        ~has_cluster, "no fibrosis trajectory",
        np.where(~both_known, "trajectory direction undefined",
                 np.where(agrees, "trajectory supports",
                          "trajectory contradicts")))

    # The label itself, with trajectory folded in. A relationship keeps its
    # reversal class only where the trajectory does not argue against the gene
    # direction that class was built on; where it does, the row is held at
    # "ambiguous - directions disagree" rather than being counted either way.
    e["reversal_class_with_trajectory"] = np.where(
        e.reversal_class.isin(["reversal-consistent", "reversal-inconsistent"])
        & (e.trajectory_support == "trajectory contradicts"),
        "ambiguous - rho and stage endpoints disagree",
        e.reversal_class)
    moved = int((e.reversal_class_with_trajectory != e.reversal_class).sum())
    print(f"trajectory: {int(has_traj.sum()):,} relationships sit on a gene "
          f"with a fibrosis trajectory; "
          f"{int((e.trajectory_support == 'trajectory contradicts').sum()):,} "
          f"contradict the association direction, of which {moved:,} held a "
          f"reversal label and are withheld")
    print(f"   {int((~has_cluster).sum()):,} relationships are on "
          f"inflammation-only genes and are not trajectory-tested")

    # ---- the required table ------------------------------------------------
    cols = ["Drug", "Drug_ID", "Gene", "Gene_ID", "gene_direction",
            "fibrosis_rho", "inflammation_rho", "progression_class",
            "Cluster", "Cluster_pattern", "Largest_transition", "Tier",
            "Action_Mechanism", "drug_action_direction",
            "Evidence_Source", "Evidence_Level", "reversal_class",
            "drug_direction_known", "gene_direction_conflict",
            "trajectory_direction", "trajectory_support",
            "reversal_class_with_trajectory",
            "non_therapeutic_entity"]
    # whatever provenance Task 2 recovered, carried through unchanged
    cols += [c for c in ["sources_direct", "sources_indirect",
                         "relation_assertions", "relation_conflict",
                         "source_urls", "mechanisms_of_action", "n_sources"]
             if c in e.columns]
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
        ("    ...lowers the target's ACTIVITY",
         int((e.drug_action_direction == "lowers").sum()),
         round(100 * (e.drug_action_direction == "lowers").mean(), 1)),
        ("    ...raises the target's ACTIVITY",
         int((e.drug_action_direction == "raises").sum()),
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

    # THE NULL PRESERVES PROGRESSION DIRECTION.
    # A free shuffle moved labels between rising and falling genes, and those
    # two have different consistency baselines by construction: 68% of
    # directional drugs lower their target, so a rising gene is consistent 68%
    # of the time by chance and a falling gene 32%. Mixing them lets a null
    # draw inherit the wrong baseline, which makes any group whose direction is
    # over-represented look enriched. Only the CLASS part of the label is
    # permuted, and only among genes sharing a direction, so each draw keeps
    # the group's own baseline and tests the thing the claim is about: whether
    # a class does better than other classes going the same way.
    strata = np.array([lab.split(" / ")[-1] for lab in labels])
    classes = np.array([lab.split(" / ")[0] for lab in labels])
    stratum_idx = {st: np.flatnonzero(strata == st) for st in set(strata)}

    rows_t = []
    for g, s in dd.groupby("paper1_group"):
        k, n = int((s.reversal_class == "reversal-consistent").sum()), len(s)
        expected = p_lower if g.endswith("positive") else 1 - p_lower
        p_binom = stats.binomtest(k, n, expected).pvalue
        obs = k / n
        null = np.empty(N_PERM)
        for i in range(N_PERM):
            shuffled = classes.copy()
            for st, where in stratum_idx.items():
                shuffled[where] = rng.permutation(classes[where])
            lab = np.char.add(np.char.add(shuffled, " / "), strata)[idx]
            m = lab == g
            null[i] = consistent[m].mean() if m.any() else np.nan
        centre = float(np.nanmean(null))
        kept = null[~np.isnan(null)]
        extreme = int(np.sum(np.abs(kept - centre) >= abs(obs - centre)))
        p_perm = (1 + extreme) / (len(kept) + 1)      # finite-simulation
        rows_t.append({"paper1_group": g, "relationships": n, "consistent": k,
                       "observed_percent": round(100 * obs, 1),
                       "expected_from_vocabulary": round(100 * expected, 1),
                       # descriptive only: edges on one gene are not
                       # independent draws, so this p is not inferential
                       "binomial_p_descriptive": p_binom,
                       "gene_permutation_null": round(100 * centre, 1),
                       "gene_permutation_p": round(p_perm, 5),
                       "permutations": N_PERM})
    tests = pd.DataFrame(rows_t)
    # The binomial treats every relationship as an independent draw. They are
    # not: 4,984 relationships sit on 1,072 genes and 3,027 drugs, so one
    # well-annotated gene contributes dozens of correlated rows. BH does not
    # repair that, it only controls the family error rate among tests that are
    # each individually wrong. These columns are kept as a descriptive check
    # and are explicitly not the basis for any claim; the gene-level
    # permutation is.
    tests["binomial_q_BH_descriptive"] = stats.false_discovery_control(
        tests.binomial_p_descriptive.values)
    tests["binomial_p_descriptive"] = tests.binomial_p_descriptive.map(
        lambda v: f"{v:.2e}")
    tests["binomial_q_BH_descriptive"] = tests.binomial_q_BH_descriptive.map(
        lambda v: f"{v:.2e}")
    tests["inference_basis"] = "gene-level permutation within progression direction"
    tests["permutation_q_BH"] = stats.false_discovery_control(
        tests.gene_permutation_p.values)
    tests["survives_gene_permutation"] = np.where(
        (tests.observed_percent > tests.expected_from_vocabulary)
        & (tests.permutation_q_BH < 0.05), "yes", "no")
    tests["permutation_q_BH"] = tests.permutation_q_BH.map(lambda v: f"{v:.3e}")
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
                 "expected_from_vocabulary", "binomial_q_BH_descriptive",
                 "gene_permutation_null", "gene_permutation_p", "permutation_q_BH",
                 "survives_gene_permutation"]].to_string(index=False))
    for f in ["task7_action_direction_evidence.csv",
              "task7_consistency_significance.csv",
              "task7_known_vs_unknown_direction.csv",
              "task7_consistency_by_group.csv",
              "task7_consistency_by_cluster.csv"]:
        print(f"wrote {OUT_DIR}/{f}")


if __name__ == "__main__":
    main()
