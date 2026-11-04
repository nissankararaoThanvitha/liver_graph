# Rebuild current outputs

Run scripts from the repository root. Keep outputs paired and archive a current run before replacing it. The correction audit records the actual verified run, inputs, timings and environment.

## Three different reproduction tasks

Reading the committed result tables needs no raw downloads or database. Importing
an existing graph uses the release described in [../graph_export/IMPORT.md](../graph_export/IMPORT.md).
Re-running the expression analyses requires the original-format analysis inputs.
A fresh clone does **not** contain those large inputs. Do not run the analysis
commands below until preparation is complete.

### Fresh clone: recover the analysis inputs from the published graph

1. Install Python 3.12 and `pip install -r requirements.txt`.
2. Download `liver_kg_graph_export_2026-11-03.zip` and `SHA256SUMS.txt` from
   https://github.com/nissankararaoThanvitha/liver_graph/releases/tag/graph-export-2026-11-03 .
   Keep them outside the repository. Verify the ZIP against its entry in the
   published checksum file before using it; the checksum file also lists other
   release assets, which must be downloaded if checking all entries together.
3. From the repository root, prepare NEW output directories:

```bash
python scripts/prepare_analysis_core.py --archive /path/to/liver_kg_graph_export_2026-11-03.zip
python scripts/prepare_analysis_core.py --archive /path/to/liver_kg_graph_export_2026-11-03.zip --annotations-only
```

The first command streams the release into `data/expression_analysis_core`:
`nodes_gene.csv` and one `edges_GSE*.csv` per study. It requires every one of the
14,794 eligible genes in every one of 1,085 samples exactly once (16,051,490
rows), preserves measured zeros, and rejects duplicates, missing pairs,
non-finite standardised values and mismatched sample metadata. The second
recovers only the original Reactome/GO annotation layer into `data/graph_okg`
for the subgraph analysis; added KEGG/Hallmark nodes are deliberately excluded.
Both commands refuse existing output directories. Use `--out` for an alternate
location. A recovery manifest is written with the expression core.

This route reproduces analyses from retained graph measurements. It does not
recreate the initial expression processing from raw reads/matrices, restore
excluded KEGG data, or constitute independent validation. Never use this core
for reloading the full expression graph.

4. Download the four original MSigDB 2024.1 GMT files into `data/genesets` as
   described in [DATA_SOURCES.md](DATA_SOURCES.md); verify their hashes against
   `SOURCE_CHECKSUMS.txt`. Restricted source files stay outside version control.
5. Run `python -m unittest discover -s tests`, then the analysis sequence below.
   These scripts write their named output folders; use an isolated clone when
   comparing a re-run against the committed results.

### Primary processing from original source matrices

The deposited GEO files, series metadata, HGNC dictionary and OptimusKG parquet
files are listed in DATA_SOURCES.md. Existing clinical/mapping metadata are
committed. After obtaining the raw inputs, the processing sequence is:

```bash
python parse_expression.py --raw-dir data/raw --out-dir data/interim_full
python map_gene_ids.py --interim-dir data/interim_full --hgnc data/raw/hgnc_complete_set.txt --out-dir data/processed
python build_crosswalk.py
python normalize_clinical.py
python build_graph_all.py --interim data/interim_full --out data/graph_full
python build_optimuskg_layer.py
```

Do not use `--drop-zeros`. Metadata acquisition for all eight studies is not
fully scripted: this sequence uses the committed `data/processed/samples_metadata.csv`.
It is not a claim of fully automated raw acquisition. Consult each script's
help before changing its inputs. The exact final-run environment is in
`final_combined_2026-10-10/runtime_requirements.txt`; required packages are in
`requirements.txt`. Source dates/hashes are in `SOURCE_CHECKSUMS.txt`.

## Existing recovered-core analysis

The scripts choose data/expression_analysis_core when available; otherwise they expect data/graph_full. The recovered subset is sufficient for eligible-gene analyses, not full graph expression loading.

```bash
python find_progression_genes.py --repeat-policy same_stage_mean --graph data/expression_analysis_core --out data/progression_full
python export_for_mentor.py
python paper1_task1_groups.py --out Paper1_Results/Task1
python paper1_task2_trajectories.py --out Paper1_Results/Task2 5
python paper1_task3_transitions.py --out Paper1_Results/Task3 --clusters Paper1_Results/Task2/task2_gene_clusters.csv
python paper1_task4_enrichment.py --out Paper1_Results/Task4 --clusters Paper1_Results/Task2/task2_gene_clusters.csv
python scripts/00_all_4692_progression_genes.py --out Paper1_HighConfidence --results Paper1_Results
python scripts/powermatched_transitions.py --out Paper1_HighConfidence --results Paper1_Results
python scripts/high_confidence_genes.py --out Paper1_HighConfidence --results Paper1_Results
python scripts/loso_validation.py --out Paper1_HighConfidence --results Paper1_Results
python scripts/high_confidence_genes.py --out Paper1_HighConfidence --results Paper1_Results
python scripts/kg_subgraph.py --out Paper1_HighConfidence --results Paper1_Results
# Optional: scripts/make_fig1.py renders a historical analysis overview,
# not the final manuscript figure, and requires full graph node CSVs.
```

The historical source name00_all_4692_progression_genes.py remains for caller compatibility; its output is now00_all_progression_genes.csv and contains6,222 genes. Old first/average discovery options remain only for explicit historical comparisons. The representative shortlist contains 23 genes (up to five per cluster); the annotation display retains 12 terms.

## Loading and verification

The sequence above re-runs analyses only. A full graph rebuild additionally
requires the complete union-gene expression CSVs and all OptimusKG node/edge
files from the primary-processing route. The four recovered annotation CSVs
are sufficient for the subgraph analysis, not a complete knowledge reload.
With the full inputs prepared, generate the progression CSV explicitly:

```bash
python build_progression_edges.py --progression data/progression_full --knowledge data/graph_okg --out data/graph_full
```

Then load the full measurement/knowledge CSVs using the documented Neo4j
import/loader procedures before applying the graph additions below. Do not
run the full expression CREATE loader against a recovered core.


The selected final approach is documented in final_combined_2026-10-10/FINAL_SELECTION.md. Check its graph_verification.json for live synchronisation. Only restore/reload them from verified current CSVs using a saved backup. MERGE alone does not remove obsolete selected edges; the correction used atomic type-limited replacement after checking endpoints. The full expression loader uses CREATE and expects all53,993 union-gene measurements; do not execute it on the core-only recovery.

Mechanism CSVs and current selected memberships match the live graph at final verification. Source-node constraints and imported annotations are preserved. The archive holds historical outputs and is excluded from normal analysis paths.

## Graph additions (drug, pathway and indication data)

These steps take the graph of 10 October 2026 (126,244 nodes; 35,132,831 relationships; 14 types) to the extended graph (126,999; 35,160,254; 15). Run them in this order from the repository root. Graph writes are opt-in. The commands below explicitly write to the selected database; they are not needed just to read result tables or import the published graph. Set NEO4J_URI, NEO4J_DATABASE and credentials for the intended instance before using the migration/verifier. The historical HTTP drug writers target database neo4j on port 7474; do not run them against a different instance without configuring/inspecting their connection code.

```bash
python scripts/write_new_links_to_graph.py --apply
# Complete the historical layer in one backed-up, verified transaction.
python scripts/unify_drug_schema.py --apply --backup /path/outside/repo/drug-schema-before.json
python scripts/write_external_directions_to_graph.py --apply
python scripts/add_msigdb_pathways.py --apply
python scripts/build_pathway_nafld_links.py --load
python scripts/write_added_drug_indications_to_graph.py --apply
python scripts/verify_extended_graph_counts.py --live
```

- Step 0.4 (new drug–gene links) and 0.5 (action directions) read the committed tables in data/graph_drug_layer. The API search scripts that made those tables are in the Paper 2 repository (https://github.com/knarendrakumar187/Drug_Repurposing).
- add_msigdb_pathways.py needs the MSigDB 2024.1 GMT files in data/genesets. It writes Hallmark rows to the committed data/graph_msigdb/*_msigdb.csv and KEGG rows to *_kegg.csv, which are not committed because KEGG data may not be redistributed (counts in data/graph_msigdb/counts.json). build_pathway_nafld_links.py reads both, so run add_msigdb_pathways.py first. build_pathway_nafld_links.py needs data/ctd/CTD_diseases_pathways.csv.gz, data/optimuskg/pathway.parquet and data/graph_okg/nodes_pathway.csv. None of these are committed (see .gitignore for sources). The Hallmark CSVs and the pathway–NAFLD CSVs these scripts wrote are committed in data/graph_msigdb and data/graph_pathway_disease.
- `unify_drug_schema.py` is read-only by default. `--apply` requires a new
  backup path. It converts each legacy relationship separately (never collapses
  duplicate evidence), retains all properties/endpoints, removes the auxiliary
  ExternalDrug label and verifies preservation before committing. It refuses
  ambiguous drug IDs. A repeated run on a unified graph makes no changes. Stop
  other writers during migration; a Neo4j relationship-type token can remain
  listed after its last relationship is removed, so check actual edge counts.
- Run `python scripts/verify_against_neo4j.py` for original annotation memberships;
  `--workbook`, `--knowledge`, `--uri` and `--database` select the inputs. This
  verifier is read-only and does not compare the old layer with expanded totals.
- Without `--live`, verify_extended_graph_counts.py rebuilds the expected counts from the committed tables and write logs. It writes docs/provenance/extended_graph_verification.json.

## Final combined inputs

Five flagged GSE130970 disease labels are unclassified (fibrosis/histology retained); normalize_clinical.py reproduces this policy. GSE193066 uses deposited linear RLE counts without CPM rescaling; build_graph_all.py preserves this transform. The active core contains the matching final value_z measurements. The raw GCT was checked in unit_audit_GSE193066_2026-10-10 (fetch_sources.py downloads it again). Final shortlist23: up to five Tier1 genes per cluster, C4 only three. Alternative sensitivity outputs are removed from active folders and retained in a local recovery archive. Retained comparison evidence and original commands are in final_combined_2026-10-10.
