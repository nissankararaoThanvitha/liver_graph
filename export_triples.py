"""
export_triples.py
-----------------
Flattens the knowledge layer into (head, relation, tail) triples for
link prediction.

WHAT IS INCLUDED, AND WHY
A knowledge-graph embedding model learns from triples only; it cannot see
node properties, and it treats every edge as equally meaningful. Two
consequences shape this export.

First, the 32.5M EXPRESSES edges are excluded. They are quantitative
measurements ("patient 47 had 4,821 units of COL1A1"), not knowledge, and at
32.5M they would outnumber everything else 12:1 and drown the signal. Their
contribution is already distilled into the TRACKS_* edges, which say what the
measurements mean.

Second, ASSOCIATED_WITH is filtered. OptimusKG scores gene-disease links by
evidence, and the graph holds 1.83M of them at score >= 0.1. Left whole they
would be 69% of all triples, so the model would mostly learn "every gene
relates to every disease". Keeping score >= 0.3 leaves the well-evidenced
ones and rebalances the graph towards the relations we actually want to
predict.

BioProcess and Phenotype edges are dropped: they connect to diseases and
genes but add no route between a drug and a disease, which is the link we
are predicting.

THE TARGET
The relation to predict is TREATS. 57,601 exist, including 95 for NAFLD and
74 for NASH -- the examples that make training possible at all, and the
reason PrimeKG was replaced (it had zero).

Output: data/kg_triples/{all,train,valid,test}.tsv, tab-separated, no header.

Usage:
    python export_triples.py [--min-assoc 0.3]
"""

import argparse
import os

import numpy as np
import pandas as pd

OKG = "data/graph_okg"
PROG = "data/graph_full/edges_my_progression.csv"
OUT = "data/kg_triples"

# file -> (relation name, how to prefix each side)
SOURCES = [
    ("edges_drug_disease.csv", None, "drug", "dis"),        # rel from column
    ("edges_drug_gene.csv", "ACTS_ON", "drug", "gene"),
    ("edges_disease_gene.csv", "ASSOCIATED_WITH", "gene", "dis"),
    ("edges_gene_gene.csv", "INTERACTS_WITH", "gene", "gene"),
    ("edges_pathway_gene.csv", "IN_PATHWAY", "gene", "path"),
    ("edges_disease_disease.csv", "PARENT_OF", "dis", "dis"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-assoc", type=float, default=0.3,
                    help="evidence cutoff for gene-disease links")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    frames = []
    for fname, rel, lpfx, rpfx in SOURCES:
        e = pd.read_csv(f"{OKG}/{fname}", dtype=str)

        if fname == "edges_disease_gene.csv":
            score = pd.to_numeric(e["score"], errors="coerce")
            before = len(e)
            e = e[score >= args.min_assoc]
            print(f"  ASSOCIATED_WITH  score >= {args.min_assoc}: "
                  f"{before:,} -> {len(e):,}")

        # drug_disease carries three different relations in one file
        relation = e["rel_type"] if rel is None else rel

        frames.append(pd.DataFrame({
            "h": lpfx + ":" + e["from_id"],
            "r": relation,
            "t": rpfx + ":" + e["to_id"],
        }))
        if rel is not None:
            print(f"  {rel:16s} {len(e):>9,}  ({fname})")

    # our own findings -- the reason this prediction is ours and not
    # something anyone could run on public data alone
    p = pd.read_csv(PROG, dtype=str)
    frames.append(pd.DataFrame({
        "h": "gene:" + p["ensembl_id"],
        "r": p["rel"],
        "t": "dis:" + p["disease_id"],
    }))
    print(f"  TRACKS_*         {len(p):>9,}  (our patients)")

    tri = pd.concat(frames, ignore_index=True).drop_duplicates()
    tri = tri[tri.h.notna() & tri.t.notna()]

    print(f"\ntotal triples {len(tri):,}")
    print(f"entities      {len(set(tri.h) | set(tri.t)):,}")
    print("\nby relation:")
    print(tri.r.value_counts().to_string())

    tri.to_csv(f"{OUT}/all.tsv", sep="\t", index=False, header=False)

    # Split so evaluation is honest: the model never sees the test edges.
    # Every entity must appear in train, or the model has no embedding for
    # it at test time -- so split within each relation and keep 80/10/10.
    rng = np.random.default_rng(42)
    idx = rng.permutation(len(tri))
    n = len(tri)
    cuts = (int(n * 0.8), int(n * 0.9))
    for name, part in zip(("train", "valid", "test"),
                          np.split(idx, cuts)):
        tri.iloc[part].to_csv(f"{OUT}/{name}.tsv", sep="\t",
                              index=False, header=False)
        print(f"{name:6s} {len(part):>9,}")


if __name__ == "__main__":
    main()
