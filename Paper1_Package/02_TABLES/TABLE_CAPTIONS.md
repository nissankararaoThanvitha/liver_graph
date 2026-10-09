# Table captions

Captions for every table, ready to paste. Each is the committed analysis output copied unmodified, except Table 1, which this package builds from the harmonised clinical table.

## Table 1

**The eight studies and what each contributes.**

Samples, patients, fibrosis staging, disease labels and demographic coverage per study. Built by build_paper1_package.py from the harmonised clinical table, so it cannot drift from it.

`Table1_cohort.csv`

## Table 2

**Progression genes by group and direction.**

Counts and percentages for the fibrosis-only, inflammation-only and shared partitions, split by direction of change.

`Table2_gene_groups.csv`

## Table 3

**The five trajectory clusters.**

Genes per cluster with the cluster mean standardised expression at each fibrosis stage.

`Table3_trajectory_clusters.csv`

## Table 4

**The four stage transitions compared.**

Patient counts, substantially changing genes, direction split, median effect size and power-matched counts for each transition.

`Table4_stage_transitions.csv`

## Table 5

**Significantly enriched terms per group.**

Counts of terms at FDR < 0.05 in each database, per gene group and per trajectory cluster.

`Table5_enrichment_counts.csv`

## Table 6

**The prioritised fibrosis genes.**

The five highest-scoring Tier 1 genes per trajectory cluster, ties broken by correlation magnitude, with all five evidence scores, the stage of largest change, leave-one-study-out results and cluster confidence.

`Table6_prioritised_genes.csv`

## Table S1

**Strongest fibrosis-associated genes.**

Top 20 increasing and top 20 decreasing genes by cross-study fibrosis correlation.

`TableS1_top20_fibrosis_genes.csv`

## Table S2

**Cluster assignment for every fibrosis gene.**

Stage means F0-F4, cluster, correlation to the cluster centroid, bootstrap membership confidence and the number of bootstraps each gene was assessed in. Use membership_confidence for any claim about an individual gene.

`TableS2_gene_cluster_assignments.csv`

## Table S3

**Representative genes per cluster.**

Fifteen genes per cluster ranked by membership confidence, then by closeness to the cluster shape.

`TableS3_representative_genes.csv`

## Table S4

**Cluster-number diagnostics.**

Silhouette score and both stability measures for k = 3 to 8.

`TableS4_choosing_k.csv`

## Table S5

**Shape reproducibility and membership confidence per cluster.**

Median and minimum correlation of each cluster's shape across 100 patient bootstraps, and how many of its genes are confidently assigned.

`TableS5_cluster_stability.csv`

## Table S6

**Every gene at every transition.**

Per gene and transition: stage-mean difference, study-adjusted beta, standard error, p, q, patient counts, substantial flag and cluster.

`TableS6_all_genes_all_transitions.csv`

## Table S7

**Strongest genes per transition.**

Top 20 increasing and decreasing genes per transition at q < 0.05.

`TableS7_top_genes_per_transition.csv`

## Table S8

**Leading enriched terms per group.**

Top ten terms per group and database with the genes responsible.

`TableS8_top_pathways_per_group.csv`

## Table S9

**Every significantly enriched term.**

All terms at FDR < 0.05 across every group and database.

`TableS9_all_significant_terms.csv`

## Table S10

**Enrichment on all genes against high-confidence members.**

Whether each cluster's leading biology survives when only confidently assigned members are used. Clusters with too few confident members to test are recorded as such.

`TableS10_cluster_core_check.csv`

## Table S11

**Evidence scores for every fibrosis gene.**

Every intermediate behind the five scores, the total and the tier, for every scored gene.

`TableS11_evidence_scores_all_genes.csv`

## Table S12

**All Tier 1 genes.**

The full high-confidence set, same columns as Table 6.

`TableS12_tier1_genes.csv`

## Table S13

**Leave-one-study-out results per gene.**

Direction retained, still significant, still above the correlation threshold, weakest median correlation and largest percentage loss, over the five fibrosis-staging studies.

`TableS13_leave_one_study_out.csv`

## Table S14

**Sensitivity of the Tier 1 boundary.**

Tier 1 membership at score cutoffs 6, 7 and 8.

`TableS14_tier_cutoff_sensitivity.csv`

## Table S15

**Sensitivity of the ranking to each score.**

Dropping each of the five scores in turn: Spearman correlation against the full ranking and overlap of the top band.

`TableS15_leave_one_score_out.csv`

## Table S16

**Sensitivity of the progression-strength cutoffs.**

How many genes score 2, 1 and 0 at three choices of the correlation thresholds.

`TableS16_rho_cutoff_sensitivity.csv`

## Table S17

**Sensitivity of the trajectory cutoffs.**

How many genes score 2, 1 and 0 at three choices of the F0-F4 difference thresholds.

`TableS17_trajectory_cutoff.csv`

## Table S18

**The two shortlist rules considered.**

Composition of the chosen rule (top five per cluster) against the alternative (each cluster's own top score).

`TableS18_shortlist_rule.csv`

## Table S19

**Knowledge-graph connections and mechanism ranking.**

Per-gene connections for the shortlist and for all Tier 1 genes, every mechanism ranked with fold enrichment and q, and the nodes and edges drawn in Figure 9.

`TableS19_knowledge_graph_connections.xlsx`

---

Each table is produced by the script named for it in `05_CODE/`, and the numbering is set in one place in `build_paper1_package.py`.
