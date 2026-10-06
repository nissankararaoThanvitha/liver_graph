TASK 2 -- How fibrosis genes change from F0 to F4
=================================================

Source: genes_by_fibrosis_stage.csv. 3,645 fibrosis-associated genes
(fibrosis-only 1,953 + shared 1,692). Stage means from 668 staged samples:
F0 152, F1 168, F2 186, F3 127, F4 35 (F4 means are the noisiest).

METHOD
  1. Each gene's five stage means were z-scored across stages, so genes
     group by the SHAPE of their curve, not its size.
  2. K-means clustering (50 random starts), k = 3..8 tested.
  3. k chosen from silhouette score and stability:
       gene subsample    = 50 random 80% subsets of genes, reclustered
       patient bootstrap = 50 resamples of patients (within study, with
                           replacement), stage means recomputed, reclustered
     ARI = adjusted Rand index against the full-data clustering.
       k  silhouette  gene-subsample ARI  patient-bootstrap ARI
       3    0.560          0.981                0.754
       4    0.461          0.968                0.564
       5    0.338          0.957                0.526   <- chosen
       6    0.291          0.932                0.464
       7    0.280          0.795                0.423
       8    0.258          0.757                0.367
     Rule: largest k with gene-subsample ARI >= 0.95 -> k = 5.
     NOTE: silhouette alone favours k = 3, and this rule was set after
     inspecting the k = 3..6 curves: k = 3/4 merge visibly different shapes
     (e.g. the two decreasing ones), k = 6 splits the late-increase cluster
     into two near-identical ones.
  4. Clusters were named AFTER clustering, from their average curves.
     No gene was assigned to a pattern by hand.

CLUSTERS
                                              genes   high-confidence genes*
  C1  Early increase (F0->F1), then continued   927           47
  C2  Late increase (largest at F3->F4)        1,514          841
  C3  Early rise, then plateau                  197           36
  C4  Mid decrease (largest at F1->F2)          309           78
  C5  Late decrease (largest at F3->F4)         698          423
  * membership_confidence >= 0.8 (see ROBUSTNESS)

  C3 was first named "Rise to F3, then reverse" from its stage means. Task 3's
  patient-level test found no significant F3->F4 drop (0 of 197 genes), so it
  was renamed. Its core genes are cell-cycle genes (ANLN, ASPM, KIF20A, RRM2,
  TTK, TOP2A).

ROBUSTNESS -- what is solid and what is not
  * The five SHAPES are reproducible. In 100 patient bootstraps each shape
    was recovered with median correlation 0.97-0.997 to the original.
  * Study mix does not create the shapes. Stage profiles re-estimated with
    value_z ~ stage + study correlate 0.998 (median per gene) with the plain
    stage means; reclustering them gives ARI 0.84 with the main clusters.
  * Individual gene MEMBERSHIP is less certain. Under patient bootstrap many
    genes move between neighbouring clusters, mostly among the three
    increasing clusters (C1/C2/C3), which differ only in timing.
    membership_confidence (fraction of 100 bootstraps in which a gene stays
    in its cluster) is given per gene. C2 and C5 have large stable cores;
    C1, C3 and C4 are dominated by borderline genes.
  => Report the shapes with confidence; for statements about specific genes
     in a cluster, use high-confidence genes.

FILES
  task2_gene_clusters.csv         Gene | F0..F4 | cluster | cluster_name |
                                  corr_to_centroid | membership_confidence |
                                  fibrosis_rho | ladder
                                  (F0..F4 = mean value_z per stage)
  task2_cluster_sizes.csv         genes per cluster + cluster mean per stage
  task2_representative_genes.csv  15 genes per cluster, ranked by membership
                                  confidence, then closeness to the shape
  task2_heatmap.png               all 3,645 genes x F0..F4, grouped by cluster
  task2_cluster_trajectories.png  every gene (grey) + cluster average (red)
  task2_cluster_means.png         cluster averages on the original scale
  task2_choosing_k.png / .csv     silhouette and both stabilities, k = 3..8
  task2_bootstrap_shape_stability.csv  shape recovery + confident genes per cluster
  task2_robustness.csv            study-adjustment and bootstrap summary
  task2_robustness_crosstab.csv   main clusters vs study-adjusted clusters
