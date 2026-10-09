"""Paper 1, Task 2 -- cluster fibrosis-associated genes by their F0->F4 pattern.

Each gene's five stage means (value_z, from genes_by_fibrosis_stage.csv) are
z-scored across stages so genes are grouped by shape, not magnitude. K-means is
run for k = 3..8; k is chosen from silhouette score and subsample stability
(adjusted Rand index). Clusters are named only after clustering, from their
mean curves. Outputs go to Paper1_Results/Task2/.

Two robustness checks use patient-level value_z:
  * patient bootstrap -- resample patients (within study, with replacement),
    recompute stage means, recluster; ARI against the full-data clusters.
  * study adjustment  -- stage profiles from value_z ~ stage + study, so the
    different stage mix of each study cannot shape the curves; recluster and
    compare.
"""
import argparse
import glob
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, silhouette_score

SRC = Path("data/for_mentor/genes_by_fibrosis_stage.csv")
SAMPLES = Path("data/for_mentor/sample_demographics.csv")
GRAPH = "data/graph_full"
# Output folder. Defaults to the committed location; --out redirects
# it so a re-run can be compared against the previous version instead
# of overwriting it.
_ap = argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default="Paper1_Results/Task2")
_args, _rest = _ap.parse_known_args()
sys.argv = [sys.argv[0]] + _rest
OUT = Path(_args.out)
OUT.mkdir(parents=True, exist_ok=True)
STAGES = [f"stage_{i}" for i in range(5)]
LABELS = ["F0", "F1", "F2", "F3", "F4"]
K_RANGE = range(3, 9)
N_SUBSAMPLES = 50
SUBSAMPLE_FRAC = 0.8
SEED = 42

df = pd.read_csv(SRC)
fib = df[df.fibrosis_rho.notna()].reset_index(drop=True)
raw = fib[STAGES].to_numpy()
X = (raw - raw.mean(axis=1, keepdims=True)) / raw.std(axis=1, keepdims=True)
print(f"{len(fib):,} fibrosis-associated genes")


def zrows(a):
    return (a - a.mean(axis=1, keepdims=True)) / a.std(axis=1, keepdims=True)


def kmeans(k, data, seed=SEED):
    return KMeans(n_clusters=k, n_init=50, random_state=seed).fit(data)


# --- patient-level expression: one row per patient x stage ---
samples = pd.read_csv(SAMPLES)
samples = samples[samples.fibrosis_stage.notna()]
print("reading patient-level expression ...", flush=True)
parts = []
for p in sorted(glob.glob(f"{GRAPH}/edges_GSE*.csv")):
    for ch in pd.read_csv(p, usecols=["sample_id", "ensembl_id", "value_z"], chunksize=2_000_000):
        parts.append(ch[ch.ensembl_id.isin(fib.ensembl_id) & ch.sample_id.isin(samples.sample_id)])
expr = pd.concat(parts).merge(
    samples[["sample_id", "patient_id", "dataset_id", "fibrosis_stage"]], on="sample_id")
pw = expr.pivot_table(index=["patient_id", "dataset_id", "fibrosis_stage"],
                      columns="ensembl_id", values="value_z", aggfunc="mean")[fib.ensembl_id]
pmeta = pw.index.to_frame(index=False)
pmeta["fibrosis_stage"] = pmeta.fibrosis_stage.astype(int)
PY = pw.to_numpy()
stage_onehot = pd.get_dummies(pmeta.fibrosis_stage).to_numpy(float)
patient_rows = pmeta.groupby(["dataset_id", "patient_id"]).indices
study_patients = {ds: [k for k in patient_rows if k[0] == ds] for ds in pmeta.dataset_id.unique()}


def bootstrap_profiles(rng):
    """Stage means after resampling patients within each study, with replacement."""
    rows = []
    for ds, keys in study_patients.items():
        for i in rng.integers(0, len(keys), len(keys)):
            rows.extend(patient_rows[keys[i]])
    rows = np.array(rows)
    oh = stage_onehot[rows]
    return zrows(((oh.T @ PY[rows]) / oh.sum(0)[:, None]).T)


# --- choose k: silhouette + subsample stability ---
rng = np.random.default_rng(SEED)
rows = []
for k in K_RANGE:
    ref = kmeans(k, X).labels_
    sil = silhouette_score(X, ref)
    aris = []
    for s in range(N_SUBSAMPLES):
        idx = rng.choice(len(X), int(SUBSAMPLE_FRAC * len(X)), replace=False)
        sub = KMeans(n_clusters=k, n_init=10, random_state=s).fit(X[idx]).labels_
        aris.append(adjusted_rand_score(ref[idx], sub))
    boot = [adjusted_rand_score(ref, KMeans(n_clusters=k, n_init=10, random_state=s)
                                .fit(bootstrap_profiles(rng)).labels_)
            for s in range(N_SUBSAMPLES)]
    rows.append({"k": k, "silhouette": sil, "stability_ARI_mean": np.mean(aris),
                 "stability_ARI_sd": np.std(aris),
                 "patient_bootstrap_ARI_mean": np.mean(boot),
                 "patient_bootstrap_ARI_sd": np.std(boot)})
    print(f"k={k}  silhouette={sil:.3f}  gene-subsample ARI={np.mean(aris):.3f} ± {np.std(aris):.3f}"
          f"  patient-bootstrap ARI={np.mean(boot):.3f} ± {np.std(boot):.3f}")
kscores = pd.DataFrame(rows)
kscores.to_csv(OUT / "task2_choosing_k.csv", index=False, encoding="utf-8-sig")

# Rule: largest k whose mean stability ARI stays >= 0.95 (override with argv[1]).
K = int(sys.argv[1]) if len(sys.argv) > 1 else int(kscores[kscores.stability_ARI_mean >= 0.95].k.max())
print(f"\nChosen k = {K}")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].plot(kscores.k, kscores.silhouette, "o-", color="#333")
axes[0].set_ylabel("Silhouette score (higher = better separated)")
axes[1].errorbar(kscores.k, kscores.stability_ARI_mean, yerr=kscores.stability_ARI_sd,
                 fmt="o-", color="#333", capsize=3)
axes[1].errorbar(kscores.k + 0.08, kscores.patient_bootstrap_ARI_mean,
                 yerr=kscores.patient_bootstrap_ARI_sd, fmt="s--", color="#7d3c98", capsize=3,
                 label="patient bootstrap")
axes[1].lines[0].set_label(f"gene subsample ({int(SUBSAMPLE_FRAC*100)}%)")
axes[1].axhline(0.95, color="#c0392b", ls="--", lw=1, label="ARI = 0.95")
axes[1].set_ylabel(f"Stability (ARI, {N_SUBSAMPLES} resamples)")
axes[1].legend(loc="lower left")
for ax in axes:
    ax.axvline(K, color="#2471a3", lw=6, alpha=0.2)
    ax.set_xlabel("Number of clusters k")
fig.suptitle(f"Choosing k (chosen k = {K}: largest k with stability ARI ≥ 0.95)")
fig.tight_layout()
fig.savefig(OUT / "task2_choosing_k.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# --- final clustering; number clusters from most increasing to most decreasing ---
model = kmeans(K, X)
cent = model.cluster_centers_
order = np.argsort(-(cent[:, 4] - cent[:, 0]))
remap = {old: new + 1 for new, old in enumerate(order)}
fib["cluster"] = [remap[c] for c in model.labels_]
cent = cent[order]


def name_pattern(c):
    """Describe a centroid curve from where its change happens."""
    steps = np.diff(c)
    total = c[4] - c[0]
    peak = int(np.argmax(c)) if total > 0 else int(np.argmin(c))
    if 0 < peak < 4 and abs(c[peak] - c[4]) > 0.4:
        return f"{'Rise' if total > 0 else 'Fall'} to F{peak}, then reverse"
    word = "increase" if total > 0 else "decrease"
    early, late = steps[0] / total, steps[3] / total
    if early >= 0.25:
        return f"Early {word} (F0→F1), then continued"
    if late >= 0.4:
        return f"Late {word} (largest at F3→F4)"
    j = int(np.argmax(np.abs(steps)))
    return f"Mid {word} (largest at F{j}→F{j+1})"


# Task 3's patient-level test found no significant F3->F4 drop for this
# cluster (0 of 197 genes), so the stage-mean "reverse" is not supported.
NAME_OVERRIDES = {"Rise to F3, then reverse": "Early rise, then plateau"}
names = {k + 1: NAME_OVERRIDES.get(n, n) for k, n in
         ((k, name_pattern(cent[k])) for k in range(K))}
fib["cluster_name"] = fib.cluster.map(names)
fib["corr_to_centroid"] = [np.corrcoef(X[i], cent[c - 1])[0, 1] for i, c in enumerate(fib.cluster)]

# --- patient bootstrap at chosen k: are the SHAPES stable, and how sure is each gene? ---
# Bootstrap clusters are matched to the main clusters by centroid shape.
N_BOOT = 100
# A bootstrap's clusters come out in arbitrary order, so they are matched to
# the main ones by Hungarian assignment on centroid correlation. That
# assignment is forced to be one-to-one: it returns a complete pairing even
# when no good pairing exists. When a bootstrap merges two clusters and
# splits a third -- which is what happens when clusters differ only in WHEN a
# gene rises -- the leftover pairing can be arbitrary, and matched pairs then
# correlate near zero or negative.
#
# Scoring every gene against such a bootstrap measures the failure, not the
# gene. Measured at k=5: 30 of 100 bootstraps contained a failed pair, 29 of
# them hitting one cluster, whose 683 genes were consequently reported as 0
# confidently assigned while its shape was recovered at median r = 0.994.
#
# So a gene is scored only in the bootstraps where ITS OWN cluster was
# matched soundly. Discarding the whole bootstrap would throw away the
# clusters that did match; this keeps them and records the denominator per
# gene in confidence_n_bootstraps.
MIN_MATCH_R = 0.5
same = np.zeros(len(X))
assessable = np.zeros(len(X))
failed_pairs = 0
shape_r = []
for b in range(N_BOOT):
    bm = KMeans(n_clusters=K, n_init=10, random_state=b).fit(bootstrap_profiles(rng))
    sim = np.corrcoef(cent, bm.cluster_centers_)[:K, K:]
    ri, ci = linear_sum_assignment(-sim)
    corrs = sim[ri, ci]
    shape_r.append(corrs)
    failed_pairs += int((corrs < MIN_MATCH_R).sum())
    to_main = {c: r + 1 for r, c in zip(ri, ci)}
    hit = np.array([to_main[l] for l in bm.labels_]) == fib.cluster.to_numpy()
    sound = corrs[fib.cluster.to_numpy() - 1] >= MIN_MATCH_R
    same += hit & sound
    assessable += sound
shape_r = np.array(shape_r)
fib["membership_confidence"] = (same / np.maximum(assessable, 1)).round(2)
fib["confidence_n_bootstraps"] = assessable.astype(int)
print(f"\nlabel matching: {failed_pairs} of {N_BOOT * K} matched pairs fell "
      f"below r = {MIN_MATCH_R} and were not scored")
print(f"                genes assessed in {int(assessable.min())}-"
      f"{int(assessable.max())} of {N_BOOT} bootstraps "
      f"(median {int(np.median(assessable))})")
shape_stab = pd.DataFrame({"cluster": range(1, K + 1), "cluster_name": [names[k] for k in range(1, K + 1)],
                           "median_shape_corr": np.median(shape_r, 0).round(3),
                           "min_shape_corr": shape_r.min(0).round(3),
                           "genes_confidence>=0.8": [int(((fib.cluster == k) & (fib.membership_confidence >= 0.8)).sum())
                                                     for k in range(1, K + 1)],
                           "n_genes": [int((fib.cluster == k).sum()) for k in range(1, K + 1)]})
shape_stab.to_csv(OUT / "task2_bootstrap_shape_stability.csv", index=False, encoding="utf-8-sig")
print(f"\nPatient bootstrap ({N_BOOT}x), shape recovery and gene confidence:\n" + shape_stab.to_string(index=False))

# --- main CSV ---
main = fib[["symbol", "ensembl_id", *STAGES, "cluster", "cluster_name",
            "corr_to_centroid", "membership_confidence", "confidence_n_bootstraps",
            "fibrosis_rho", "ladder"]].rename(
    columns={"symbol": "Gene", **dict(zip(STAGES, LABELS))})
main = main.sort_values(["cluster", "corr_to_centroid"], ascending=[True, False])
main.to_csv(OUT / "task2_gene_clusters.csv", index=False, encoding="utf-8-sig")

# --- cluster sizes ---
sizes = (fib.groupby(["cluster", "cluster_name"]).size().rename("n_genes").reset_index())
sizes["pct_of_fibrosis_genes"] = (100 * sizes.n_genes / len(fib)).round(1)
for i, lab in enumerate(LABELS):
    sizes[f"mean_{lab}"] = fib.groupby("cluster")[STAGES[i]].mean().round(3).values
sizes.to_csv(OUT / "task2_cluster_sizes.csv", index=False, encoding="utf-8-sig")
print("\n" + sizes.to_string(index=False))

# --- representative genes: closest to the cluster's average shape ---
# ranked by bootstrap membership confidence first, then closeness to the shape
rep = (main.sort_values(["cluster", "membership_confidence", "corr_to_centroid"],
                        ascending=[True, False, False])
       .groupby("cluster", group_keys=False).head(15)
       [["cluster", "cluster_name", "Gene", "membership_confidence", "corr_to_centroid",
         "fibrosis_rho", *LABELS]])
rep.insert(1, "rank", rep.groupby("cluster").cumcount() + 1)
rep.to_csv(OUT / "task2_representative_genes.csv", index=False, encoding="utf-8-sig")
print("\nRepresentative genes:")
for c, g in rep.groupby("cluster"):
    print(f"  C{c} {names[c]}: {', '.join(g.Gene.head(10))}")

# --- heatmap of all genes, grouped by cluster ---
hm_order = main.index.to_numpy()
fig, ax = plt.subplots(figsize=(5, 10))
im = ax.imshow(X[hm_order], aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2, interpolation="nearest")
bounds = np.cumsum(sizes.n_genes.to_numpy())
for b in bounds[:-1]:
    ax.axhline(b - 0.5, color="black", lw=1.2)
mids = bounds - sizes.n_genes.to_numpy() / 2
ax.set_yticks(mids, [f"C{c} (n={n:,})" for c, n in zip(sizes.cluster, sizes.n_genes)])
ax.set_xticks(range(5), LABELS)
ax.set_title(f"{len(fib):,} fibrosis-associated genes across F0–F4")
fig.colorbar(im, ax=ax, fraction=0.05, pad=0.03, label="Expression (z-scored across stages)")
fig.savefig(OUT / "task2_heatmap.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# --- trajectory plot per cluster ---
ncol = 3
nrow = int(np.ceil(K / ncol))
fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 3.4 * nrow), sharey=True)
axes = axes.ravel()
for k in range(K):
    ax = axes[k]
    members = X[fib.cluster.to_numpy() == k + 1]
    ax.plot(range(5), members.T, color="grey", alpha=0.05, lw=0.6)
    ax.plot(range(5), cent[k], color="#c0392b", lw=3)
    ax.set_title(f"C{k+1}: {names[k+1]}\n(n={len(members):,})", fontsize=10)
    ax.set_xticks(range(5), LABELS)
    ax.axhline(0, color="black", lw=0.5)
for ax in axes[K:]:
    ax.axis("off")
for ax in axes[::ncol]:
    ax.set_ylabel("Expression (z across stages)")
fig.tight_layout()
fig.savefig(OUT / "task2_cluster_trajectories.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# --- all cluster means on the original value_z scale ---
fig, ax = plt.subplots(figsize=(7, 5))
for _, r in sizes.iterrows():
    ax.plot(LABELS, [r[f"mean_{l}"] for l in LABELS], "o-", lw=2,
            label=f"C{r.cluster}: {r.cluster_name} (n={r.n_genes:,})")
ax.axhline(0, color="black", lw=0.5)
ax.set_ylabel("Mean expression (value_z)")
ax.set_xlabel("Fibrosis stage")
ax.set_title("Cluster average trajectories (original scale)")
ax.legend(fontsize=8, loc="best")
fig.savefig(OUT / "task2_cluster_means.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# --- robustness: study-adjusted stage profiles (value_z ~ stage + study) ---
design = np.column_stack([stage_onehot,
                          pd.get_dummies(pmeta.dataset_id, drop_first=True).to_numpy(float)])
adj = zrows(np.linalg.lstsq(design, PY, rcond=None)[0][:5].T)
adj_labels = kmeans(K, adj).labels_
curve_r = np.array([np.corrcoef(adj[i], X[i])[0, 1] for i in range(len(X))])
robust = pd.DataFrame([
    {"check": "study-adjusted profiles: ARI vs main clusters",
     "value": round(adjusted_rand_score(fib.cluster, adj_labels), 3)},
    {"check": "study-adjusted profiles: median per-gene curve correlation",
     "value": round(float(np.median(curve_r)), 3)},
    {"check": f"patient bootstrap ARI at chosen k={K} (mean)",
     "value": round(float(kscores.set_index("k").patient_bootstrap_ARI_mean[K]), 3)},
])
robust.to_csv(OUT / "task2_robustness.csv", index=False, encoding="utf-8-sig")
xt = pd.crosstab(fib.cluster.map(lambda c: f"C{c} {names[c]}"), adj_labels,
                 rownames=["main cluster"], colnames=["study-adjusted cluster"])
xt.to_csv(OUT / "task2_robustness_crosstab.csv", encoding="utf-8-sig")
print("\nRobustness:\n" + robust.to_string(index=False) + "\n" + xt.to_string())
print(f"\nWrote outputs to {OUT}/")
