"""Per-gene power-matched transition results.

Task 3 already ran this analysis. It computed beta and q for all 3,645 genes
in every repetition and then kept only the count of substantial genes, so the
per-gene detail existed for a moment and was discarded. This script re-runs
the identical design and keeps it.

WHY A MATCHED DESIGN AT ALL
F4 has 34 patients where the other stages have 100-170, so a comparison
involving F4 rests on far less data than one that does not. The matched design
takes an equal number of patients from each stage, study by study, so every
transition is judged on the same amount of evidence. 50 repetitions, different
random patients each time, so one unlucky draw cannot decide anything.

TWO NUMBERS PER GENE PER TRANSITION, AND THEY MEAN DIFFERENT THINGS

  reps_reproducible  in how many of the 50 draws the jump stayed big
                     (|beta| >= 0.2) AND kept the sign it has in the
                     full-patient fit.
                     -> asks "is this effect reproducible?". A fluke depends on
                        which patients were drawn, so redrawing kills it. This
                        is the number the X score uses.

  reps_significant   in how many of the 50 draws it ALSO passed q < 0.05.
                     -> asks "could this be chance?", which at 30 patients per
                        stage and BH-FDR across 3,645 genes the design cannot
                        answer: Task 3 measured a median of ZERO significant
                        genes per draw at F0->F1. A low value here cannot
                        distinguish "no effect" from "no power", so it scores
                        nothing. It is reported because it is evidence about
                        the study's limits, not about the genes.

The matched design drops GSE193066: it lacks patients at some stage, so it
cannot contribute an equal cell to every transition. Four studies remain.

Usage:
    python Paper1_HighConfidence/powermatched_transitions.py
"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

STAGE_FILE = ROOT / "data/for_mentor/genes_by_fibrosis_stage.csv"
SAMPLES = ROOT / "data/for_mentor/sample_demographics.csv"
FULL_FIT = ROOT / "Paper1_Results/Task3/task3_all_genes_all_transitions.csv"
GRAPH = ROOT / "data/graph_full"

TRANSITIONS = [(0, 1), (1, 2), (2, 3), (3, 4)]
TLAB = {t: f"F{t[0]}→F{t[1]}" for t in TRANSITIONS}
# identical to Task 3, so this is the same test, not a new one
Q_CUT, EFFECT_CUT, N_REPS, SEED = 0.05, 0.2, 50, 42

rng = np.random.default_rng(SEED)

# --- genes, samples, expression (same construction as Task 3) ---
genes = pd.read_csv(STAGE_FILE)
genes = genes[genes.fibrosis_rho.notna()].reset_index(drop=True)
gene_ids = set(genes.ensembl_id)

samples = pd.read_csv(SAMPLES)
samples = samples[samples.fibrosis_stage.notna()].copy()
samples["fibrosis_stage"] = samples.fibrosis_stage.astype(int)

print("reading expression ...", flush=True)
parts = []
for p in sorted(glob.glob(str(GRAPH / "edges_GSE*.csv"))):
    for ch in pd.read_csv(p, usecols=["sample_id", "ensembl_id", "value_z"],
                          chunksize=2_000_000):
        parts.append(ch[ch.ensembl_id.isin(gene_ids)
                        & ch.sample_id.isin(samples.sample_id)])
expr = pd.concat(parts, ignore_index=True)
expr = expr.merge(samples[["sample_id", "patient_id", "dataset_id",
                           "fibrosis_stage"]], on="sample_id")

wide = expr.pivot_table(index=["patient_id", "dataset_id", "fibrosis_stage"],
                        columns="ensembl_id", values="value_z", aggfunc="mean")
wide = wide[genes.ensembl_id[genes.ensembl_id.isin(wide.columns)]]
meta = wide.index.to_frame(index=False)
Y_all = wide.to_numpy()
gene_order = wide.columns.to_numpy()
print(f"  {len(meta):,} patient-stage rows, {Y_all.shape[1]:,} genes")


def fit(rows, a):
    """OLS of each gene on [stage_b indicator + study dummies]."""
    m = meta.iloc[rows]
    Y = Y_all[rows]
    xb = (m.fibrosis_stage.to_numpy() != a).astype(float)
    study = pd.get_dummies(m.dataset_id).to_numpy(float)
    X = np.column_stack([xb, study])
    beta = np.full(Y.shape[1], np.nan)
    se = beta.copy()
    complete = ~np.isnan(Y).any(axis=0)
    groups = [(complete, None)] + [(np.array([j]), j)
                                   for j in np.where(~complete)[0]]
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
        s2 = (resid ** 2).sum(0) / (Xg.shape[0] - Xg.shape[1])
        beta[cols] = B[0]
        se[cols] = np.sqrt(s2 * XtX_inv[0, 0])
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), max(len(rows) - X.shape[1], 1))
    return beta, p


def transition_rows(a, b):
    """Patient-stage rows for one transition, within studies having both."""
    m = meta[meta.fibrosis_stage.isin([a, b])]
    both = m.groupby("dataset_id").fibrosis_stage.nunique()
    m = m[m.dataset_id.isin(both[both == 2].index)]
    dup = m.patient_id.duplicated(keep=False)
    drop = [rng.choice(g.index.to_numpy())
            for _, g in m[dup].groupby("patient_id")]
    return m.drop(index=drop).index.to_numpy()


# --- the matched design: equal patients per stage per study ---
pools = {t: meta.iloc[transition_rows(*t)] for t in TRANSITIONS}
studies = sorted(meta.dataset_id.unique())
per_study = pd.concat([
    p.groupby(["dataset_id", "fibrosis_stage"]).size()
     .reindex(pd.MultiIndex.from_product([studies, t]), fill_value=0)
    for t, p in pools.items()])
k_study = per_study.groupby(level=0).min()
k_study = k_study[k_study > 0]
M = int(k_study.sum())
dropped = sorted(set(studies) - set(k_study.index))
print(f"\nmatched design: {M} patients per stage, "
      f"per study {k_study.to_dict()}")
print(f"  studies used {len(k_study)}; dropped (no patients at some stage): "
      f"{dropped or 'none'}")

# sign from the full-patient fit: 'reproducible' means the matched draw keeps
# the direction the full analysis found, not merely any large value
full = pd.read_csv(FULL_FIT)
ref = {lab: (full[full.transition == lab]
             .set_index("ensembl_id").beta_adjusted
             .reindex(gene_order).to_numpy())
       for lab in TLAB.values()}

print(f"\nrunning {N_REPS} repetitions x {len(TRANSITIONS)} transitions ...")
repro = {TLAB[t]: np.zeros(len(gene_order), int) for t in TRANSITIONS}
signif = {TLAB[t]: np.zeros(len(gene_order), int) for t in TRANSITIONS}
betas = {TLAB[t]: [] for t in TRANSITIONS}

for rep in range(N_REPS):
    for a, b in TRANSITIONS:
        lab = TLAB[(a, b)]
        m = pools[(a, b)]
        pick = np.concatenate([
            rng.choice(m.index[(m.fibrosis_stage == s)
                               & (m.dataset_id == ds)].to_numpy(),
                       k, replace=False)
            for ds, k in k_study.items() for s in (a, b)])
        beta, p = fit(pick, a)
        q = np.full_like(p, np.nan)
        ok = ~np.isnan(p)
        q[ok] = stats.false_discovery_control(p[ok], method="bh")

        big = np.abs(beta) >= EFFECT_CUT
        same_sign = np.sign(beta) == np.sign(ref[lab])
        repro[lab] += np.nan_to_num(big & same_sign).astype(int)
        signif[lab] += np.nan_to_num(big & (q < Q_CUT)).astype(int)
        betas[lab].append(beta)
    if (rep + 1) % 10 == 0:
        print(f"  {rep + 1}/{N_REPS} repetitions done", flush=True)

rows = []
for t in TRANSITIONS:
    lab = TLAB[t]
    rows.append(pd.DataFrame({
        "ensembl_id": gene_order,
        "transition": lab,
        "matched_reps_reproducible": repro[lab],
        "matched_reps_significant": signif[lab],
        "matched_frac_reproducible": (repro[lab] / N_REPS).round(3),
        "matched_frac_significant": (signif[lab] / N_REPS).round(3),
        "matched_median_beta": np.nanmedian(np.vstack(betas[lab]), axis=0).round(4),
    }))
out = pd.concat(rows, ignore_index=True)
out.attrs = {}
path = HERE / "05_powermatched_per_gene.csv"
out.to_csv(path, index=False)

print(f"\nmedian genes per draw (these are the Task 3 headline numbers, "
      f"reproduced):")
for t in TRANSITIONS:
    lab = TLAB[t]
    print(f"  {lab}  reproducible (|beta|>=0.2, same sign): "
          f"{int((out[out.transition == lab].matched_frac_reproducible >= 0.5).sum()):>5,} genes in >=50% of draws"
          f"   |   significant in >=50% of draws: "
          f"{int((out[out.transition == lab].matched_frac_significant >= 0.5).sum()):>5,}")
print(f"\n-> {path.relative_to(ROOT)}  ({len(out):,} rows)")
