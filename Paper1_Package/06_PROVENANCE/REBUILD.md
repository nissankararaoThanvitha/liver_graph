# Rebuild current outputs

Run source scripts from the repository root; packaged copies retain relative-path assumptions. Keep outputs paired and archive a current run before replacing it. The correction audit records the actual verified run, inputs, timings and environment.

## Inputs and limits

The active checkout has clinical/mapping metadata, current derived tables and a14,794-gene expression analysis core recovered from Neo4j. Original raw downloads,HGNC/OptimusKG reference assets and the complete expression-load export remain unavailable locally. Recover original inputs according to DATA_SOURCES before primary reprocessing; the metadata acquisition chain is not fully scripted in this checkout.

Use requirements.txt for Paper1. Optional failed link-prediction work has a separate requirements file and is not needed.

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
python build_progression_edges.py --progression data/progression_full --knowledge data/graph_okg --out data/graph_full
python scripts/make_fig1.py
python build_paper1_package.py
```

The historical source name00_all_4692_progression_genes.py remains for caller compatibility; its output is now00_all_progression_genes.csv and contains5,904 genes. Old first/average discovery options remain only for explicit historical comparisons. Neither top25 nor top12 selection rules changed.

## Loading and verification

The live graph already contains corrected progression links. Only restore/reload them from verified current CSVs using a saved backup. MERGE alone does not remove obsolete selected edges; the correction used atomic type-limited replacement after checking endpoints. The full expression loader uses CREATE and expects all53,993 union-gene measurements; do not execute it on the core-only recovery.

Mechanism CSVs and current selected memberships match the live graph at final verification. Source-node constraints and imported annotations are preserved. The archive holds historical outputs and is excluded from normal analysis paths.
