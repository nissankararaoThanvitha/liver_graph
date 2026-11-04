"""Check the node and relationship counts of the extended graph (3 Nov 2026).

The Paper 1 graph (126,244 nodes; 35,132,831 relationships; 14 types) was
extended for Paper 2 in these steps:

  0.4  5,216 drug-gene links and 519 new Drug nodes       data/graph_drug_layer/new_drug_gene_links
  0.5  action directions on 297 existing ACTS_ON links    data/graph_drug_layer/external_action_directions
       (properties only; no count change)
  0.6  236 KEGG/Hallmark Pathway nodes, 20,031 IN_PATHWAY data/graph_msigdb
  0.7  89 Pathway -> NAFLD IMPLICATED_IN links (new type) data/graph_pathway_disease
  0.8  2,087 TREATS links for the drugs added in 0.4      data/graph_drug_layer/added_drug_indications

Expected result: 126,999 nodes; 35,160,254 relationships; 15 types.

Without --live this rebuilds the expected counts from the committed files:
the Paper 1 per-type counts (final_combined_2026-10-10/graph_verification.json)
plus the rows each step wrote, and checks them against the before/after
counts in each step's write log.

With --live it also counts a running database and compares, per type:
    NEO4J_PASSWORD=... python scripts/verify_extended_graph_counts.py --live

Writes docs/provenance/extended_graph_verification.json. Run from the project root.
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
DL = ROOT / "data/graph_drug_layer"
OUT = ROOT / "docs/provenance/extended_graph_verification.json"
TARGET = {"nodes": 126999, "relationships": 35160254, "relationship_types": 15}


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

    l04 = log(DL / "new_drug_gene_links/graph_write/write_log.json")
    l05 = log(DL / "external_action_directions/graph_write/write_log.json")
    l08 = log(DL / "added_drug_indications/graph_write/write_log.json")
    nodes = l04["before"]["nodes"]
    assert l04["before"]["rels"] == base["total_relationships"]

    links = rows(DL / "new_drug_gene_links/graph_write/links_written.csv")
    new_drugs = {r["Drug_ID"] for r in links if r["node_kind"].startswith("ExternalDrug")}
    pathways = rows(ROOT / "data/graph_msigdb/nodes_pathway_msigdb.csv")
    in_pathway = rows(ROOT / "data/graph_msigdb/edges_pathway_gene_msigdb.csv")
    implicated = rows(ROOT / "data/graph_pathway_disease/edges_pathway_nafld.csv")
    treats = rows(DL / "added_drug_indications/graph_write/indication_pairs_plan.csv",
                  lambda r: r["status"] == "write")
    directions = rows(DL / "external_action_directions/external_layer_links.csv")

    steps = [
        # step, nodes added, {type: relationships added}
        ("0.4 drug-gene links", len(new_drugs), {"ACTS_ON": len(links)}),
        ("0.5 action directions", 0, {}),
        ("0.6 KEGG/Hallmark pathways", len(pathways), {"IN_PATHWAY": len(in_pathway)}),
        ("0.7 pathway-NAFLD links", 0, {"IMPLICATED_IN": len(implicated)}),
        ("0.8 added-drug indications", 0, {"TREATS": len(treats)}),
    ]
    trail = []
    for name, dn, drels in steps:
        nodes += dn
        for t, n in drels.items():
            counts[t] = counts.get(t, 0) + n
        trail.append({"step": name, "nodes_added": dn, "relationships_added": drels,
                      "nodes_after": nodes, "relationships_after": sum(counts.values())})

    # each write log must agree with the running totals
    checks = {
        "0.4 log after = files": (l04["after"]["nodes"], l04["after"]["rels"])
                                 == (trail[0]["nodes_after"], trail[0]["relationships_after"]),
        "0.4 log links/new drugs = files": (l04["links_written"], l04["external_drug_nodes_created"])
                                           == (len(links), len(new_drugs)),
        "0.5 log links = files, ACTS_ON count unchanged": l05["relationships_written"] == len(directions) == 297
                                                          and l05["ACTS_ON_before"] == l05["ACTS_ON_after"],
        "0.8 log before = files after 0.7": (l08["before"]["nodes"], l08["before"]["rels"])
                                            == (trail[3]["nodes_after"], trail[3]["relationships_after"]),
        "0.8 log after = files": (l08["after"]["nodes"], l08["after"]["rels"], l08["links_written"])
                                 == (trail[4]["nodes_after"], trail[4]["relationships_after"], len(treats)),
        "0.8 log TREATS after = files": l08["after"]["treats"] == counts["TREATS"],
    }
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
        "mode": "live" if args.live else "files and write logs only",
        "target": TARGET,
        "expected_from_files": {"nodes": nodes, "relationships": total,
                                "relationship_types": len(counts), "counts": counts},
        "steps": trail,
        "write_log_checks": checks,
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
