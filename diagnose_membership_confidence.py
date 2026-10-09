"""diagnose_membership_confidence.py
------------------------------------
Is `membership_confidence` measuring gene stability, or is it measuring
failures of its own label-matching step?

THE SUSPICION
Task 2 reports, for v2 at k=5, a cluster whose shape is recovered at median
correlation 0.994 across 100 bootstraps while NOT ONE of its 683 genes is
confidently assigned to it. A cluster cannot be near-perfectly reproducible
and simultaneously contain no reliably-assigned gene. One of the two numbers
is not measuring what it claims.

HOW CONFIDENCE IS BUILT
Each bootstrap reclusters genes on resampled patients, then matches its
clusters to the main ones by Hungarian assignment on centroid correlation.
A gene scores a point when its bootstrap cluster maps back to its main
cluster. The matching is the weak link: Hungarian assignment is forced to be
one-to-one, so if a bootstrap merges two clusters and splits a third -- which
is exactly what happens when clusters differ only in the timing of a rise --
it still returns a full pairing, just a wrong one. Every gene in the
mispaired clusters then scores zero for that bootstrap, through no fault of
its own.

WHAT THIS MEASURES
For each bootstrap it records the correlation of every matched pair. A pair
matched at r < 0.5 is a failed match, not a real disagreement. It then
recomputes confidence using only bootstraps where every pair matched cleanly,
and compares. If confidence rises sharply, the published number is dominated
by matching failures and should not be used to filter genes.

Usage:
    python diagnose_membership_confidence.py 5
    python diagnose_membership_confidence.py 6
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from biopsy_policy import select_biopsies, expression_directory
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans

SRC = Path("data/for_mentor/genes_by_fibrosis_stage.csv")
SAMPLES = Path("data/for_mentor/sample_demographics.csv")
GRAPH = str(expression_directory())
STAGES = [f"stage_{i}" for i in range(5)]
K_RANGE = range(3, 9)
N_SUBSAMPLES, SUBSAMPLE_FRAC, SEED, N_BOOT = 50, 0.8, 42, 100
BAD_MATCH = 0.5

K = int(sys.argv[1]) if len(sys.argv) > 1 else 6


def zrows(a):
    return (a - a.mean(axis=1, keepdims=True)) / a.std(axis=1, keepdims=True)


def kmeans(k, data):
    return KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(data)


df = pd.read_csv(SRC)
fib = df[df.fibrosis_rho.notna()].reset_index(drop=True)
raw = fib[STAGES].to_numpy()
X = zrows(raw)
print(f"{len(fib):,} fibrosis-associated genes, k = {K}\n")

# --- patient-level matrix, same construction as Task 2 -------------------
import glob
sm = select_biopsies(pd.read_csv(SAMPLES))
sm = sm[sm.fibrosis_stage.notna()]
frames = []
for path in sorted(glob.glob(f"{GRAPH}/edges_GSE*.csv")):
    e = pd.read_csv(path, usecols=["sample_id", "ensembl_id", "value_z"])
    e = e[e.ensembl_id.isin(set(fib.ensembl_id))]
    e = e.merge(sm[["sample_id", "patient_id", "dataset_id", "fibrosis_stage"]],
                on="sample_id")
    if len(e):
        frames.append(e)
e = pd.concat(frames, ignore_index=True)
e = (e.groupby(["dataset_id", "patient_id", "ensembl_id"], as_index=False)
       .agg(value_z=("value_z", "mean"),
            fibrosis_stage=("fibrosis_stage", "first")))
pw = e.pivot_table(index=["dataset_id", "patient_id", "fibrosis_stage"],
                   columns="ensembl_id", values="value_z")
pw = pw.reindex(columns=fib.ensembl_id).dropna(axis=0, how="any")
pmeta = pw.index.to_frame(index=False)
PY = pw.to_numpy()
stage_onehot = pd.get_dummies(pmeta.fibrosis_stage).to_numpy(float)
patient_rows = pmeta.groupby(["dataset_id", "patient_id"]).indices
study_patients = {ds: [k for k in patient_rows if k[0] == ds]
                  for ds in pmeta.dataset_id.unique()}
print(f"{len(pmeta):,} patients usable for the bootstrap\n")


def bootstrap_profiles(rng):
    rows = []
    for ds, keys in study_patients.items():
        for i in rng.integers(0, len(keys), len(keys)):
            rows.extend(patient_rows[keys[i]])
    rows = np.array(rows)
    oh = stage_onehot[rows]
    return zrows(((oh.T @ PY[rows]) / oh.sum(0)[:, None]).T)


# --- burn the RNG exactly as Task 2 does, so the draws match -------------
rng = np.random.default_rng(SEED)
for k in K_RANGE:
    for s in range(N_SUBSAMPLES):
        rng.choice(len(X), int(SUBSAMPLE_FRAC * len(X)), replace=False)
    for s in range(N_SUBSAMPLES):
        bootstrap_profiles(rng)

model = kmeans(K, X)
cent = model.cluster_centers_
order = np.argsort(-(cent[:, 4] - cent[:, 0]))
remap = {old: new + 1 for new, old in enumerate(order)}
main_cluster = np.array([remap[c] for c in model.labels_])
cent = cent[order]

same_all = np.zeros(len(X))
same_clean = np.zeros(len(X))
n_clean = 0
pair_corrs, worst = [], []

for b in range(N_BOOT):
    bm = KMeans(n_clusters=K, n_init=10, random_state=b).fit(
        bootstrap_profiles(rng))
    sim = np.corrcoef(cent, bm.cluster_centers_)[:K, K:]
    ri, ci = linear_sum_assignment(-sim)
    corrs = sim[ri, ci]
    pair_corrs.append(corrs)
    worst.append(corrs.min())
    to_main = {c: r + 1 for r, c in zip(ri, ci)}
    hit = np.array([to_main[l] for l in bm.labels_]) == main_cluster
    same_all += hit
    if corrs.min() >= BAD_MATCH:
        same_clean += hit
        n_clean += 1

pair_corrs = np.array(pair_corrs)
worst = np.array(worst)

print("=" * 70)
print("HOW WELL DID THE LABEL MATCHING WORK?")
print("=" * 70)
print(f"  bootstraps run                         {N_BOOT}")
print(f"  with every pair matched at r >= {BAD_MATCH}     {n_clean}")
print(f"  with at least one failed match         {N_BOOT - n_clean}")
print(f"  worst matched pair, median over runs   {np.median(worst):.3f}")
print(f"  worst matched pair, minimum            {worst.min():.3f}")
print(f"  matched pairs below r = {BAD_MATCH} in total    "
      f"{int((pair_corrs < BAD_MATCH).sum())} of {pair_corrs.size}")

print("\n  per main cluster, how often its matched pair fell below "
      f"r = {BAD_MATCH}:")
for k in range(K):
    bad = int((pair_corrs[:, k] < BAD_MATCH).sum())
    print(f"    cluster {k+1}   {bad:3d} of {N_BOOT} bootstraps   "
          f"(median matched r = {np.median(pair_corrs[:, k]):.3f})")

conf_all = same_all / N_BOOT
conf_clean = same_clean / max(n_clean, 1)

print("\n" + "=" * 70)
print("WHAT THAT DID TO THE PUBLISHED NUMBER")
print("=" * 70)
print(f"  {'cluster':>8}  {'genes':>6}  {'conf>=0.8 as published':>23}  "
      f"{'conf>=0.8, clean runs only':>27}")
for k in range(1, K + 1):
    m = main_cluster == k
    print(f"  {k:>8}  {m.sum():>6}  {int((conf_all[m] >= 0.8).sum()):>23}  "
          f"{int((conf_clean[m] >= 0.8).sum()):>27}")
print(f"  {'TOTAL':>8}  {len(X):>6}  {int((conf_all >= 0.8).sum()):>23}  "
      f"{int((conf_clean >= 0.8).sum()):>27}")

if n_clean == 0:
    print("\n  No bootstrap matched cleanly. The published confidence column "
          "is\n  measuring matching failure, not gene stability.")
elif (conf_clean >= 0.8).sum() > 1.3 * max((conf_all >= 0.8).sum(), 1):
    print("\n  VERDICT: the published column understates stability badly. "
          f"{N_BOOT - n_clean} of {N_BOOT}\n  bootstraps were scored through "
          "a failed matching, and excluding those\n  raises the confident-gene "
          f"count from {int((conf_all >= 0.8).sum())} to "
          f"{int((conf_clean >= 0.8).sum())}. Do not filter genes on it "
          "as it stands.")
else:
    print("\n  VERDICT: matching failures do not explain the low confidence. "
          "The\n  genes really do move between clusters, and the column is "
          "reporting\n  that honestly.")
