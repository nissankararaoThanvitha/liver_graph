"""
paper2_task2_drug_gene_edges.py
-------------------------------
Paper 2, Task 2: extract every drug-gene relationship for the progression genes.

WHAT THE PLAN ASKS FOR
"For every progression gene, extract all connected drugs... For each edge
retain the original evidence and source information. Where the knowledge source
contains mechanism/action information, record it exactly; otherwise mark the
action as unknown."

Columns asked for:
  Drug | Drug ID | Gene | Gene ID | Relationship | Action/Mechanism |
  Evidence/Source | Database ID

WHAT THE GRAPH CAN AND CANNOT GIVE
ACTS_ON carries exactly one property, `action`. The loader
(load_knowledge_layer.cypher, 8/11 drug-gene) does `SET r.action = row.rel_type`
and nothing else, and build_optimuskg_layer.py only ever carried
from_id / to_id / rel_type / score out of the source parquet -- with `score`
left empty for every edge type except disease_gene.

So:
  Drug, Drug ID, Gene, Gene ID    available
  Relationship                    ACTS_ON for all of them
  Action/Mechanism                available, recorded exactly as stored
  Database ID                     the drug's ChEMBL id and the gene's Ensembl id
  Evidence/Source                 NOT available per edge

Per-edge provenance was never loaded into the graph. It is recorded here at
dataset level (OptimusKG, Harvard Dataverse DOI 10.7910/DVN/IYNGEV) and the
column says so explicitly rather than being left blank, so nobody later reads a
blank as "no evidence". Recovering true per-edge evidence means re-parsing the
OptimusKG parquet, which is not in the repository.

ACTION IS NOT THE SAME THING AS DIRECTION
`action` holds OptimusKG's relation value. Most of it is not a pharmacological
direction at all:

  pharmacokinetic   ENZYME, TRANSPORTER, CARRIER, SUBSTRATE
                    The gene product metabolises or transports the drug. It is
                    NOT a therapeutic target. In a liver study this is a
                    systematic bias, not noise: the cytochromes live in the
                    liver and their expression genuinely changes as it fails,
                    so they appear among progression genes while telling you
                    nothing therapeutic.
  non-directional   TARGET, MODULATOR, BINDING_AGENT
                    A real target, but the effect direction is unrecorded.
  directional       everything else, split into lowers / raises below.

MECHANISM CONSISTENCY -- an early check, not therapeutic proof
The plan asks how many relationships can be reconciled with the Paper 1
progression direction. A relationship is called reversal-consistent only when
the drug's action opposes the direction the gene moves in as disease worsens:

  gene rises with disease  + drug lowers it   -> reversal-consistent
  gene falls with disease  + drug raises it   -> reversal-consistent
  gene rises               + drug raises      -> reversal-inconsistent
  gene falls               + drug lowers      -> reversal-inconsistent
  action non-directional                      -> unknown
  action pharmacokinetic                      -> not-applicable
  gene direction contradictory (the 30)       -> ambiguous

The plan is explicit that this is "an early mechanism-consistency check without
treating it as therapeutic proof", and the repurposing handoff is blunter: the
graph records association direction and timing, it does NOT establish whether
inhibition or activation is beneficial. Nothing here says a consistent pair
works.

THE 30 CONTRADICTORY GENES
Task 1 found 30 shared genes that fall with fibrosis but rise with
inflammation. They cannot be given one direction, so every edge touching them
is classified `ambiguous` and counted separately rather than being forced onto
one ladder.

Usage:
    uv run --with neo4j --with pandas python scripts/paper2_task2_drug_gene_edges.py
"""

import json
import os

import pandas as pd
from neo4j import GraphDatabase

MASTER = "Paper2_Results/Task1/Paper2_progression_genes.csv"
TRAJECTORY = "Paper1_HighConfidence/11_final_all_3845_genes.csv"
OUT_DIR = "Paper2_Results/Task2"

SOURCE_NOTE = "OptimusKG (Harvard Dataverse DOI 10.7910/DVN/IYNGEV); per-edge evidence not loaded"

PHARMACOKINETIC = {"ENZYME", "TRANSPORTER", "CARRIER", "SUBSTRATE"}
LOWERS = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE_ALLOSTERIC_MODULATOR",
          "NEGATIVE_MODULATOR", "INVERSE_AGONIST", "ALLOSTERIC_ANTAGONIST",
          "DEGRADER"}
RAISES = {"AGONIST", "PARTIAL_AGONIST", "ACTIVATOR",
          "POSITIVE_ALLOSTERIC_MODULATOR", "POSITIVE_MODULATOR", "OPENER",
          "RELEASING_AGENT", "STABILISER"}
NON_DIRECTIONAL = {"TARGET", "MODULATOR", "BINDING_AGENT"}


def driver():
    """Credentials come from the MCP server config, never from source."""
    cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
    for scope in cfg.get("projects", {}).values():
        srv = (scope.get("mcpServers") or {}).get("neo4j")
        if srv:
            env = srv["env"]
            return (GraphDatabase.driver(env["NEO4J_URI"],
                                         auth=(env["NEO4J_USERNAME"],
                                               env["NEO4J_PASSWORD"])),
                    env.get("NEO4J_DATABASE", "neo4j"))
    raise SystemExit("no neo4j MCP config found")


def action_class(a):
    if a in PHARMACOKINETIC:
        return "pharmacokinetic"
    if a in LOWERS:
        return "therapeutic-lowers"
    if a in RAISES:
        return "therapeutic-raises"
    if a in NON_DIRECTIONAL:
        return "therapeutic-nondirectional"
    return "unclassified"


def gene_direction(row):
    """One direction per gene, or None where the two ladders disagree."""
    f, i = row.fibrosis_direction, row.inflammation_direction
    if pd.notna(f) and pd.notna(i):
        return f if f == i else None        # None marks the contradictory 30
    return f if pd.notna(f) else i


def consistency(row):
    cls = row.action_class
    if cls == "pharmacokinetic":
        return "not-applicable"
    if cls in ("therapeutic-nondirectional", "unclassified"):
        return "unknown"
    if row.gene_direction is None or pd.isna(row.gene_direction):
        return "ambiguous"
    lowers = cls == "therapeutic-lowers"
    rises = row.gene_direction == "increasing"
    return "reversal-consistent" if lowers == rises else "reversal-inconsistent"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    master = pd.read_csv(MASTER)

    drv, db = driver()
    with drv.session(database=db) as s:
        inst = s.run("CALL dbms.listConfig('server.directories.data') "
                     "YIELD value RETURN value").single()["value"]
        rows = s.run("""
            MATCH (g:Gene)
            WHERE (g)-[:TRACKS_FIBROSIS]->() OR (g)-[:TRACKS_INFLAMMATION]->()
            WITH DISTINCT g
            MATCH (dr:Drug)-[a:ACTS_ON]->(g)
            RETURN dr.name AS Drug, dr.node_id AS Drug_ID,
                   g.symbol AS Gene, g.ensembl_id AS Gene_ID,
                   type(a) AS Relationship,
                   coalesce(a.action, 'unknown') AS Action_Mechanism
        """).data()
    drv.close()
    print(f"instance: {inst}\ndatabase: {db}\n")

    e = pd.DataFrame(rows)
    print(f"edges pulled from the graph: {len(e):,}")

    # ---- join Paper 1 evidence -------------------------------------------
    cols = ["Ensembl_ID", "progression_class", "fibrosis_rho",
            "fibrosis_direction", "inflammation_rho", "inflammation_direction",
            "in_fibrosis_starting_set"]
    e = e.merge(master[cols], left_on="Gene_ID", right_on="Ensembl_ID",
                how="left").drop(columns="Ensembl_ID")
    assert e.progression_class.notna().all(), "edge on a non-progression gene"

    traj = pd.read_csv(TRAJECTORY)[["Ensembl_ID", "Cluster", "Cluster_pattern",
                                    "Largest_transition", "Tier"]]
    e = e.merge(traj, left_on="Gene_ID", right_on="Ensembl_ID",
                how="left").drop(columns="Ensembl_ID")

    # ---- classify ---------------------------------------------------------
    e["Evidence_Source"] = SOURCE_NOTE
    e["Database_ID"] = e["Drug_ID"]              # ChEMBL; gene side is Ensembl
    e["action_class"] = e.Action_Mechanism.map(action_class)
    e["gene_direction"] = e.apply(gene_direction, axis=1)
    e["mechanism_consistency"] = e.apply(consistency, axis=1)

    unclassified = sorted(e.loc[e.action_class == "unclassified",
                                "Action_Mechanism"].unique())
    if unclassified:
        print(f"WARNING unclassified action values: {unclassified}")

    order = ["Drug", "Drug_ID", "Gene", "Gene_ID", "Relationship",
             "Action_Mechanism", "Evidence_Source", "Database_ID",
             "action_class", "progression_class", "gene_direction",
             "fibrosis_rho", "inflammation_rho", "Cluster", "Cluster_pattern",
             "Largest_transition", "Tier", "in_fibrosis_starting_set",
             "mechanism_consistency"]
    e = e[order].sort_values(["Gene", "Drug"]).reset_index(drop=True)
    e.to_csv(f"{OUT_DIR}/task2_drug_gene_edges.csv", index=False)

    # ---- the counts the plan asks for -------------------------------------
    directional = e.action_class.isin(["therapeutic-lowers", "therapeutic-raises"])
    reconciled = e.mechanism_consistency.isin(["reversal-consistent",
                                               "reversal-inconsistent"])
    with_traj = reconciled & e.Cluster.notna()

    summary = pd.DataFrame([
        ("progression genes in the master table", len(master)),
        ("progression genes with >=1 drug connection", e.Gene_ID.nunique()),
        ("total unique drugs", e.Drug_ID.nunique()),
        ("total drug-gene relationships", len(e)),
        ("relationships with known action direction", int(directional.sum())),
        ("relationships reconcilable with Paper 1 direction", int(reconciled.sum())),
        ("  ...of those, with an F0-F4 trajectory pattern", int(with_traj.sum())),
    ], columns=["measure", "value"])
    # A percentage only means something for the rows whose denominator is the
    # relationship count; gene and drug counts are left blank rather than given
    # a number that would invite the wrong comparison.
    not_a_rate = {"progression genes in the master table",
                  "progression genes with >=1 drug connection",
                  "total unique drugs"}
    summary["percent_of_relationships"] = [
        "" if m in not_a_rate else f"{100 * v / len(e):.1f}"
        for m, v in zip(summary.measure, summary.value)]
    summary.to_csv(f"{OUT_DIR}/task2_summary.csv", index=False)

    action = (e.groupby(["action_class", "Action_Mechanism"])
                .agg(edges=("Drug_ID", "size"),
                     drugs=("Drug_ID", "nunique"),
                     genes=("Gene_ID", "nunique"))
                .reset_index()
                .sort_values(["action_class", "edges"], ascending=[True, False]))
    action.to_csv(f"{OUT_DIR}/task2_action_breakdown.csv", index=False)

    cons = (e.groupby(["mechanism_consistency", "progression_class"])
              .agg(edges=("Drug_ID", "size"), drugs=("Drug_ID", "nunique"),
                   genes=("Gene_ID", "nunique"))
              .reset_index().sort_values("edges", ascending=False))
    cons.to_csv(f"{OUT_DIR}/task2_mechanism_consistency.csv", index=False)

    cons_clu = (e[reconciled].groupby(["mechanism_consistency", "Cluster_pattern"])
                  .agg(edges=("Drug_ID", "size"), drugs=("Drug_ID", "nunique"),
                       genes=("Gene_ID", "nunique"))
                  .reset_index().sort_values("edges", ascending=False))
    cons_clu.to_csv(f"{OUT_DIR}/task2_consistency_by_cluster.csv", index=False)

    # ---- report -----------------------------------------------------------
    print(f"\nwrote {OUT_DIR}/task2_drug_gene_edges.csv  ({len(e):,} rows)")
    print(f"wrote {OUT_DIR}/task2_summary.csv")
    print(f"wrote {OUT_DIR}/task2_action_breakdown.csv")
    print(f"wrote {OUT_DIR}/task2_mechanism_consistency.csv")
    print(f"wrote {OUT_DIR}/task2_consistency_by_cluster.csv\n")
    print(summary.to_string(index=False))
    print("\naction classes:")
    print(e.action_class.value_counts().to_string())
    print("\nmechanism consistency:")
    print(e.mechanism_consistency.value_counts().to_string())
    amb = e[e.mechanism_consistency == "ambiguous"]
    print(f"\nambiguous edges come from {amb.Gene_ID.nunique()} contradictory genes")


if __name__ == "__main__":
    main()
