"""
find_progression_genes.py
-------------------------
Finds the genes whose expression tracks disease progression, which is the
mentor's stated primary aim: "our aim is to predict the stages".

TWO LADDERS, NOT ONE
Liver disease progresses along two axes that pathologists score separately
because they are not the same thing:

    fibrosis   0 -> 1 -> 2 -> 3 -> 4     how much scarring (largely permanent)
    disease    control -> NAFL -> NASH   how much inflammation (reversible)

40 of our NASH patients have fibrosis stage 0 -- inflamed but not yet
scarred. That is the most treatable moment in the disease, and it is
invisible if you only look at the fibrosis ladder. So both are run.

METHOD
For each gene, within each study separately, correlate value_z against the
ladder position (Spearman, because the stages are ordered ranks and the
spacing between them is not meaningful).

Running per study and combining afterwards, rather than pooling all patients,
is deliberate. Studies differ in cohort, sequencing depth and centre; a gene
that climbs beautifully in one study and does nothing in the other four is a
quirk of that study, not biology. Requiring agreement across independent
studies is the same rule that validated the recovered GSE162694 labels and
caught the bad GSE193066 ones.

Per-study rho values are combined by their median, and significance by
Fisher's method over the per-study p-values. Genes are kept only when most
studies agree on the direction.

PSEUDO-REPLICATION GUARD
GSE193066 biopsied 58 patients twice. Counting those as 116 independent
people would give them double weight. Samples are collapsed to one row per
patient_id per study before any statistics are computed.

Only genes measured in all 8 studies (n_datasets == 8) are tested: every
study then contributes to every gene, and 100% of them carry the PrimeKG
biology needed for the drug step that follows.

Usage:
    python find_progression_genes.py
"""

import glob
import os

import numpy as np
import pandas as pd
from scipy import stats

GRAPH_ALL = "data/graph_all"
CLINICAL = "data/graph/nodes_sample_clinical.csv"
OUT = "data/progression"

DISEASE_LADDER = {"control": 0, "NAFL": 1, "NASH": 2}
MIN_PATIENTS = 25          # per study, else that study is skipped for the axis
MIN_STUDIES = 3            # a gene must be testable in at least this many


def load_labels():
    c = pd.read_csv(CLINICAL, dtype=str).fillna("")
    c["fibrosis"] = pd.to_numeric(c["fibrosis_stage"], errors="coerce")
    c["disease"] = c["disease_group"].map(DISEASE_LADDER)
    return c[["sample_id", "dataset_id", "patient_id", "fibrosis", "disease"]]


def spearman_matrix(mat, y):
    """Spearman rho + p for every column of `mat` against `y`.

    Ranks both sides then takes Pearson, which is what Spearman is. Done as
    one matrix operation because doing it gene by gene over 14,794 genes x 5
    studies is thousands of times slower for an identical answer.
    """
    n = len(y)
    ry = stats.rankdata(y)
    ry = (ry - ry.mean()) / ry.std()
    rm = np.apply_along_axis(stats.rankdata, 0, mat)
    rm = (rm - rm.mean(axis=0)) / np.where(rm.std(axis=0) == 0, np.nan,
                                           rm.std(axis=0))
    rho = (rm * ry[:, None]).mean(axis=0)
    rho = np.clip(rho, -0.9999999, 0.9999999)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = rho * np.sqrt((n - 2) / (1 - rho ** 2))
    p = 2 * stats.t.sf(np.abs(t), df=n - 2)
    return rho, p


def run_axis(axis, labels, core):
    """One ladder, every study, one row per gene."""
    per_study = {}
    for path in sorted(glob.glob(f"{GRAPH_ALL}/edges_GSE*.csv")):
        gse = os.path.basename(path)[6:-4]
        lab = labels[(labels.dataset_id == gse) & labels[axis].notna()]
        if len(lab) < MIN_PATIENTS:
            continue

        e = pd.read_csv(path, usecols=["sample_id", "ensembl_id", "value_z"])
        e = e[e.ensembl_id.isin(core)]
        e = e.merge(lab[["sample_id", "patient_id", axis]], on="sample_id")
        if e.empty:
            continue

        # One row per patient: the 58 twice-biopsied people must not count
        # twice. Averaging their two biopsies keeps both measurements.
        e = (e.groupby(["patient_id", "ensembl_id"], as_index=False)
               .agg(value_z=("value_z", "mean"), y=(axis, "first")))

        wide = e.pivot(index="patient_id", columns="ensembl_id",
                       values="value_z")
        y = e.drop_duplicates("patient_id").set_index("patient_id")["y"]
        y = y.reindex(wide.index)
        keep = wide.notna().all(axis=0)
        wide = wide.loc[:, keep]
        if wide.shape[1] == 0:
            continue

        rho, p = spearman_matrix(wide.to_numpy(float), y.to_numpy(float))
        per_study[gse] = pd.DataFrame({"rho": rho, "p": p}, index=wide.columns)
        print(f"  {axis:9s} {gse}: {len(wide):>4} patients, "
              f"{wide.shape[1]:,} genes")

    if not per_study:
        return pd.DataFrame()

    rho = pd.DataFrame({k: v["rho"] for k, v in per_study.items()})
    pv = pd.DataFrame({k: v["p"] for k, v in per_study.items()})

    n_tested = rho.notna().sum(axis=1)
    med = rho.median(axis=1)
    # how many studies agree with the median direction
    agree = ((rho.gt(0)).eq(med.gt(0), axis=0) & rho.notna()).sum(axis=1)
    # Fisher's method over the per-study p-values
    chi = -2 * np.log(pv.clip(lower=1e-300)).sum(axis=1)
    comb = stats.chi2.sf(chi, df=2 * pv.notna().sum(axis=1))

    out = pd.DataFrame({
        "median_rho": med, "n_studies": n_tested, "n_agree": agree,
        "combined_p": comb, "min_rho": rho.min(axis=1),
        "max_rho": rho.max(axis=1),
    })
    return out[out.n_studies >= MIN_STUDIES]


def main():
    os.makedirs(OUT, exist_ok=True)
    labels = load_labels()
    genes = pd.read_csv(f"{GRAPH_ALL}/nodes_gene.csv", dtype=str).fillna("")
    core = set(genes[genes.n_datasets == "8"].ensembl_id)
    sym = genes.set_index("ensembl_id")["symbol"].to_dict()
    print(f"testing {len(core):,} genes measured in all 8 studies\n")

    results = {}
    for axis in ("fibrosis", "disease"):
        print(f"--- {axis.upper()} LADDER ---")
        r = run_axis(axis, labels, core)
        if r.empty:
            continue
        # Benjamini-Hochberg across genes: with ~15k tests, raw p-values
        # would hand back hundreds of false positives.
        r = r.sort_values("combined_p")
        m = len(r)
        r["q_value"] = np.minimum.accumulate(
            (r["combined_p"] * m / np.arange(1, m + 1))[::-1])[::-1]
        r["symbol"] = [sym.get(i, "") for i in r.index]
        r = r.reset_index().rename(columns={"index": "ensembl_id"})
        r.to_csv(f"{OUT}/progression_{axis}.csv", index=False)
        results[axis] = r
        sig = r[(r.q_value < 0.05) & (r.n_agree == r.n_studies)]
        print(f"  -> {len(r):,} genes tested, {len(sig):,} significant "
              f"with ALL studies agreeing\n")

    for axis, r in results.items():
        top = r[(r.q_value < 0.05) & (r.n_agree == r.n_studies)]
        up = top[top.median_rho > 0].nlargest(15, "median_rho")
        dn = top[top.median_rho < 0].nsmallest(15, "median_rho")
        print(f"=== {axis.upper()}: strongest RISING genes ===")
        print(up[["symbol", "median_rho", "n_studies", "q_value"]]
              .to_string(index=False))
        print(f"\n=== {axis.upper()}: strongest FALLING genes ===")
        print(dn[["symbol", "median_rho", "n_studies", "q_value"]]
              .to_string(index=False))
        print()

    if len(results) == 2:
        a, b = results["fibrosis"], results["disease"]
        m = a.merge(b, on="ensembl_id", suffixes=("_fib", "_dis"))
        both = m[(m.q_value_fib < 0.05) & (m.q_value_dis < 0.05) &
                 (np.sign(m.median_rho_fib) == np.sign(m.median_rho_dis))]
        both = both.reindex(
            both[["median_rho_fib", "median_rho_dis"]].abs().min(axis=1)
            .sort_values(ascending=False).index)
        both.to_csv(f"{OUT}/progression_both.csv", index=False)
        print(f"=== GENES ON *BOTH* LADDERS: {len(both):,} ===")
        print(both.head(20)[["symbol_fib", "median_rho_fib",
                             "median_rho_dis"]].to_string(index=False))


if __name__ == "__main__":
    main()
