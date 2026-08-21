"""
show_keys.py
------------
Prints the first few sample keys from each parsed expression file, next to the
GSM accessions and sample titles we have in the metadata. Purely a diagnostic
for working out how to join the two sides.

Usage:
    python show_keys.py
"""

import glob
import os

import pandas as pd

INTERIM = "data/interim"
META = "data/processed/samples_metadata.csv"

meta = pd.read_csv(META, dtype=str)

for path in sorted(glob.glob(os.path.join(INTERIM, "*_expression_long.csv.gz"))):
    gse = os.path.basename(path).split("_")[0]

    # Only need a few rows to see the column naming scheme -- read one chunk
    # rather than the whole 5M-row file.
    chunk = next(pd.read_csv(path, chunksize=200_000, compression="gzip",
                             usecols=["sample_key"]))
    keys = sorted(chunk["sample_key"].astype(str).unique())

    m = meta[meta["dataset_id"] == gse]
    print("=" * 70)
    print(gse)
    print(f"  expression keys : {keys[:4]}")
    print(f"  metadata GSM    : {m['sample_id'].head(4).tolist()}")
    print(f"  metadata title  : {m['sample_title'].head(4).tolist()}")