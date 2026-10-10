"""Write the corrected selected-union gene inventory.

Apply q<.05 and all-study direction agreement on each axis, then union the two
selected sets. The historical source filename is retained for callers; output
is00_all_progression_genes.csv. Row count is derived from current inputs.
"""
import pathlib
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
import argparse as _argparse
import sys as _sys

_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default=None,
                 help="folder for this script's own numbered outputs")
_ap.add_argument("--results", default=None,
                 help="Paper1_Results folder to read Task2/3/4 from")
_args, _rest = _ap.parse_known_args()
_sys.argv = [_sys.argv[0]] + _rest
# These scripts used to live inside the results folder, so HERE was
# both 'where the code is' and 'where results go'. They now live in
# scripts/, so the output location has to be named rather than
# inherited from the file's own position.
HERE = (pathlib.Path(_args.out).resolve() if _args.out
        else ROOT / "Paper1_HighConfidence")
HERE.mkdir(parents=True, exist_ok=True)
RESULTS = pathlib.Path(_args.results) if _args.results else ROOT / "Paper1_Results"

PROG = ROOT / "data/progression_full"
STAGE = ROOT / "data/for_mentor/genes_by_fibrosis_stage.csv"


def qualifying(path, name):
    """Genes passing both conditions on one ladder."""
    d = pd.read_csv(path)
    sig = d[(d.q_value < 0.05) & (d.n_agree == d.n_studies)]
    print(f"  {name:12s} tested {len(d):>6,}   "
          f"q<0.05 {int((d.q_value < 0.05).sum()):>6,}   "
          f"+ all studies agree {len(sig):>6,}")
    return sig.set_index("ensembl_id")


print("qualifying on each ladder:")
fib = qualifying(PROG / "progression_fibrosis.csv", "fibrosis")
dis = qualifying(PROG / "progression_disease.csv", "inflammation")

ids = sorted(set(fib.index) | set(dis.index))
t = pd.DataFrame({"ensembl_id": ids})

sym = pd.concat([fib.symbol, dis.symbol])
sym = sym[~sym.index.duplicated()]
t["symbol"] = t.ensembl_id.map(sym).fillna("")

on_f, on_d = t.ensembl_id.isin(fib.index), t.ensembl_id.isin(dis.index)
t["ladder"] = np.select([on_f & on_d, on_f], ["both", "fibrosis_only"],
                        default="inflammation_only")

for src, pre in ((fib, "fibrosis"), (dis, "inflammation")):
    t[f"{pre}_rho"] = t.ensembl_id.map(src.median_rho).round(4)
    t[f"{pre}_q"] = t.ensembl_id.map(src.q_value)
    t[f"{pre}_direction"] = np.where(
        t[f"{pre}_rho"].isna(), "",
        np.where(t[f"{pre}_rho"] > 0, "increasing", "decreasing"))
    t[f"{pre}_n_studies"] = t.ensembl_id.map(src.n_studies).astype("Int64")
    t[f"{pre}_min_rho"] = t.ensembl_id.map(src.min_rho).round(4)
    t[f"{pre}_max_rho"] = t.ensembl_id.map(src.max_rho).round(4)

# the five fibrosis stage means, where the gene has them
stage = pd.read_csv(STAGE)[["ensembl_id"] + [f"stage_{i}" for i in range(5)]]
t = t.merge(stage.rename(columns={f"stage_{i}": f"F{i}" for i in range(5)}),
            on="ensembl_id", how="left")

t["in_fibrosis_starting_set"] = t.ladder.ne("inflammation_only")

out = HERE / "00_all_progression_genes.csv"
t.to_csv(out, index=False)

print(f"\nunion = {len(t):,} progression genes")
print("  " + t.ladder.value_counts().to_string().replace("\n", "\n  "))
print(f"\nfibrosis starting set (fibrosis_only + both): "
      f"{int(t.in_fibrosis_starting_set.sum()):,}")
print(f"\n-> {out.relative_to(ROOT)}  ({len(t):,} x {t.shape[1]})")
