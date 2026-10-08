"""
map_gene_ids.py
---------------
Translates every gene identifier in the parsed expression files into ONE
canonical identifier (Ensembl gene ID, version stripped), using the HGNC
complete set as the dictionary.

Why this design:
  * We map the UNIQUE gene IDs per dataset (~20k-64k), never the 23M rows.
    Mapping a small set then joining is orders of magnitude cheaper than
    mapping row by row.
  * Nothing is silently dropped. Anything that fails to map is written to an
    unmapped report so you can inspect it and decide.

Usage:
    python map_gene_ids.py \
        --interim-dir data/interim \
        --hgnc data/raw/hgnc_complete_set.txt \
        --out-dir data/processed
"""

import argparse
import glob
import os
from collections import defaultdict

import pandas as pd

CHUNK = 500_000


def strip_version(ensembl_id):
    """ENSG00000163631.15 -> ENSG00000163631

    The .15 is an annotation version, not part of the gene's identity.
    Different datasets ship different versions of the same gene, so leaving
    the suffix on makes a gene fail to join with itself.
    """
    s = str(ensembl_id).strip()
    return s.split(".", 1)[0] if s.upper().startswith("ENSG") else s


def split_multi(cell):
    """HGNC packs multi-valued fields as "A|B|C" (quoted, pipe-delimited)."""
    if pd.isna(cell) or not str(cell).strip():
        return []
    return [p.strip().strip('"') for p in str(cell).split("|") if p.strip()]


def build_lookups(hgnc_path):
    """Build the four dictionaries we need, in priority order.

    Priority matters: current symbol is authoritative, previous symbol is a
    documented rename, alias is informal and the most likely to be ambiguous.
    We only keep prev/alias entries that resolve to exactly ONE gene --
    an ambiguous alias silently merging two real genes is a corruption that
    produces no error and is nearly impossible to detect later.
    """
    usecols = ["symbol", "alias_symbol", "prev_symbol",
               "entrez_id", "ensembl_gene_id", "status"]
    hg = pd.read_csv(hgnc_path, sep="\t", usecols=usecols,
                     dtype=str, low_memory=False)

    # Withdrawn entries are retired genes -- excluding them avoids resurrecting
    # identifiers that HGNC has deliberately removed.
    hg = hg[hg["status"].fillna("").str.strip() == "Approved"]
    hg = hg[hg["ensembl_gene_id"].notna()]

    by_ensembl = {}      # canonical ensembl -> (symbol, entrez)
    by_entrez = {}
    by_symbol = {}
    prev_candidates = defaultdict(set)
    alias_candidates = defaultdict(set)

    for row in hg.itertuples(index=False):
        ens = str(row.ensembl_gene_id).strip()
        sym = str(row.symbol).strip() if pd.notna(row.symbol) else ""
        ent = str(row.entrez_id).strip() if pd.notna(row.entrez_id) else ""
        if ent.endswith(".0"):
            ent = ent[:-2]          # pandas reads some IDs as floats

        by_ensembl[ens] = (sym, ent)
        if ent:
            by_entrez[ent] = ens
        if sym:
            by_symbol[sym.upper()] = ens
        for p in split_multi(row.prev_symbol):
            prev_candidates[p.upper()].add(ens)
        for a in split_multi(row.alias_symbol):
            alias_candidates[a.upper()].add(ens)

    # Keep only unambiguous prev/alias entries, and never let them shadow a
    # current approved symbol.
    by_prev = {k: next(iter(v)) for k, v in prev_candidates.items()
               if len(v) == 1 and k not in by_symbol}
    by_alias = {k: next(iter(v)) for k, v in alias_candidates.items()
                if len(v) == 1 and k not in by_symbol and k not in by_prev}

    n_amb = sum(1 for v in prev_candidates.values() if len(v) > 1) + \
            sum(1 for v in alias_candidates.values() if len(v) > 1)

    print(f"HGNC loaded: {len(by_ensembl):,} approved genes with Ensembl IDs")
    print(f"  entrez keys : {len(by_entrez):,}")
    print(f"  symbol keys : {len(by_symbol):,}")
    print(f"  prev keys   : {len(by_prev):,}  (unambiguous only)")
    print(f"  alias keys  : {len(by_alias):,}  (unambiguous only)")
    print(f"  discarded   : {n_amb:,} ambiguous prev/alias entries\n")

    return by_ensembl, by_entrez, by_symbol, by_prev, by_alias


def collect_unique_genes(path):
    """Stream the long file and return its unique (gene_id_raw, gene_id_type)."""
    genes = set()
    gene_type = None
    for chunk in pd.read_csv(path, chunksize=CHUNK, compression="gzip",
                             usecols=["gene_id_raw", "gene_id_type"]):
        genes.update(chunk["gene_id_raw"].astype(str).unique().tolist())
        if gene_type is None and len(chunk):
            gene_type = chunk["gene_id_type"].iloc[0]
    return genes, gene_type


def resolve(raw, id_type, lk):
    """Return (ensembl_id, symbol, entrez_id, method) or None if unmappable."""
    by_ensembl, by_entrez, by_symbol, by_prev, by_alias = lk
    raw = str(raw).strip()

    if id_type == "ensembl":
        ens = strip_version(raw)
        if ens in by_ensembl:
            sym, ent = by_ensembl[ens]
            return ens, sym, ent, "ensembl_direct"
        # Present in the data but not in HGNC: usually a pseudogene, novel
        # transcript, or retired ID. Keep it -- it is still a valid Ensembl
        # identifier and joins correctly across datasets.
        return ens, "", "", "ensembl_not_in_hgnc"

    if id_type == "entrez":
        key = raw[:-2] if raw.endswith(".0") else raw
        if key in by_entrez:
            ens = by_entrez[key]
            sym, ent = by_ensembl[ens]
            return ens, sym, ent, "entrez_direct"
        return None

    # symbol -- try current, then previous, then alias
    key = raw.upper()
    for table, method in ((by_symbol, "symbol_current"),
                          (by_prev, "symbol_previous"),
                          (by_alias, "symbol_alias")):
        if key in table:
            ens = table[key]
            sym, ent = by_ensembl[ens]
            return ens, sym, ent, method
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interim-dir", default="data/interim")
    ap.add_argument("--hgnc", default="data/raw/hgnc_complete_set.txt")
    ap.add_argument("--out-dir", default="data/processed")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    lk = build_lookups(args.hgnc)

    map_rows = []
    unmapped_rows = []
    summary = []

    for path in sorted(glob.glob(os.path.join(args.interim_dir,
                                              "*_expression_long.csv.gz"))):
        gse = os.path.basename(path).split("_")[0]
        genes, id_type = collect_unique_genes(path)
        print(f"{gse}: {len(genes):,} unique gene IDs ({id_type})")

        methods = defaultdict(int)
        n_mapped = 0
        for raw in genes:
            res = resolve(raw, id_type, lk)
            if res is None:
                unmapped_rows.append(dict(dataset_id=gse, gene_id_raw=raw,
                                          gene_id_type=id_type))
                methods["UNMAPPED"] += 1
                continue
            ens, sym, ent, method = res
            map_rows.append(dict(dataset_id=gse, gene_id_raw=raw,
                                 gene_id_type=id_type, ensembl_id=ens,
                                 symbol=sym, entrez_id=ent, method=method))
            methods[method] += 1
            n_mapped += 1

        pct = 100 * n_mapped / len(genes) if genes else 0
        summary.append(dict(dataset_id=gse, id_type=id_type,
                            n_unique=len(genes), n_mapped=n_mapped,
                            pct_mapped=round(pct, 1),
                            n_unmapped=methods["UNMAPPED"]))
        detail = ", ".join(f"{k}={v:,}" for k, v in sorted(methods.items()))
        print(f"   {pct:.1f}% mapped  [{detail}]")

    map_df = pd.DataFrame(map_rows)
    map_df.to_csv(os.path.join(args.out_dir, "gene_id_map.csv"), index=False)
    pd.DataFrame(unmapped_rows).to_csv(
        os.path.join(args.out_dir, "unmapped_genes.csv"), index=False)

    # How many canonical genes are shared by ALL datasets? This is the number
    # that was impossible to compute before harmonization -- it was zero.
    sets = [set(g["ensembl_id"]) for _, g in map_df.groupby("dataset_id")]
    common = set.intersection(*sets) if sets else set()
    union = set.union(*sets) if sets else set()

    s = pd.DataFrame(summary)
    s.to_csv(os.path.join(args.out_dir, "_mapping_summary.csv"), index=False)
    print("\n=== MAPPING SUMMARY ===")
    print(s.to_string(index=False))
    print(f"\nDistinct canonical genes (union)      : {len(union):,}")
    print(f"Genes present in ALL {len(sets)} datasets     : {len(common):,}")


if __name__ == "__main__":
    main()