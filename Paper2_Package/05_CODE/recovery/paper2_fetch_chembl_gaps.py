"""
paper2_fetch_chembl_gaps.py
---------------------------
Fill the drug-metadata gaps OptimusKG leaves, from ChEMBL.

WHY ONLY THE GAPS
OptimusKG is itself built from ChEMBL and DrugBank, so most of what ChEMBL holds
is already recovered by paper2_recover_optimuskg_evidence.py. Re-fetching all
12,025 drugs would be slow and would mostly re-download what we have. This asks
ChEMBL only where OptimusKG is short.

WHAT THE SAMPLE SAID, BEFORE COMMITTING TO THE FULL RUN
60 drugs from each gap population were tested first:

  no NAME in OptimusKG     ChEMBL supplies a pref_name for  3 / 60
  no SMILES in OptimusKG   ChEMBL supplies a structure for 57 / 59

So ChEMBL closes the structure gap and does not close the naming gap -- those
drugs are genuinely unnamed rather than missing from our copy. A first test on
four drugs suggested ChEMBL added nothing at all; that test happened to pick
cisplatin and bismuth subsalicylate, inorganics with no standard SMILES, and
was misleading. Hence sixty.

NETWORK
curl does the fetching. The requests library cannot resolve ebi.ac.uk from
inside the uv subprocess while curl reaches it fine, and shelling out is less
trouble than diagnosing that.

Usage:
    uv run --with pandas python scripts/paper2_fetch_chembl_gaps.py
"""

import json
import os
import subprocess
import sys
import time

import pandas as pd

RECOVERED = "data/optimuskg_recovered/drug_metadata.csv"
OUT = "data/optimuskg_recovered/chembl_gap_fill.csv"
BATCH = 20
API = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"


def fetch(ids):
    url = f"{API}?molecule_chembl_id__in={','.join(ids)}&limit=100"
    for attempt in range(3):
        r = subprocess.run(["curl", "-s", "--max-time", "90", url],
                           capture_output=True, text=True)
        try:
            return json.loads(r.stdout).get("molecules", [])
        except json.JSONDecodeError:
            time.sleep(2 * (attempt + 1))
    print(f"   batch failed after 3 attempts: {ids[0]}...")
    return []


def main():
    m = pd.read_csv(RECOVERED)

    # drugs the graph actually holds, where OptimusKG is missing something
    need = m[(m.canonical_smiles.isna())
             | (m.type.isna())
             | (m.maximum_clinical_trial_phase.isna())
             | (m.name == m.Drug_ID)]
    ids = need.Drug_ID.dropna().unique().tolist()
    print(f"OptimusKG drug records: {len(m):,}")
    print(f"records with a gap:     {len(ids):,}")
    print(f"batches of {BATCH}:          {(len(ids) + BATCH - 1) // BATCH:,}\n")

    rows, done = [], 0
    for i in range(0, len(ids), BATCH):
        for x in fetch(ids[i:i + BATCH]):
            struct = x.get("molecule_structures") or {}
            rows.append({
                "Drug_ID": x.get("molecule_chembl_id"),
                "chembl_pref_name": x.get("pref_name"),
                "chembl_molecule_type": x.get("molecule_type"),
                "chembl_max_phase": x.get("max_phase"),
                "chembl_first_approval": x.get("first_approval"),
                "chembl_withdrawn": x.get("withdrawn_flag"),
                "chembl_oral": x.get("oral"),
                "chembl_canonical_smiles": struct.get("canonical_smiles"),
                "chembl_inchi_key": struct.get("standard_inchi_key"),
            })
        done += BATCH
        if done % 400 == 0:
            print(f"   {min(done, len(ids)):,} / {len(ids):,}")

    out = pd.DataFrame(rows).drop_duplicates(subset="Drug_ID")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"\nreturned: {len(out):,} drug records")
    for c in ["chembl_pref_name", "chembl_molecule_type", "chembl_max_phase",
              "chembl_canonical_smiles"]:
        print(f"   {c:<26} {out[c].notna().sum():>6,}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
