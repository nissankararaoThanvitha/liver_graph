"""Export the whole live graph as gzipped CSV files that neo4j-admin can import.

Every node and relationship is written with all its properties. Files are
split by label / relationship type and, where the graph mixes sources, by
source, so parts with different licences can be included or left out of a
release file by file:

    nodes/<Label>[__<source>].csv.gz
    relationships/<TYPE>__<StartLabel>__<EndLabel>[__<source>].csv.gz

Splits by source:
    Pathway nodes, IN_PATHWAY     Reactome / KEGG_legacy / Hallmark
    IMPLICATED_IN                 Reactome / KEGG (pathway database)
    Drug nodes, ACTS_ON, TREATS   OptimusKG

Header format is neo4j-admin import (name:type, :ID(Label), :START_ID(Label),
:END_ID(Label), :TYPE, :LABEL). Strings are always quoted, so an empty string
stays an empty string ("") and a missing property stays empty. Lists use ';'.

Writes export_counts.json (rows per file) next to the files. Run from the
project root:
    python scripts/export_graph.py --out <folder>
Password: NEO4J_PASSWORD, or else the neo4j-liver-kg entry in .mcp.json.
"""
import argparse
import csv
import gzip
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
KEY = {"Gene": "ensembl_id", "Sample": "sample_id", "Dataset": "dataset_id"}  # all others: node_id
TYPES = {"STRING": "string", "INTEGER": "long", "FLOAT": "double", "BOOLEAN": "boolean",
         "LIST<STRING NOT NULL>": "string[]"}


def password():
    if os.environ.get("NEO4J_PASSWORD"):
        return os.environ["NEO4J_PASSWORD"]
    return json.load(open(ROOT / ".mcp.json"))["mcpServers"]["neo4j-liver-kg"]["env"]["NEO4J_PASSWORD"]


def admin_type(types):
    names = {t.replace(" NOT NULL", "") if not t.startswith("LIST") else t.rsplit(" NOT NULL", 1)[0]
             for t in types or []}
    if len(names) != 1 or next(iter(names)) not in TYPES:
        sys.exit(f"property with unsupported or mixed types: {types}")
    return TYPES[next(iter(names))]


def schema(s):
    nodes, rels = defaultdict(dict), defaultdict(dict)
    for r in s.run("CALL db.schema.nodeTypeProperties()"):
        if r["propertyName"]:
            nodes[r["nodeLabels"][0]][r["propertyName"]] = admin_type(r["propertyTypes"])
    for r in s.run("CALL db.schema.relTypeProperties()"):
        t = r["relType"].strip(":`")
        rels.setdefault(t, {})
        if r["propertyName"]:
            rels[t][r["propertyName"]] = admin_type(r["propertyTypes"])
    return nodes, rels


def cell(v, kind):
    if v is None:
        return None
    if kind == "string[]":
        return ";".join(v)
    if kind == "boolean":
        return "true" if v else "false"
    return v


def node_split(label, p):
    if label == "Pathway":
        return p.get("source") or "Reactome"
    if label == "Drug":
        if p.get("source") not in (None, "OptimusKG"):
            raise ValueError("Drug node outside the current OptimusKG-only scope")
        for field in ("smiles_source", "max_phase_source", "molecule_type_source", "recovered_name_source"):
            if p.get(field) not in (None, "OptimusKG"):
                raise ValueError(f"Drug field outside the current scope: {field}")
        return "OptimusKG"
    return None


def rel_split(t, p):
    if t == "IN_PATHWAY":
        return p.get("source") or "Reactome"
    if t == "IMPLICATED_IN":
        return p.get("database")
    if t == "ACTS_ON":
        if p.get("layer") or any(k.startswith("external_action_") for k in p):
            raise ValueError("Drug-gene annotation outside the current OptimusKG-only scope")
        return "OptimusKG"
    if t == "TREATS":
        if p.get("layer") or p.get("source"):
            raise ValueError("Drug indication outside the current OptimusKG-only scope")
        return "OptimusKG"
    return None


class Files:
    """One open gzip CSV writer per output file, created on first row."""

    def __init__(self, out):
        self.out, self.open, self.rows = out, {}, defaultdict(int)

    def write(self, rel_path, header, row):
        if rel_path not in self.open:
            path = self.out / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            fh = gzip.open(path, "wt", encoding="utf-8", newline="", compresslevel=6)
            w = csv.writer(fh, quoting=csv.QUOTE_STRINGS, lineterminator="\n")
            w.writerow(header)
            self.open[rel_path] = (fh, w)
        self.open[rel_path][1].writerow(row)
        self.rows[rel_path] += 1

    def close(self):
        for fh, _ in self.open.values():
            fh.close()


def name(*parts):
    return "__".join(p for p in parts if p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    ap.add_argument("--user", default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} is not empty; use a new folder so no old file is mixed in")
    out.mkdir(parents=True, exist_ok=True)

    drv = GraphDatabase.driver(args.uri, auth=(args.user, password()))
    files = Files(out)
    t0 = time.time()
    with drv.session(database="neo4j", fetch_size=20000) as s:
        nprops, rprops = schema(s)
        labels = [r["l"] for r in s.run("CALL db.labels() YIELD label AS l RETURN l ORDER BY l")]
        types = [r["t"] for r in s.run("CALL db.relationshipTypes() YIELD relationshipType AS t RETURN t ORDER BY t")]
        # Neo4j retains label/type tokens after their last record is removed.
        labels = [label for label in labels if s.run(f"MATCH (n:`{label}`) RETURN count(n) AS n").single()["n"]]
        types = [rel for rel in types if s.run(f"MATCH ()-[r:`{rel}`]->() RETURN count(r) AS n").single()["n"]]

        for label in labels:
            key = KEY.get(label, "node_id")
            cols = [key] + sorted(c for c in nprops[label] if c != key)
            header = [f"{key}:ID({label})"] + [f"{c}:{nprops[label][c]}" for c in cols[1:]] + [":LABEL"]
            for r in s.run(f"MATCH (n:`{label}`) RETURN properties(n) AS p"):
                p = r["p"]
                row = [p[key]] + [cell(p.get(c), nprops[label][c]) for c in cols[1:]] + [label]
                files.write(f"nodes/{name(label, node_split(label, p))}.csv.gz", header, row)
            print(f"{time.time() - t0:7.0f}s  nodes {label}", flush=True)

        for t in types:
            cols = sorted(rprops.get(t, {}))
            q = (f"MATCH (a)-[r:`{t}`]->(b) RETURN labels(a)[0] AS la, labels(b)[0] AS lb, "
                 "coalesce(a.node_id, a.ensembl_id, a.sample_id, a.dataset_id) AS ia, "
                 "coalesce(b.node_id, b.ensembl_id, b.sample_id, b.dataset_id) AS ib, properties(r) AS p")
            for r in s.run(q):
                la, lb, p = r["la"], r["lb"], r["p"]
                header = [f":START_ID({la})", f":END_ID({lb})"] + [f"{c}:{rprops[t][c]}" for c in cols] + [":TYPE"]
                row = [r["ia"], r["ib"]] + [cell(p.get(c), rprops[t][c]) for c in cols] + [t]
                files.write(f"relationships/{name(t, la, lb, rel_split(t, p))}.csv.gz", header, row)
            print(f"{time.time() - t0:7.0f}s  relationships {t}", flush=True)

        live_nodes = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        live_rels = sum(s.run(f"MATCH ()-[r:`{t}`]->() RETURN count(r) AS n").single()["n"] for t in types)
    files.close()
    drv.close()

    rows = dict(sorted(files.rows.items()))
    n_nodes = sum(v for k, v in rows.items() if k.startswith("nodes/"))
    n_rels = sum(v for k, v in rows.items() if k.startswith("relationships/"))
    summary = {"exported": time.strftime("%Y-%m-%d"), "labels": labels, "relationship_types": types,
               "nodes": n_nodes, "relationships": n_rels, "live_nodes": live_nodes,
               "live_relationships": live_rels,
               "matches_live": n_nodes == live_nodes and n_rels == live_rels, "rows_per_file": rows}
    (out / "export_counts.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"exported {n_nodes:,} nodes, {n_rels:,} relationships in {len(rows)} files; "
          f"matches live graph: {summary['matches_live']}")
    return 0 if summary["matches_live"] else 1


if __name__ == "__main__":
    sys.exit(main())
