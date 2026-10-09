"""
export_for_mentor.py
--------------------
Builds the CSVs the mentor asked for in the 2026-09-07 meeting:

    "send me those genes ... that is for stage wise genes. I just want to see
     how the genes are progressing ... do a CSV, first stage, second stage,
     each and every should give this, I will do analysis"

    "phenotypes are not very useful, if you have age and sex, only add those
     things ... sample having a gene, and maybe its age is from 30 to 35, and
     the gender is male, same gene, for fibrosis, the age is from 20 to 25 --
     you understand the comparison we are doing"

    "do not send me any pathway information"
    "don't send me 54,000 [genes]"

So: only the 4,692 progression genes, their expression per stage, split by
sex and by age band. No pathways, no drugs, no phenotype nodes.

SEX NEEDS HARMONISING FIRST
The eight studies write sex six different ways -- Female, female, F, Male,
male, M -- so grouping on the raw value silently splits every group in two.
Same class of bug as the F4/4 fibrosis mismatch fixed earlier.

AGE COVERAGE IS THE REAL LIMIT
Age and sex are only recorded by five of the eight studies, and only three of
those also stage fibrosis. So the stage x age x sex comparison rests on 385
samples from GSE130970, GSE162694 and GSE193066 -- not the full 1,085. The
per-stage gene table itself uses all 668 staged samples; only the demographic
splits are restricted. Every output file carries its own n so the limit is
visible rather than assumed.

Values are value_z: expression standardised per gene within each study, which
is what makes the eight cohorts comparable at all. A positive number means
above average for that gene in that study.

Output (data/for_mentor/):
    genes_by_fibrosis_stage.csv      4,692 rows x stages 0-4
    genes_by_disease_group.csv       control / NAFL / NASH
    genes_by_stage_and_sex.csv       stage x sex
    genes_by_stage_and_age.csv       stage x age band
    sample_demographics.csv          one row per sample
    README.txt                       what each column means

Usage:
    python export_for_mentor.py
"""

import glob
import os

import numpy as np
import pandas as pd

GRAPH = "data/graph_full"
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
        c[["sample_id", "patient_id", "fibrosis_stage", "disease_group"]],
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
    e = load_expression(genes).merge(samples, on="sample_id")
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
                  "age_band", "fibrosis_stage", "disease_group"]]
    d5.to_csv(f"{OUT}/sample_demographics.csv", index=False)
    print(f"sample_demographics.csv      {len(d5):,} samples")

    with open(f"{OUT}/README.txt", "w") as fh:
        fh.write(
            "PROGRESSION GENES -- for analysis\n"
            "=================================\n\n"
            "4,692 genes whose expression tracks liver disease progression,\n"
            "from 1,027 patients across 8 GEO studies. Only genes measured in\n"
            "ALL 8 studies were tested, and a gene is included only where every\n"
            "study agreed on the direction (Spearman per study, combined by\n"
            "Fisher's method, Benjamini-Hochberg q < 0.05).\n\n"
            "VALUES\n"
            "  All numbers are value_z: expression standardised per gene within\n"
            "  each study (mean 0, sd 1). This is what makes 8 cohorts\n"
            "  comparable. Positive = above average for that gene.\n\n"
            "COLUMNS\n"
            "  fibrosis_rho       correlation with fibrosis stage 0-4 (-1..+1)\n"
            "  inflammation_rho   correlation with control->NAFL->NASH\n"
            "  n_studies          how many studies the gene was tested in\n"
            "  ladder             fibrosis_only / inflammation_only / both\n"
            "  blank rho          gene not significant on that ladder\n\n"
            "FILES\n"
            "  genes_by_fibrosis_stage.csv   mean per stage 0,1,2,3,4\n"
            "  genes_by_disease_group.csv    mean per control/NAFL/NASH etc\n"
            "  genes_by_stage_and_sex.csv    stage x M/F\n"
            "  genes_by_stage_and_age.csv    stage x age band\n"
            "  sample_demographics.csv       one row per sample\n\n"
            "COVERAGE LIMIT -- important\n"
            "  Age and sex are recorded by 5 of the 8 studies, and only 3 of\n"
            "  those also stage fibrosis. The stage x age and stage x sex files\n"
            "  therefore rest on 385 samples (GSE130970, GSE162694, GSE193066),\n"
            "  not all 1,085. The per-stage file uses all 668 staged samples.\n"
            "  Sex was written six ways across studies (Female/female/F/Male/\n"
            "  male/M) and has been harmonised to M/F.\n\n"
            "  GSE193066 contributes 164 samples from 106 patients -- 58 were\n"
            "  biopsied twice. Group by patient_id, not sample_id, for stats.\n")

    print(f"\nwritten to {OUT}/")


if __name__ == "__main__":
    main()
