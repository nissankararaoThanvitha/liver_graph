"""Independent-patient gene summaries for stage-informed liver analysis.

Export the corrected selected union by fibrosis stage, disease group, sex and
age. Shared biopsy policy averages equal-stage repeats; differing stages retain
biopsy1. Each patient contributes once to means. Raw sample metadata remains a
separate table with biopsy order. Actual counts are written from inputs, not
hardcoded. Values are within-study value_z, not fold changes.
"""

import glob
import os

import numpy as np
import pandas as pd
from biopsy_policy import select_biopsies, patient_expression, expression_directory

GRAPH = str(expression_directory())
PROG = "data/progression_full"
META = "data/processed/samples_metadata.csv"
CLIN = "data/graph/nodes_sample_clinical.csv"
OUT = "data/for_mentor"

SEX_MAP = {"F": "F", "FEMALE": "F", "M": "M", "MALE": "M"}
AGE_BANDS = [(0, 29, "<30"), (30, 39, "30-39"), (40, 49, "40-49"),
             (50, 59, "50-59"), (60, 200, "60+")]
DISEASE_ORDER = ["control", "obese", "NAFL", "NAFLD", "NASH"]


def band(age):
    if pd.isna(age):
        return ""
    for lo, hi, lbl in AGE_BANDS:
        if lo <= age <= hi:
            return lbl
    return ""


def load_samples():
    m = pd.read_csv(META, dtype=str).fillna("")
    c = pd.read_csv(CLIN, dtype=str).fillna("")
    s = m[["sample_id", "dataset_id", "sex", "age"]].merge(
        c[["sample_id", "patient_id", "fibrosis_stage", "disease_group", "biopsy_number"]],
        on="sample_id")
    s["sex"] = s["sex"].str.strip().str.upper().map(SEX_MAP).fillna("")
    s["age_years"] = pd.to_numeric(s["age"], errors="coerce")
    s["age_band"] = s["age_years"].apply(band)
    s["fibrosis_stage"] = pd.to_numeric(s["fibrosis_stage"], errors="coerce")
    return s


def load_expression(genes):
    """value_z for the progression genes only, all studies."""
    parts = []
    for p in sorted(glob.glob(f"{GRAPH}/edges_GSE*.csv")):
        for ch in pd.read_csv(p, usecols=["sample_id", "ensembl_id", "value_z"],
                              chunksize=2_000_000):
            parts.append(ch[ch.ensembl_id.isin(genes)])
    return pd.concat(parts, ignore_index=True)


def pivot(df, index, columns, prefix):
    t = df.pivot_table(index=index, columns=columns, values="value_z",
                       aggfunc="mean").round(3)
    t.columns = [f"{prefix}{c}" for c in t.columns]
    return t.reset_index()


def main():
    os.makedirs(OUT, exist_ok=True)
    samples = load_samples()

    def sig(path):
        d = pd.read_csv(path)
        return d[(d.q_value < 0.05) & (d.n_agree == d.n_studies)]

    fib = sig(f"{PROG}/progression_fibrosis.csv")
    dis = sig(f"{PROG}/progression_disease.csv")
    genes = set(fib.ensembl_id) | set(dis.ensembl_id)
    print(f"progression genes: {len(genes):,}  "
          f"(fibrosis {len(fib):,}, inflammation {len(dis):,})")

    print("reading expression ...", flush=True)
    e = patient_expression(load_expression(genes), samples)
    print(f"  {len(e):,} measurements over {e.sample_id.nunique():,} samples")

    label = pd.concat([
        fib[["ensembl_id", "symbol"]], dis[["ensembl_id", "symbol"]]
    ]).drop_duplicates("ensembl_id").set_index("ensembl_id")["symbol"]

    def annotate(t):
        t.insert(1, "symbol", t.ensembl_id.map(label).fillna(""))
        f = fib.set_index("ensembl_id")
        d = dis.set_index("ensembl_id")
        t["fibrosis_rho"] = t.ensembl_id.map(f["median_rho"]).round(3)
        t["fibrosis_q"] = t.ensembl_id.map(f["q_value"])
        t["inflammation_rho"] = t.ensembl_id.map(d["median_rho"]).round(3)
        t["inflammation_q"] = t.ensembl_id.map(d["q_value"])
        t["n_studies"] = t.ensembl_id.map(f["n_studies"]).fillna(
            t.ensembl_id.map(d["n_studies"]))
        t["ladder"] = np.where(t.ensembl_id.isin(fib.ensembl_id) &
                               t.ensembl_id.isin(dis.ensembl_id), "both",
                      np.where(t.ensembl_id.isin(fib.ensembl_id),
                               "fibrosis_only", "inflammation_only"))
        return t

    # ---- 1. genes by fibrosis stage ---------------------------------------
    st = e[e.fibrosis_stage.notna()].copy()
    st["fibrosis_stage"] = st["fibrosis_stage"].astype(int)
    t1 = annotate(pivot(st, "ensembl_id", "fibrosis_stage", "stage_"))
    t1.to_csv(f"{OUT}/genes_by_fibrosis_stage.csv", index=False)
    n_st = st.groupby("fibrosis_stage")["sample_id"].nunique()
    print(f"\ngenes_by_fibrosis_stage.csv  {len(t1):,} genes  "
          f"patients per stage: {n_st.to_dict()}")

    # ---- 2. genes by disease group ----------------------------------------
    dg = e[e.disease_group != ""]
    t2 = annotate(pivot(dg, "ensembl_id", "disease_group", ""))
    keep = ["ensembl_id", "symbol"] + [c for c in DISEASE_ORDER if c in t2]
    t2 = t2[keep + [c for c in t2.columns if c not in keep]]
    t2.to_csv(f"{OUT}/genes_by_disease_group.csv", index=False)
    print(f"genes_by_disease_group.csv   {len(t2):,} genes  "
          f"patients: {dg.groupby('disease_group')['sample_id'].nunique().to_dict()}")

    # ---- 3. stage x sex ----------------------------------------------------
    ss = st[st.sex != ""].copy()
    ss["grp"] = ss.fibrosis_stage.astype(int).astype(str) + "_" + ss.sex
    t3 = annotate(pivot(ss, "ensembl_id", "grp", "stage"))
    t3.to_csv(f"{OUT}/genes_by_stage_and_sex.csv", index=False)
    print(f"genes_by_stage_and_sex.csv   {len(t3):,} genes  "
          f"{ss.sample_id.nunique()} samples")

    # ---- 4. stage x age band ----------------------------------------------
    sa = st[st.age_band != ""].copy()
    sa["grp"] = sa.fibrosis_stage.astype(int).astype(str) + "_" + sa.age_band
    t4 = annotate(pivot(sa, "ensembl_id", "grp", "stage"))
    t4.to_csv(f"{OUT}/genes_by_stage_and_age.csv", index=False)
    print(f"genes_by_stage_and_age.csv   {len(t4):,} genes  "
          f"{sa.sample_id.nunique()} samples")

    # ---- 5. sample demographics -------------------------------------------
    d5 = samples[["sample_id", "patient_id", "dataset_id", "sex", "age_years",
                  "age_band", "fibrosis_stage", "disease_group", "biopsy_number"]]
    d5.to_csv(f"{OUT}/sample_demographics.csv", index=False)
    print(f"sample_demographics.csv      {len(d5):,} samples")

    with open(f"{OUT}/README.txt", "w") as fh:
        fh.write(
            f"PROGRESSION GENES — corrected patient-level summaries\n\n"
            f"{len(genes):,} unique genes qualifying on at least one axis.\n"
            "Association is Spearman within each study, Fisher combined p,\n"
            "BH q < 0.05 and unanimous direction among testable studies.\n\n"
            "Biopsy policy: average when stages match; otherwise keep biopsy 1.\n"
            "Stage means give each patient one observation, not each biopsy.\n"
            f"Staged patients: {st.patient_id.nunique()}; with sex: {ss.patient_id.nunique()}; "
            f"with age: {sa.patient_id.nunique()}.\n"
            "Samples in sample_demographics.csv remain raw sample records and\n"
            "include biopsy_number; the biopsy policy is applied before analysis.\n\n"
            "Values are within-study gene-standardised value_z, not fold changes.\n"
            "Blank rho means that gene did not qualify on that axis.\n"
            "Files: stage means, disease-group means, stage x sex, stage x age\n"
            "and the raw sample-demographics table.\n")

    print(f"\nwritten to {OUT}/")


if __name__ == "__main__":
    main()
