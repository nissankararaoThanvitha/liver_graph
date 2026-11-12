"""External validation of the Paper 1 fibrosis genes in four independent GEO cohorts.

The Paper 1 gene lists are frozen: nothing here selects, re-ranks or refits genes.

Cohorts (none is one of the eight Paper 1 studies):
  GSE213621  Duke, NAFLD, FPKM            stages F0-F1 / F2 / F3-F4 (controls left out)
  GSE225740  Indiana, NAFLD, raw counts   stages F0..F4
  GSE268273  Spain, NAFLD, limma-voom log2-CPM   stages F0..F4
  GSE276114  Turkey/Sweden, MASLD + viral + alcohol, counts   stages F0-2 / F3 / F4

Preprocessing follows Paper 1 (map_gene_ids.py + build_graph_all.py):
  duplicate raw IDs -> keep first; map to Ensembl (version stripped) with the same HGNC file
  and priority (Ensembl, Entrez, current symbol, unique previous symbol, unique alias);
  unmappable and _PAR_Y rows dropped; raw IDs mapping to one Ensembl ID summed (linear scale);
  counts -> log2(CPM+1) with library size taken before mapping; FPKM -> log2(FPKM+1);
  already-log data kept on its log2 scale; every gene z-scored within the study.

Tests, per cohort and gene set (Top 23, Tier 1, Tier 2, Tier 3, all 3,845):
  1. Direction agreement: % of genes whose within-cohort Spearman rho with stage has the sign
     of the Paper 1 direction; p from 1,000 stage-label permutations (seed 42).
  2. Replication: % of genes with BH q < 0.05 (BH over the testable Paper 1 universe of
     14,794 genes) and the Paper 1 sign; compared with 1,000 expression-matched random sets of
     non-selected universe genes (sign taken from their Paper 1 median rho).
  3. Effect agreement: Spearman correlation between Paper 1 rho and cohort rho.
  4. Score: per patient, mean z of rising genes minus mean z of falling genes (no weights);
     Spearman with stage (permutation p) and AUC for advanced (F3-F4) vs mild
     (F0-F1; F0-2 in GSE276114), bootstrap 95% CI.

Run from the repository root:  python Paper1_Validation/code/validate_external.py
"""
import gzip
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from map_gene_ids import build_lookups, resolve, strip_version  # noqa: E402  (Paper 1 code)

RAW = ROOT / "data/raw_validation"
OUT = ROOT / "Paper1_Validation/results"
HGNC = ROOT / "data/raw/hgnc_complete_set.txt"
B = 1000
SEED = 42


# ------------------------------------------------------------------ sample annotations
def series_matrix(gse):
    """GSM-level annotations from the GEO series matrix: title, description, characteristics."""
    rows = {}
    with gzip.open(RAW / gse / f"{gse}_series_matrix.txt.gz", "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("!series_matrix_table_begin"):
                break
            if not line.startswith("!Sample_"):
                continue
            key, *vals = line.rstrip("\n").split("\t")
            vals = [v.strip('"') for v in vals]
            if key == "!Sample_characteristics_ch1":
                k = vals[0].split(":", 1)[0].strip().lower() if vals and ":" in vals[0] else "char"
                vals = [v.split(":", 1)[1].strip() if ":" in v else v for v in vals]
                key = k
            else:
                key = key.replace("!Sample_", "")
            if key in rows:
                continue
            rows[key] = vals
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ expression readers
def read_gse213621():
    x = pd.read_csv(RAW / "GSE213621/GSE213621_FPKMs_allsamples.txt.gz", sep="\t", index_col=0)
    m = series_matrix("GSE213621")
    m["col"] = "Sample_" + m.title.str.replace("human liver sample ", "", regex=False).str.strip()
    codes = {"F0F1": 0, "F2": 1, "F3F4": 2}
    m["stage"] = m["fibrotic stage"].map(codes)
    m["mild"] = m["fibrotic stage"].eq("F0F1")
    m["advanced"] = m["fibrotic stage"].eq("F3F4")
    m["group"] = "NAFLD"
    return x, "symbol", "FPKM", m[["col", "geo_accession", "stage", "mild", "advanced", "group"]]


def read_gse225740():
    x = pd.read_csv(RAW / "GSE225740/GSE225740_NAFLD_RNA_counts.csv.gz", index_col=0)
    x.index = x.index.astype(str)
    ph = pd.read_csv(RAW / "GSE225740/GSE225740_NAFLD_phenotypes.csv.gz")
    m = series_matrix("GSE225740")
    m["col"] = m.description.str.strip()
    m = m.merge(ph.assign(col=ph["pt. ID"].astype(str)), on="col", how="left")
    m["stage"] = pd.to_numeric(m["fibrosis_y"] if "fibrosis_y" in m else m["fibrosis"], errors="coerce")
    m["mild"] = m.stage.le(1)
    m["advanced"] = m.stage.ge(3)
    m["group"] = "NAFLD"
    return x, "entrez", "raw_count", m[["col", "geo_accession", "stage", "mild", "advanced", "group"]]


def read_gse268273():
    x = pd.read_excel(RAW / "GSE268273/GSE268273_EGN_RNAseq_Normalized_data.xlsx")
    x = x.rename(columns={x.columns[0]: "gene"}).drop(columns=x.columns[1:3]).set_index("gene")
    m = series_matrix("GSE268273")
    m["col"] = m.description.str.strip()
    m["stage"] = m["fibrosis degree"].str.extract(r"F(\d)")[0].astype(float)
    m["mild"] = m.stage.le(1)
    m["advanced"] = m.stage.ge(3)
    m["group"] = m["disease"]
    return x, "ensembl", "log2_voom", m[["col", "geo_accession", "stage", "mild", "advanced", "group"]]


def read_gse276114():
    x = pd.read_csv(RAW / "GSE276114/GSE276114_raw.count.txt.gz", sep="\t", index_col=0)
    m = series_matrix("GSE276114")
    m["col"] = m.title.str.strip()
    codes = {"F0-2": 0, "F3": 1, "F4": 2}
    m["stage"] = m["disease group"].map(codes)
    m["mild"] = m["disease group"].eq("F0-2")
    m["advanced"] = m["disease group"].isin(["F3", "F4"])
    m["group"] = m["disease"]
    return x, "symbol", "raw_count", m[["col", "geo_accession", "stage", "mild", "advanced", "group"]]


READERS = {"GSE213621": read_gse213621, "GSE225740": read_gse225740,
           "GSE268273": read_gse268273, "GSE276114": read_gse276114}


# ------------------------------------------------------------------ Paper 1 preprocessing
def preprocess(x, id_type, unit, lk, log):
    x = x.select_dtypes(include="number")
    x.index = x.index.astype(str).str.strip()
    n_raw = len(x)
    x = x[~x.index.duplicated(keep="first")]
    lib = x.sum(axis=0) if unit == "raw_count" else None          # before mapping/filtering
    n_unique = len(x)
    x = x[~x.index.str.contains("_PAR_Y", na=False)]
    n_par = n_unique - len(x)
    ens = {}
    for raw in x.index:
        r = resolve(raw, id_type, lk)
        if r is not None:
            ens[raw] = r[0]
    log.append(f"  raw IDs {n_raw:,} -> unique {n_unique:,} -> _PAR_Y dropped {n_par:,} -> "
               f"mapped {len(ens):,} (unmapped dropped {len(x) - len(ens):,})")
    x = x.loc[list(ens)]
    if unit == "log2_voom":                                          # back to linear only to sum
        lin = np.power(2.0, x)
        lin = lin.groupby(lin.index.map(ens)).sum()
        v = np.log2(lin)
    else:
        lin = x.groupby(x.index.map(ens)).sum()
        v = np.log2(lin / lib * 1e6 + 1) if unit == "raw_count" else np.log2(lin + 1)
    log.append(f"  Ensembl genes {len(v):,}; transform {unit}")
    sd = v.std(axis=1, ddof=0).replace(0, np.nan)
    z = v.sub(v.mean(axis=1), axis=0).div(sd, axis=0)
    return v, z


# ------------------------------------------------------------------ statistics
def rankz(a, axis):
    r = np.apply_along_axis(stats.rankdata, axis, a)
    r = r - r.mean(axis=axis, keepdims=True)
    sd = r.std(axis=axis, keepdims=True)
    return r / np.where(sd == 0, np.nan, sd)


def spearman_rows(mat, y):
    """Spearman rho and p of every row of mat (genes x samples) against y (as in Paper 1)."""
    n = len(y)
    rm = rankz(mat, 1)
    ry = rankz(np.asarray(y, float)[None, :], 1)[0]
    rho = np.clip((rm * ry).mean(axis=1), -0.9999999, 0.9999999)
    t = rho * np.sqrt((n - 2) / (1 - rho ** 2))
    return rho, 2 * stats.t.sf(np.abs(t), df=n - 2), rm


def bh(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    q = p[o] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[o] = np.minimum(q, 1)
    return out


def auc(score, pos, neg):
    a, b = score[pos], score[neg]
    if len(a) == 0 or len(b) == 0:
        return np.nan
    u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic
    return u / (len(a) * len(b))


# ------------------------------------------------------------------ main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    genes = pd.read_csv(ROOT / "Paper1_HighConfidence/11_final_all_3845_genes.csv")
    short = set(pd.read_csv(ROOT / "Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv").Ensembl_ID)
    universe = pd.read_csv(ROOT / "data/progression_full/progression_fibrosis.csv")  # 14,794 Paper 1 genes
    p1_sign = np.sign(universe.set_index("ensembl_id").median_rho)
    genes["sign"] = genes.Direction.map({"increasing": 1, "decreasing": -1})
    gsign = genes.set_index("Ensembl_ID").sign
    sets = {
        "Top 23 shortlist": short,
        "Tier 1 (447)": set(genes.loc[genes.Tier.str.startswith("Tier 1"), "Ensembl_ID"]),
        "Tier 2 (1,403)": set(genes.loc[genes.Tier.str.startswith("Tier 2"), "Ensembl_ID"]),
        "Tier 3 (1,995)": set(genes.loc[genes.Tier.str.startswith("Tier 3"), "Ensembl_ID"]),
        "All 3,845": set(genes.Ensembl_ID),
    }
    selected = set(genes.Ensembl_ID)
    lk = build_lookups(str(HGNC))
    log, rows, per_gene = [], [], []

    for gse, reader in READERS.items():
        x, id_type, unit, meta = reader()
        log.append(f"{gse}: {x.shape[1]} expression columns, {len(meta)} GEO samples")
        miss = set(meta.col) - set(x.columns)
        if miss:
            raise SystemExit(f"{gse}: {len(miss)} annotated samples missing from expression file: {sorted(miss)[:5]}")
        v, z = preprocess(x, id_type, unit, lk, log)
        cohorts = [(gse, "all", meta)]
        if gse == "GSE276114":
            # ARLD (14 patients) is not tested on its own: all 14 are F3-F4, so stage does not vary
            cohorts += [(gse, g, meta[meta.group == g]) for g in ["MASLD", "CVH"]]
        for name, sub, m in cohorts:
            m = m[m.stage.notna()]
            cols = list(m.col)
            y = m.stage.to_numpy(float)
            zz = z.loc[z.index.intersection(universe.ensembl_id), cols]
            zz = zz[zz.notna().all(axis=1) & (zz.nunique(axis=1) > 1)]
            rho, p, rm = spearman_rows(zz.to_numpy(float), y)
            q = bh(p)
            res = pd.DataFrame({"ensembl_id": zz.index, "rho": rho, "p": p, "q": q})
            res["paper1_sign"] = res.ensembl_id.map(p1_sign)
            res["agree"] = np.sign(res.rho) == res.paper1_sign
            res["replicated"] = res.agree & (res.q < 0.05)
            res["mean_log"] = v.loc[res.ensembl_id, cols].mean(axis=1).to_numpy()
            res["decile"] = pd.qcut(res.mean_log.rank(method="first"), 10, labels=False)
            res = res.set_index("ensembl_id")
            # permuted stage labels, shared by all gene sets of this cohort
            ry = rankz(y[None, :], 1)[0]
            perm = np.stack([rng.permutation(ry) for _ in range(B)], axis=1)   # samples x B
            rho_perm = (np.nan_to_num(rm) @ perm) / len(y)                       # genes x B
            idx = {g: i for i, g in enumerate(zz.index)}
            pos, neg = m.advanced.to_numpy(bool), m.mild.to_numpy(bool)
            null_pool = res[~res.index.isin(selected)]
            log.append(f"  {name} [{sub}]: {len(cols)} staged patients "
                       f"(mild {neg.sum()}, advanced {pos.sum()}); testable universe genes {len(res):,}")
            for sname, s in sets.items():
                g = [x_ for x_ in s if x_ in idx]
                if not g:
                    continue
                r = res.loc[g]
                exp_sign = gsign.loc[g].to_numpy()
                agree = float((np.sign(r.rho.to_numpy()) == exp_sign).mean())
                ii = [idx[x_] for x_ in g]
                agree_perm = (np.sign(rho_perm[ii]) == exp_sign[:, None]).mean(axis=0)
                p_agree = (1 + (agree_perm >= agree).sum()) / (B + 1)
                rep = float(((np.sign(r.rho.to_numpy()) == exp_sign) & (r.q.to_numpy() < 0.05)).mean())
                # expression-matched random sets of non-selected genes
                need = r.decile.value_counts()
                pools = {d: null_pool.index[null_pool.decile == d].to_numpy() for d in need.index}
                null_rep = np.empty(B)
                for b in range(B):
                    pick = np.concatenate([rng.choice(pools[d], size=k, replace=len(pools[d]) < k)
                                           for d, k in need.items()])
                    null_rep[b] = null_pool.loc[pick, "replicated"].mean()
                p_rep = (1 + (null_rep >= rep).sum()) / (B + 1)
                eff = stats.spearmanr(genes.set_index("Ensembl_ID").loc[g, "Fibrosis_rho"], r.rho).statistic \
                    if len(g) > 2 else np.nan
                up = [x_ for x_ in g if gsign[x_] > 0]
                dn = [x_ for x_ in g if gsign[x_] < 0]
                score = (zz.loc[up].mean(axis=0) if up else 0) - (zz.loc[dn].mean(axis=0) if dn else 0)
                score = np.asarray(score, float)
                s_rho = stats.spearmanr(score, y).statistic
                s_perm = np.array([stats.spearmanr(score, rng.permutation(y)).statistic for _ in range(B)])
                p_score = (1 + (s_perm >= s_rho).sum()) / (B + 1)
                a = auc(score, pos, neg)
                boots = []
                pi, ni = np.where(pos)[0], np.where(neg)[0]
                if len(pi) and len(ni):
                    for _ in range(B):
                        bp, bn = rng.choice(pi, len(pi)), rng.choice(ni, len(ni))
                        boots.append(auc(score, bp, bn))
                lo, hi = (np.nanpercentile(boots, [2.5, 97.5]) if boots else (np.nan, np.nan))
                rows.append(dict(
                    cohort=gse, subgroup=sub, gene_set=sname, patients=len(cols),
                    mild=int(neg.sum()), advanced=int(pos.sum()),
                    genes_in_set=len(s), genes_testable=len(g),
                    direction_agree_pct=round(100 * agree, 1),
                    direction_perm_mean_pct=round(100 * agree_perm.mean(), 1), direction_p=p_agree,
                    replicated_pct=round(100 * rep, 1),
                    replicated_matched_random_pct=round(100 * null_rep.mean(), 1), replicated_p=p_rep,
                    rho_vs_paper1_rho=round(eff, 3),
                    score_rho_with_stage=round(s_rho, 3), score_p=p_score,
                    auc_advanced_vs_mild=round(a, 3), auc_ci_low=round(lo, 3), auc_ci_high=round(hi, 3)))
                print(f"{gse:9s} {sub:5s} {sname:17s} n={len(cols):3d} genes={len(g):4d} "
                      f"agree={100*agree:5.1f}% rep={100*rep:5.1f}% (rand {100*null_rep.mean():4.1f}%) "
                      f"score rho={s_rho:.2f} AUC={a:.2f} [{lo:.2f}-{hi:.2f}]", flush=True)
            if sub == "all":
                out = res.loc[res.index.isin(selected), ["rho", "p", "q"]].add_prefix(f"{gse}_")
                per_gene.append(out)

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "validation_summary.csv", index=False)
    pg = genes[["Gene", "Ensembl_ID", "Direction", "Tier", "Cluster", "Fibrosis_rho", "Largest_transition"]].copy()
    pg["Top23"] = pg.Ensembl_ID.isin(short)
    for t in per_gene:
        pg = pg.merge(t, left_on="Ensembl_ID", right_index=True, how="left")
    rcols = [c for c in pg.columns if c.endswith("_rho") and c.startswith("GSE")]
    qcols = [c for c in pg.columns if c.endswith("_q")]
    pg["cohorts_testable"] = pg[rcols].notna().sum(axis=1)
    sgn = pg.Direction.map({"increasing": 1, "decreasing": -1})
    pg["cohorts_same_direction"] = sum((np.sign(pg[c]) == sgn).astype(int) for c in rcols)
    pg["cohorts_replicated_q05"] = sum(((np.sign(pg[r]) == sgn) & (pg[q] < 0.05)).astype(int)
                                       for r, q in zip(rcols, qcols))
    pg.to_csv(OUT / "validation_per_gene.csv", index=False)
    (OUT / "preprocessing_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()
