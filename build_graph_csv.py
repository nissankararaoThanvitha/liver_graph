"""
build_graph_csv.py
------------------
Turns the cleaned data into Neo4j-ready CSV files.

Produces:
    nodes_dataset.csv    8 rows
    nodes_sample.csv     1,085 rows
    nodes_gene.csv       ~300 rows (whatever the panel matches)
    edges_expresses.csv  ~325,000 rows

Three normalised values go on every edge:
    value_raw  - the original number, never modified
    value_log  - log2(CPM + 1), corrects for sequencing depth
    value_z    - z-score per gene within its dataset, for cross-study comparison

Usage:
    python build_graph_csv.py
"""

import glob
import os

import numpy as np
import pandas as pd

INTERIM = "data/interim"
PROC = "data/processed"
GRAPH = "data/graph"
PANEL = "data/gene_panel.csv"
CHUNK = 1_000_000


def library_sizes(path):
    """Total counts per sample, computed over ALL genes.

    This must happen BEFORE filtering to the panel. CPM means "counts per
    million reads in the whole library" -- if you compute it from 300 genes
    you get counts per million *panel* reads, which is a different and
    meaningless quantity. Classic normalisation bug.
    """
    totals = {}
    for chunk in pd.read_csv(path, chunksize=CHUNK, compression="gzip",
                             usecols=["sample_key", "value"]):
        for k, v in chunk.groupby("sample_key")["value"].sum().items():
            totals[k] = totals.get(k, 0.0) + float(v)
    return totals


def load_panel_genes(panel_path, gene_map):
    """Resolve panel symbols to canonical Ensembl IDs via the mapping we built."""
    panel = pd.read_csv(panel_path)

    # gene_id_map has a symbol column filled in from HGNC during mapping.
    sym2ens = (gene_map[gene_map["symbol"].notna() & (gene_map["symbol"] != "")]
               .drop_duplicates(subset="symbol")
               .set_index("symbol")["ensembl_id"].to_dict())

    rows, missing = [], []
    for _, r in panel.iterrows():
        ens = sym2ens.get(r["symbol"])
        if ens:
            rows.append(dict(ensembl_id=ens, symbol=r["symbol"],
                             category=r["category"]))
        else:
            missing.append(r["symbol"])

    genes = pd.DataFrame(rows).drop_duplicates(subset="ensembl_id")
    if missing:
        print(f"  panel symbols not found in the data ({len(missing)}): "
              f"{missing[:12]}{'...' if len(missing) > 12 else ''}")
    return genes, missing


def main():
    os.makedirs(GRAPH, exist_ok=True)

    gene_map = pd.read_csv(os.path.join(PROC, "gene_id_map.csv"), dtype=str)
    crosswalk = pd.read_csv(os.path.join(PROC, "sample_crosswalk.csv"), dtype=str)
    meta = pd.read_csv(os.path.join(PROC, "samples_metadata.csv"), dtype=str).fillna("")

    # ---- Which genes are in ALL datasets? Only those make sound edges. -----
    sets = [set(g["ensembl_id"]) for _, g in gene_map.groupby("dataset_id")]
    common = set.intersection(*sets)
    print(f"Common genes across all datasets: {len(common):,}")

    panel_genes, _ = load_panel_genes(PANEL, gene_map)
    panel_genes = panel_genes[panel_genes["ensembl_id"].isin(common)]
    keep_ens = set(panel_genes["ensembl_id"])
    print(f"Panel genes present in all datasets: {len(keep_ens)}\n")

    # ---- Drop the suspicious alias-based mappings we flagged earlier -------
    # 'symbol_alias' matches rely on an informal nickname being unique, which
    # is a weaker guarantee than a current or previous official symbol.
    suspicious = set(gene_map.loc[gene_map["method"] == "symbol_alias", "ensembl_id"])
    dropped = keep_ens & suspicious
    if dropped:
        print(f"Dropping {len(dropped)} genes matched only via informal alias")
        keep_ens -= dropped
        panel_genes = panel_genes[panel_genes["ensembl_id"].isin(keep_ens)]

    all_edges = []

    for path in sorted(glob.glob(os.path.join(INTERIM, "*_expression_long.csv.gz"))):
        gse = os.path.basename(path).split("_")[0]
        print(f"[{gse}] computing library sizes ...", flush=True)
        libsize = library_sizes(path)

        gmap = (gene_map[gene_map["dataset_id"] == gse]
                .set_index("gene_id_raw")["ensembl_id"].to_dict())
        cw = (crosswalk[crosswalk["dataset_id"] == gse]
              .set_index("sample_key")["sample_id"].to_dict())

        parts = []
        for chunk in pd.read_csv(path, chunksize=CHUNK, compression="gzip"):
            chunk["gene_id_raw"] = chunk["gene_id_raw"].astype(str)

            # FIX 1: drop pseudoautosomal Y duplicates -- same gene, listed
            # twice because the tips of X and Y are identical.
            chunk = chunk[~chunk["gene_id_raw"].str.contains("_PAR_Y", na=False)]

            chunk["ensembl_id"] = chunk["gene_id_raw"].map(gmap)
            chunk = chunk[chunk["ensembl_id"].isin(keep_ens)]
            if chunk.empty:
                continue
            chunk["sample_id"] = chunk["sample_key"].astype(str).map(cw)
            parts.append(chunk[["sample_id", "sample_key", "ensembl_id",
                                "value", "unit"]])

        if not parts:
            print(f"  no panel genes found -- skipping")
            continue
        df = pd.concat(parts, ignore_index=True)

        # FIX 2: old and new symbol both present -> one gene, sum the reads.
        before = len(df)
        df = (df.groupby(["sample_id", "sample_key", "ensembl_id", "unit"],
                         as_index=False)["value"].sum())
        if before != len(df):
            print(f"  merged {before - len(df):,} duplicate rows (old/new symbol pairs)")

        unit = df["unit"].iloc[0]

        # ---- value_log ----------------------------------------------------
        # For counts: counts per million, then log2. The +1 avoids log(0),
        # and log compresses the huge dynamic range of expression data
        # (a few genes are ~1000x more expressed than the rest).
        # For TPM: already depth-normalised, so just log it.
        if unit == "TPM":
            df["value_log"] = np.log2(df["value"] + 1)
        else:
            lib = df["sample_key"].map(libsize).replace(0, np.nan)
            df["value_log"] = np.log2(df["value"] / lib * 1e6 + 1)

        # ---- value_z ------------------------------------------------------
        # Per gene, within this dataset: how unusual is this sample?
        # Measured in standard deviations, so it is unit-free and comparable
        # across studies. std==0 (gene flat in this study) -> 0, not infinity.
        g = df.groupby("ensembl_id")["value_log"]
        df["value_z"] = ((df["value_log"] - g.transform("mean"))
                         / g.transform("std").replace(0, np.nan)).fillna(0)

        df["dataset_id"] = gse
        all_edges.append(df)
        print(f"  {len(df):,} edges  ({df['sample_id'].nunique()} samples "
              f"x {df['ensembl_id'].nunique()} genes)")

    edges = pd.concat(all_edges, ignore_index=True)
    edges = edges.rename(columns={"value": "value_raw"})
    edges = edges[["sample_id", "ensembl_id", "dataset_id", "unit",
                   "value_raw", "value_log", "value_z"]]

    # ---- node files -------------------------------------------------------
    used_samples = set(edges["sample_id"])
    samples = meta[meta["sample_id"].isin(used_samples)][
        ["sample_id", "dataset_id", "sample_title", "sex", "age", "tissue",
         "disease_group_raw", "fibrosis_stage_raw", "nas_score_raw"]]

    datasets = (meta.groupby("dataset_id").size()
                .reset_index(name="n_samples_total"))

    genes = panel_genes[panel_genes["ensembl_id"].isin(set(edges["ensembl_id"]))]

    samples.to_csv(f"{GRAPH}/nodes_sample.csv", index=False)
    genes.to_csv(f"{GRAPH}/nodes_gene.csv", index=False)
    datasets.to_csv(f"{GRAPH}/nodes_dataset.csv", index=False)
    edges.to_csv(f"{GRAPH}/edges_expresses.csv", index=False)

    print("\n=== GRAPH FILES WRITTEN ===")
    print(f"  nodes_dataset.csv    {len(datasets):>9,} rows")
    print(f"  nodes_sample.csv     {len(samples):>9,} rows")
    print(f"  nodes_gene.csv       {len(genes):>9,} rows")
    print(f"  edges_expresses.csv  {len(edges):>9,} rows")
    print(f"\n  z-score range: {edges['value_z'].min():.2f} .. {edges['value_z'].max():.2f}")
    print(f"  any missing sample_id? {edges['sample_id'].isna().sum()}")


if __name__ == "__main__":
    main()