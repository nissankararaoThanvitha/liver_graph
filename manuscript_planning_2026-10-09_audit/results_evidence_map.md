> **Follow-up, 10 October 2026:** This is the preserved first-stage audit of the earlier results. The researcher clarified that the final goal is drug repurposing to stop progression at different stages; a patient-stage classifier is not the intended endpoint. Biopsy handling and affected analyses have since been corrected. Use `biopsy_correction_2026-10-10/CORRECTION_REPORT.md` for current counts, validation and graph status; historical findings below remain for traceability.

# Results evidence map and manuscript architecture

9 October 2026. This maps existing findings to potential manuscript sections; it is not a draft. File paths are relative to the project root unless stated otherwise. P denotes Paper1_Package/. Row identifiers and sheet names are preferred over mutable physical row numbers.

Status: confirmed stored result; interpretation; provisional pending repair; historical only; unsupported. “Confirmed” describes the inspected evidence and does not establish independent biological or clinical validation.

## Proposed article argument

The evidence supports a computational resource and exploratory cross-study transcriptomic study of stage-associated liver gene programmes, with explicit harmonisation, sampling and annotation boundaries. It supports neither diagnostic accuracy nor causal disease progression. The mentor’s original stage-prediction aim must be reconciled with this completed scope before choosing the title/abstract claim.

| Manuscript section | Existing material to use | Boundary or additional input |
|---|---|---|
| Introduction: biological problem | Historical aim, two clinical axes, heterogeneous public cohorts; handover/session02 “The problem”; package01_OVERVIEW | Disease burden, fibrosis prognosis, clinical staging alternatives, MASLD/MASH nomenclature and biological background need primary literature verification. Do not copy “biopsy is the only way” or “fibrosis cannot reverse” from old sessions. |
| Introduction: computational gap | Measurement plus curated knowledge, identifier and clinical harmonisation; package02_METHODS stages2–9 | Broad novelty relative to other biomedical graphs needs literature comparison; absence of an edge does not prove a novel gene/disease finding. |
| Materials and Methods | complete_workflow.md stages2–17; package code and provenance | State log-CPM/log-TPM transformations, different repeat policies, actual BH families, k-rule override, graph directions and score definitions. Resolve LOSO and rebuild issues. |
| Results: cohort/resource | R01–R03 below | Separate 1,085 samples, 1,027 patient IDs, 668 staged samples, 610 first-biopsy staged patients and 221 disease-axis patients. |
| Results: association/grouping | R04–R05 | Correlation and consistency, not differential expression or stage prediction. |
| Results: stage shapes/contrasts | R06–R08 | Cross-sectional stage ordering; conditional stability; selected-set inference. |
| Results: enrichment | R09–R10 | Association with annotations, not demonstrated cellular mechanism. C1/C3 cores untested. |
| Results: prioritisation/network | R11–R14 | Exploratory scoring; related evidence features; Table6 cluster confidence; LOSO provisional. |
| Discussion | Documented limits plus discrepancies in missing_information.md | External validation and biological plausibility need review; no mechanistic or therapeutic efficacy claims. |
| Supplementary material | Full inventories, per-gene tables, sensitivity outputs, graph schema/membership checks | Replace residual stale artifacts, make tested versus untested explicit, include acquisition/rebuild details. |
| Data/code availability | GSE accessions, repository cited in handover/SETUP, package assets | Versioned release/archive DOI, downloadable graph/data and dependency lock are not supplied. Confirm permissions and original study ethics with authors. |

Scientific Reports’ official guidance requires a Data Availability statement and legible submission figures; full page opening was blocked by an identity redirect during this audit, so detailed current formatting limits remain to be checked: [official guidance](https://www.nature.com/srep/author-instructions/submission-guidelines).

## Claim by claim

| ID | Completed finding or claim | Exact supporting evidence and locator | Proposed display/section | Status and permitted claim boundary |
|---|---|---|---|---|
| R01 | Eight studies; 1,085 samples; 1,027 patient IDs; 58 repeats | P/02_TABLES/main/Table1_cohort.csv study/TOTAL rows; P/04_DATA/harmonisation/nodes_sample_clinical.csv patient_id/biopsy_number | Table1; cohort Methods/Results | Confirmed table counts. Original acquisition and cross-study patient overlap not independently verified. |
| R02 | 668 staged samples; 610 unique staged patients; first-biopsy cells152/160/152/112/34; disease-axis221 | Clinical table filtered by fibrosis_stage and biopsy_number; progression script DISEASE_LADDER/run_axis; audit/computed_checks.txt | Table1 expanded; design schematic | Confirmed clinical counts plus implemented eligibility. Different downstream n must be stated per analysis. |
| R03 | Integrated8-node/14-edge graph;126,244 nodes/35,132,486 relationships | audit/live_graph_readonly.json/count queries; live_graph_properties.json/schema; package knowledge CSVs | Resource Results; new schema/statistics table; Figure1 | Live checks confirmed current user instance. Full expression values not compared against absent bulk CSVs. Untrimmed biomedical graph applied to liver study. |
| R04 | Significant fibrosis3,681, disease4,018, union5,884, shared1,815 | P/04_DATA/progression_genes/progression_fibrosis.csv and progression_disease.csv: q_value<.05 AND n_agree=n_studies; Table2 group rows | Figures2–3; Table2 | Confirmed counts. Tests involve5 versus3 studies, not all eight for each axis. progression_both.csv is not the membership source. |
| R05 | Shared direction:1,472 rising,330 falling,13 discordant; overall rho.657 | Table2; gene_tables/genes_by_fibrosis_stage.csv ladder=both; audit/computed_checks.txt | Figure3; supplementary within-direction panel | Confirmed across-gene statistic on rounded exported rhos; within-direction.380/.219. Not within-patient coupling or causation. |
| R06 | Five reported trajectory clusters948/1528/209/313/683 | P/03_RESULTS/Task2_trajectories/task2_cluster_sizes.csv; Table3; TableS2 | Figures4–5; Table3 | Confirmed stored solution. k5 was an override; automatically applying the documented rule gives6. |
| R07 | Median shape recovery.976/.996/.970/.960/.994; confident members3/772/1/130/510; study-adjusted ARI.870 | task2_bootstrap_shape_stability.csv cluster rows; task2_robustness.csv check rows; TableS2 confidence_n_bootstraps | Figure6 amended; S5; new confidence/robustness panel | Confirmed statistics. Medians conceal some poor matches; confidence conditions on sound matching. Specific genes require own confidence. |
| R08 | Full substantial counts1197/1145/1127/934; matched medians0/0/2/287; late median|beta|.3753 | Table4 transition rows; TableS6 gene/transition rows; task3_cluster_by_transition.csv | Figure7; S2; Table4 | Confirmed stored comparisons among3,681 preselected genes. Late matched SD412.4; no direct longitudinal progression, external validation or guarantee selection bias cancels. |
| R09 | Distinct group enrichment, with3706 significant group/database/term rows | P/03_RESULTS/Task4_enrichment/task4_all_significant.csv; Table5; TableS8–S9; per-run current group CSVs | Figure8; S3–S12,S14–S16,S18,S20–S21; Table5 | Confirmed current aggregate. Numeric term counts refer to overlapping annotation families, not independent pathways. Membership lists support biological descriptions. |
| R10 | C2/C5 core biology persists; C4 core has0 terms; C1/C3 cores untested | Table5 n_genes core rows; TableS10; Task2 confidence counts; task4_enrichment.py MIN_GROUP_GENES | S10 and corrected core panel | Confirmed aggregate distinction. S13/S17/S19 and residual C1/C3 per-run tables conflict and are excluded. |
| R11 | P/T/X/F/B ranking525 Tier1,1464 Tier2,1692 Tier3 | TableS11 Total_score/Tier; Task5/01_master_table.csv; hc2 score definitions | New priority/sensitivity figure; Methods/Results | Confirmed administrative tiers, not calibrated confidence probabilities. Features share data; no five independent validations. |
| R12 | Chosen25, five per cluster;15 increasing/10 decreasing; alternative53 | Table6; Task5/09b_option_A_top5_per_cluster.csv,09b_option_B_cluster_top_score.csv,09b_option_comparison.csv; S18 | Table6 with confidence; Results | Confirmed exploratory shortlist. Only10/25 confidence≥.8. No known predictive accuracy or assay validation. |
| R13 | Stored LOSO521 significant all five;263 strong all five;76 strong0/5 | Task5/10_loso_runs.csv,10_loso_summary.csv; TableS13; hc3 lines96–147 | Supplement robustness after repair | Provisional interpretation: repeat aggregation disagrees with discovery; BH family selected 525. These are table contents, not certified current validation. |
| R14 | Twelve enriched graph mechanisms;47 genes,165 edges;6/25 shortlist shown | TableS19 sheets3_all_mechanisms_ranked,4_figure_edges,5_figure_nodes; live_membership_comparison.json | Figure9 corrected; TableS19 | Confirmed stored network and full membership equality for12 nodes. Enrichment BH over4330 reached nodes; pancreatic ductal annotation needs review; no causal validation. |
| R15 | Threshold sensitivity: score6→1127,7→525,8→148; droppingP leaves52/148 top band | TableS14–S17 rows; TableS15 score_dropped=P | Supplement; prioritisation limitations | Confirmed, material sensitivity. Do not claim candidate membership is insensitive to reasonable thresholds. |
| R16 | Age/sex stage summaries available for385 samples | P/04_DATA/gene_tables/genes_by_stage_and_age.csv,genes_by_stage_and_sex.csv; sample_demographics; export code | Supplement demographic table | Descriptive only. No adjusted association/interaction/predictive analysis or comprehensive covariate control. |
| R17 | Drug/missing-link models and meta-paths | Historical sessions; export_triples.py/train_link_prediction.py | Context/future work, normally outside Paper1 Results | Failed model documented; current model/logs/candidate tables absent. Descriptive walks are not validated predictions or causal evidence. |

## Existing main figures and readiness

All paths below are P/01_FIGURES/main/. Dimensions/dpi are recorded in audit/file_inventory.json. Review was at overview/contact-sheet resolution, not a final-size publication proof.

| Figure | Actual file and underlying outputs | Evidence/message | Readiness and changes needed |
|---|---|---|---|
|1|Figure1_study_design.png; make_figure1.py; cohort/progression tables|Harmonisation and Tasks1–4 overview|Current headline counts, but omits Task5. Add prioritisation/network branch and exact eligible n, simplify technical script labels for readers; add schema panel if resource is central. |
|2|Figure2_ladder_overlap.png; task1_summary.csv|1866/1815/2203 overlap|Counts agree. Caption must explain unequal axes/cohorts and “associated” classification. Circle areas are illustrative rather than quantitatively scaled. |
|3|Figure3_shared_gene_agreement.png; shared rows of stage table|Overall rho.657|Counts/statistic agree. Add or supplement within-direction associations; do not imply paired patient effects. |
|4|Figure4_trajectory_shapes.png; Table3 stage means|Five mean shapes|Counts agree. No uncertainty bands; describe sample-based stage means, not followed trajectories. |
|5|Figure5_stage_heatmap.png; TableS2 row-stage profiles|3681 genes grouped by shape|Image scale is z across stages, not merely within-study value_z; caption currently vague. Explain both normalisations. |
|6|Figure6_choosing_k.png; TableS4|k diagnostics|**Incorrect title:** says5chosen by largest k ARI≥.95; actual rule gives6. Redraw labels and explain override. |
|7|Figure7_stage_transitions.png; Table4/S6|Full versus matched contrasts, effects|Counts agree. State preselection, repeated sampling,30/stage and IQR; large dispersion; no causal or precise gene-number claim. |
|8|Figure8_hallmark_enrichment.png; task4_all_significant.csv|Hallmark programme associations|Usable evidence; dense text needs proof at journal width. Colour cap10 and blank=not significant, not absence of biology. |
|9|Figure9_mechanism_network.png; TableS19|Tier1 network with6 shortlisted genes|Membership confirmed live. Title “most-connected” contradicts q-based selection; legend should identify only6 of25 depicted. Review pancreatic pathway and small labels; sheet annotations stale. |

## Supplementary figures

Paths are P/01_FIGURES/supplementary/. Publication labels are existing package labels, not a newly proposed renumbering.

| Label | Filename | Evidence source | Status |
|---|---|---|---|
|S1|FigureS1_all_gene_trajectories.png|Task2 profiles/centroids|Supports distributions; no longitudinal interpretation |
|S2|FigureS2_transition_deltas.png|Task3 delta_mean/beta_adjusted|Current; selected-gene set and SD scale |
|S3|FigureS3_enrichment_GO_BP.png|Task4 aggregate, top5/group|Current; dense labels |
|S4|FigureS4_enrichment_Reactome.png|same, Reactome|Current; dense labels |
|S5|FigureS5_enrichment_KEGG.png|same, KEGG legacy|Current; version/licensing disclosure |
|S6|FigureS6_dotplot_fibrosis_only_up.png|fibrosis_only_up per-run tables|Current n1212 |
|S7|FigureS7_dotplot_fibrosis_only_down.png|fibrosis_only_down|Current n654 |
|S8|FigureS8_dotplot_inflammation_only_up.png|inflammation_only_up|Current n1782 |
|S9|FigureS9_dotplot_inflammation_only_down.png|inflammation_only_down|Current n421; one Hallmark term, not zero findings |
|S10|FigureS10_dotplot_shared_up.png|shared_up|Current n1472 |
|S11|FigureS11_dotplot_shared_down.png|shared_down|Current n330 |
|S12|FigureS12_dotplot_C1_all.png|C1_all|Current n948; full-cluster inference |
|S13|FigureS13_dotplot_C1_core.png|old core47|**Exclude:** current core3 untestable |
|S14|FigureS14_dotplot_C2_all.png|C2_all|Current n1528 |
|S15|FigureS15_dotplot_C2_core.png|C2_core|Current n772 |
|S16|FigureS16_dotplot_C3_all.png|C3_all|Current n209; full-cluster inference |
|S17|FigureS17_dotplot_C3_core.png|old core36|**Exclude:** current core1 untestable |
|S18|FigureS18_dotplot_C4_all.png|C4_all|Current n313; sparse terms |
|S19|FigureS19_dotplot_C4_core.png|old core78, one Reactome term|**Exclude/regenerate:** current core130, zero enriched terms |
|S20|FigureS20_dotplot_C5_all.png|C5_all|Current n683 |
|S21|FigureS21_dotplot_C5_core.png|C5_core|Current n510 |

## Existing tables and exact use

Paths: P/02_TABLES/main or supplementary. Copies of analysis outputs may have different byte line endings from originals; check content, not filename counts alone.

| Label | Filename | What it supports and qualification |
|---|---|---|
|1|Table1_cohort.csv|All study samples/IDs/labels/demographic coverage; staged-sample n not independent-patient n |
|2|Table2_gene_groups.csv|Current group/direction counts; percentages denominator5884 |
|3|Table3_trajectory_clusters.csv|Five clusters and unadjusted stage means |
|4|Table4_stage_transitions.csv|Patient-cell n, full and matched results; transition-specific sample policy |
|5|Table5_enrichment_counts.csv|Aggregate current group/database counts; zeros for C1/C3 core represent skip, distinct from tested C4 zero |
|6|Table6_prioritised_genes.csv|25 genes, scores, effects and provisional LOSO; add confidence and disclosure |
|S1|TableS1_top20_fibrosis_genes.csv|Top20 per direction; not entire shortlist or validated biomarkers |
|S2|TableS2_gene_cluster_assignments.csv|3681 genes, five stages, membership confidence/denominators |
|S3|TableS3_representative_genes.csv|15/cluster ranked by confidence; many early-cluster choices still uncertain |
|S4|TableS4_choosing_k.csv|k3…8 scores and SDs; rule gives6 |
|S5|TableS5_cluster_stability.csv|Shape recovery versus gene-level confidence |
|S6|TableS6_all_genes_all_transitions.csv|14724 gene×transition statistical records |
|S7|TableS7_top_genes_per_transition.csv|Displayed top genes among significant fits; verify direction rather than assume ranking label |
|S8|TableS8_top_pathways_per_group.csv|Top10 per group/database, not complete tested set |
|S9|TableS9_all_significant_terms.csv|3706 significant rows across group/database; overlapping terms |
|S10|TableS10_cluster_core_check.csv|All versus current core term overlap; does not carry explicit untested flags itself |
|S11|TableS11_evidence_scores_all_genes.csv|3681scored genes and intermediate features |
|S12|TableS12_tier1_genes.csv|525full score-qualified genes; includes provisional LOSO |
|S13|TableS13_leave_one_study_out.csv|525 gene summaries from2625 runs; repair policy/testing-family first |
|S14|TableS14_tier_cutoff_sensitivity.csv|1127/525/148atcutoffs 6/7/8 |
|S15|TableS15_leave_one_score_out.csv|Rank/top-band dependence; P top-band overlap52/148 |
|S16|TableS16_rho_cutoff_sensitivity.csv|P threshold pairs(.35,.25),(.4,.3),(.45,.35) |
|S17|TableS17_trajectory_cutoff.csv|T threshold pairs(.8,.4),(1,.5),(1.2,.6) |
|S18|TableS18_shortlist_rule.csv|OptionA25 versusOptionB53; chosenA |
|S19|TableS19_knowledge_graph_connections.xlsx|All gene-mechanism memberships, ranking, figure edges/nodes and empty collapse list |

TableS19 sheet locators: 0_README (stale507, Figure12, degree 2 language); 1_shortlist_25_KG (478 connection rows); 2_tier1_507_KG (10,543 connection rows, **525 distinct genes**); 3_all_mechanisms_ranked (4,330 nodes); 4_figure_edges (165); 5_figure_nodes (59); 6_duplicates_collapsed (header only, zero records). Row counts exclude headers. All sheets were read, including notes. Equivalent workbook copies exist in Task5 and Paper1_HighConfidence.

## Missing or revised publication displays

Necessary before submission:

1. Update Figure1 to include actual Task5 and a clear schema/count panel if graph integration is a principal contribution.
2. Correct Figure6’s selection claim; supply k6 comparison as supplementary sensitivity or document reproducible override.
3. Replace S13/S17 with an explicit “untestable, core n<5” panel or omit them; replace S19 with the tested-null result. Do not recycle old enrichment.
4. Add confidence/denominator columns to the shortlist and explain provisional C1/C3/C4 gene assignments.
5. Show corrected LOSO distributions and testing family after rerun; retain current sensitivity as evidence of uncertainty.
6. Correct Figure9’s q-ranked subset wording and workbook metadata; inspect relevant gene memberships behind the pancreatic pathway.
7. Create final-size/vector exports where possible; proof dense pathway/network labels and exact axis scales. No submission-quality PDF/vector figures are presently supplied.

Useful additions if supported by later approved work: per-study rho forest/heterogeneity display; disease-label derivation exclusion sensitivity; patient-policy sensitivity; cohort/stage coverage plot; covariate/cell-composition sensitivity. These have not been completed in this audit and must not be described as results.

## Claim exclusions and literature work

Do not state: validated non-invasive stage predictor; successful drug repurposing; independent confirmation by five scoring features; causal immune activation preceding scarring; complete modern MASLD/MASH eligibility; all shared genes act on both axes in the same patients; absence from the filtered KG proves novel biology; complete end-to-end reproducibility from the package alone; all core enrichments independently confirmed.

Primary literature still needed for the8source cohorts, HGNC/OptimusKG/MSigDB resources, histological diagnosis definitions, MASLD/MASH nomenclature, prognostic relevance of fibrosis, and chosen biological interpretations. Existing REF/PMID/PMC identifiers are intake leads, not permission to fabricate a bibliography. Direct graph annotations are contextual evidence; they do not validate therapeutic direction, efficacy or cell-type mechanism.
