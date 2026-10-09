"""verify_graph_counts.py
------------------------
Reconciles the edge CSVs against the relationship counts the live graph
reports, per relationship type, and prints every disagreement.

WHY THIS EXISTS
The CSVs ship 57,601 drug->disease INDICATION rows. The live graph reports
43,636 TREATS relationships. Five relationship types disagree and the total
gap is 40,247 links. Nothing caught it, because nothing compared the two.

Two innocent explanations were tested here and both fail:

  * DEDUPLICATION. If the loader used MERGE, duplicate (from, to) pairs in a
    CSV would collapse into one relationship. Measured: distinct pair count
    equals row count for all five affected types, so there are no duplicates
    to collapse.
  * DANGLING ENDPOINTS. A relationship whose endpoint node is absent is
    silently skipped by a MATCH-based load. Measured: 0 dangling rows for
    four of the five types, and 142 for PARENT_OF against a shortfall of
    15,296.

What remains is the pattern this script prints: every relationship type that
touches a Disease node is short EXCEPT ASSOCIATED_WITH, and no relationship
type that avoids Disease nodes is short at all. The session history records a
disease-node deletion followed by restoration of the nodes and the
gene-disease links. That is consistent with the pattern, and it is the
explanation this script supports -- it does not prove the history of any
individual link.

Run it with --live to check against a running database instead of the
recorded numbers:

    NEO4J_PASSWORD=... python verify_graph_counts.py --live

Usage:
    python verify_graph_counts.py
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
OKG = os.path.join(ROOT, "data", "graph_okg")
FULL = os.path.join(ROOT, "data", "graph_full")

# The counts the live graph reported, as recorded in CLAUDE.md. Replaced by
# real queries under --live.
RECORDED = {
    "EXPRESSES": 32471042, "ASSOCIATED_WITH": 1832441,
    "INTERACTS_WITH": 324116, "INVOLVED_IN": 157081,
    "HAS_PHENOTYPE": 149960, "IN_PATHWAY": 46751, "TREATS": 43636,
    "PARENT_OF": 28919, "ACTS_ON": 20674, "CONTRAINDICATED_IN": 8255,
    "TRACKS_FIBROSIS": 3645, "TRACKS_INFLAMMATION": 2739,
    "IN_DATASET": 1085, "OFF_LABEL_FOR": 722,
}

# (csv file, rel_type value in that file or None for all rows) -> graph name.
# Both ends are named so dangling endpoints can be counted.
SOURCES = [
    ("edges_drug_disease.csv", "INDICATION", "TREATS", "drug", "disease"),
    ("edges_drug_disease.csv", "CONTRAINDICATION", "CONTRAINDICATED_IN",
     "drug", "disease"),
    ("edges_drug_disease.csv", "OFF_LABEL_USE", "OFF_LABEL_FOR",
     "drug", "disease"),
    ("edges_disease_disease.csv", None, "PARENT_OF", "disease", "disease"),
    ("edges_disease_phenotype.csv", None, "HAS_PHENOTYPE",
     "disease", "phenotype"),
    ("edges_disease_gene.csv", None, "ASSOCIATED_WITH", "disease", "gene"),
    ("edges_gene_gene.csv", None, "INTERACTS_WITH", "gene", "gene"),
    ("edges_biological_process_gene.csv", None, "INVOLVED_IN",
     "bioprocess", "gene"),
    ("edges_pathway_gene.csv", None, "IN_PATHWAY", "pathway", "gene"),
    ("edges_drug_gene.csv", None, "ACTS_ON", "drug", "gene"),
]

TOUCHES_DISEASE = {"TREATS", "CONTRAINDICATED_IN", "OFF_LABEL_FOR",
                   "PARENT_OF", "HAS_PHENOTYPE", "ASSOCIATED_WITH"}


def node_ids(name):
    """Node id sets, for counting relationships with an absent endpoint."""
    if name == "gene":
        path = os.path.join(FULL, "nodes_gene.csv")
        key = "ensembl_id"
    else:
        path = os.path.join(OKG, "nodes_%s.csv" % name)
        key = "node_id"
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return {r[key] for r in csv.DictReader(fh)}


def measure():
    """Row count, distinct-pair count and dangling count per graph type."""
    nodes, out = {}, {}
    rows = Counter()
    pairs = defaultdict(set)
    dangling = Counter()
    wanted = defaultdict(list)
    for fname, rel, graph, a, b in SOURCES:
        wanted[fname].append((rel, graph, a, b))

    for fname, specs in wanted.items():
        path = os.path.join(OKG, fname)
        if not os.path.exists(path):
            print("  missing, skipped:", fname)
            continue
        for _rel, _g, a, b in specs:
            for side in (a, b):
                if side not in nodes:
                    nodes[side] = node_ids(side)
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                for rel, graph, a, b in specs:
                    if rel is not None and row.get("rel_type") != rel:
                        continue
                    f, t = row["from_id"], row["to_id"]
                    rows[graph] += 1
                    pairs[graph].add((f, t))
                    if ((nodes[a] is not None and f not in nodes[a])
                            or (nodes[b] is not None and t not in nodes[b])):
                        dangling[graph] += 1
                    break

    # the project's own edges, and the expression edges, live elsewhere
    prog = os.path.join(FULL, "edges_my_progression.csv")
    if os.path.exists(prog):
        with open(prog, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                g = row["rel"]
                rows[g] += 1
                pairs[g].add((row["ensembl_id"], row["disease_id"]))
    for graph in rows:
        out[graph] = (rows[graph], len(pairs[graph]), dangling[graph])
    return out


def live_counts():
    try:
        from neo4j import GraphDatabase
    except ImportError:
        sys.exit("--live needs `pip install neo4j`.")
    pw = os.environ.get("NEO4J_PASSWORD")
    if not pw:
        sys.exit("--live needs NEO4J_PASSWORD set.")
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    got = {}
    with GraphDatabase.driver(uri, auth=(user, pw)) as drv, \
            drv.session() as s:
        # per type, never all at once: the whole-graph count times out on a
        # 1 GB heap, while a per-type count hits the count store
        for rel in RECORDED:
            q = "MATCH ()-[r:`%s`]->() RETURN count(r) AS n" % rel
            got[rel] = s.run(q).single()["n"]
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="query a running database instead of using the "
                         "counts recorded in CLAUDE.md")
    args = ap.parse_args()

    measured = measure()
    graph = live_counts() if args.live else dict(RECORDED)
    label = "live graph" if args.live else "recorded"

    print("\n%-20s %12s %12s %12s %10s  %s"
          % ("relationship", "CSV rows", "distinct", label, "shortfall",
             "touches Disease"))
    print("-" * 94)

    total_csv = total_graph = total_gap = 0
    short = []
    for rel in sorted(measured, key=lambda r: -measured[r][0]):
        rows, distinct, dang = measured[rel]
        g = graph.get(rel)
        if g is None:
            print("%-20s %12d %12d %12s" % (rel, rows, distinct, "n/a"))
            continue
        gap = rows - g
        total_csv += rows
        total_graph += g
        total_gap += gap
        if gap:
            short.append((rel, rows, g, gap, distinct, dang))
        print("%-20s %12d %12d %12d %10s  %s"
              % (rel, rows, distinct, g, ("%+d" % -gap) if gap else "ok",
                 "yes" if rel in TOUCHES_DISEASE else "no"))

    # EXPRESSES and IN_DATASET are not in the knowledge-layer CSVs
    print("-" * 94)
    print("%-20s %12d %12s %12d %10s"
          % ("TOTAL (compared)", total_csv, "", total_graph,
             "%+d" % -total_gap if total_gap else "ok"))

    if not short:
        print("\nEverything reconciles.")
        return 0

    print("\n%d relationship type(s) short, %d links in total.\n"
          % (len(short), total_gap))
    print("Both innocent explanations tested and rejected:\n")
    for rel, rows, g, gap, distinct, dang in short:
        dup = rows - distinct
        print("  %-20s short %6d | duplicate rows %5d | dangling %5d"
              % (rel, gap, dup, dang))
        if dup >= gap:
            print("      -> duplicates could explain this one")
        if dang >= gap:
            print("      -> dangling endpoints could explain this one")
    print("\n  Deduplication cannot explain a shortfall larger than the "
          "duplicate count,\n  and a MATCH-based load cannot skip more "
          "relationships than it has dangling\n  endpoints. Where both "
          "columns are far below the shortfall, neither applies.\n")

    disease = [r for r, *_ in short if r in TOUCHES_DISEASE]
    clean = [r for r in measured
             if r in TOUCHES_DISEASE and r not in [s[0] for s in short]]
    print("  Short AND touches a Disease node:     ", ", ".join(disease)
          or "none")
    print("  Touches a Disease node but is intact: ", ", ".join(clean)
          or "none")
    print("  Short but avoids Disease nodes:       ",
          ", ".join(r for r, *_ in short if r not in TOUCHES_DISEASE)
          or "none")
    print("\n  The CSVs are the reproducible build output and are the "
          "dataset.\n  Reload the knowledge layer before trusting a live "
          "query on these types.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
