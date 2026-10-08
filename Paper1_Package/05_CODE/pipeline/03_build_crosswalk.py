"""
build_crosswalk.py
------------------
Builds the bridge between the two halves of the data:

    expression file's sample_key   ->   GEO accession (GSM...)

Each dataset labels its expression columns differently, so each gets its own
small rule. The rules were derived by eye from show_keys.py output and then
verified against every title in the series matrix.

The script does NOT trust the rules blindly -- it applies each rule, then
checks the result against the sample keys actually present in the expression
files, and reports the match rate per dataset. A rule that works on the first
four samples but fails on the fifth will show up here rather than silently
producing a half-connected graph.

Usage:
    python build_crosswalk.py
"""

import glob
import os
import re

import pandas as pd

INTERIM = "data/interim"
META = "data/processed/samples_metadata.csv"
OUT = "data/processed/sample_crosswalk.csv"


# --- one rule per dataset -------------------------------------------------
# Each takes a metadata row and returns the key the expression file should use.

def rule_gsm(row):
    """Expression file already uses the GEO accession."""
    return row["sample_id"]


def rule_title(row):
    """Expression file uses the study's own sample title, unchanged."""
    return row["sample_title"]


def rule_description(row):
    """GSE126848 labels columns with the internal lab ID, which GEO stores in
    the !Sample_description field (e.g. '869') rather than the title."""
    return row["sample_description"]


def rule_last_token(row):
    """GSE162694 title is 'nash1_F0 548nash1' -- the column name is the part
    after the space."""
    t = str(row["sample_title"]).strip()
    return t.split()[-1] if t else None


def rule_prefix_s(row):
    """GSE240729 title is '7068-04-001-001', the column adds a leading 's'."""
    return "s" + str(row["sample_title"]).strip()


def rule_nafld_padded(row):
    """GSE167523 title is 'NAFLD liver 7' -> column is 'NAFLD07'.
    All 98 titles follow this pattern, verified against the series matrix."""
    m = re.search(r"(\d+)\s*$", str(row["sample_title"]))
    return f"NAFLD{int(m.group(1)):02d}" if m else None


RULES = {
    "GSE126848": rule_description,
    "GSE130970": rule_title,
    "GSE135251": rule_gsm,
    "GSE162694": rule_last_token,
    "GSE167523": rule_nafld_padded,
    "GSE193066": rule_title,
    "GSE240729": rule_prefix_s,
    "GSE269412": rule_title,
}


def actual_keys(path):
    """The sample keys really present in one expression file."""
    keys = set()
    for chunk in pd.read_csv(path, chunksize=500_000, compression="gzip",
                             usecols=["sample_key"]):
        keys.update(chunk["sample_key"].astype(str).unique().tolist())
    return keys


def main():
    meta = pd.read_csv(META, dtype=str).fillna("")
    rows, summary = [], []

    for path in sorted(glob.glob(os.path.join(INTERIM, "*_expression_long.csv.gz"))):
        gse = os.path.basename(path).split("_")[0]
        rule = RULES.get(gse)
        if rule is None:
            print(f"[SKIP] {gse}: no rule defined")
            continue

        found = actual_keys(path)
        m = meta[meta["dataset_id"] == gse]

        matched, unmatched_meta = 0, []
        for _, r in m.iterrows():
            key = rule(r)
            if key and str(key) in found:
                rows.append(dict(dataset_id=gse, sample_key=str(key),
                                 sample_id=r["sample_id"]))
                matched += 1
            else:
                unmatched_meta.append((r["sample_id"], key))

        # Keys in the expression file that no metadata row claimed
        claimed = {x["sample_key"] for x in rows if x["dataset_id"] == gse}
        orphan_keys = sorted(found - claimed)

        summary.append(dict(dataset_id=gse, n_meta=len(m), n_expr_keys=len(found),
                            n_matched=matched,
                            pct=round(100 * matched / len(m), 1) if len(m) else 0,
                            n_orphan_keys=len(orphan_keys)))
        if unmatched_meta[:3]:
            print(f"  {gse} unmatched examples: {unmatched_meta[:3]}")
        if orphan_keys[:3]:
            print(f"  {gse} orphan keys: {orphan_keys[:3]}")

    cw = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cw.to_csv(OUT, index=False)

    print("\n=== CROSSWALK SUMMARY ===")
    print(pd.DataFrame(summary).to_string(index=False))
    print(f"\nTotal linked samples: {len(cw):,} (target 1,085)")
    print(f"Written to {OUT}")


if __name__ == "__main__":
    main()