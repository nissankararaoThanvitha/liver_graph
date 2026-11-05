"""Verify the current OptimusKG drug layer and retained pathway additions.

The original graph (126,244 nodes; 35,132,831 relationships; 14 types) plus
236 KEGG/Hallmark pathways, 20,031 memberships and 89 pathway--NAFLD links
contains 126,480 nodes and 35,152,951 relationships across 15 types.
Drug entities and drug relationships come through OptimusKG only.
--live compares every active relationship type against a running database.
The saved result is docs/provenance/extended_graph_verification.json.
"""
import argparse
import csv
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "final_combined_2026-10-10/graph_verification.json"
OUT = ROOT / "docs/provenance/extended_graph_verification.json"
TARGET = {"nodes": 126480, "relationships": 35152951, "relationship_types": 15}


def rows(path, where=None):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [r for r in csv.DictReader(fh) if where is None or where(r)]


def log(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def expected():
    base = log(BASE)
    counts = dict(base["counts"])
    assert sum(counts.values()) == base["total_relationships"] == 35132831
    assert len(counts) == 14
    msig = log(ROOT / "data/graph_msigdb/counts.json")
    hallmark_nodes = rows(ROOT / "data/graph_msigdb/nodes_pathway_msigdb.csv")
    hallmark_links = rows(ROOT / "data/graph_msigdb/edges_pathway_gene_msigdb.csv")
    implicated = rows(ROOT / "data/graph_pathway_disease/edges_pathway_nafld.csv")
    checks = {
        "Hallmark node/link CSVs match the source counts":
            (len(hallmark_nodes), len(hallmark_links)) ==
            (msig["Hallmark"]["pathways"], msig["Hallmark"]["in_pathway_links"]),
        "original OptimusKG drug-gene count retained": counts["ACTS_ON"] == 20674,
        "original OptimusKG indication count retained": counts["TREATS"] == 57601,
        "pathway-disease rows have unique endpoints":
            len({(r["pathway_id"], r["disease_id"]) for r in implicated}) == len(implicated),
    }
    nodes = 126244
    trail = []
    for name, dn, dr in (
        ("KEGG/Hallmark pathways", sum(msig[x]["pathways"] for x in ("KEGG_legacy", "Hallmark")),
         {"IN_PATHWAY": sum(msig[x]["in_pathway_links"] for x in ("KEGG_legacy", "Hallmark"))}),
        ("pathway-NAFLD links", 0, {"IMPLICATED_IN": len(implicated)}),
    ):
        nodes += dn
        for rel, n in dr.items():
            counts[rel] = counts.get(rel, 0) + n
        trail.append({"step": name, "nodes_added": dn, "relationships_added": dr,
                      "nodes_after": nodes, "relationships_after": sum(counts.values())})
    return nodes, counts, trail, checks


def password():
    if os.environ.get("NEO4J_PASSWORD"):
        return os.environ["NEO4J_PASSWORD"]
    return json.load(open(ROOT / ".mcp.json"))["mcpServers"]["neo4j-liver-kg"]["env"]["NEO4J_PASSWORD"]


def live():
    from neo4j import GraphDatabase
    drv = GraphDatabase.driver(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                               auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password()))
    with drv.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        types = [r["t"] for r in s.run("CALL db.relationshipTypes() YIELD relationshipType AS t RETURN t")]
        # one type at a time: each hits the count store; a whole-graph scan can time out
        counts = {t: s.run(f"MATCH ()-[r:`{t}`]->() RETURN count(r) AS n").single()["n"] for t in types}
    drv.close()
    return nodes, {t: n for t, n in counts.items() if n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="also count a running Neo4j database")
    args = ap.parse_args()

    nodes, counts, trail, checks = expected()
    total = sum(counts.values())
    result = {
        "date": date.today().isoformat(),
        "mode": "live" if args.live else "files only",
        "target": TARGET,
        "expected_from_files": {"nodes": nodes, "relationships": total,
                                "relationship_types": len(counts), "counts": counts},
        "steps": trail,
        "input_checks": checks,
        "files_match_target": (nodes, total, len(counts)) == tuple(TARGET.values()),
    }
    if args.live:
        ln, lc = live()
        result["live"] = {"nodes": ln, "relationships": sum(lc.values()),
                          "relationship_types": len(lc), "counts": lc}
        result["live_per_type_differences"] = {t: lc.get(t, 0) - counts.get(t, 0)
                                               for t in sorted(set(lc) | set(counts))
                                               if lc.get(t, 0) != counts.get(t, 0)}
        result["live_matches_target"] = (ln, sum(lc.values()), len(lc)) == tuple(TARGET.values())
    result["verified"] = (result["files_match_target"] and all(checks.values())
                          and result.get("live_matches_target", True)
                          and not result.get("live_per_type_differences"))

    print(f"{'relationship':20s} {'expected':>12s}" + (f" {'live':>12s}" if args.live else ""))
    for t in sorted(counts, key=lambda t: -counts[t]):
        print(f"{t:20s} {counts[t]:12,d}" + (f" {result['live']['counts'].get(t, 0):12,d}" if args.live else ""))
    print(f"\nexpected: {nodes:,} nodes; {total:,} relationships; {len(counts)} types")
    if args.live:
        L = result["live"]
        print(f"live:     {L['nodes']:,} nodes; {L['relationships']:,} relationships; {L['relationship_types']} types")
    for k, v in checks.items():
        print(("ok    " if v else "FAIL  ") + k)
    print("verified:", result["verified"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("written:", OUT.relative_to(ROOT))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
