"""
build_graph_all.py
------------------
Builds the FULL graph: every mapped gene, not just the curated panel and not
just the genes shared by all eight studies.

Difference from build_graph_csv.py
----------------------------------
build_graph_csv.py kept only genes that were (a) in data/gene_panel.csv AND
(b) present in all 8 datasets -- 290 genes, 311,322 edges. That was the pilot.

This script drops both filters and keeps the union: 53,993 genes and
~23.3M edges. Every measurement that mapped to a canonical Ensembl ID
becomes an edge, so filtering decisions move from load time to query time.

The consequence has to stay visible, so each Gene node carries:

    n_datasets   how many of the 8 studies measured this gene (1-8)

39,199 of the 53,993 genes are missing from at least one study and 10,621
appear in exactly one. Those are real data, but a gene backed by one cohort
is not evidence of the same weight as one backed by eight. n_datasets is what
lets a query say so instead of silently averaging them together.

Edge schema is leaner than the pilot's: dataset_id and unit are dropped from
the relationship because both are reachable from the Sample node one hop
away. At 23M edges that redundancy costs real store size.

Both correctness fixes from the pilot are kept:
  * _PAR_Y rows dropped (X/Y chromosome-tip duplicates)
  * two raw IDs collapsing to one Ensembl ID have their values SUMMED

Output (data/graph_all/):
    nodes_gene.csv               53,993 rows
    nodes_dataset.csv                 8 rows
    edges_<GSE>.csv              one file per study, ~23.3M rows total

Usage:
    python build_graph_all.py
"""

import argparse
import glob
import os

import numpy as np
import pandas as pd

PROC = "data/processed"
CHUNK = 1_000_000

# Set by main() from the command line. data/interim was parsed with
# --drop-zeros; data/interim_full keeps them, which is what the progression
# work needs -- a gene switching off IS the signal there.
INTERIM = "data/interim_full"
OUT = "data/graph_all"


def library_sizes(path):
    """Total counts per sample, over ALL genes.

    Must be computed before any gene filtering. CPM means "counts per million
    reads in the whole library"; computing it from a subset gives counts per
    million *subset* reads, which is a different and meaningless quantity.
    """
    totals = {}
    for chunk in pd.read_csv(path, chunksize=CHUNK, compression="gzip",
                             usecols=["sample_key", "value"]):
        for k, v in chunk.groupby("sample_key")["value"].sum().items():
            totals[k] = totals.get(k, 0.0) + float(v)
    return totals


def main():
    global INTERIM, OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--interim", default=INTERIM)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    INTERIM, OUT = args.interim, args.out
    print(f"reading {INTERIM}  ->  writing {OUT}\n")

    os.makedirs(OUT, exist_ok=True)

    gene_map = pd.read_csv(os.path.join(PROC, "gene_id_map.csv"), dtype=str)
    crosswalk = pd.read_csv(os.path.join(PROC, "sample_crosswalk.csv"), dtype=str)
    meta = pd.read_csv(os.path.join(PROC, "samples_metadata.csv"),
                       dtype=str).fillna("")

    # ---- gene nodes: the union, with an evidence count --------------------
    per_ds = gene_map.groupby("dataset_id")["ensembl_id"].apply(set)
    n_datasets = {}
    for s in per_ds:
        for e in s:
            n_datasets[e] = n_datasets.get(e, 0) + 1

    # symbol/entrez come from HGNC via the mapping; take the first non-blank.
    lab = (gene_map.sort_values("symbol", na_position="last")
           .drop_duplicates(subset="ensembl_id")
           .set_index("ensembl_id")[["symbol", "entrez_id"]])

    genes = pd.DataFrame({"ensembl_id": list(n_datasets)})
    genes["symbol"] = genes["ensembl_id"].map(lab["symbol"]).fillna("")
    genes["entrez_id"] = genes["ensembl_id"].map(lab["entrez_id"]).fillna("")
    genes["n_datasets"] = genes["ensembl_id"].map(n_datasets)

    # Carry the pilot's panel category across where it exists, so the 290
    # curated genes stay identifiable inside the larger set.
    panel_path = os.path.join(OUT, os.pardir, "graph", "nodes_gene.csv")
    if os.path.exists(panel_path):
        p = pd.read_csv(panel_path, dtype=str).set_index("ensembl_id")["category"]
        genes["category"] = genes["ensembl_id"].map(p).fillna("")
    else:
        genes["category"] = ""

    genes.to_csv(f"{OUT}/nodes_gene.csv", index=False)
    print(f"nodes_gene.csv        {len(genes):>10,} genes")
    print(genes["n_datasets"].value_counts().sort_index(ascending=False)
          .rename_axis("in_n_studies").to_string())
    print()

    datasets = (meta.groupby("dataset_id").size()
                .reset_index(name="n_samples_total"))
    datasets.to_csv(f"{OUT}/nodes_dataset.csv", index=False)

    # ---- edges, one file per study ----------------------------------------
    total = 0
    for path in sorted(glob.glob(os.path.join(INTERIM, "*_expression_long.csv.gz"))):
        gse = os.path.basename(path).split("_")[0]
        libsize = library_sizes(path)

        gmap = (gene_map[gene_map["dataset_id"] == gse]
                .set_index("gene_id_raw")["ensembl_id"].to_dict())
        cw = (crosswalk[crosswalk["dataset_id"] == gse]
              .set_index("sample_key")["sample_id"].to_dict())

        parts = []
        for chunk in pd.read_csv(path, chunksize=CHUNK, compression="gzip"):
            chunk["gene_id_raw"] = chunk["gene_id_raw"].astype(str)
            # X/Y chromosome-tip duplicates: same gene listed twice.
            chunk = chunk[~chunk["gene_id_raw"].str.contains("_PAR_Y", na=False)]
            chunk["ensembl_id"] = chunk["gene_id_raw"].map(gmap)
            chunk = chunk[chunk["ensembl_id"].notna()]
            if chunk.empty:
                continue
            chunk["sample_id"] = chunk["sample_key"].astype(str).map(cw)
            parts.append(chunk[["sample_id", "sample_key", "ensembl_id",
                                "value", "unit"]])

        df = pd.concat(parts, ignore_index=True)
        del parts

        # Old symbol and new symbol both present -> one gene, sum the reads.
        before = len(df)
        df = (df.groupby(["sample_id", "sample_key", "ensembl_id", "unit"],
                         as_index=False)["value"].sum())
        merged = before - len(df)

        unit = df["unit"].iloc[0]
        if unit == "TPM":
            df["value_log"] = np.log2(df["value"] + 1)
        else:
            lib = df["sample_key"].map(libsize).replace(0, np.nan)
            df["value_log"] = np.log2(df["value"] / lib * 1e6 + 1)

        g = df.groupby("ensembl_id")["value_log"]
        df["value_z"] = ((df["value_log"] - g.transform("mean"))
                         / g.transform("std").replace(0, np.nan)).fillna(0)

        out = df.rename(columns={"value": "value_raw"})[
            ["sample_id", "ensembl_id", "value_raw", "value_log", "value_z"]]
        out.to_csv(f"{OUT}/edges_{gse}.csv", index=False)
        total += len(out)
        print(f"edges_{gse}.csv  {len(out):>10,} edges  "
              f"({out['sample_id'].nunique()} samples x "
              f"{out['ensembl_id'].nunique():,} genes"
              f"{f', merged {merged:,} duplicates' if merged else ''})")
        del df, out

    print(f"\nTOTAL EDGES {total:,}")


if __name__ == "__main__":
    main()
