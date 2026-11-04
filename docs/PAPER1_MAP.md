# Where each part of Paper 1 lives in this repository

Paper: *Stage-Resolved Transcriptomic Analysis Reveals Distinct Molecular Programs Associated with Liver Fibrosis Severity* (Thanvitha, Nikitha, Dinesh, Maity, Dey). Run every script from the repository root. The order of the full pipeline is in [provenance/REBUILD.md](provenance/REBUILD.md).

## Methods

| Paper section | Code | Output / record |
|---|---|---|
| Study design and data sources (Table 2) | — | [provenance/DATA_SOURCES.md](provenance/DATA_SOURCES.md) (accessions and exact files); `data/processed/samples_metadata.csv` |
| Clinical annotation; five ambiguous GSE130970 samples | `normalize_clinical.py` | `data/graph/nodes_sample_clinical.csv`; `label_audit_GSE130970_2026-10-10/` |
| Repeat-biopsy policy | `biopsy_policy.py`, `tests/test_biopsy_policy.py` | applied by every analysis script |
| Gene harmonisation and expression preprocessing | `parse_expression.py`, `map_gene_ids.py`, `build_crosswalk.py`, `check_mapping.py`, `build_graph_all.py` | `data/processed/` (gene ID map, sample crosswalk, unmapped genes); GSE193066 units: `unit_audit_GSE193066_2026-10-10/` |
| Cross-study association analysis | `find_progression_genes.py` | `data/progression_full/progression_fibrosis.csv`, `progression_disease.csv` |
| Patient-level stage and group summaries | `export_for_mentor.py` | `data/for_mentor/` |
| Fibrosis-stage profiles and clustering; choice of k, stability, membership bootstraps | `paper1_task2_trajectories.py` | `Paper1_Results/Task2/`; study-adjusted reclustering (ARI 0.901) in `final_combined_2026-10-10/logs/clustering.log` |
| Nesting of the five clusters in the k = 3 solution (91.9%; C1 split 311 / 546) | `scripts/cluster_nesting_k3.py` | `Paper1_Results/Task2/task2_nesting_k3.csv`, `task2_nesting_k3_summary.json` |
| Adjacent-stage comparisons | `paper1_task3_transitions.py` | `Paper1_Results/Task3/` |
| Matched refits (30 patients per stage) | `scripts/powermatched_transitions.py` | `Paper1_HighConfidence/05_powermatched_per_gene.csv` |
| Functional enrichment (MSigDB 2024.1) | `paper1_task4_enrichment.py` | `Paper1_Results/Task4/` |
| Gene prioritisation (9-point score, tiers, shortlist) | `scripts/00_all_4692_progression_genes.py`, `scripts/high_confidence_genes.py` | `Paper1_HighConfidence/01_master_table.csv`, `11_final_all_3845_genes.csv`, `11_final_tier1_genes.csv`, `11_FINAL_shortlist_23_genes.csv` |
| LOSO | `scripts/loso_validation.py` | `Paper1_HighConfidence/10_loso_*.csv` |
| Sensitivity: four label/normalisation configurations | — (runs recorded) | `final_combined_2026-10-10/SENSITIVITY_REPORT.md`, `candidate_stability.csv` |
| Sensitivity: thresholds, score components, shortlist rule | `scripts/high_confidence_genes.py` | `Paper1_HighConfidence/03_rho_sensitivity.csv`, `04_delta_sensitivity.csv`, `08_tier_sensitivity.csv`, `08_leave_one_score_out.csv`, `09b_option_*.csv` |
| Knowledge-graph construction | `build_optimuskg_layer.py`, `create_kg_constraints.cypher`, `load_knowledge_layer.cypher`, `reload_expression.cypher`, `build_progression_edges.py` | `final_combined_2026-10-10/graph_verification.json` (8,044 progression links match the exports) |
| Graph additions (ChEMBL, DGIdb, GtoPdb, Open Targets; KEGG/Hallmark; pathway–NAFLD; ChEMBL indications) | `scripts/write_new_links_to_graph.py`, `write_external_directions_to_graph.py`, `add_msigdb_pathways.py`, `build_pathway_nafld_links.py`, `write_added_drug_indications_to_graph.py` | `data/graph_drug_layer/`, `data/graph_msigdb/`, `data/graph_pathway_disease/` |
| Graph composition (126,999 nodes; 35,160,254 relationships; 15 types) | `scripts/verify_extended_graph_counts.py` | `docs/provenance/extended_graph_verification.json` (live check) |
| Knowledge-graph annotation analysis (3,980 annotations; 42 genes, 12 annotations, 154 links) | `scripts/kg_subgraph.py`, `scripts/verify_against_neo4j.py` | `Paper1_HighConfidence/12_KG_supplementary.xlsx`, `12_mechanistic_subgraph.png` |
| Software versions | — | `requirements.txt` |
| Reference-file versions and checksums (HGNC, OptimusKG, MSigDB) | — | `docs/provenance/SOURCE_CHECKSUMS.txt` |

## Results

| Paper item | File |
|---|---|
| Fig. 2a–b, gene groups and shared-gene agreement | `Paper1_Results/Task1/` (`task1_summary.csv`, `task1_venn.png`, `task1_shared_rho_scatter.png`) |
| Fig. 3, Table 3, Additional file 1 Table S1 and Fig. S1 | `Paper1_Results/Task2/` (`task2_gene_clusters.csv`, `task2_cluster_sizes.csv`, `task2_choosing_k.csv`, `task2_robustness*.csv`, `task2_bootstrap_shape_stability.csv`) |
| Additional file 1 Fig. S1c, nesting in k = 3 | `Paper1_Results/Task2/task2_nesting_k3.csv` |
| Fig. 3d, cluster vs largest study-adjusted step | `Paper1_Results/Task3/task3_cluster_by_transition.csv` |
| Fig. 4, adjacent-stage counts and effect sizes | `Paper1_Results/Task3/`; matched refits in `Paper1_HighConfidence/05_powermatched_per_gene.csv` |
| Fig. 5a, enrichment | `Paper1_Results/Task4/task4_all_significant.csv` (per-group tables in `enrichment_tables/`) |
| Fig. 5b and Fig. S2, graph annotations and subgraph | `Paper1_HighConfidence/12_KG_supplementary.xlsx`, `12_mechanistic_subgraph.png` |
| Table 4, marker genes | `Paper1_HighConfidence/11_final_all_3845_genes.csv` |
| Fig. 6, Table 5, the 23-gene shortlist | `Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv`, `shortlist_with_membership_confidence.csv` |
| Tiers (447 / 1,403 / 1,995) | `Paper1_HighConfidence/11_final_all_3845_genes.csv` (`Tier` column) |
| LOSO retention (442 of 447) | `Paper1_HighConfidence/10_loso_summary.csv` |
| 16 shortlisted genes stable across configurations | `final_combined_2026-10-10/candidate_stability.csv` |
| 286 Tier 1 / 21 shortlisted without the fibrosis-only component | `final_combined_2026-10-10/SENSITIVITY_REPORT.md` |
| Whole graph (graph exports) | GitHub release `graph-export-2026-11-03`, without KEGG (see the README) |

## Not in this repository

- **The final paper figures** (Figs. 1–6, S1–S2) were laid out in the manuscript project. The PNG figures in `Paper1_Results/` are the analysis figures they were built from.
- **Raw downloads** (GEO matrices, HGNC, OptimusKG parquet, MSigDB, CTD) are not committed; [provenance/DATA_SOURCES.md](provenance/DATA_SOURCES.md) and `.gitignore` say where each comes from.
- **The full expression layer** (32,471,042 measurements) is in the graph export release, not in git.
- **The Paper 2 drug-repurposing analysis** is in its own repository: https://github.com/knarendrakumar187/Drug_Repurposing.
