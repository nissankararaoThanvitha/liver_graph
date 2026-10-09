"""Prove the subgraph matches the graph Neo4j actually holds.

kg_subgraph.py reads CSVs (data/graph_okg) rather than querying Neo4j, so it
runs for anyone with a clone and no database. The cost of that choice is an
assumption: that those CSVs are what the database contains.

That assumption is exactly what went wrong once. An earlier version read
data/graph_kg -- the superseded PrimeKG layer -- while its docstring claimed
it read "the same CSVs that were loaded into Neo4j". Nothing caught it,
because nothing checked.

This checks, at four levels, and prints every disagreement rather than
summarising:

    1. node counts        Pathway and BioProcess
    2. edge counts        IN_PATHWAY and INVOLVED_IN, whole graph
    3. membership counts  genes per mechanism, for the twelve in the figure
    4. membership itself  the actual gene IDs of each of the twelve

Level 4 is the one that matters: counts can agree while the sets differ.

CONNECTION
Credentials come from the environment, never from this file:

    NEO4J_URI       default bolt://localhost:7687
    NEO4J_USER      default neo4j
    NEO4J_PASSWORD  required

Needs `pip install neo4j` and the database running. kg_subgraph.py needs
neither -- that is the point of it reading CSVs.

Usage:
    NEO4J_PASSWORD=... python Paper1_HighConfidence/verify_against_neo4j.py
"""
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KG = ROOT / "data/graph_okg"

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
USER = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD")

fails = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        fails.append(name)


if not PASSWORD:
    sys.exit("NEO4J_PASSWORD is not set. See this file's docstring.")
try:
    from neo4j import GraphDatabase
except ImportError:
    sys.exit("pip install neo4j")

# --- the CSV side: exactly the files kg_subgraph.py reads ---
csv_edges = pd.concat([
    pd.read_csv(KG / "edges_pathway_gene.csv",
                usecols=["from_id", "to_id"]).assign(rel="IN_PATHWAY"),
    pd.read_csv(KG / "edges_biological_process_gene.csv",
                usecols=["from_id", "to_id"]).assign(rel="INVOLVED_IN"),
], ignore_index=True)
csv_edges["to_id"] = csv_edges.to_id.astype(str)

sel = pd.read_excel(HERE / "12_KG_supplementary.xlsx",
                    sheet_name="3_all_mechanisms_ranked")
sel = sel[sel.selected_for_figure]
ids = [str(i) for i in sel.Mechanism_ID]

drv = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
with drv.session() as s:
    nodes = {r["label"]: r["n"] for r in s.run(
        "MATCH (n) WHERE n:Pathway OR n:BioProcess "
        "RETURN labels(n)[0] AS label, count(*) AS n").data()}
    rels = {r["rel"]: r["n"] for r in s.run(
        "MATCH (g:Gene)-[r:IN_PATHWAY|INVOLVED_IN]->() "
        "RETURN type(r) AS rel, count(*) AS n").data()}
    members = {r["id"]: set(r["genes"]) for r in s.run(
        "MATCH (g:Gene)-[:IN_PATHWAY|INVOLVED_IN]->(m) "
        "WHERE m.node_id IN $ids "
        "RETURN m.node_id AS id, collect(DISTINCT g.ensembl_id) AS genes",
        ids=ids).data()}
drv.close()

print("1. NODE COUNTS")
for label, f in (("Pathway", "nodes_pathway.csv"),
                 ("BioProcess", "nodes_bioprocess.csv")):
    n_csv = len(pd.read_csv(KG / f))
    check(label, n_csv == nodes.get(label),
          f"CSV {n_csv:,} vs Neo4j {nodes.get(label):,}")

print("\n2. EDGE COUNTS (whole graph)")
for rel, want in (("IN_PATHWAY", "edges_pathway_gene.csv"),
                  ("INVOLVED_IN", "edges_biological_process_gene.csv")):
    n_csv = int((csv_edges.rel == rel).sum())
    check(rel, n_csv == rels.get(rel),
          f"CSV {n_csv:,} vs Neo4j {rels.get(rel):,}")

print("\n3 & 4. THE TWELVE MECHANISMS IN THE FIGURE")
for _, r in sel.iterrows():
    mid = str(r.Mechanism_ID)
    csv_set = set(csv_edges[csv_edges.to_id == mid].from_id)
    db_set = members.get(mid, set())
    same = csv_set == db_set
    extra = ""
    if not same:
        extra = (f"CSV {len(csv_set)} vs Neo4j {len(db_set)}; "
                 f"CSV-only {sorted(csv_set - db_set)[:3]}, "
                 f"Neo4j-only {sorted(db_set - csv_set)[:3]}")
    check(f"{r.mechanism[:50]:50s} ({len(csv_set):>3} genes)", same, extra)

print("\n" + "=" * 66)
if fails:
    print(f"{len(fails)} CHECK(S) FAILED -- the figure does NOT match the graph:")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("ALL CHECKS PASSED -- every mechanism in the figure has exactly the")
print("same gene membership in data/graph_okg as in the live Neo4j graph.")
print("=" * 66)
