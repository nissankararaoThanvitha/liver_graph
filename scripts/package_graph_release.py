"""Package an export from scripts/export_graph.py as a GitHub release.

Leaves out the parts that may not be redistributed (KEGG: 186 Pathway nodes,
their IN_PATHWAY links and the KEGG IMPLICATED_IN links), then writes:

    <release>/liver_kg_graph_export_<version>.zip   all included CSV files + docs
    <release>/MANIFEST.csv                           file, description, rows, SHA-256
    <release>/SHA256SUMS.txt                         checksums of every asset
    <release>/VERIFICATION.json                      counts: live graph, excluded, released

Inside the zip: nodes/, relationships/, MANIFEST.csv, VERIFICATION.json,
IMPORT.md, constraints.cypher, DATA_TERMS.md. Text docs come from
docs/graph_export/.

    python scripts/package_graph_release.py --export <export folder> --release <new folder>

Second step, after the zip's CSVs have been imported into an empty database
and that database dumped with neo4j-admin database dump:

    python scripts/package_graph_release.py --release <folder> --add-dump <file.dump> \
        --imported-nodes N --imported-relationships M
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs/graph_export"
VERSION = "2026-11-03"
EXCLUDE = {  # file -> reason
    "nodes/Pathway__KEGG_legacy.csv.gz": "KEGG pathways (MSigDB KEGG legacy): KEGG data may not be redistributed",
    "relationships/IN_PATHWAY__Gene__Pathway__KEGG_legacy.csv.gz": "gene memberships of the KEGG pathways",
    "relationships/IMPLICATED_IN__Pathway__Disease__KEGG.csv.gz": "Pathway -> NAFLD links whose pathway is a KEGG pathway",
}
LABELS = 8
TYPES = 15
TARGET = {"nodes": 126999, "relationships": 35160254}

SOURCE_TEXT = {
    "Reactome": "Reactome", "Hallmark": "MSigDB Hallmark", "OptimusKG": "from OptimusKG",
    "external": "added from ChEMBL, DGIdb, GtoPdb and Open Targets",
    "ChEMBL_indication": "ChEMBL_37 indications of the added drugs", "KEGG_legacy": "KEGG legacy", "KEGG": "KEGG",
}


def describe(rel):
    parts = Path(rel).name[:-len(".csv.gz")].split("__")
    if rel.startswith("nodes/"):
        d = f"{parts[0]} nodes"
        return d + (f" ({SOURCE_TEXT.get(parts[1], parts[1])})" if len(parts) > 1 else "")
    d = f"{parts[0]} relationships, {parts[1]} -> {parts[2]}"
    return d + (f" ({SOURCE_TEXT.get(parts[3], parts[3])})" if len(parts) > 3 else "")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_sums(rel_dir):
    assets = sorted(p.name for p in rel_dir.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt")
    (rel_dir / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(rel_dir / a)}  {a}\n" for a in assets), encoding="utf-8")
    return assets


def add_dump(rel_dir, dump, nodes, rels):
    """Add the dump of the test-imported database and the import counts."""
    v = json.loads((rel_dir / "VERIFICATION.json").read_text(encoding="utf-8"))
    name = f"liver_kg_{VERSION}.dump"
    shutil.copy(dump, rel_dir / name)
    v["test_import"] = {"imported_nodes": nodes, "imported_relationships": rels,
                        "matches_release": (nodes, rels) == (v["released"]["nodes"], v["released"]["relationships"]),
                        "dump": name, "dump_made_from": "the database test-imported from the CSV files"}
    v["checks"]["test import of the CSV files gives the released counts"] = v["test_import"]["matches_release"]
    v["verified"] = all(v["checks"].values())
    (rel_dir / "VERIFICATION.json").write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(v["test_import"], indent=2), "\nverified:", v["verified"])
    print("assets:", ", ".join(write_sums(rel_dir) + ["SHA256SUMS.txt"]))
    return 0 if v["verified"] else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export")
    ap.add_argument("--release", required=True)
    ap.add_argument("--add-dump", help="second step: add the dump of the test-imported database")
    ap.add_argument("--imported-nodes", type=int)
    ap.add_argument("--imported-relationships", type=int)
    args = ap.parse_args()
    if args.add_dump:
        return add_dump(Path(args.release), Path(args.add_dump), args.imported_nodes, args.imported_relationships)
    exp, rel_dir = Path(args.export), Path(args.release)
    if rel_dir.exists() and any(rel_dir.iterdir()):
        sys.exit(f"{rel_dir} is not empty")
    rel_dir.mkdir(parents=True, exist_ok=True)

    counts = json.loads((exp / "export_counts.json").read_text(encoding="utf-8"))
    assert counts["matches_live"], "export does not match the live graph"
    assert (counts["live_nodes"], counts["live_relationships"]) == tuple(TARGET.values())
    rows = counts["rows_per_file"]
    missing = [f for f in EXCLUDE if f not in rows]
    assert not missing, f"expected files not in export: {missing}"

    included = {f: n for f, n in rows.items() if f not in EXCLUDE}
    excluded = {f: rows[f] for f in EXCLUDE}

    def total(d, kind):
        return sum(n for f, n in d.items() if f.startswith(kind))

    labels = sorted({Path(f).name.split("__")[0].replace(".csv.gz", "") for f in included if f.startswith("nodes/")})
    types = sorted({Path(f).name.split("__")[0] for f in included if f.startswith("relationships/")})
    verification = {
        "graph_version": VERSION,
        "exported": counts["exported"],
        "live_graph": {"nodes": counts["live_nodes"], "relationships": counts["live_relationships"],
                       "entity_types": len(counts["labels"]), "relationship_types": len(counts["relationship_types"])},
        "export_matches_live_graph": counts["matches_live"],
        "excluded": {"nodes": total(excluded, "nodes/"), "relationships": total(excluded, "relationships/"),
                     "files": {f: {"rows": excluded[f], "reason": EXCLUDE[f]} for f in excluded}},
        "released": {"nodes": total(included, "nodes/"), "relationships": total(included, "relationships/"),
                     "entity_types": len(labels), "relationship_types": len(types),
                     "entity_type_names": labels, "relationship_type_names": types},
    }
    v = verification
    v["checks"] = {
        "live graph: 126,999 nodes, 35,160,254 relationships, 8 entity types, 15 relationship types":
            (v["live_graph"]["nodes"], v["live_graph"]["relationships"], v["live_graph"]["entity_types"],
             v["live_graph"]["relationship_types"]) == (TARGET["nodes"], TARGET["relationships"], LABELS, TYPES),
        "released + excluded = live graph":
            v["released"]["nodes"] + v["excluded"]["nodes"] == v["live_graph"]["nodes"]
            and v["released"]["relationships"] + v["excluded"]["relationships"] == v["live_graph"]["relationships"],
        "release keeps all 8 entity types and 15 relationship types":
            (len(labels), len(types)) == (LABELS, TYPES),
    }
    v["verified"] = all(v["checks"].values())

    manifest = [{"file": f, "description": describe(f), "rows": n, "sha256": sha256(exp / f)}
                for f, n in sorted(included.items())]
    with open(rel_dir / "MANIFEST.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "description", "rows", "sha256"])
        w.writeheader()
        w.writerows(manifest)
    (rel_dir / "VERIFICATION.json").write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")

    zip_name = f"liver_kg_graph_export_{VERSION}.zip"
    with zipfile.ZipFile(rel_dir / zip_name, "w", compression=zipfile.ZIP_STORED) as z:  # CSVs already gzipped
        for f in sorted(included):
            z.write(exp / f, f)
        z.write(rel_dir / "MANIFEST.csv", "MANIFEST.csv")
        z.write(rel_dir / "VERIFICATION.json", "VERIFICATION.json")
        for doc in ("IMPORT.md", "constraints.cypher", "DATA_TERMS.md"):
            z.write(DOCS / doc, doc)
    for doc in ("IMPORT.md", "DATA_TERMS.md"):
        shutil.copy(DOCS / doc, rel_dir / doc)

    assets = write_sums(rel_dir)

    print(json.dumps({k: v[k] for k in ("live_graph", "released", "checks", "verified")}, indent=2))
    print("excluded:", v["excluded"]["nodes"], "nodes,", v["excluded"]["relationships"], "relationships")
    print("assets in", rel_dir, ":", ", ".join(assets + ["SHA256SUMS.txt"]))
    return 0 if v["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
