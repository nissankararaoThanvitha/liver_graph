# Current research inventory

Active version:10 October2026, after researcher selection of the combined approach. Current source of truth is Paper1_Package plus canonical root result/data paths. Historical originals are preserved only in the recovery archive. No manuscript prose or new drug prediction is produced here.

## Objectives and claim boundary

The final objective clarified by the researcher is drug repurposing to interrupt progression at different stages. Completed evidence supplies a stage-informed biomedical knowledge graph and association/trajectory/annotation/prioritisation analyses. No therapeutic efficacy, causal pathway, non-invasive stage prediction or external clinical validation is established.

Source: researcher clarification; package01_OVERVIEW/Research objective;02_METHODS;04_LIMITATIONS.

## Cohorts

The table below is raw-resource sample/patient/metadata coverage. Independent fibrosis analysis uses610 patients and demographic stage means327; raw staging covers668 biopsies. Disease axis216 patients,three varying studies. The repeat rule averages28 equal-stage pairs and discards the second biopsy in30 differing-stage pairs.

Source:02_TABLES/main/Table1_cohort.csv and additive harmonisation/nodes_sample_clinical.csv; root biopsy_policy.py; correction decision ledger.

| study | samples | patients | repeat_biopsies | fibrosis_staged | F0 | F1 | F2 | F3 | F4 | disease_labelled | disease_groups | age_recorded | sex_recorded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GSE126848 | 57 | 57 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 57 | NAFL 15; NASH 16; control 14; obese 12 | 0 | 57 |
| GSE130970 | 78 | 78 | 0 | 78 | 25 | 28 | 9 | 14 | 2 | 73 | NAFL 23; NASH 46; control 4 | 78 | 78 |
| GSE135251 | 216 | 216 | 0 | 216 | 46 | 48 | 54 | 54 | 14 | 216 | NAFLD 206; control 10 | 0 | 0 |
| GSE162694 | 143 | 143 | 0 | 143 | 66 | 30 | 27 | 8 | 12 | 143 | NAFLD 112; control 31 | 143 | 143 |
| GSE167523 | 98 | 98 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 98 | NAFL 51; NASH 47 | 98 | 98 |
| GSE193066 | 164 | 106 | 58 | 164 | 6 | 45 | 71 | 41 | 1 | 0 | none | 164 | 164 |
| GSE240729 | 67 | 67 | 0 | 67 | 9 | 17 | 25 | 10 | 6 | 0 | none | 0 | 0 |
| GSE269412 | 262 | 262 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | none | 0 | 0 |
| TOTAL | 1085 | 1027 | 58 | 668 | 152 | 168 | 186 | 127 | 35 | 587 |  | 483 | 540 |

## Methods, identifiers and integration

# Completed methodology

## 1. Collection and deposited expression parsing

Eight GEO studies and exact downloaded filenames are listed in06_PROVENANCE/DATA_SOURCES.md. Deposited matrices are parsed by matrix/GCT/tar branches; missing/non-numeric values removed, duplicate raw gene rows keep first, measured zeros retained. This is reanalysis of deposited counts/TPM, not a new alignment/quantification pipeline. Raw source downloads and the full acquisition chain are not supplied here.

## 2. Identifiers and clinical metadata

HGNC approved symbols, Entrez IDs, unambiguous previous symbols/aliases map to canonical version-stripped Ensembl IDs; non-HGNC Ensembl IDs pass through without annotation. Mapping failures are reported. _PAR_Y rows removed; distinct raw IDs collapsing to a gene are summed. The graph holds53,993 union genes;14,794 are measured in all eight studies. Gene category records the pilot categories, not complete HGNC biotypes.

Study-specific expression keys map to GSM via checked title/description/prefix rules. Clinical fibrosis labels, diagnosis provenance, patient identity and biopsy order are added beside raw fields. GSE135251/GSE162694 broad NAFLD is not treated as NASH. GSE130970 labels remain derived from steatosis/ballooning; five flagged samples are unclassified, leaving73 used on the disease axis. Original individual diagnoses were not recovered; GSE193066 has no usable disease diagnoses.

## 3. Measurement transformation

Library sums are calculated before mapping/filtering. TPM uses log2(TPM+1). GSE193066 uses log2(deposited linear DESeq2 RLE-normalised counts+1), without CPM rescaling; mapped aliases are summed before logging. Other count inputs retain log2(CPM+1). Expression is then standardised by within-study/gene mean and sample SD (ddof1); undefined SD gives0. No DESeq2/limma/edgeR or fitted batch-correction algorithm is used. Effect values are within-study SD units, not fold changes.

## 4. Shared repeat-biopsy policy

biopsy_policy.py selects repeat measurements before filtering any stage contrast. Same-stage repeats are averaged; differing stages retain biopsy1 only. There are28 same-stage and30 different-stage repeated patients. Stage means, discovery, trajectory bootstraps, stage contrasts, matched refits and LOSO use one observation per patient. Raw sample-demographics files continue to contain every original biopsy plus biopsy_number.

## 5. Progression discovery and stage summaries

Spearman within study correlates value_z with each axis; median rho summarises effects; Fisher combines p-values (clipped at10^-300); BH applies separately to retained tests on each axis. Require q<.05, all testable studies agreeing in direction, at least three testable studies. The fibrosis table tests14,794 genes; disease14,784 after testability filtering. Discovery has no minimum rho cutoff. Exported stage means average patients and rho is rounded to three decimals in downstream summary/scoring inputs.

The file diagnostic_both_q_significant.csv is a separate historical-style diagnostic: q significance on both axes plus matching median sign, without the unanimity filter. It is neither the selected shared set nor union. Define selected sets from the two complete progression tables.

## 6. Groups and trajectories

Task1 partitions selected genes into fibrosis-only, disease-only and shared, with direction. Task2 row-z-scores five patient-weighted stage means (ddof0); K-means with50 starts,seed42. Try k3–8;50 gene subsets of80% and50 patient bootstraps,10-start refits. Largest k with mean gene-subset ARI≥.95 is5 in the corrected run. Historical run selected6 under the rule and reported5 as an override; do not transfer that historical selection claim to current results.

A further100 patient bootstraps match centroids by Hungarian assignment. Membership confidence uses only own-cluster matches with r≥.5 and publishes denominators. Study-adjusted profiles use categorical stage+study OLS, then compare cluster/profile agreement.

## 7. Adjacent-stage contrasts

Fit value_z on binary higher-stage indicator plus study dummies, restricting to studies with both stages. Use one patient observation under the shared policy; no random choice between different-stage biopsies remains. OLS t test, BH across the selected fibrosis set within each contrast; substantial means q<.05 and|beta|≥.2. Power-matched refits use four studies,30 patients/stage,50 draws,seed42. Counts are within a preselected set; sampling and selection bias limit inference.

## 8. Local enrichment

MSigDB2024.1.Hs GO BP,KEGG legacy,Reactome,Hallmark; eligible background14,794 unique symbols. Intersect sets with background and retain10–500 members; group minimum5 genes. One-sided hypergeometric via gseapy; BH within group/database,q<.05. Six direction groups,five clusters,five cores at confidence≥.8. Groups below5 are untested, not tested-null.

## 9. Scores, shortlist and LOSO

P:2/1 at|rho|≥.4/.3. T:2/1 at|F4−F0|≥1/.5SD,0 if direction conflicts. X:2 if largest|beta| is substantial in full fit and reproducible with same sign/|beta|≥.2 in≥50% draws,1 for one condition. F:1 for fibrosis-only. B:2/1 for enriched membership in≥2/1 annotation databases via own group/cluster. Sum maximum9; Tier1≥7,Tier2≥5. These features share data and are not five independent validations.

The shortlist takes up to five Tier1 genes per cluster (C4 has only three, giving23 total), ranking total score then absolute rho. Alternative cluster-top-score list remains an unselected comparison. LOSO refits per-study correlations on the same biopsy rule, removes one of five staged studies and applies BH to all14,794 eligible genes before reporting Tier1. Selection is not repeated within a held-out clinical prediction design; this is internal robustness.

## 10. OptimusKG and mechanism subgraph

Gene–disease score≥.1; matched measured genes; symmetric interactions deduplicated; source drug indications/actions preserved. Eight node types/fourteen relationship types. Knowledge-loader MERGE does not remove obsolete edges automatically. Raw measurement CREATE loaders need full source exports; the core recovery is not suitable for reloading all measurements.

Pathway and BioProcess each attach directly to Gene. Test Tier1 enrichment against Ensembl background14,794 with BH over Tier1-reached mechanism nodes. Eligible mechanism size10–500,at least10 Tier1 members,q<.05. Rank byq; check Jaccard>.5 redundancy; select12. Draw genes reaching≥3 selected nodes plus shortlisted genes reaching any. No top25/top12 selection rule changed. Annotation connectivity is not causal validation.



## Current result groups

Source:02_TABLES/main/Table2_gene_groups.csv.

| group | direction | n_genes | pct_of_group | pct_of_all_6222 |
| --- | --- | --- | --- | --- |
| fibrosis_only | all | 2023 | 100.0 | 32.5 |
| fibrosis_only | positive | 1040 | 51.4 | 16.7 |
| fibrosis_only | negative | 983 | 48.6 | 15.8 |
| inflammation_only | all | 2377 | 100.0 | 38.2 |
| inflammation_only | positive | 2042 | 85.9 | 32.8 |
| inflammation_only | negative | 335 | 14.1 | 5.4 |
| shared | all | 1822 | 100.0 | 29.3 |
| shared | positive (both up) | 1408 | 77.3 | 22.6 |
| shared | negative (both down) | 384 | 21.1 | 6.2 |
| shared | discordant (fib up, inf down) | 0 | 0.0 | 0.0 |
| shared | discordant (fib down, inf up) | 30 | 1.6 | 0.5 |

## Cluster profiles and confidence

Sources:Table3 andTableS5.

| cluster | cluster_name | n_genes | pct_of_fibrosis_genes | mean_F0 | mean_F1 | mean_F2 | mean_F3 | mean_F4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Early increase (F0→F1), then continued | 857 | 22.3 | -0.295 | -0.057 | 0.067 | 0.237 | 0.515 |
| 2 | Late increase (largest at F3→F4) | 1367 | 35.6 | -0.227 | -0.142 | -0.018 | 0.266 | 0.86 |
| 3 | Early rise, then plateau | 226 | 5.9 | -0.27 | -0.012 | 0.108 | 0.213 | 0.136 |
| 4 | Mid decrease (largest at F1→F2) | 397 | 10.3 | 0.161 | 0.182 | -0.075 | -0.26 | -0.279 |
| 5 | Late decrease (largest at F3→F4) | 998 | 26.0 | 0.184 | 0.195 | -0.034 | -0.259 | -0.658 |

| cluster | cluster_name | median_shape_corr | min_shape_corr | genes_confidence>=0.8 | n_genes |
| --- | --- | --- | --- | --- | --- |
| 1 | Early increase (F0→F1), then continued | 0.977 | 0.825 | 90 | 857 |
| 2 | Late increase (largest at F3→F4) | 0.996 | -0.426 | 806 | 1367 |
| 3 | Early rise, then plateau | 0.967 | -0.62 | 74 | 226 |
| 4 | Mid decrease (largest at F1→F2) | 0.968 | 0.756 | 126 | 397 |
| 5 | Late decrease (largest at F3→F4) | 0.993 | -0.374 | 742 | 998 |

## Prioritisation sensitivity

Source:TableS14. Tiers are administrative scores, not probability of validation.

| tier1_cutoff | n_genes | shared_with_frozen | pct_of_frozen_retained | frozen_choice |
| --- | --- | --- | --- | --- |
| 6 | 988 | 447 | 100.0 | False |
| 7 | 447 | 447 | 100.0 | True |
| 8 | 123 | 123 | 27.5 | False |

## Graph schema and current counts

Eight node types:Gene,Sample,Dataset,Disease,Drug,Pathway,BioProcess,Phenotype. Patient is a property, not a node. Fourteen relation types;126,244 nodes and35,132,831 relationships at corrected-run live verification. The final graph has8,044 progression links; curated relationships and raw expression values preserved; derived GSE193066 expression and five derived disease labels updated. Sources:canonical graph CSVs and final_combined_2026-10-10/graph_verification.json.

## External source inventory

# Where every input came from

Full provenance for each external input, with the exact file taken. Nothing
in this project generated new human data; every analysis uses existing public
data, so no sample-size calculation or randomisation applies and the
available sample size is a constraint rather than a design choice.

---

## The eight expression studies

All from the NCBI Gene Expression Omnibus,
`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<accession>`.

**Two files were taken from each study:** the supplementary expression matrix
(listed below) and the **series matrix**, which carries the per-sample
clinical characteristics. Without the series matrix a sample is an anonymous
column.

| Study | Samples | Supplementary expression file taken |
|---|---|---|
| GSE126848 | 57 | `GSE126848_Gene_counts_raw.txt.gz` |
| GSE130970 | 78 | `GSE130970_all_sample_salmon_tximport_TPM_entrez_gene_ID.csv.gz` |
| GSE135251 | 216 | `GSE135251_RAW.tar` (per-sample files inside) |
| GSE162694 | 143 | `GSE162694_raw_counts.csv.gz` |
| GSE167523 | 98 | `GSE167523_Raw_gene_counts_matrix.txt.gz` |
| GSE193066 | 164 | `GSE193066_NAFLD.HUn164.gct.gz` |
| GSE240729 | 67 | `GSE240729_merged.counts.67samp.txt.gz` |
| GSE269412 | 262 | `GSE269412_DRX0FLO_rnaseq_count_mat.txt.gz` |

Total 1,085 samples from 1,027 patients. Compressed download size ~104 MB.

**Papers referenced while resolving clinical labels:** GSE193066 — PMID
35731891 (confirmed the 106-patient / 58-repeat-biopsy structure);
GSE269412 — *JCI Insight* 2025, PMID 39998893 (reports its cohort only in
aggregate, which is why that study carries no usable clinical labels).

---

## Gene identifier dictionary

**HGNC complete set** — `hgnc_complete_set.txt`, 16.2 MB, from
`https://www.genenames.org/download/archive/`.

Used by `02_map_gene_ids.py` to translate every symbol, Entrez ID and
Ensembl ID onto one canonical Ensembl gene ID with the version stripped.

---

## Knowledge graphs

**OptimusKG** — Harvard Dataverse, DOI `10.7910/DVN/IYNGEV`, 161 MB.
The source of the curated knowledge layer: diseases, drugs, pathways,
biological processes, phenotypes and the relationships between them.
Genes are identified by Ensembl ID, the same namespace this pipeline
standardises on, so the join needs no translation.

Underlying gene–disease association scores are Open Targets, carried through
OptimusKG. Links are kept at score ≥ 0.1 and the score is stored on every
edge.

---

## Gene sets for enrichment

**MSigDB v2024.1, human gene symbols**, from
`https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2024.1.Hs/`

Four collections, 5.7 MB total:

| File | Collection |
|---|---|
| `c5.go.bp.v2024.1.Hs.symbols.gmt` | GO Biological Process |
| `c2.cp.kegg_legacy.v2024.1.Hs.symbols.gmt` | KEGG legacy |
| `c2.cp.reactome.v2024.1.Hs.symbols.gmt` | Reactome |
| `h.all.v2024.1.Hs.symbols.gmt` | Hallmark |

**These are not shipped in this package.** The KEGG-derived sets may not be
redistributed. Download them from the URL above into `data/genesets/` before
re-running `task4_enrichment.py`.

A free MSigDB registration may be required. The version matters: MSigDB
2024.1 renamed some GO terms relative to earlier releases, which is itself a
documented finding in this project — see `00_START_HERE/04_LIMITATIONS.md` and the
note on name matching in `00_START_HERE/02_METHODS.md`.

---

## Software and recovered expression inputs

Historical upstream results documented Python3.13.7. Corrected analyses used Python3.12.14 with pandas2.3.3,numpy2.2.4,scipy1.16.3,scikit-learn1.7.2,matplotlib3.10.7,gseapy1.3.1. Baseline tested gene IDs/rhos/p/q and agreement counts reproduced before correction. Exact corrected environment is retained in biopsy_correction_2026-10-10/runtime_requirements.txt.

Graph at correction verification: Neo4j Enterprise2026.09.0. No raw expression or curated links were modified by the biopsy correction; only patient-derived progression links were updated with backup and verified identities/properties.

The recovered input is14,794 eligible genes across1,085 samples:16,051,490 value_z records, at data/expression_analysis_core. Every eligible sample/gene pair was verified. This is not the full32,471,042-measurement export. Do not reload all EXPRESSES edges from it. Download/recovery manifests and hashes are retained in the correction audit. MSigDB2024.1.Hs files were recovered from the documented URLs; local GMTs are excluded from version control/package redistribution.

---

## Ethics and data availability wording

No new human data were generated. All eight studies are publicly available
from GEO under their own accessions and their original consent and ethics
approvals. For the manuscript's data-availability statement: the accessions
above, plus a pointer to wherever the project repository is published.


## Every package file

Table counts exclude headers; workbook sheet rows include their headers. File presence does not prove independent validation.

| File | Inspected size/count |
|---|---|
| Paper1_Package/00_START_HERE/01_OVERVIEW.md | 3065 bytes |
| Paper1_Package/00_START_HERE/02_METHODS.md | 6672 bytes |
| Paper1_Package/00_START_HERE/03_STATISTICS.md | 5694 bytes |
| Paper1_Package/00_START_HERE/04_LIMITATIONS.md | 2657 bytes |
| Paper1_Package/00_START_HERE/05_HOW_TO_VERIFY.md | 1341 bytes |
| Paper1_Package/00_START_HERE/06_FILE_MANIFEST.csv | 35243 bytes; 277 rows |
| Paper1_Package/01_FIGURES/FIGURE_CAPTIONS.md | 7271 bytes |
| Paper1_Package/01_FIGURES/main/Figure1_study_design.png | 616077 bytes; (1780, 2254) pixels |
| Paper1_Package/01_FIGURES/main/Figure2_ladder_overlap.png | 150297 bytes; (1433, 1280) pixels |
| Paper1_Package/01_FIGURES/main/Figure3_shared_gene_agreement.png | 350473 bytes; (1643, 1694) pixels |
| Paper1_Package/01_FIGURES/main/Figure4_trajectory_shapes.png | 239998 bytes; (1877, 1407) pixels |
| Paper1_Package/01_FIGURES/main/Figure5_stage_heatmap.png | 214695 bytes; (1722, 2504) pixels |
| Paper1_Package/01_FIGURES/main/Figure6_choosing_k.png | 223679 bytes; (2970, 1191) pixels |
| Paper1_Package/01_FIGURES/main/Figure7_stage_transitions.png | 214250 bytes; (4470, 1311) pixels |
| Paper1_Package/01_FIGURES/main/Figure8_hallmark_enrichment.png | 598663 bytes; (3581, 4010) pixels |
| Paper1_Package/01_FIGURES/main/Figure9_mechanism_network.png | 1807160 bytes; (5370, 3866) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS10_dotplot_shared_up.png | 413709 bytes; (2666, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS11_dotplot_shared_down.png | 390271 bytes; (2667, 2612) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS12_dotplot_C1_all.png | 418417 bytes; (2664, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS13_dotplot_C1_core.png | 371780 bytes; (2665, 2612) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS14_dotplot_C2_all.png | 402949 bytes; (2665, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS15_dotplot_C2_core.png | 421970 bytes; (2665, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS16_dotplot_C3_all.png | 318147 bytes; (2668, 2156) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS17_dotplot_C3_core.png | 309280 bytes; (2668, 2156) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS18_dotplot_C4_all.png | 169802 bytes; (2685, 1016) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS19_dotplot_C4_core.png | 100695 bytes; (2665, 560) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS1_all_gene_trajectories.png | 1211938 bytes; (3789, 2009) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS20_dotplot_C5_all.png | 419003 bytes; (2666, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS21_dotplot_C5_core.png | 413904 bytes; (2666, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS2_transition_deltas.png | 182161 bytes; (3570, 1337) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS3_enrichment_GO_BP.png | 649698 bytes; (3581, 3422) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS4_enrichment_Reactome.png | 636842 bytes; (3580, 3674) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS5_enrichment_KEGG.png | 573699 bytes; (3580, 3002) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS6_dotplot_fibrosis_only_up.png | 413099 bytes; (2666, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS7_dotplot_fibrosis_only_down.png | 410837 bytes; (2665, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS8_dotplot_inflammation_only_up.png | 432712 bytes; (2737, 2725) pixels |
| Paper1_Package/01_FIGURES/supplementary/FigureS9_dotplot_inflammation_only_down.png | 103546 bytes; (2662, 560) pixels |
| Paper1_Package/02_TABLES/TABLE_CAPTIONS.md | 5484 bytes |
| Paper1_Package/02_TABLES/main/Table1_cohort.csv | 679 bytes; 9 rows |
| Paper1_Package/02_TABLES/main/Table2_gene_groups.csv | 493 bytes; 11 rows |
| Paper1_Package/02_TABLES/main/Table3_trajectory_clusters.csv | 483 bytes; 5 rows |
| Paper1_Package/02_TABLES/main/Table4_stage_transitions.csv | 572 bytes; 4 rows |
| Paper1_Package/02_TABLES/main/Table5_enrichment_counts.csv | 466 bytes; 16 rows |
| Paper1_Package/02_TABLES/main/Table6_prioritised_genes.csv | 7155 bytes; 23 rows |
| Paper1_Package/02_TABLES/supplementary/TableS10_cluster_core_check.csv | 1318 bytes; 20 rows |
| Paper1_Package/02_TABLES/supplementary/TableS11_evidence_scores_all_genes.csv | 1321154 bytes; 3845 rows |
| Paper1_Package/02_TABLES/supplementary/TableS12_tier1_genes.csv | 126470 bytes; 447 rows |
| Paper1_Package/02_TABLES/supplementary/TableS13_leave_one_study_out.csv | 38268 bytes; 447 rows |
| Paper1_Package/02_TABLES/supplementary/TableS14_tier_cutoff_sensitivity.csv | 141 bytes; 3 rows |
| Paper1_Package/02_TABLES/supplementary/TableS15_leave_one_score_out.csv | 209 bytes; 5 rows |
| Paper1_Package/02_TABLES/supplementary/TableS16_rho_cutoff_sensitivity.csv | 143 bytes; 3 rows |
| Paper1_Package/02_TABLES/supplementary/TableS17_trajectory_cutoff.csv | 142 bytes; 3 rows |
| Paper1_Package/02_TABLES/supplementary/TableS18_shortlist_rule.csv | 398 bytes; 2 rows |
| Paper1_Package/02_TABLES/supplementary/TableS19_knowledge_graph_connections.xlsx | 852070 bytes; 0_README, 1_shortlist_25_KG, 2_tier1_447_KG, 3_all_mechanisms_ranked, 4_figure_edges, 5_figure_nodes, 6_duplicates_collapsed |
| Paper1_Package/02_TABLES/supplementary/TableS1_top20_fibrosis_genes.csv | 3053 bytes; 40 rows |
| Paper1_Package/02_TABLES/supplementary/TableS2_gene_cluster_assignments.csv | 521052 bytes; 3845 rows |
| Paper1_Package/02_TABLES/supplementary/TableS3_representative_genes.csv | 8122 bytes; 75 rows |
| Paper1_Package/02_TABLES/supplementary/TableS4_choosing_k.csv | 703 bytes; 6 rows |
| Paper1_Package/02_TABLES/supplementary/TableS5_cluster_stability.csv | 372 bytes; 5 rows |
| Paper1_Package/02_TABLES/supplementary/TableS6_all_genes_all_transitions.csv | 2524377 bytes; 15380 rows |
| Paper1_Package/02_TABLES/supplementary/TableS7_top_genes_per_transition.csv | 20684 bytes; 160 rows |
| Paper1_Package/02_TABLES/supplementary/TableS8_top_pathways_per_group.csv | 171708 bytes; 456 rows |
| Paper1_Package/02_TABLES/supplementary/TableS9_all_significant_terms.csv | 1268831 bytes; 3945 rows |
| Paper1_Package/03_RESULTS/Task1_gene_groups/task1_shared_rho_scatter.png | 350473 bytes; (1643, 1694) pixels |
| Paper1_Package/03_RESULTS/Task1_gene_groups/task1_summary.csv | 493 bytes; 11 rows |
| Paper1_Package/03_RESULTS/Task1_gene_groups/task1_top20_fibrosis_genes.csv | 3053 bytes; 40 rows |
| Paper1_Package/03_RESULTS/Task1_gene_groups/task1_venn.png | 150297 bytes; (1433, 1280) pixels |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_bootstrap_shape_stability.csv | 372 bytes; 5 rows |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_choosing_k.csv | 703 bytes; 6 rows |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_choosing_k.png | 223679 bytes; (2970, 1191) pixels |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_cluster_means.png | 239998 bytes; (1877, 1407) pixels |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_cluster_sizes.csv | 483 bytes; 5 rows |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_cluster_trajectories.png | 1211938 bytes; (3789, 2009) pixels |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_gene_clusters.csv | 521052 bytes; 3845 rows |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_heatmap.png | 214695 bytes; (1722, 2504) pixels |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_representative_genes.csv | 8122 bytes; 75 rows |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_robustness.csv | 181 bytes; 3 rows |
| Paper1_Package/03_RESULTS/Task2_trajectories/task2_robustness_crosstab.csv | 281 bytes; 5 rows |
| Paper1_Package/03_RESULTS/Task3_transitions/task3_all_genes_all_transitions.csv | 2524377 bytes; 15380 rows |
| Paper1_Package/03_RESULTS/Task3_transitions/task3_cluster_by_transition.csv | 1560 bytes; 20 rows |
| Paper1_Package/03_RESULTS/Task3_transitions/task3_delta_distributions.png | 182161 bytes; (3570, 1337) pixels |
| Paper1_Package/03_RESULTS/Task3_transitions/task3_top_genes_per_transition.csv | 20684 bytes; 160 rows |
| Paper1_Package/03_RESULTS/Task3_transitions/task3_transition_comparison.png | 214250 bytes; (4470, 1311) pixels |
| Paper1_Package/03_RESULTS/Task3_transitions/task3_transition_summary.csv | 572 bytes; 4 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C1_all.png | 418417 bytes; (2664, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C1_core.png | 371780 bytes; (2665, 2612) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C2_all.png | 402949 bytes; (2665, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C2_core.png | 421970 bytes; (2665, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C3_all.png | 318147 bytes; (2668, 2156) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C3_core.png | 309280 bytes; (2668, 2156) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C4_all.png | 169802 bytes; (2685, 1016) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C4_core.png | 100695 bytes; (2665, 560) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C5_all.png | 419003 bytes; (2666, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_C5_core.png | 413904 bytes; (2666, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_fibrosis_only_down.png | 410837 bytes; (2665, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_fibrosis_only_up.png | 413099 bytes; (2666, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_inflammation_only_down.png | 103546 bytes; (2662, 560) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_inflammation_only_up.png | 432712 bytes; (2737, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_shared_down.png | 390271 bytes; (2667, 2612) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/dot_plots/dot_shared_up.png | 413709 bytes; (2666, 2725) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_all__GO_BP.csv | 859465 bytes; 4029 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_all__Hallmark.csv | 11517 bytes; 50 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_all__KEGG.csv | 31088 bytes; 162 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_all__Reactome.csv | 204919 bytes; 1014 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_core__GO_BP.csv | 336112 bytes; 1841 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_core__Hallmark.csv | 4903 bytes; 31 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_core__KEGG.csv | 11993 bytes; 75 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C1_core__Reactome.csv | 68793 bytes; 395 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_all__GO_BP.csv | 982179 bytes; 4251 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_all__Hallmark.csv | 13522 bytes; 50 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_all__KEGG.csv | 31151 bytes; 152 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_all__Reactome.csv | 216542 bytes; 1030 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_core__GO_BP.csv | 798572 bytes; 3789 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_core__Hallmark.csv | 11416 bytes; 50 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_core__KEGG.csv | 23693 bytes; 131 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C2_core__Reactome.csv | 163668 bytes; 832 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_all__GO_BP.csv | 415578 bytes; 2247 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_all__Hallmark.csv | 6457 bytes; 39 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_all__KEGG.csv | 14012 bytes; 88 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_all__Reactome.csv | 91599 bytes; 492 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_core__GO_BP.csv | 173546 bytes; 982 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_core__Hallmark.csv | 4195 bytes; 27 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_core__KEGG.csv | 4579 bytes; 29 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C3_core__Reactome.csv | 41920 bytes; 231 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_all__GO_BP.csv | 571364 bytes; 3026 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_all__Hallmark.csv | 7671 bytes; 44 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_all__KEGG.csv | 21869 bytes; 138 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_all__Reactome.csv | 152146 bytes; 824 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_core__GO_BP.csv | 363027 bytes; 2002 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_core__Hallmark.csv | 5428 bytes; 34 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_core__KEGG.csv | 14258 bytes; 92 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C4_core__Reactome.csv | 93354 bytes; 522 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_all__GO_BP.csv | 779441 bytes; 3809 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_all__Hallmark.csv | 10116 bytes; 49 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_all__KEGG.csv | 28321 bytes; 155 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_all__Reactome.csv | 178871 bytes; 915 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_core__GO_BP.csv | 672804 bytes; 3406 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_core__Hallmark.csv | 8422 bytes; 44 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_core__KEGG.csv | 23349 bytes; 130 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/C5_core__Reactome.csv | 138031 bytes; 715 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_down__GO_BP.csv | 837216 bytes; 3895 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_down__Hallmark.csv | 10806 bytes; 49 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_down__KEGG.csv | 30803 bytes; 161 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_down__Reactome.csv | 201547 bytes; 961 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_up__GO_BP.csv | 942528 bytes; 4115 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_up__Hallmark.csv | 11396 bytes; 50 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_up__KEGG.csv | 30948 bytes; 151 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/fibrosis_only_up__Reactome.csv | 203826 bytes; 968 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_down__GO_BP.csv | 513676 bytes; 2583 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_down__Hallmark.csv | 6580 bytes; 38 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_down__KEGG.csv | 18656 bytes; 106 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_down__Reactome.csv | 122263 bytes; 621 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_up__GO_BP.csv | 1149668 bytes; 4500 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_up__Hallmark.csv | 16140 bytes; 50 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_up__KEGG.csv | 40066 bytes; 179 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/inflammation_only_up__Reactome.csv | 314841 bytes; 1205 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_down__GO_BP.csv | 555636 bytes; 2856 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_down__Hallmark.csv | 7264 bytes; 41 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_down__KEGG.csv | 20815 bytes; 122 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_down__Reactome.csv | 137655 bytes; 728 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_up__GO_BP.csv | 1040024 bytes; 4417 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_up__Hallmark.csv | 15422 bytes; 50 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_up__KEGG.csv | 35552 bytes; 171 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/enrichment_tables/shared_up__Reactome.csv | 246143 bytes; 1124 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_all_significant.csv | 1268831 bytes; 3945 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_cluster_core_check.csv | 1318 bytes; 20 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_heatmap_go_bp.png | 649698 bytes; (3581, 3422) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_heatmap_hallmark.png | 598663 bytes; (3581, 4010) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_heatmap_kegg.png | 573699 bytes; (3580, 3002) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_heatmap_reactome.png | 636842 bytes; (3580, 3674) pixels |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_significant_counts.csv | 466 bytes; 16 rows |
| Paper1_Package/03_RESULTS/Task4_enrichment/task4_top_pathways_per_group.csv | 171708 bytes; 456 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/00_all_progression_genes.csv | 922830 bytes; 6222 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/01_master_table.csv | 1321154 bytes; 3845 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/03_rho_sensitivity.csv | 143 bytes; 3 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/04_delta_sensitivity.csv | 142 bytes; 3 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/05_powermatched_per_gene.csv | 694472 bytes; 15380 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/08_leave_one_score_out.csv | 209 bytes; 5 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/08_tier_sensitivity.csv | 141 bytes; 3 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/09a_tier1_genes.csv | 157498 bytes; 447 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/09a_tier1_pathway_dominance.csv | 72307 bytes; 1474 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/09b_option_A_top5_per_cluster.csv | 6355 bytes; 23 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/09b_option_B_cluster_top_score.csv | 13144 bytes; 48 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/09b_option_comparison.csv | 398 bytes; 2 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/10_loso_all_eligible_runs.csv | 5225571 bytes; 73970 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/10_loso_per_study_all_eligible.csv | 3226961 bytes; 14794 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/10_loso_runs.csv | 158114 bytes; 2235 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/10_loso_summary.csv | 38268 bytes; 447 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/11_FINAL_shortlist_25_genes.csv | 6916 bytes; 23 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/11_final_all_3845_genes.csv | 1017003 bytes; 3845 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/11_final_tier1_genes.csv | 126470 bytes; 447 rows |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/12_KG_supplementary.xlsx | 852070 bytes; 0_README, 1_shortlist_25_KG, 2_tier1_447_KG, 3_all_mechanisms_ranked, 4_figure_edges, 5_figure_nodes, 6_duplicates_collapsed |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/12_mechanistic_subgraph.png | 1807160 bytes; (5370, 3866) pixels |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/README.md | 867 bytes |
| Paper1_Package/03_RESULTS/Task5_gene_prioritisation/shortlist_with_membership_confidence.csv | 7155 bytes; 23 rows |
| Paper1_Package/04_DATA/DATA_DICTIONARY.md | 1788 bytes |
| Paper1_Package/04_DATA/gene_tables/README.txt | 780 bytes |
| Paper1_Package/04_DATA/gene_tables/genes_by_disease_group.csv | 669725 bytes; 6222 rows |
| Paper1_Package/04_DATA/gene_tables/genes_by_fibrosis_stage.csv | 668809 bytes; 6222 rows |
| Paper1_Package/04_DATA/gene_tables/genes_by_stage_and_age.csv | 1341438 bytes; 6222 rows |
| Paper1_Package/04_DATA/gene_tables/genes_by_stage_and_sex.csv | 868658 bytes; 6222 rows |
| Paper1_Package/04_DATA/gene_tables/sample_demographics.csv | 51821 bytes; 1085 rows |
| Paper1_Package/04_DATA/graph_nodes/edges_my_progression.csv | 829816 bytes; 8044 rows |
| Paper1_Package/04_DATA/graph_nodes/gene_progression_scores.csv | 411402 bytes; 5904 rows |
| Paper1_Package/04_DATA/graph_nodes/nodes_dataset.csv | 135 bytes; 8 rows |
| Paper1_Package/04_DATA/graph_nodes/nodes_gene.csv | 1614333 bytes; 53993 rows |
| Paper1_Package/04_DATA/harmonisation/_mapping_summary.csv | 363 bytes; 8 rows |
| Paper1_Package/04_DATA/harmonisation/_parse_summary.csv | 678 bytes; 8 rows |
| Paper1_Package/04_DATA/harmonisation/gene_id_map.csv | 16819870 bytes; 223956 rows |
| Paper1_Package/04_DATA/harmonisation/nodes_sample_clinical.csv | 81305 bytes; 1085 rows |
| Paper1_Package/04_DATA/harmonisation/sample_crosswalk.csv | 33758 bytes; 1085 rows |
| Paper1_Package/04_DATA/harmonisation/samples_metadata.csv | 198170 bytes; 1085 rows |
| Paper1_Package/04_DATA/harmonisation/unmapped_genes.csv | 50855 bytes; 1807 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_biological_process_gene.csv | 6754512 bytes; 157081 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_disease_disease.csv | 1491728 bytes; 44215 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_disease_gene.csv | 94486582 bytes; 1832441 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_disease_phenotype.csv | 6921179 bytes; 157144 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_drug_disease.csv | 2681209 bytes; 70380 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_drug_gene.csv | 779801 bytes; 20674 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_gene_gene.csv | 15557597 bytes; 324116 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_my_progression.csv | 829816 bytes; 8044 rows |
| Paper1_Package/04_DATA/knowledge_layer/edges_pathway_gene.csv | 2410576 bytes; 46751 rows |
| Paper1_Package/04_DATA/knowledge_layer/nodes_bioprocess.csv | 642509 bytes; 12203 rows |
| Paper1_Package/04_DATA/knowledge_layer/nodes_disease.csv | 1919380 bytes; 36044 rows |
| Paper1_Package/04_DATA/knowledge_layer/nodes_drug.csv | 333089 bytes; 12025 rows |
| Paper1_Package/04_DATA/knowledge_layer/nodes_pathway.csv | 133546 bytes; 2220 rows |
| Paper1_Package/04_DATA/knowledge_layer/nodes_phenotype.csv | 333572 bytes; 8666 rows |
| Paper1_Package/04_DATA/progression_genes/diagnostic_both_q_significant.csv | 1340268 bytes; 5494 rows |
| Paper1_Package/04_DATA/progression_genes/genes_by_disease_group.csv | 669725 bytes; 6222 rows |
| Paper1_Package/04_DATA/progression_genes/genes_by_fibrosis_stage.csv | 668809 bytes; 6222 rows |
| Paper1_Package/04_DATA/progression_genes/progression_disease.csv | 1898738 bytes; 14784 rows |
| Paper1_Package/04_DATA/progression_genes/progression_fibrosis.csv | 1915295 bytes; 14794 rows |
| Paper1_Package/04_DATA/progression_genes/sample_demographics.csv | 51821 bytes; 1085 rows |
| Paper1_Package/05_CODE/CODE_MAP.md | 1645 bytes |
| Paper1_Package/05_CODE/analysis/make_figure1.py | 8446 bytes |
| Paper1_Package/05_CODE/analysis/task1_groups.py | 4817 bytes |
| Paper1_Package/05_CODE/analysis/task2_trajectories.py | 16105 bytes |
| Paper1_Package/05_CODE/analysis/task3_transitions.py | 13071 bytes |
| Paper1_Package/05_CODE/analysis/task4_enrichment.py | 13112 bytes |
| Paper1_Package/05_CODE/biopsy_policy.py | 2514 bytes |
| Paper1_Package/05_CODE/build_paper1_package.py | 26451 bytes |
| Paper1_Package/05_CODE/cypher/01_create_constraints.cypher | 1117 bytes |
| Paper1_Package/05_CODE/cypher/02_load_expression_edges.cypher | 6404 bytes |
| Paper1_Package/05_CODE/cypher/03_load_knowledge_layer.cypher | 10664 bytes |
| Paper1_Package/05_CODE/pipeline/01_parse_expression.py | 6707 bytes |
| Paper1_Package/05_CODE/pipeline/02_map_gene_ids.py | 8748 bytes |
| Paper1_Package/05_CODE/pipeline/03_build_crosswalk.py | 4722 bytes |
| Paper1_Package/05_CODE/pipeline/04_normalize_clinical.py | 14741 bytes |
| Paper1_Package/05_CODE/pipeline/05_build_graph_all.py | 7594 bytes |
| Paper1_Package/05_CODE/pipeline/06_build_optimuskg_layer.py | 7219 bytes |
| Paper1_Package/05_CODE/pipeline/07_find_progression_genes.py | 10165 bytes |
| Paper1_Package/05_CODE/pipeline/08_export_gene_tables.py | 7501 bytes |
| Paper1_Package/05_CODE/pipeline/09_build_progression_edges.py | 4394 bytes |
| Paper1_Package/05_CODE/prioritisation/hc0_master_gene_table.py | 3547 bytes |
| Paper1_Package/05_CODE/prioritisation/hc1_powermatched_transitions.py | 8228 bytes |
| Paper1_Package/05_CODE/prioritisation/hc2_evidence_scores.py | 40400 bytes |
| Paper1_Package/05_CODE/prioritisation/hc3_leave_one_study_out.py | 6916 bytes |
| Paper1_Package/05_CODE/prioritisation/hc4_mechanism_subgraph.py | 26529 bytes |
| Paper1_Package/05_CODE/requirements.txt | 404 bytes |
| Paper1_Package/05_CODE/validation/check_gene_mapping.py | 3811 bytes |
| Paper1_Package/05_CODE/validation/compare_result_versions.py | 7488 bytes |
| Paper1_Package/05_CODE/validation/diagnose_membership_confidence.py | 7689 bytes |
| Paper1_Package/05_CODE/validation/expected_graph_counts.py | 3017 bytes |
| Paper1_Package/05_CODE/validation/inspect_parsed_files.py | 4832 bytes |
| Paper1_Package/05_CODE/validation/verify_graph_counts.py | 9692 bytes |
| Paper1_Package/05_CODE/validation/verify_subgraph_against_neo4j.py | 4741 bytes |
| Paper1_Package/06_PROVENANCE/DATA_SOURCES.md | 4850 bytes |
| Paper1_Package/06_PROVENANCE/REBUILD.md | 4053 bytes |
| Paper1_Package/06_PROVENANCE/drug_connection_audit/nafld_nash_indication_annotations.csv | 1392 bytes; 13 rows |
| Paper1_Package/06_PROVENANCE/drug_connection_audit/per_gene_drug_counts.csv | 631 bytes; 23 rows |
| Paper1_Package/06_PROVENANCE/drug_connection_audit/summary.json | 1406 bytes |
| Paper1_Package/06_PROVENANCE/final_combined/FINAL_SELECTION.md | 2491 bytes |
| Paper1_Package/06_PROVENANCE/final_combined/PROTOCOL.md | 3510 bytes |
| Paper1_Package/06_PROVENANCE/final_combined/candidate_stability.csv | 4113 bytes; 45 rows |
| Paper1_Package/06_PROVENANCE/final_combined/comparison_summary.csv | 766 bytes; 4 rows |
| Paper1_Package/06_PROVENANCE/final_combined/graph_verification.json | 795 bytes |
| Paper1_Package/06_PROVENANCE/final_combined/network_comparison.csv | 348 bytes; 8 rows |
| Paper1_Package/README.md | 1583 bytes |
