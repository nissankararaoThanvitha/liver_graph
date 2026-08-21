"""
check_mapping.py
----------------
Two validations that the mapping summary cannot show:

  1. COLLAPSES: within one dataset, do two different raw IDs resolve to the
     SAME canonical Ensembl ID? If so, that sample-gene pair now has two
     values and would become duplicate edges in Neo4j.

  2. UNMAPPED PROFILE: what kinds of IDs failed? Excel-corrupted symbols
     ("1-Mar"), novel/clone IDs, or genuinely retired entries?

Also breaks the common gene set down by biotype, so you can decide whether
to build the graph on all 14,794 or just the protein-coding core.

Usage:
    python check_mapping.py --processed-dir data/processed --hgnc data/raw/hgnc_complete_set.txt
"""

import argparse
import os
import re

import pandas as pd

# Symbols mangled by Excel autocorrect: SEPT9 -> "9-Sep", MARCH1 -> "1-Mar".
EXCEL_DATE = re.compile(r"^\d{1,2}[-/](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed-dir", default="data/processed")
    ap.add_argument("--hgnc", default="data/raw/hgnc_complete_set.txt")
    args = ap.parse_args()

    gmap = pd.read_csv(os.path.join(args.processed_dir, "gene_id_map.csv"),
                       dtype=str)

    # ---- 1. Collapse check -------------------------------------------------
    print("=== COLLAPSE CHECK (two raw IDs -> one Ensembl ID) ===")
    rows = []
    for gse, grp in gmap.groupby("dataset_id"):
        counts = grp.groupby("ensembl_id")["gene_id_raw"].nunique()
        collapsed = counts[counts > 1]
        rows.append(dict(dataset_id=gse,
                         n_canonical=len(counts),
                         n_collapsed_genes=len(collapsed),
                         n_extra_rows=int((collapsed - 1).sum())))
        if len(collapsed):
            ex = grp[grp["ensembl_id"].isin(collapsed.index[:3])]
            ex = ex.sort_values("ensembl_id")[["ensembl_id", "gene_id_raw", "symbol", "method"]]
            print(f"\n  {gse} examples:")
            print(ex.head(6).to_string(index=False))
    print()
    print(pd.DataFrame(rows).to_string(index=False))

    # ---- 2. Unmapped profile ----------------------------------------------
    unmapped_path = os.path.join(args.processed_dir, "unmapped_genes.csv")
    if os.path.exists(unmapped_path):
        un = pd.read_csv(unmapped_path, dtype=str)
        print("\n=== UNMAPPED PROFILE ===")
        for gse, grp in un.groupby("dataset_id"):
            ids = grp["gene_id_raw"].astype(str)
            n_excel = int(ids.apply(lambda s: bool(EXCEL_DATE.match(s))).sum())
            n_orf = int(ids.str.match(r"^(LOC|LINC|C\d+orf|MIR|SNOR|RNU|AC\d|AL\d|AP\d)",
                                      case=False).sum())
            print(f"\n  {gse}: {len(grp):,} unmapped "
                  f"| excel-corrupted={n_excel} | clone/novel-style={n_orf}")
            print(f"    examples: {ids.head(12).tolist()}")

    # ---- 3. Biotype of the common gene set --------------------------------
    sets = [set(g["ensembl_id"]) for _, g in gmap.groupby("dataset_id")]
    common = set.intersection(*sets)
    print(f"\n=== COMMON GENE SET: {len(common):,} genes ===")

    hg_cols = pd.read_csv(args.hgnc, sep="\t", nrows=0).columns
    if "locus_group" not in hg_cols or "ensembl_gene_id" not in hg_cols:
        print("(HGNC file lacks locus_group -- skipping biotype breakdown)")
        return
    hg = pd.read_csv(args.hgnc, sep="\t", dtype=str, low_memory=False,
                     usecols=["ensembl_gene_id", "locus_group"])
    hg = hg[hg["ensembl_gene_id"].isin(common)]
    counts = hg["locus_group"].value_counts()
    print(counts.to_string())
    n_unknown = len(common) - len(hg)
    print(f"not in HGNC (novel/pseudogene): {n_unknown:,}")


if __name__ == "__main__":
    main()