TASK 4 -- Pathway enrichment per gene group
===========================================

GROUPS (each analysed separately, never all 4,692 genes together)
  fibrosis_only_up 1,301    fibrosis_only_down 652
  inflammation_only_up 597  inflammation_only_down 450
  shared_up 1,335           shared_down 356     (GPD1, discordant, excluded)
  Task 2 clusters, all genes:   C1 927, C2 1,514, C3 197, C4 309, C5 698
  Task 2 clusters, CHECK only:  high-confidence genes (bootstrap membership
                                confidence >= 0.8): C1 47, C2 841, C3 36,
                                C4 78, C5 423

DATABASES  (MSigDB v2024.1, human gene symbols)
  GO Biological Process (c5.go.bp)   KEGG legacy (c2.cp.kegg_legacy)
  Reactome (c2.cp.reactome)          Hallmark (h.all)

BACKGROUND -- the key methodological point
  The 14,794 genes eligible for the cross-study progression analysis
  (measured in all studies), NOT all ~20,000 human genes. Every gene set was
  first restricted to these 14,794 genes, then kept only if it had 10-500 of
  them (GO BP 4,853, KEGG 183, Reactome 1,279, Hallmark 50 sets tested).
  Test: one-sided hypergeometric (gseapy.enrich, run locally), BH-FDR within
  each group x database, significant at FDR < 0.05.
  Check: one p-value recomputed directly with scipy's hypergeometric
  distribution matched gseapy exactly.

SIGNIFICANT TERMS (FDR < 0.05)
                         genes  GO_BP  KEGG  Reactome  Hallmark
  fibrosis_only_up        1301    234    35        18         7
  fibrosis_only_down       652    106    26        33         8
  inflammation_only_up     597      2     1        30         2
  inflammation_only_down   450      0     0         0         0
  shared_up               1335    446    27        71        30
  shared_down              356     62    22        19         5
  C1 early increase        927    348    47        50        15
  C2 late increase        1514    542    20        48        21
  C3 early rise, plateau   197     85     3        29         3
  C4 mid decrease          309      5     1         2         2
  C5 late decrease         698    159    35        38         7

MAIN BIOLOGY
  fibrosis_only_up    immune cell activation (myeloid, T cell), IL6-JAK-STAT3,
                      allograft rejection, inflammatory response
  fibrosis_only_down  xenobiotic, fatty acid and bile acid metabolism,
                      peroxisome -- loss of normal liver metabolism
  inflammation_only   weak: interferon-alpha response and G2/M up;
                      nothing significant for the down genes
  shared_up           extracellular matrix / collagen formation, epithelial-
                      mesenchymal transition, TNFa-NFkB, apoptosis, p53,
                      angiogenesis -- the core fibrogenic programme
  shared_down         amino acid / organic acid catabolism, xenobiotic and
                      bile acid metabolism, coagulation
  C1 early increase   adaptive immunity, T cell activation, interferon-gamma,
                      allograft rejection -- immune activation starts early
  C2 late increase    EMT, matrix organisation, cell migration, TNFa-NFkB,
                      hypoxia, TGF-beta -- scarring accelerates late
  C3 early rise       cell cycle: E2F targets, G2/M checkpoint, chromosome
                      segregation, mitotic spindle -- proliferation
  C4 mid decrease     few terms (xenobiotic metabolism, metal-ion response)
  C5 late decrease    bile acid, fatty acid and xenobiotic metabolism,
                      peroxisome -- metabolic failure as cirrhosis develops

CLUSTER CHECK -- does the biology hold with only high-confidence genes?
  (task4_cluster_core_check.csv)
  C2, C3, C5: yes. Most top-10 terms of the all-gene analysis stay
              significant with high-confidence genes only (C2, C5: 10/10
              GO BP, Reactome, Hallmark; C3: 10/10 GO BP, 8/10 Reactome).
  C1:         only partly. 8/10 top GO BP terms (immune) survive, but with
              just 47 core genes the Hallmark/KEGG/Reactome terms do not.
  C4:         too weak to judge (few terms either way).
  => Statements about C2, C3 and C5 biology are robust; C1 is supported
     at the level of "immune activation" (GO BP); C4 has no clear theme.

FILES
  task4_significant_counts.csv        the counts table above
  task4_top_pathways_per_group.csv    top 10 terms per group x database,
                                      with genes responsible
  task4_all_significant.csv           every FDR < 0.05 term, all groups
  task4_cluster_core_check.csv        all-gene vs high-confidence comparison
  task4_heatmap_hallmark.png          combined heatmap: all significant
                                      Hallmark processes x groups
  task4_heatmap_go_bp.png             combined heatmap: top 5 GO BP per group
  task4_heatmap_reactome.png          combined heatmap: top 5 Reactome per group
  task4_heatmap_kegg.png              combined heatmap: top 5 KEGG per group
  enrichment_tables/<group>__<db>.csv one CSV per enrichment, ALL tested terms
                                      (significant column marks FDR < 0.05)
  dot_plots/dot_<group>.png           top 5 terms per database per group
                                      (x = gene ratio, size = genes,
                                      colour = -log10 FDR)

  Columns: overlap = group genes in the set; set_size = set genes in the
  background; gene_ratio = overlap / group size; bg_ratio = set_size /
  14,794; fold_enrichment = gene_ratio / bg_ratio; genes = responsible genes.
