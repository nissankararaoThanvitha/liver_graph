"""build_progression_edges.py
-----------------------------
Writes the TRACKS_FIBROSIS and TRACKS_INFLAMMATION edges -- the only edges in
the graph derived from these patients rather than imported.

WHY THIS SCRIPT EXISTS
These edges were previously produced interactively, and nothing in the
pipeline regenerated them. The file therefore kept the gene counts of an
earlier progression run while every other output moved on, and three scripts
read it without noticing -- including export_triples.py, which feeds the
drug-repurposing work. An edge file that nothing regenerates is a result that
cannot be re-derived.

WHAT IT WRITES
One edge per gene per ladder, for genes that pass the project's inclusion
rule: BH q < 0.05 AND every study that tested the gene agreeing on the
direction of change. Both conditions -- q alone admits roughly 10,900 genes.

    Gene -TRACKS_FIBROSIS->     EFO_0003095  non-alcoholic fatty liver disease
    Gene -TRACKS_INFLAMMATION-> EFO_1001249  non-alcoholic steatohepatitis

Each edge carries the cross-study median rho, the combined q, how many
studies contributed, and the direction, so a query can filter on strength
without returning to the source tables.

Usage:
    python build_progression_edges.py
    python build_progression_edges.py --progression data/progression_full \\
                                      --out data/graph_full
"""
import argparse
import csv
import os
import sys

# The two ladders, and the disease node each attaches to. Both ids are
# checked against the knowledge layer before anything is written: an edge
# pointing at a node that does not exist loads as nothing and reports no
# error.
LADDERS = [
    ("fibrosis", "TRACKS_FIBROSIS", "EFO_0003095"),
    ("disease", "TRACKS_INFLAMMATION", "EFO_1001249"),
]
FIELDS = ["ensembl_id", "symbol", "rel", "disease_id", "rho", "q",
          "n_studies", "direction"]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--progression", default="data/progression_full")
    ap.add_argument("--knowledge", default="data/graph_okg",
                    help="used only to confirm the disease nodes exist")
    ap.add_argument("--out", default="data/graph_full")
    a = ap.parse_args()

    dis_path = os.path.join(a.knowledge, "nodes_disease.csv")
    if os.path.exists(dis_path):
        known = {r["node_id"] for r in read_csv(dis_path)}
        for _axis, rel, did in LADDERS:
            if did not in known:
                sys.exit("%s points at %s, which is not a node in %s"
                         % (rel, did, dis_path))
        print("disease nodes confirmed present in the knowledge layer")
    else:
        print("WARNING: %s not found, disease ids not checked" % dis_path)

    rows, counts = [], {}
    for axis, rel, did in LADDERS:
        src = os.path.join(a.progression, "progression_%s.csv" % axis)
        if not os.path.exists(src):
            sys.exit("missing %s" % src)
        n = 0
        for r in read_csv(src):
            # the project's inclusion rule, both conditions
            if not (float(r["q_value"]) < 0.05
                    and r["n_agree"] == r["n_studies"]):
                continue
            rho = float(r["median_rho"])
            rows.append({
                "ensembl_id": r["ensembl_id"],
                "symbol": r.get("symbol", ""),
                "rel": rel,
                "disease_id": did,
                "rho": rho,
                "q": r["q_value"],
                "n_studies": int(float(r["n_studies"])),
                "direction": "rises" if rho > 0 else "falls",
            })
            n += 1
        counts[rel] = n
        print("  %-22s %5d genes  (from %s)" % (rel, n, os.path.basename(src)))

    rows.sort(key=lambda d: (d["rel"], -abs(d["rho"])))
    os.makedirs(a.out, exist_ok=True)
    out = os.path.join(a.out, "edges_my_progression.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print("\n-> %s  (%d edges)" % (out, len(rows)))
    print("   these are the project's own contribution to the graph;")
    print("   every other edge type is imported or measured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
