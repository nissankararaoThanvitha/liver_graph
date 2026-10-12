"""
paper2_task1_master_table.py
----------------------------
Paper 2, Task 1: build the master progression-gene table.

WHAT THE PLAN ASKS FOR
"Start with all progression-associated genes. Create one master file
containing, wherever available: Gene; fibrosis_rho; fibrosis_q/FDR;
inflammation_rho; inflammation_q/FDR; progression class (fibrosis-only,
inflammation-only, both); F0; F1; F2; F3; F4."

"Do not remove genes simply because they are not already known drug targets."
Nothing is filtered here. Every progression gene is carried through.

THE GENE COUNT CHANGED SINCE THE PLAN WAS WRITTEN
The plan says 4,692 genes. That number predates the biopsy-pairing correction
of 9-10 October 2026 (BIOPSY_CORRECTION.md), after which repeat biopsies are
averaged only when the fibrosis stage matches and biopsy 1 is retained
otherwise. The corrected, current set is 6,222 genes:

    fibrosis-associated      3,845
    disease-associated       4,199
    shared (both ladders)    1,822
    union                    6,222

The plan's intent is "all of them", so the current 6,222 are used. The counts
are asserted below: if Paper 1 is ever regenerated and these move, this script
fails loudly rather than writing a table that silently disagrees with the graph.

WHY THE MISSING VALUES ARE NOT GAPS
A fibrosis-only gene has no inflammation rho, and an inflammation-only gene has
no fibrosis rho -- that is what those class labels mean. 2,377 blank fibrosis
columns and 2,023 blank inflammation columns are therefore expected and
correct. They are NOT measurement failures and must not be imputed.

A WARNING THIS TABLE CARRIES FORWARD TO TASK 6
Paper 1's trajectory, transition, pathway and tier work covers only the 3,845
fibrosis-associated genes. The 2,377 inflammation-only genes have none of it.
Any composite TargetScore with a trajectory (T) or pathway (B) component will
therefore rank those 2,377 last for MISSING DATA, not for biology -- while the
plan simultaneously requires the three classes stay distinct. The rule for
handling that must be decided before Task 6 computes anything: normalise within
class, or score the classes separately. `in_fibrosis_starting_set` is carried
on every row so the affected genes are always identifiable.

Usage:
    python scripts/paper2_task1_master_table.py
"""

import os

import pandas as pd

SRC = "Paper1_HighConfidence/00_all_progression_genes.csv"
OUT_DIR = "Paper2_Results/Task1"

# From CLAUDE.md / final_combined_2026-10-10/FINAL_SELECTION.md, and verified
# against the live Neo4j graph on 12 October 2026.
EXPECTED = {"fibrosis-only": 2023, "inflammation-only": 2377, "both": 1822}
EXPECTED_TOTAL = 6222
EXPECTED_FIBROSIS_SET = 3845      # fibrosis-only + both
EXPECTED_DISEASE_SET = 4199       # inflammation-only + both

CLASS_MAP = {
    "fibrosis_only": "fibrosis-only",
    "inflammation_only": "inflammation-only",
    "both": "both",
}

COLUMNS = [
    "Gene", "Ensembl_ID", "progression_class",
    "fibrosis_rho", "fibrosis_q_FDR", "fibrosis_direction", "fibrosis_n_studies",
    "inflammation_rho", "inflammation_q_FDR", "inflammation_direction",
    "inflammation_n_studies",
    "F0", "F1", "F2", "F3", "F4",
    "in_fibrosis_starting_set",
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    src = pd.read_csv(SRC)

    out = pd.DataFrame({
        "Gene": src["symbol"],
        "Ensembl_ID": src["ensembl_id"],
        "progression_class": src["ladder"].map(CLASS_MAP),
        "fibrosis_rho": src["fibrosis_rho"],
        "fibrosis_q_FDR": src["fibrosis_q"],
        "fibrosis_direction": src["fibrosis_direction"],
        "fibrosis_n_studies": src["fibrosis_n_studies"],
        "inflammation_rho": src["inflammation_rho"],
        "inflammation_q_FDR": src["inflammation_q"],
        "inflammation_direction": src["inflammation_direction"],
        "inflammation_n_studies": src["inflammation_n_studies"],
        "F0": src["F0"], "F1": src["F1"], "F2": src["F2"],
        "F3": src["F3"], "F4": src["F4"],
        "in_fibrosis_starting_set": src["in_fibrosis_starting_set"],
    })[COLUMNS]

    # ---- checks: fail rather than write a table that disagrees with Paper 1 --
    assert out["progression_class"].notna().all(), "unmapped ladder value"
    assert len(out) == EXPECTED_TOTAL, f"expected {EXPECTED_TOTAL}, got {len(out)}"
    assert out["Ensembl_ID"].is_unique, "duplicate Ensembl IDs"
    counts = out["progression_class"].value_counts().to_dict()
    assert counts == EXPECTED, f"class counts moved: {counts} != {EXPECTED}"

    fib_set = counts["fibrosis-only"] + counts["both"]
    dis_set = counts["inflammation-only"] + counts["both"]
    assert fib_set == EXPECTED_FIBROSIS_SET, f"fibrosis set {fib_set}"
    assert dis_set == EXPECTED_DISEASE_SET, f"disease set {dis_set}"

    # Structural missingness: exactly the rows the class says should be blank.
    assert out.loc[out.progression_class == "inflammation-only",
                   "fibrosis_rho"].isna().all()
    assert out.loc[out.progression_class == "fibrosis-only",
                   "inflammation_rho"].isna().all()
    assert out.loc[out.progression_class == "both",
                   ["fibrosis_rho", "inflammation_rho"]].notna().all().all()
    assert out[["F0", "F1", "F2", "F3", "F4"]].notna().all().all(), \
        "F0-F4 must be complete for every gene"

    out.to_csv(f"{OUT_DIR}/Paper2_progression_genes.csv", index=False)

    # ---- the short summary the plan asks for ------------------------------
    rows = []
    for cls in ["fibrosis-only", "inflammation-only", "both"]:
        sub = out[out.progression_class == cls]
        rows.append({
            "progression_class": cls,
            "genes": len(sub),
            "percent_of_union": round(100 * len(sub) / len(out), 1),
            # The direction of the ladder the gene belongs to. For shared genes
            # the two ladders could in principle disagree, so both are counted
            # and any disagreement is reported separately below.
            "increasing": int((sub.fibrosis_direction.eq("increasing")
                               | sub.inflammation_direction.eq("increasing")).sum()),
            "decreasing": int((sub.fibrosis_direction.eq("decreasing")
                               | sub.inflammation_direction.eq("decreasing")).sum()),
            "has_trajectory_tier_evidence": cls != "inflammation-only",
        })
    rows.append({
        "progression_class": "UNION (all)",
        "genes": len(out), "percent_of_union": 100.0,
        "increasing": "", "decreasing": "",
        "has_trajectory_tier_evidence": "3,845 of 6,222",
    })
    summary = pd.DataFrame(rows)
    summary.to_csv(f"{OUT_DIR}/task1_class_summary.csv", index=False)

    print(f"wrote {OUT_DIR}/Paper2_progression_genes.csv  ({len(out):,} genes)")
    print(f"wrote {OUT_DIR}/task1_class_summary.csv\n")
    print(summary.to_string(index=False))
    print(f"\nfibrosis-associated set (fibrosis-only + both): {fib_set:,}")
    print(f"disease-associated set (inflammation-only + both): {dis_set:,}")

    # Shared genes whose two ladders point opposite ways. Paper 1 Task 1 found
    # exactly one of these on the pre-correction set (GPD1); any such gene is
    # worth naming rather than averaging away.
    both = out[out.progression_class == "both"]
    disc = both[both.fibrosis_direction != both.inflammation_direction]
    print(f"\nshared genes with DISCORDANT directions: {len(disc)}")
    if len(disc):
        print(disc[["Gene", "fibrosis_direction", "inflammation_direction",
                    "fibrosis_rho", "inflammation_rho"]].to_string(index=False))
        disc.to_csv(f"{OUT_DIR}/task1_discordant_shared_genes.csv", index=False)


if __name__ == "__main__":
    main()
