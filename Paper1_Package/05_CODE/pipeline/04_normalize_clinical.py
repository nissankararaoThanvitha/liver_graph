"""
normalize_clinical.py
---------------------
Harmonises the per-sample CLINICAL labels the way map_gene_ids.py harmonised
the gene identifiers.

The gene side of this project is fully harmonised; the patient side was not.
Each study recorded severity on its own ruler:

    fibrosis   GSE130970/135251/162694/193066 -> "0".."4"
               GSE240729                      -> "F0".."F4"
               GSE162694                      -> "normal liver histology"

    disease    GSE126848 -> healthy / obese / NAFLD / NASH
               GSE135251 -> control / early / moderate
               GSE167523 -> NAFL / NASH

Querying fibrosis_stage_raw = '4' therefore returns 29 of the 35 real
cirrhosis samples and reports no error. That silent undercount is the bug
this script removes.

Two clean fields are ADDED; the *_raw originals are never modified, so every
translation stays auditable:

    fibrosis_stage   integer 0-4, or blank when the study never staged it
    disease_group    one of: control, obese, NAFL, NASH, NAFLD
    patient_id       the person the biopsy came from
    biopsy_number    1 or 2, for studies that re-biopsied

patient_id matters because GSE193066's 164 samples are NOT 164 people: they
are 106 patients, 58 of whom were biopsied twice ("1st biopsy" / "2nd
biopsy" in its GEO characteristics, confirmed by the paper, PMID 35731891).
Treating them as independent is pseudo-replication and inflates significance
in any test run across that study. No other dataset repeats a patient.

Recovered labels
----------------
    GSE162694  "nash100_N" -> control,  "nash12_F3" -> NAFLD

    CORRECTED. This study previously read every "_F0".."_F4" sample as
    NASH, labelling 112 of its 143 samples NASH. That was wrong, and the
    check that was supposed to catch it tested the wrong thing.

    GEO records only {tissue, age, sex, fibrosis stage, nas score} for
    this series -- no diagnosis field at all. The suffix is the fibrosis
    stage. Reading a stage as a diagnosis assumes that anyone whose
    scarring was measured has steatohepatitis, which is not true: 35 of
    these samples sit at F0, with no scarring, and were all called NASH.

    The old justification -- "the suffix was cross-checked against
    fibrosis_stage_raw for all 143 samples and agreed on every one" --
    is circular. The suffix IS the fibrosis stage, so that check only
    confirmed that "_F3" means stage 3. It never tested the diagnosis.

    The source paper (Sci Rep 2021, PMC8433177, this series' own
    publication) gives the real counts in its Table 1, and its group
    sizes match this cohort exactly:

        normal histology  31 samples,  0 NASH
        NAFLD stage 0     35 samples,  9 NASH   (26%)
        NAFLD stage 1     30 samples, 21 NASH   (70%)
        NAFLD stage 2     27 samples, 26 NASH   (96%)
        NAFLD stage 3      8 samples,  7 NASH   (88%)
        NAFLD stage 4     12 samples,  6 NASH   (50%)
        total            143 samples, 69 NASH

    So 69 of 143, not 112 -- 43 samples were mislabelled, and the error
    is concentrated where it does most damage: 26 of the 35 stage-0
    samples are not NASH.

    Table 1 is a summary by group, and no supplementary file lists
    samples individually (checked: all four of the paper's supplements
    hold figures, gene signatures and methods, no sample IDs). Knowing
    that 9 of 35 stage-0 samples are NASH does not say WHICH 9, so the
    labels cannot be repaired, only corrected downward to what the data
    supports.

    NAFLD is what the paper itself calls these patients, and it is true
    of all 112. It does not place them on the control -> NAFL -> NASH
    ladder, because it does not say which rung -- which is the honest
    position, since nobody knows. This study therefore no longer
    contributes to the disease ladder, leaving three studies there.
    Its fibrosis staging is unaffected and still contributes in full.

    The NAS score cannot rescue this either, for the reason already
    given below for GSE193066: Kleiner is explicit that NAS alone is not
    a diagnostic criterion and cannot separate NASH from NAFL.

Recovery that was tried and REJECTED
------------------------------------
GSE193066's sample_description looks like a label ("NAFLD.HUn106.gct" /
"NASH.*") but reading it as a diagnosis produced a group that was MORE
fibrotic (mean stage 2.16 vs 1.78) yet had LOWER COL1A1 than its NAFL group
-- backwards, and contradicting that study's own fibrosis staging. Every
other study runs the correct direction. The string is a processed-filename
prefix, not a characteristic, and its 106/58 split does not match the 116/48
split of the sample titles. So it encodes a file batch, not a patient, and
the study is left unlabelled.

GSE130970 states no diagnosis, but GEO carries its full Kleiner panel
(steatosis / ballooning / lobular inflammation), which is what a pathologist
scores the diagnosis FROM. Applying the standard NASH-CRN definition:

    steatosis 0                -> control   (no steatosis, no fatty liver)
    ballooning >= 1            -> NASH      (hepatocyte ballooning is the
                                             defining lesion of steatohepatitis)
    steatosis >=1, ballooning 0 -> NAFL     (steatosis without steatohepatitis)

This is a derivation, not a stated label, so it is marked
derived_from_histology and can be excluded with one filter.

Deliberately left blank
-----------------------
    GSE269412  (262) GEO stores only {"tissue": "Liver"} -- confirmed at the
                     sample record itself, not just in our parse. The paper
                     (JCI Insight 2025, PMID 39998893) reports the cohort only
                     in aggregate, and the GEO titles are anonymised codes
                     (KYL112), so no join key exists. Needs the authors.
    GSE240729  (67)  GEO carries fibrosisscore only, no diagnosis field
    GSE167523  (98)  diagnosed but never staged
    GSE126848  (57)  diagnosed but never staged
    GSE193066  (164) see rejected recovery above. Its NAS is present but NAS
                     alone cannot separate NASH from NAFL -- Kleiner is
                     explicit that the score is not a diagnostic criterion.
A blank field is a known unknown. A guessed label is an unknown unknown, and
would quietly contaminate every group comparison built on it.

Usage:
    python normalize_clinical.py
"""

import json
import os
import re

import pandas as pd

PROC = "data/processed"
GRAPH = "data/graph"

# "F3" and "3" are the same Kleiner stage; a histologically normal liver has
# no fibrosis and is therefore stage 0.
FIBROSIS_MAP = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
    "F0": 0, "F1": 1, "F2": 2, "F3": 3, "F4": 4,
    "NORMAL LIVER HISTOLOGY": 0,
}

# Where a study lists NAFLD *alongside* NASH as separate arms, its "NAFLD"
# arm means fatty liver without steatohepatitis -- i.e. NAFL. Both GSE126848
# and GSE193066 do exactly that, so NAFLD collapses to NAFL there.
DISEASE_MAP = {
    "HEALTHY": "control",
    "CONTROL": "control",
    "OBESE": "obese",          # obese *without* NAFLD: its own comparison arm,
                               # not a disease and not a lean control
    "NAFL": "NAFL",
    "NAFLD": "NAFL",
    "NASH": "NASH",
}

# GSE135251 labels severity, not diagnosis: "early" is fibrosis 0-2 and
# "moderate" is fibrosis 3-4, which fibrosis_stage already records. They mark
# NAFLD-spectrum patients whose NAFL/NASH subtype the series never states.
SEVERITY_BAND = {"EARLY": "NAFLD", "MODERATE": "NAFLD"}

# The suffix encodes normal histology or a fibrosis stage, nothing more.
GSE162694_SUFFIX = re.compile(r"_(F\d|N)$")


def norm_fibrosis(raw):
    return FIBROSIS_MAP.get(str(raw).strip().upper(), None)


def norm_disease(row):
    """Return (disease_group, provenance) for one sample."""
    gse = row["dataset_id"]
    raw = str(row["disease_group_raw"]).strip()
    desc = str(row["sample_description"]).strip()

    # -- recovered from sample_description ---------------------------------
    if gse == "GSE162694" and desc:
        m = GSE162694_SUFFIX.search(desc)
        if m:
            # "_N" is normal liver histology, which is a stated finding.
            # "_F0".."_F4" is a FIBROSIS STAGE, not a diagnosis, so the
            # most it supports is NAFLD -- the same label GSE135251
            # carries for patients whose NAFL/NASH subtype is unstated.
            # See the module docstring for why NASH was wrong here.
            return ("control" if m.group(1) == "N" else "NAFLD",
                    "recovered_from_description")

    # GSE193066 intentionally omitted here -- see the rejected-recovery note
    # in the module docstring.

    # -- derived from the Kleiner histology panel ---------------------------
    if gse == "GSE130970":
        h = row.get("_hist") or {}
        steat = h.get("steatosis grade")
        ball = h.get("cytological ballooning grade")
        if steat is not None and ball is not None:
            if steat == 0:
                return "control", "derived_from_histology"
            return ("NASH" if ball >= 1 else "NAFL"), "derived_from_histology"

    # -- stated outright ----------------------------------------------------
    key = raw.upper()
    if key in DISEASE_MAP:
        return DISEASE_MAP[key], "stated"
    if key in SEVERITY_BAND:
        return SEVERITY_BAND[key], "severity_band_to_spectrum"

    return None, "unavailable"


def main():
    os.makedirs(GRAPH, exist_ok=True)
    meta = pd.read_csv(os.path.join(PROC, "samples_metadata.csv"),
                       dtype=str).fillna("")

    # GSE162694 stages a subset only in raw_characteristics; prefer the column
    # already parsed, and fall back to the JSON blob when it is blank.
    def fibrosis_of(row):
        s = norm_fibrosis(row["fibrosis_stage_raw"])
        if s is not None:
            return s
        blob = row.get("raw_characteristics", "")
        if blob.startswith("{"):
            try:
                return norm_fibrosis(json.loads(blob).get("fibrosis stage", ""))
            except (ValueError, AttributeError):
                return None
        return None

    meta["fibrosis_stage"] = meta.apply(fibrosis_of, axis=1)

    # Parse the histology panel out of raw_characteristics once, so
    # norm_disease can read integer grades rather than re-parsing JSON.
    def hist_of(blob):
        if not blob.startswith("{"):
            return {}
        try:
            d = json.loads(blob)
        except ValueError:
            return {}
        out = {}
        for k in ("steatosis grade", "cytological ballooning grade",
                  "lobular inflammation grade"):
            v = str(d.get(k, "")).strip()
            if v.isdigit():
                out[k] = int(v)
        return out

    meta["_hist"] = meta["raw_characteristics"].apply(hist_of)
    derived = meta.apply(norm_disease, axis=1, result_type="expand")

    # -- patient identity ---------------------------------------------------
    # Only GSE193066 re-biopsies; everywhere else one sample is one person,
    # so the sample's own accession is the patient key.
    def biopsy_no(blob):
        if blob.startswith("{"):
            try:
                v = str(json.loads(blob).get("biopsy", "")).strip().lower()
            except ValueError:
                return 1
            if v.startswith("2"):
                return 2
        return 1

    meta["biopsy_number"] = meta["raw_characteristics"].apply(biopsy_no)
    pid = meta["sample_title"].str.extract(r"^(HUnafld\d+)")[0]
    meta["patient_id"] = pid.where(meta["dataset_id"] == "GSE193066",
                                   meta["sample_id"]).fillna(meta["sample_id"])
    meta["disease_group"] = derived[0]
    meta["disease_provenance"] = derived[1]

    out = meta[["sample_id", "dataset_id", "patient_id", "biopsy_number",
                "fibrosis_stage", "disease_group", "disease_provenance",
                "fibrosis_stage_raw", "disease_group_raw"]].copy()
    out["fibrosis_stage"] = out["fibrosis_stage"].apply(
        lambda v: "" if pd.isna(v) else str(int(v)))
    out["disease_group"] = out["disease_group"].fillna("")

    path = os.path.join(GRAPH, "nodes_sample_clinical.csv")
    out.to_csv(path, index=False)

    # ---- audit ------------------------------------------------------------
    print("=== FIBROSIS: raw value -> harmonised stage ===")
    aud = (meta.groupby([meta["fibrosis_stage_raw"].replace("", "(blank)"),
                         meta["fibrosis_stage"].apply(
                             lambda v: "(none)" if pd.isna(v) else int(v))])
           .size().reset_index(name="n"))
    aud.columns = ["raw", "harmonised", "n"]
    print(aud.to_string(index=False))

    staged = meta["fibrosis_stage"].notna().sum()
    print(f"\nstaged: {staged:,} of {len(meta):,} samples")
    print("cirrhosis (stage 4): "
          f"{int((meta['fibrosis_stage'] == 4).sum())}  "
          f"[was 29 with the naive raw=='4' query]")

    print("\n=== DISEASE: harmonised group by provenance ===")
    ct = pd.crosstab(meta["disease_group"].fillna("(none)"),
                     meta["disease_provenance"])
    print(ct.to_string())

    print("\n=== COVERAGE BY DATASET ===")
    cov = meta.groupby("dataset_id").agg(
        samples=("sample_id", "size"),
        staged=("fibrosis_stage", lambda s: int(s.notna().sum())),
        grouped=("disease_group", lambda s: int(s.notna().sum())),
    ).reset_index()
    print(cov.to_string(index=False))

    print("\n=== PATIENT IDENTITY ===")
    pat = meta.groupby("dataset_id").agg(
        samples=("sample_id", "size"),
        patients=("patient_id", "nunique")).reset_index()
    pat["repeated"] = pat["samples"] - pat["patients"]
    print(pat.to_string(index=False))
    print(f"\ntotal: {len(meta):,} samples from "
          f"{meta['patient_id'].nunique():,} patients")

    print(f"\nwrote {path}  ({len(out):,} rows)")


if __name__ == "__main__":
    main()
