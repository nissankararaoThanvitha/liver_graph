"""
inspect_parsed.py
-----------------
Reads the *_expression_long.csv.gz files produced by parse_expression.py and
answers three questions we can't answer from the summary table alone:

  1. Do the expression sample keys actually MATCH the GSM accessions in
     samples_metadata.csv?  (If not, we can't connect Sample -> Gene at all.)
  2. What do the gene IDs really look like -- any version suffixes, any
     mixed formats?
  3. What unit is GSE193066 in?  (parse_expression.py marked it "unknown".)

Memory-safe: reads in chunks, so a 5.8M-row file never lands in RAM at once.

Usage:
    python inspect_parsed.py --interim-dir data/interim --metadata data/processed/samples_metadata.csv
"""

import argparse
import glob
import os

import pandas as pd

CHUNK = 500_000


def scan_file(path):
    """One streaming pass over a long-format file.

    We collect only tiny summaries (a set of sample keys, a handful of gene IDs,
    running min/max/sum), so peak memory stays flat regardless of file size.
    Time: O(n_rows). Space: O(n_samples), not O(n_rows).
    """
    sample_keys = set()
    gene_examples = []
    n_rows = 0
    vmin, vmax, vsum = None, None, 0.0
    n_integer_like = 0
    n_checked = 0
    per_sample_sum = {}

    for chunk in pd.read_csv(path, chunksize=CHUNK, compression="gzip"):
        n_rows += len(chunk)
        sample_keys.update(chunk["sample_key"].unique().tolist())

        if len(gene_examples) < 8:
            gene_examples.extend(chunk["gene_id_raw"].head(8).astype(str).tolist())

        v = chunk["value"]
        vmin = v.min() if vmin is None else min(vmin, v.min())
        vmax = v.max() if vmax is None else max(vmax, v.max())
        vsum += float(v.sum())

        # Are values whole numbers? Raw counts are; TPM/FPKM/log values are not.
        head = v.head(5000)
        n_integer_like += int((head == head.round()).sum())
        n_checked += len(head)

        # Per-sample totals: TPM columns sum to ~1,000,000 by definition.
        grp = chunk.groupby("sample_key")["value"].sum()
        for k, val in grp.items():
            per_sample_sum[k] = per_sample_sum.get(k, 0.0) + float(val)

    frac_integer = n_integer_like / n_checked if n_checked else 0.0
    median_sample_sum = pd.Series(per_sample_sum).median() if per_sample_sum else float("nan")

    return dict(
        n_rows=n_rows,
        sample_keys=sorted(sample_keys),
        gene_examples=gene_examples[:8],
        vmin=vmin, vmax=vmax,
        frac_integer=frac_integer,
        median_sample_sum=median_sample_sum,
    )


def guess_unit(info):
    """Infer the unit from the value distribution.

    Reasoning, in order of confidence:
      - whole numbers everywhere  -> raw counts
      - per-sample total ~= 1e6   -> TPM (TPM is DEFINED to sum to a million)
      - negative values present   -> log-transformed
      - otherwise                 -> some normalised scale, needs a human look
    """
    if info["frac_integer"] > 0.98:
        return "raw_count (values are whole numbers)"
    s = info["median_sample_sum"]
    if 9e5 < s < 1.1e6:
        return "TPM (per-sample total is ~1,000,000)"
    if info["vmin"] is not None and info["vmin"] < 0:
        return "log-transformed (negative values present)"
    return f"normalised, unclear (per-sample total ~{s:,.0f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interim-dir", default="data/interim")
    ap.add_argument("--metadata", default="data/processed/samples_metadata.csv")
    args = ap.parse_args()

    meta_ids = set()
    meta_titles = set()
    if os.path.exists(args.metadata):
        meta = pd.read_csv(args.metadata)
        meta_ids = set(meta["sample_id"].astype(str))
        meta_titles = set(meta["sample_title"].astype(str))
    else:
        print(f"[warn] metadata not found at {args.metadata} -- skipping join check\n")

    files = sorted(glob.glob(os.path.join(args.interim_dir, "*_expression_long.csv.gz")))
    rows = []

    for path in files:
        gse = os.path.basename(path).split("_")[0]
        print(f"scanning {gse} ...", flush=True)
        info = scan_file(path)

        keys = info["sample_keys"]
        n_match_gsm = len(set(keys) & meta_ids)
        n_match_title = len(set(keys) & meta_titles)

        rows.append(dict(
            dataset=gse,
            n_samples=len(keys),
            matches_GSM=n_match_gsm,
            matches_title=n_match_title,
            unit_guess=guess_unit(info),
        ))

        print(f"   sample keys : {keys[:3]}")
        print(f"   gene ids    : {info['gene_examples'][:3]}")
        print(f"   value range : {info['vmin']} .. {info['vmax']}")
        print()

    if rows:
        print("=== JOIN + UNIT REPORT ===")
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()