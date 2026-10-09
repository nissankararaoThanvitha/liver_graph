"""
parse_expression.py
Reads GEO supplementary expression files and converts each into a long-format
table: dataset_id, sample_key, gene_id_raw, gene_id_type, value, unit

Usage:
    python parse_expression.py --raw-dir data/raw --out-dir data/interim
"""

import argparse
import gzip
import io
import os
import re
import tarfile

import pandas as pd

DATASETS = {
    "GSE126848": dict(file_glob="Gene_counts_raw",        fmt="matrix", unit="raw_count", sep="\t"),
    "GSE130970": dict(file_glob="tximport_TPM",           fmt="matrix", unit="TPM",       sep=","),
    "GSE135251": dict(file_glob="RAW.tar",                fmt="tar",    unit="raw_count", sep="\t"),
    "GSE162694": dict(file_glob="raw_counts",             fmt="matrix", unit="raw_count", sep=","),
    "GSE167523": dict(file_glob="Raw_gene_counts_matrix", fmt="matrix", unit="raw_count", sep="\t"),
    "GSE193066": dict(file_glob="HUn164.gct",             fmt="gct",    unit="unknown",   sep="\t"),
    "GSE240729": dict(file_glob="merged.counts",          fmt="matrix", unit="raw_count", sep="\t"),
    "GSE269412": dict(file_glob="rnaseq_count_mat",       fmt="matrix", unit="raw_count", sep="\t"),
}


def smart_open(path):
    """Open a file whether or not it is gzip-compressed."""
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == b"\x1f\x8b":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def find_file(raw_dir, needle):
    """Locate the file under raw_dir whose name contains `needle`."""
    for root, _dirs, files in os.walk(raw_dir):
        for name in files:
            if needle.lower() in name.lower():
                return os.path.join(root, name)
    return None


def detect_gene_id_type(sample_ids):
    """Guess whether gene IDs are Ensembl, Entrez, or HGNC symbols."""
    sample = [str(s) for s in sample_ids[:500] if str(s).strip()]
    if not sample:
        return "unknown"
    n_ensembl = sum(1 for s in sample if s.upper().startswith("ENSG"))
    n_entrez = sum(1 for s in sample if s.isdigit())
    if n_ensembl > len(sample) * 0.8:
        return "ensembl"
    if n_entrez > len(sample) * 0.8:
        return "entrez"
    return "symbol"


def read_matrix(path, sep):
    """Standard genes-as-rows, samples-as-columns matrix."""
    with smart_open(path) as fh:
        df = pd.read_csv(fh, sep=sep, index_col=0, low_memory=False)
    return df


def read_gct(path, sep="\t"):
    """GCT format: skip 2 header lines, drop the Description column."""
    with smart_open(path) as fh:
        df = pd.read_csv(fh, sep=sep, skiprows=2, index_col=0, low_memory=False)
    for annot_col in ("Description", "description", "DESCRIPTION"):
        if annot_col in df.columns:
            df = df.drop(columns=[annot_col])
    return df


def read_tar(path, sep="\t"):
    """A RAW.tar bundle of per-sample count files -> one merged matrix."""
    series_list = []
    with tarfile.open(path, "r:*") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            fh = tar.extractfile(member)
            if fh is None:
                continue
            data = fh.read()
            if data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            text = data.decode("utf-8", errors="replace")

            m = re.search(r"(GSM\d+)", member.name)
            col = m.group(1) if m else os.path.basename(member.name)

            sub = pd.read_csv(io.StringIO(text), sep=sep, index_col=0,
                              header=None, comment="#", low_memory=False)
            sub = sub.iloc[:, 0]
            sub.name = col
            series_list.append(sub)
    if not series_list:
        raise ValueError(f"No usable members found inside {path}")
    return pd.concat(series_list, axis=1)


def to_long(df, dataset_id, unit):
    """Wide matrix -> long edge list, one row per (sample, gene) pair."""
    df.index = df.index.astype(str).str.strip()
    df = df[~df.index.duplicated(keep="first")]
    gene_id_type = detect_gene_id_type(list(df.index))

    df.index.name = "gene_id_raw"
    long_df = (
        df.reset_index()
          .melt(id_vars="gene_id_raw", var_name="sample_key", value_name="value")
    )
    long_df["dataset_id"] = dataset_id
    long_df["gene_id_type"] = gene_id_type
    long_df["unit"] = unit

    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df = long_df.dropna(subset=["value"])

    return long_df[["dataset_id", "sample_key", "gene_id_raw",
                    "gene_id_type", "value", "unit"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--out-dir", default="data/interim_full")
    ap.add_argument("--drop-zeros", action="store_true",
                    help="Omit zero-expression pairs.")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    summary = []

    for gse, cfg in DATASETS.items():
        path = find_file(args.raw_dir, cfg["file_glob"])
        if path is None:
            print(f"[SKIP] {gse}: no file matching '{cfg['file_glob']}' under {args.raw_dir}")
            continue

        print(f"[READ] {gse}  <- {os.path.basename(path)}")
        try:
            if cfg["fmt"] == "gct":
                df = read_gct(path, cfg["sep"])
            elif cfg["fmt"] == "tar":
                df = read_tar(path, cfg["sep"])
            else:
                df = read_matrix(path, cfg["sep"])
        except Exception as exc:
            print(f"[FAIL] {gse}: {type(exc).__name__}: {exc}")
            continue

        df = df.select_dtypes(include="number")
        long_df = to_long(df, gse, cfg["unit"])

        if args.drop_zeros:
            long_df = long_df[long_df["value"] != 0]

        out_path = os.path.join(args.out_dir, f"{gse}_expression_long.csv.gz")
        long_df.to_csv(out_path, index=False, compression="gzip")

        summary.append(dict(
            dataset_id=gse,
            n_genes=df.shape[0],
            n_samples=df.shape[1],
            gene_id_type=long_df["gene_id_type"].iloc[0] if len(long_df) else "?",
            unit=cfg["unit"],
            n_edges=len(long_df),
            out=os.path.basename(out_path),
        ))
        print(f"       {df.shape[0]:,} genes x {df.shape[1]:,} samples "
              f"-> {len(long_df):,} edges")

    if summary:
        s = pd.DataFrame(summary)
        s.to_csv(os.path.join(args.out_dir, "_parse_summary.csv"), index=False)
        print("\n=== SUMMARY ===")
        print(s.to_string(index=False))


if __name__ == "__main__":
    main()