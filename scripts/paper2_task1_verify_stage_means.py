"""
paper2_task1_verify_stage_means.py
----------------------------------
Verify the F0-F4 columns of the Task 1 master table against the graph.

WHY THIS EXISTS
The first verification script compared rho, q, n_studies, direction and symbol
and reported "reproduces the live graph exactly". That was true of the columns
it checked and silently untrue of the ones it did not: F0-F4 were never
compared. Gene nodes do not carry stage means, so they have to be recomputed
from EXPRESSES, which the first script did not do.

THE BIOPSY POLICY HAS TO BE REPRODUCED, NOT ASSUMED
CLAUDE.md: "Repeat biopsies are averaged only if fibrosis stage matches;
otherwise biopsy 1 is retained before any stage filtering." Collapsing patients
any other way gives different means, so the comparison would fail for a reason
that has nothing to do with the table being wrong.

  same stage on every biopsy  -> average the biopsies
  stages differ               -> keep biopsy_number 1, discard the rest

Then the stage mean is the mean of value_z over the surviving patients at that
stage.

A SAMPLE, NOT EVERY GENE
Recomputing all 3,845 genes means pulling millions of EXPRESSES edges over
Bolt. A stratified sample across the rho range is enough to show the column is
right or wrong; if the policy or the column were wrong, it would be wrong
everywhere, not in a hidden corner.

Usage:
    uv run --with neo4j --with pandas --with numpy python scripts/paper2_task1_verify_stage_means.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables

MASTER = "Paper2_Results/Task1/Paper2_progression_genes.csv"
OUT_DIR = "Paper2_Results/Task1"
N_SAMPLE = 40
TOL = 5e-4           # the CSV carries four decimal places
SEED = 42


def driver():
    cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
    for scope in cfg.get("projects", {}).values():
        srv = (scope.get("mcpServers") or {}).get("neo4j")
        if srv:
            env = srv["env"]
            return (GraphDatabase.driver(env["NEO4J_URI"],
                                         auth=(env["NEO4J_USERNAME"],
                                               env["NEO4J_PASSWORD"])),
                    env.get("NEO4J_DATABASE", "neo4j"))
    raise SystemExit("no neo4j MCP config found")


def main():
    master = pd.read_csv(MASTER)
    fib = master[master.in_fibrosis_starting_set].copy()

    # Stratified across the rho range, so the sample is not all strong genes.
    rng = np.random.default_rng(SEED)
    fib["band"] = pd.qcut(fib.fibrosis_rho, 4, labels=False)
    picked = (fib.groupby("band", group_keys=False)
                 .apply(lambda g: g.sample(min(N_SAMPLE // 4, len(g)),
                                           random_state=SEED))
                 .reset_index(drop=True))
    genes = picked.Ensembl_ID.tolist()
    print(f"verifying {len(genes)} genes, stratified across the rho range\n")

    drv, db = driver()
    with drv.session(database=db) as s:
        samples = pd.DataFrame(s.run("""
            MATCH (sm:Sample) WHERE sm.fibrosis_stage IS NOT NULL
            RETURN sm.sample_id AS sample_id, sm.patient_id AS patient_id,
                   sm.biopsy_number AS biopsy_number,
                   sm.fibrosis_stage AS stage
        """).data())

        expr = pd.DataFrame(s.run("""
            MATCH (sm:Sample)-[e:EXPRESSES]->(g:Gene)
            WHERE sm.fibrosis_stage IS NOT NULL AND g.ensembl_id IN $genes
            RETURN g.ensembl_id AS Ensembl_ID, sm.sample_id AS sample_id,
                   e.value_z AS value_z
        """, genes=genes).data())
    drv.close()

    print(f"staged samples: {len(samples):,}")
    print(f"expression rows pulled: {len(expr):,}\n")

    # ---- reproduce the biopsy policy -------------------------------------
    nstage = samples.groupby("patient_id").stage.nunique()
    consistent = set(nstage[nstage == 1].index)       # average the biopsies
    keep = samples[samples.patient_id.isin(consistent)
                   | (samples.biopsy_number == 1)].copy()
    dropped = len(samples) - len(keep)
    print(f"patients: {samples.patient_id.nunique():,}")
    print(f"  same stage on all biopsies (averaged): {len(consistent):,}")
    print(f"  stages differ (biopsy 1 kept):         "
          f"{samples.patient_id.nunique() - len(consistent):,}")
    print(f"samples discarded by the policy: {dropped}\n")

    d = expr.merge(keep[["sample_id", "patient_id", "stage"]], on="sample_id")
    # one row per patient per gene per stage, then the stage mean over patients
    per_patient = (d.groupby(["Ensembl_ID", "stage", "patient_id"])
                     .value_z.mean().reset_index())
    print(f"independent staged patients used: "
          f"{per_patient.patient_id.nunique():,}  (CLAUDE.md states 610)\n")

    recomputed = (per_patient.groupby(["Ensembl_ID", "stage"])
                             .value_z.mean().unstack())
    recomputed.columns = [f"F{int(c)}" for c in recomputed.columns]

    # ---- compare ----------------------------------------------------------
    pub = picked.set_index("Ensembl_ID")[["Gene", "F0", "F1", "F2", "F3", "F4"]]
    j = pub.join(recomputed, rsuffix="_recomputed")
    rows, worst = [], 0.0
    for stage in ["F0", "F1", "F2", "F3", "F4"]:
        diff = (j[stage] - j[f"{stage}_recomputed"]).abs()
        worst = max(worst, diff.max())
        rows.append({"stage": stage, "genes": int(diff.notna().sum()),
                     "max_abs_diff": round(float(diff.max()), 6),
                     "mean_abs_diff": round(float(diff.mean()), 6),
                     "within_tolerance": bool(diff.max() <= TOL)})
    report = pd.DataFrame(rows)
    sup = SupportingTables(OUT_DIR, "task1")
    sup.add("stage_mean_verification", j.reset_index())
    sup.add("stage_mean_check", report)
    sup.write()
    print(report.to_string(index=False))

    if worst <= TOL:
        print(f"\nPASS - F0-F4 reproduce from EXPRESSES under the biopsy "
              f"policy (max diff {worst:.2e}, tolerance {TOL:.0e}).")
    else:
        print(f"\nFAIL - largest difference {worst:.2e} exceeds {TOL:.0e}. "
              "Either the column or the policy reproduction is wrong.")
        sys.exit(1)


if __name__ == "__main__":
    main()
