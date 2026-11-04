"""Do the five stage-pattern clusters nest inside the three-cluster solution?

The silhouette score is highest at k = 3, so this checks how the reported
k = 5 clusters relate to k = 3. It uses exactly the clustering settings of
paper1_task2_trajectories.py (same input file and row order, profiles
standardised across F0-F4, k-means with 50 initialisations, seed 42):

  1. k = 5 is re-run and compared with the published clusters
     (Paper1_Results/Task2/task2_gene_clusters.csv) by adjusted Rand index.
  2. k = 3 is run with the same settings.
  3. For each k = 5 cluster, its genes are counted in each k = 3 cluster.
     A gene "nests" when it falls in the k = 3 cluster that holds most of
     its k = 5 cluster; the share of such genes is the nesting concordance.

Writes Paper1_Results/Task2/task2_nesting_k3.csv (k = 5 by k = 3 counts) and
task2_nesting_k3_summary.json. Run from the repository root:
    python scripts/cluster_nesting_k3.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

SRC = Path("data/for_mentor/genes_by_fibrosis_stage.csv")
PUBLISHED = Path("Paper1_Results/Task2/task2_gene_clusters.csv")
OUT = Path("Paper1_Results/Task2")
STAGES = [f"stage_{i}" for i in range(5)]
SEED = 42

df = pd.read_csv(SRC)
fib = df[df.fibrosis_rho.notna()].reset_index(drop=True)  # same rows and order as Task 2
raw = fib[STAGES].to_numpy()
X = (raw - raw.mean(axis=1, keepdims=True)) / raw.std(axis=1, keepdims=True)  # ddof = 0


def kmeans(k):
    return KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(X).labels_


published = pd.read_csv(PUBLISHED, encoding="utf-8-sig").set_index("ensembl_id")
c5 = fib.ensembl_id.map(published.cluster)
assert c5.notna().all() and len(fib) == len(published) == 3845

k5 = kmeans(5)
ari_rerun = adjusted_rand_score(c5, k5)
k3 = kmeans(3)

tab = pd.crosstab(pd.Series(c5.map(lambda c: f"C{int(c)}"), name="k5_cluster"),
                  pd.Series(k3, name="k3_cluster"))
dominant = tab.idxmax(axis=1)
nested = int(tab.max(axis=1).sum())
share = nested / len(fib)

# name each k = 3 cluster by its mean F0-F4 profile
names = {}
for c in range(3):
    m = X[k3 == c].mean(axis=0)
    if m[4] < m[0]:
        names[c] = "falling"
    else:
        names[c] = "rising, mainly at lower stages" if m[1] - m[0] > m[4] - m[3] else "rising, mainly at higher stages"
tab.columns = [f"k3_{c} ({names[c]})" for c in tab.columns]

OUT.mkdir(parents=True, exist_ok=True)
tab.to_csv(OUT / "task2_nesting_k3.csv", encoding="utf-8-sig")
summary = {
    "genes": len(fib),
    "ari_rerun_k5_vs_published": round(float(ari_rerun), 3),
    "nesting_concordance": round(share, 4),
    "genes_in_dominant_k3_cluster": nested,
    "dominant_k3_cluster_per_k5_cluster": {k: names[v] for k, v in dominant.items()},
    "k5_by_k3_counts": {r: tab.loc[r].to_dict() for r in tab.index},
    "settings": "profiles standardised across F0-F4 (ddof=0); KMeans n_init=50, random_state=42; "
                "same input and row order as paper1_task2_trajectories.py",
}
(OUT / "task2_nesting_k3_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

print(f"re-run k = 5 vs published clusters: ARI {ari_rerun:.3f}")
print(f"genes in the k = 3 cluster holding most of their k = 5 cluster: {nested:,} / {len(fib):,} ({100 * share:.1f}%)")
print(tab.to_string())
