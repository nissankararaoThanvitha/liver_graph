"""
paper2_integrate_recovered_evidence.py
--------------------------------------
Fold the recovered OptimusKG evidence and chemistry into Tasks 2, 4 and 7.

WHAT THIS FIXES
Three things the plan asked for and the tasks could not supply, because
build_optimuskg_layer.py read them and kept only `name` and `relation`:

  Task 2  Evidence/Source and Database ID      said "not available per edge"
  Task 7  Evidence source and evidence level   said "not recorded"
  Task 4  filter on molecule type and phase    impossible; name heuristic only

All three are now answerable from OptimusKG's own source files, with ChEMBL
filling the structure gap OptimusKG leaves.

RUN ORDER
This runs AFTER the task scripts, and rewrites their outputs in place. Re-running
a task script drops the recovered columns, so re-run this afterwards. Paper 1
documents the same pattern for its own multi-pass steps.

    paper2_task2_drug_gene_edges.py
    paper2_task4_drug_coverage.py
    paper2_task7_action_direction.py
    paper2_integrate_recovered_evidence.py     <- this

WHAT IT DOES NOT DO
It does not re-rank anything. Tasks 3, 5, 6 and 8 are untouched, and the
candidate list is unchanged: this adds provenance and chemistry columns, not
new relationships. Any change to rankings would need its own pass and its own
verification.

Usage:
    uv run --with pandas python scripts/paper2_integrate_recovered_evidence.py
"""

import os

import pandas as pd

REC = "data/optimuskg_recovered"
EVIDENCE = f"{REC}/drug_gene_evidence.csv"
METADATA = f"{REC}/drug_metadata.csv"
CHEMBL = f"{REC}/chembl_gap_fill.csv"

T2 = "Paper2_Results/Task2/task2_drug_gene_edges.csv"
T4 = "Paper2_Results/Task4/task4_drug_coverage.csv"
T7 = "Paper2_Results/Task7/task7_action_direction_evidence.csv"

# Team 1's instruction was to filter on molecule type and clinical phase. Those
# fields are now available and they DO NOT WORK for this: all 70 name-flagged
# entries are "Small molecule", and ZINC ACETATE and ZINC CHLORIDE are
# max_phase 4.0 and is_approved True -- they genuinely are approved small
# molecules. The classification cannot separate a mineral salt from a drug
# because, as classified, there is nothing to separate.
#
# What does discriminate, for the inorganics at least, is chemistry: a molecule
# with no carbon in its formula is not an organic therapeutic. That rule is
# certain where it fires and catches ZnCl2, MgSO4, Na2SO4, AlCl3, CaCl2 and NO.
# It cannot catch the organic nutrients -- ATP, FAD, glutamic acid all contain
# carbon -- so the name heuristic stays as the broader, cruder net beside it.
#
# Both flags are reported. Neither replaces the other.
NON_THERAPEUTIC_TYPES = {"Unknown", "Inorganic", "Element"}


def load_drug_metadata():
    """OptimusKG drug properties, with ChEMBL filling what OptimusKG lacks."""
    m = pd.read_csv(METADATA, low_memory=False)
    m = m[["Drug_ID", "name", "type", "maximum_clinical_trial_phase",
           "is_approved", "has_been_withdrawn", "canonical_smiles",
           "inchi_key", "cd_formula", "cd_mol_weight"]]

    if os.path.exists(CHEMBL):
        c = pd.read_csv(CHEMBL, low_memory=False)
        m = m.merge(c, on="Drug_ID", how="left")
        # OptimusKG first, ChEMBL only where OptimusKG is silent
        m["molecule_type"] = m.type.fillna(m.chembl_molecule_type)
        m["max_phase"] = m.maximum_clinical_trial_phase.fillna(m.chembl_max_phase)
        m["smiles"] = m.canonical_smiles.fillna(m.chembl_canonical_smiles)
        m["smiles_source"] = m.canonical_smiles.notna().map(
            {True: "OptimusKG", False: None})
        m.loc[m.smiles_source.isna() & m.chembl_canonical_smiles.notna(),
              "smiles_source"] = "ChEMBL"
        m["drug_name"] = m.name.where(m.name != m.Drug_ID).fillna(
            m.chembl_pref_name)
    else:
        print("   (no ChEMBL gap-fill file; using OptimusKG alone)")
        m["molecule_type"] = m.type
        m["max_phase"] = m.maximum_clinical_trial_phase
        m["smiles"] = m.canonical_smiles
        m["smiles_source"] = m.canonical_smiles.notna().map(
            {True: "OptimusKG", False: None})
        m["drug_name"] = m.name.where(m.name != m.Drug_ID)

    m["has_smiles"] = m.smiles.notna()
    m["named"] = m.drug_name.notna()
    return m


def main():
    ev = pd.read_csv(EVIDENCE, low_memory=False)
    md = load_drug_metadata()
    print(f"recovered evidence edges : {len(ev):,}")
    print(f"recovered drug records   : {len(md):,}")
    print(f"   with SMILES           : {int(md.has_smiles.sum()):,}"
          f"  ({md.smiles_source.value_counts().to_dict()})")
    print(f"   with molecule type    : {int(md.molecule_type.notna().sum()):,}")
    print(f"   with clinical phase   : {int(md.max_phase.notna().sum()):,}")
    print(f"   with a real name      : {int(md.named.sum()):,}")

    ev_cols = ["Drug_ID", "Gene_ID", "sources_direct", "sources_indirect",
               "relation_assertions", "relation_conflict", "evidence_level",
               "source_urls", "mechanisms_of_action", "n_sources"]
    ev_small = ev[ev_cols]

    # ---- Task 2 ------------------------------------------------------------
    t2 = pd.read_csv(T2, low_memory=False)
    before = t2.Evidence_Source.iloc[0] if "Evidence_Source" in t2 else None
    t2 = t2.drop(columns=[c for c in ev_cols if c in t2.columns
                          and c not in ("Drug_ID", "Gene_ID")], errors="ignore")
    t2 = t2.merge(ev_small, on=["Drug_ID", "Gene_ID"], how="left")
    matched = t2.evidence_level.notna().sum()
    t2["Evidence_Source"] = (
        "OptimusKG: " + t2.sources_direct.fillna("unattributed")
        + t2.sources_indirect.fillna("").radd(" via ").where(
            t2.sources_indirect.notna(), ""))
    t2["Evidence_Level"] = t2.evidence_level.fillna("not matched to source")
    t2.to_csv(T2, index=False)
    print(f"\nTask 2: {matched:,} of {len(t2):,} edges matched to source evidence")
    print(f"   Evidence_Source was: {str(before)[:60]!r}")
    print(f"   now e.g.           : {t2.Evidence_Source.iloc[0][:60]!r}")

    # ---- Task 7 ------------------------------------------------------------
    t7 = pd.read_csv(T7, low_memory=False)
    t7 = t7.drop(columns=[c for c in ev_cols if c in t7.columns
                          and c not in ("Drug_ID", "Gene_ID")], errors="ignore")
    t7 = t7.merge(ev_small, on=["Drug_ID", "Gene_ID"], how="left")
    t7["Evidence_Source"] = ("OptimusKG: "
                             + t7.sources_direct.fillna("unattributed"))
    t7["Evidence_Level"] = t7.evidence_level.fillna("not matched to source")
    t7.to_csv(T7, index=False)
    print(f"Task 7: {int(t7.evidence_level.notna().sum()):,} of {len(t7):,} "
          "relationships now carry a real evidence level")
    print(t7.Evidence_Level.value_counts().to_string())

    # ---- Task 4 ------------------------------------------------------------
    t4 = pd.read_csv(T4, low_memory=False)
    keep = ["Drug_ID", "drug_name", "molecule_type", "max_phase", "is_approved",
            "has_been_withdrawn", "smiles", "smiles_source", "has_smiles",
            "inchi_key", "cd_formula", "cd_mol_weight"]
    t4 = t4.drop(columns=[c for c in keep if c in t4.columns
                          and c != "Drug_ID"], errors="ignore")
    t4 = t4.merge(md[keep], on="Drug_ID", how="left")

    # Team 1 asked to filter on molecule type and clinical phase. Both fields
    # are now available and NEITHER WORKS: all 70 name-flagged entries are
    # "Small molecule", and ZINC ACETATE and ZINC CHLORIDE carry max_phase 4.0
    # with is_approved True. They genuinely are approved small molecules, so
    # the classification has nothing to separate.
    #
    # Chemistry does discriminate, for the inorganics: a formula with no carbon
    # is not an organic therapeutic. Certain where it fires, and it catches
    # ZnCl2, MgSO4, Na2SO4, AlCl3, CaCl2 and NO. It cannot reach the organic
    # nutrients -- ATP, FAD and glutamic acid all contain carbon -- so the name
    # heuristic stays beside it as the broader, cruder net. Neither replaces
    # the other, and both are reported.
    t4["flag_molecule_type"] = t4.molecule_type.isin(NON_THERAPEUTIC_TYPES)
    t4["flag_inorganic"] = (t4.cd_formula.notna()
                            & ~t4.cd_formula.fillna("").str.contains(
                                r"C(?![a-z])", regex=True))
    t4["likely_non_therapeutic"] = t4.likely_non_therapeutic | t4.flag_inorganic
    t4.to_csv(T4, index=False)

    print(f"\nTask 4: molecule type known for "
          f"{int(t4.molecule_type.notna().sum()):,} of {len(t4):,} drugs, "
          f"formula for {int(t4.cd_formula.notna().sum()):,}")
    print("   molecule_type does NOT separate salts from drugs -- the "
          "name-flagged entries are all:")
    print("      " + t4[t4.flag_name].molecule_type.value_counts().to_string())
    print(f"   flag_name (heuristic)     {int(t4.flag_name.sum()):>5,}")
    print(f"   flag_inorganic (formula)  {int(t4.flag_inorganic.sum()):>5,}"
          f"   newly caught: {int((t4.flag_inorganic & ~t4.flag_name).sum()):,}")
    print(f"   combined                  {int(t4.likely_non_therapeutic.sum()):>5,}")
    print(f"   SMILES now available      {int(t4.has_smiles.fillna(False).sum()):>5,}")


if __name__ == "__main__":
    main()
