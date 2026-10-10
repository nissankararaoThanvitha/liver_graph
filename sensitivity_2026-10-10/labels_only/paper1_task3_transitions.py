# Patient policy (corrected 2026-10-10): average repeat measurements only
# when fibrosis stage is identical; otherwise retain biopsy 1. Existing
# packaged results are historical and are not overwritten by the isolated run.
"""Adjacent-stage expression contrasts among corrected fibrosis-selected genes.

Shared patient policy is applied before any stage contrast: equal-stage mean,
otherwise biopsy1. Fit higher-stage indicator plus study effects, t-test and
BH per contrast; substantial q<.05 and|beta|>=.2. Equal-study-cell matched refits
compare transitions under repeated sampling. Counts remain inside a selected
set and do not establish longitudinal progression or unbiased genome totals.
"""
import sys
import argparse
import glob
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from biopsy_policy import select_biopsies, expression_directory
from scipy import stats


STAGE_FILE = Path("data/for_mentor/genes_by_fibrosis_stage.csv")
SAMPLES = Path("data/for_mentor/sample_demographics.csv")
CLUSTERS = None  # set below from --clusters; see the argparse block
GRAPH = str(expression_directory())
# Output folder. Defaults to the committed location; --out redirects
# it so a re-run can be compared against the previous version instead
# of overwriting it.
# One parse for both options. Parsing twice strips --out from
# sys.argv on the first call, so the second call silently falls
# back to the default and the run writes to the wrong folder.
_ap = argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default="Paper1_Results/Task3")
_ap.add_argument("--clusters",
                 default="Paper1_Results/Task2/task2_gene_clusters.csv")
_args, _rest = _ap.parse_known_args()
sys.argv = [sys.argv[0]] + _rest
# Task 2's clusters were read from a hardcoded v1 path, so a v2
# re-run silently mixed v2 gene groups with v1 cluster
# assignments. --clusters makes the pairing explicit.
CLUSTERS = Path(_args.clusters)
OUT = Path(_args.out)
OUT.mkdir(parents=True, exist_ok=True)

TRANSITIONS = [(0, 1), (1, 2), (2, 3), (3, 4)]
TLAB = {t: f"F{t[0]}→F{t[1]}" for t in TRANSITIONS}
Q_CUT, EFFECT_CUT = 0.05, 0.2
N_MATCHED_REPS = 50
SEED = 42
rng = np.random.default_rng(SEED)

# --- genes, samples, expression ---
genes = pd.read_csv(STAGE_FILE)
genes = genes[genes.fibrosis_rho.notna()].reset_index(drop=True)
gene_ids = set(genes.ensembl_id)
symbol = genes.set_index("ensembl_id").symbol
cluster = pd.read_csv(CLUSTERS).set_index("ensembl_id")[["cluster", "cluster_name"]]

samples = select_biopsies(pd.read_csv(SAMPLES))
samples = samples[samples.fibrosis_stage.notna()].copy()
samples["fibrosis_stage"] = samples.fibrosis_stage.astype(int)

print("reading expression ...", flush=True)
parts = []
for p in sorted(glob.glob(f"{GRAPH}/edges_GSE*.csv")):
    for ch in pd.read_csv(p, usecols=["sample_id", "ensembl_id", "value_z"], chunksize=2_000_000):
        ch = ch[ch.ensembl_id.isin(gene_ids) & ch.sample_id.isin(samples.sample_id)]
        parts.append(ch)
expr = pd.concat(parts, ignore_index=True)
expr = expr.merge(samples[["sample_id", "patient_id", "dataset_id", "fibrosis_stage"]], on="sample_id")

# one row per patient x stage (repeat biopsies at the same stage averaged)
wide = expr.pivot_table(index=["patient_id", "dataset_id", "fibrosis_stage"],
                        columns="ensembl_id", values="value_z", aggfunc="mean")
wide = wide[genes.ensembl_id[genes.ensembl_id.isin(wide.columns)]]
meta = wide.index.to_frame(index=False)
Y_all = wide.to_numpy()
print(f"  {len(meta):,} patient-stage rows, {Y_all.shape[1]:,} genes, "
      f"{np.isnan(Y_all).mean()*100:.2f}% missing values")


def fit(rows, a):
    """OLS of each gene on [stage_b indicator + study dummies]; returns beta, se, p, n."""
    m = meta.iloc[rows]
    Y = Y_all[rows]
    xb = (m.fibrosis_stage.to_numpy() != a).astype(float)
    study = pd.get_dummies(m.dataset_id).to_numpy(float)
    X = np.column_stack([xb, study])
    beta = np.full(Y.shape[1], np.nan); se = beta.copy(); n = np.zeros(Y.shape[1], int)
    complete = ~np.isnan(Y).any(axis=0)
    groups = [(complete, None)] + [(np.array([j]), j) for j in np.where(~complete)[0]]
    for cols, j in groups:
        if j is None:
            Xg, Yg = X, Y[:, cols]
        else:
            ok = ~np.isnan(Y[:, j])
            Xg, Yg = X[ok], Y[ok][:, [j]]
            keep = Xg[:, 1:].sum(0) > 0
            Xg = np.column_stack([Xg[:, 0], Xg[:, 1:][:, keep]])
        if Yg.size == 0 or np.linalg.matrix_rank(Xg) < Xg.shape[1]:
            continue
        XtX_inv = np.linalg.inv(Xg.T @ Xg)
        B = XtX_inv @ Xg.T @ Yg
        resid = Yg - Xg @ B
        dof = Xg.shape[0] - Xg.shape[1]
        s2 = (resid ** 2).sum(0) / dof
        beta[cols] = B[0]
        se[cols] = np.sqrt(s2 * XtX_inv[0, 0])
        n[cols] = Xg.shape[0]
    t = beta / se
    dof_all = n - X.shape[1]
    p = 2 * stats.t.sf(np.abs(t), np.maximum(dof_all, 1))
    return beta, se, p, n


def transition_rows(a, b, rows_pool=None):
    """Patient-stage rows for one transition, within studies having both stages."""
    m = meta if rows_pool is None else meta.iloc[rows_pool]
    m = m[m.fibrosis_stage.isin([a, b])]
    both_studies = m.groupby("dataset_id").fibrosis_stage.nunique()
    m = m[m.dataset_id.isin(both_studies[both_studies == 2].index)]
    assert not m.patient_id.duplicated().any(), "Biopsy policy left duplicate patients"
    return m.index.to_numpy()


delta_mean = {t: genes[f"stage_{t[1]}"] - genes[f"stage_{t[0]}"] for t in TRANSITIONS}

results, counts = [], []
for a, b in TRANSITIONS:
    rows = transition_rows(a, b)
    m = meta.iloc[rows]
    beta, se, p, n = fit(rows, a)
    q = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    q[ok] = stats.false_discovery_control(p[ok], method="bh")
    r = pd.DataFrame({"ensembl_id": genes.ensembl_id, "symbol": genes.symbol,
                      "transition": TLAB[(a, b)], "delta_mean": delta_mean[(a, b)].round(4),
                      "beta_adjusted": beta, "se": se, "p_value": p, "q_value": q, "n_patients": n})
    r["substantial"] = (r.q_value < Q_CUT) & (r.beta_adjusted.abs() >= EFFECT_CUT)
    results.append(r)
    sub = r[r.substantial]
    counts.append({"transition": TLAB[(a, b)],
                   f"n_F{a}": int((m.fibrosis_stage == a).sum()),
                   f"n_F{b}": int((m.fibrosis_stage == b).sum()),
                   "studies_used": m.dataset_id.nunique(),
                   "n_significant_q<0.05": int((r.q_value < Q_CUT).sum()),
                   "n_substantial": len(sub),
                   "n_substantial_up": int((sub.beta_adjusted > 0).sum()),
                   "n_substantial_down": int((sub.beta_adjusted < 0).sum()),
                   "median_abs_beta": round(float(np.nanmedian(np.abs(beta))), 4),
                   "n_abs_beta>=0.2": int((np.abs(beta) >= EFFECT_CUT).sum()),
                   "median_abs_delta_mean": round(float(delta_mean[(a, b)].abs().median()), 4)})
    print(f"{TLAB[(a, b)]}: n={len(rows)} ({m.dataset_id.nunique()} studies)  "
          f"substantial={len(sub)} (up {counts[-1]['n_substantial_up']}, "
          f"down {counts[-1]['n_substantial_down']})  median|beta|={counts[-1]['median_abs_beta']}")

res = pd.concat(results, ignore_index=True)
res = res.join(cluster, on="ensembl_id")
res.to_csv(OUT / "task3_all_genes_all_transitions.csv", index=False, encoding="utf-8-sig")

# --- power-matched check: equal patients per stage group for every transition ---
# Every transition gets the same study-balanced design: per study, k_s patients
# from each stage, where k_s is the smallest per-study stage count over all transitions.
pools = {t: meta.iloc[transition_rows(*t)] for t in TRANSITIONS}
studies = sorted(meta.dataset_id.unique())
per_study = pd.concat([
    p.groupby(["dataset_id", "fibrosis_stage"]).size()
     .reindex(pd.MultiIndex.from_product([studies, t]), fill_value=0)
    for t, p in pools.items()])
k_study = per_study.groupby(level=0).min()
k_study = k_study[k_study > 0]
print(f"\npower-matched design, patients per stage per study: {k_study.to_dict()}")
M = int(k_study.sum())
matched = {TLAB[t]: [] for t in TRANSITIONS}
for rep in range(N_MATCHED_REPS):
    for a, b in TRANSITIONS:
        m = pools[(a, b)]
        pick = np.concatenate([
            rng.choice(m.index[(m.fibrosis_stage == s) & (m.dataset_id == ds)].to_numpy(), k, replace=False)
            for ds, k in k_study.items() for s in (a, b)])
        beta, se, p, n = fit(pick, a)
        ok = ~np.isnan(p)
        q = np.full_like(p, np.nan); q[ok] = stats.false_discovery_control(p[ok], method="bh")
        matched[TLAB[(a, b)]].append(int(((q < Q_CUT) & (np.abs(beta) >= EFFECT_CUT)).sum()))
cnt = pd.DataFrame(counts)
cnt[f"matched_n_substantial_mean (n={M}/stage)"] = [np.mean(matched[TLAB[t]]) for t in TRANSITIONS]
cnt["matched_n_substantial_sd"] = [round(np.std(matched[TLAB[t]]), 1) for t in TRANSITIONS]
cnt["matched_n_substantial_median"] = [np.median(matched[TLAB[t]]) for t in TRANSITIONS]
cnt.to_csv(OUT / "task3_transition_summary.csv", index=False, encoding="utf-8-sig")
print("\n" + cnt.T.to_string())

# --- top 20 increasing / decreasing per transition (among significant genes) ---
tops = []
for t in TRANSITIONS:
    r = res[(res.transition == TLAB[t]) & (res.q_value < Q_CUT)]
    for direction, d in [("increasing", r.nlargest(20, "beta_adjusted")),
                         ("decreasing", r.nsmallest(20, "beta_adjusted"))]:
        d = d.assign(direction=direction, rank=range(1, len(d) + 1))
        tops.append(d)
top = pd.concat(tops)[["transition", "direction", "rank", "symbol", "ensembl_id", "beta_adjusted",
                       "delta_mean", "q_value", "cluster", "cluster_name"]]
top.to_csv(OUT / "task3_top_genes_per_transition.csv", index=False, encoding="utf-8-sig")

# --- figure 1: distributions of delta ---
labels = [TLAB[t] for t in TRANSITIONS]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
for ax, col, title in [(axes[0], "delta_mean", "Δ of stage means"),
                       (axes[1], "beta_adjusted", "Patient-level Δ (adjusted for study)")]:
    data = [res.loc[res.transition == l, col].dropna() for l in labels]
    ax.violinplot(data, showmedians=True)
    ax.axhline(0, color="black", lw=0.6)
    for y in (EFFECT_CUT, -EFFECT_CUT):
        ax.axhline(y, color="#c0392b", lw=0.8, ls="--")
    ax.set_xticks(range(1, 5), labels)
    ax.set_title(title)
axes[0].set_ylabel("Change in expression (value_z, SD units)")
fig.suptitle(f"Δ expression for {len(genes):,} fibrosis-associated genes (dashed: ±{EFFECT_CUT})")
fig.tight_layout()
fig.savefig(OUT / "task3_delta_distributions.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# --- figure 2: comparison of the four transitions ---
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
x = np.arange(4)
axes[0].bar(x, cnt.n_substantial_up, color="#c0392b", label="up")
axes[0].bar(x, -cnt.n_substantial_down, color="#2471a3", label="down")
for i, r in cnt.iterrows():
    axes[0].text(i, r.n_substantial_up, f"{r.n_substantial_up}", ha="center", va="bottom", fontsize=9)
    axes[0].text(i, -r.n_substantial_down, f"{r.n_substantial_down}", ha="center", va="top", fontsize=9)
axes[0].axhline(0, color="black", lw=0.6)
axes[0].set_title(f"Substantially changing genes\n(q<{Q_CUT}, |Δ|≥{EFFECT_CUT}, all patients)")
axes[0].legend()
q25 = np.array([np.percentile(matched[TLAB[t]], 25) for t in TRANSITIONS])
q75 = np.array([np.percentile(matched[TLAB[t]], 75) for t in TRANSITIONS])
med = cnt.matched_n_substantial_median.to_numpy()
axes[1].bar(x, med, yerr=[med - q25, q75 - med], color="#7d3c98", capsize=4)
for i, v in enumerate(med):
    axes[1].text(i, q75[i], f"{v:.0f}", ha="center", va="bottom", fontsize=9)
axes[1].set_title(f"Power-matched: {M} patients per stage, study-balanced\n"
                  f"(median and IQR of {N_MATCHED_REPS} subsamples)")
axes[2].bar(x, cnt.median_abs_beta, color="#555")
axes[2].set_title("Median |patient-level Δ| across all genes\n(effect size, independent of sample size)")
for ax in axes:
    ax.set_xticks(x, labels)
fig.tight_layout()
fig.savefig(OUT / "task3_transition_comparison.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# --- per-cluster check (e.g. does C3 really fall at F3->F4?) ---
cl = (res.groupby(["cluster", "cluster_name", "transition"])
      .agg(median_beta=("beta_adjusted", "median"),
           n_sig_up=("q_value", lambda s: int(((s < Q_CUT) & (res.loc[s.index, "beta_adjusted"] > 0)).sum())),
           n_sig_down=("q_value", lambda s: int(((s < Q_CUT) & (res.loc[s.index, "beta_adjusted"] < 0)).sum())),
           n_genes=("q_value", "size"))
      .reset_index())
cl["transition"] = pd.Categorical(cl.transition, labels, ordered=True)
cl = cl.sort_values(["cluster", "transition"])
cl.to_csv(OUT / "task3_cluster_by_transition.csv", index=False, encoding="utf-8-sig")
print("\nPer-cluster patient-level change:")
print(cl.to_string(index=False))
print(f"\nWrote outputs to {OUT}/")
