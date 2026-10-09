"""What each relationship should count AFTER the load.

A MATCH-based load silently drops any edge whose endpoint node is absent.
That is the correct behaviour -- a knowledge edge pointing at a gene this
project never measured should be dropped, not invented -- but it means the
post-load count is not always the CSV row count, and a verification that
expects the row count would report a false shortfall.
"""
import csv
import os

OKG = "data/graph_okg"
FULL = "data/graph_full"


def ids(path, key):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return {r[key] for r in csv.DictReader(fh)}


gene = ids(os.path.join(FULL, "nodes_gene.csv"), "ensembl_id")
dis = ids(os.path.join(OKG, "nodes_disease.csv"), "node_id")
drug = ids(os.path.join(OKG, "nodes_drug.csv"), "node_id")
bp = ids(os.path.join(OKG, "nodes_bioprocess.csv"), "node_id")
pw = ids(os.path.join(OKG, "nodes_pathway.csv"), "node_id")
phe = ids(os.path.join(OKG, "nodes_phenotype.csv"), "node_id")

SPECS = [
    ("edges_gene_gene.csv", None, "INTERACTS_WITH", gene, gene),
    ("edges_disease_gene.csv", None, "ASSOCIATED_WITH", gene, dis),
    ("edges_biological_process_gene.csv", None, "INVOLVED_IN", gene, bp),
    ("edges_pathway_gene.csv", None, "IN_PATHWAY", gene, pw),
    ("edges_drug_gene.csv", None, "ACTS_ON", drug, gene),
    ("edges_drug_disease.csv", "INDICATION", "TREATS", drug, dis),
    ("edges_drug_disease.csv", "CONTRAINDICATION", "CONTRAINDICATED_IN",
     drug, dis),
    ("edges_drug_disease.csv", "OFF_LABEL_USE", "OFF_LABEL_FOR", drug, dis),
    ("edges_disease_disease.csv", None, "PARENT_OF", dis, dis),
    ("edges_disease_phenotype.csv", None, "HAS_PHENOTYPE", dis, phe),
]

print("%-22s %10s %10s %10s" % ("relationship", "CSV rows", "loadable",
                                "dropped"))
print("-" * 56)
for fname, rel_filter, name, src, dst in SPECS:
    rows = loadable = 0
    pairs = set()
    with open(os.path.join(OKG, fname), newline="",
              encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if rel_filter and r["rel_type"] != rel_filter:
                continue
            rows += 1
            if r["from_id"] in src and r["to_id"] in dst:
                loadable += 1
                pairs.add((r["from_id"], r["to_id"]))
    note = ""
    if len(pairs) != loadable:
        note = "  (%d distinct pairs -- MERGE would collapse %d)" % (
            len(pairs), loadable - len(pairs))
    print("%-22s %10d %10d %10d%s"
          % (name, rows, loadable, rows - loadable, note))

# the project's own edges, from the current file
with open(os.path.join(FULL, "edges_my_progression.csv"), newline="",
          encoding="utf-8-sig") as fh:
    prog = list(csv.DictReader(fh))
for rel in ("TRACKS_FIBROSIS", "TRACKS_INFLAMMATION"):
    sub = [r for r in prog if r["rel"] == rel]
    ok = sum(1 for r in sub
             if r["ensembl_id"] in gene and r["disease_id"] in dis)
    print("%-22s %10d %10d %10d" % (rel, len(sub), ok, len(sub) - ok))
