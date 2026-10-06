TASK 1 -- Progression genes divided into groups
===============================================

Source: genes_by_fibrosis_stage.csv (4,692 progression genes)

FILES
  task1_summary.csv               counts and % for each group, split up/down
  task1_venn.png                  overlap of fibrosis vs inflammation genes
  task1_shared_rho_scatter.png    fibrosis rho vs inflammation rho, shared genes
  task1_top20_fibrosis_genes.csv  top 20 positive and top 20 negative
                                  fibrosis-associated genes

KEY RESULTS
  Fibrosis-only       1,953 (41.6%)   up 1,301 / down 652
  Inflammation-only   1,047 (22.3%)   up 597   / down 450
  Shared              1,692 (36.1%)   up in both 1,335 / down in both 356
                                      discordant: 1 gene (GPD1)

  Shared genes, Spearman correlation of fibrosis rho vs inflammation rho:
    all shared genes     rho = 0.725  (p = 2.9e-276)
    up genes only        rho = 0.453  (p = 1.3e-68,  n = 1,335)
    down genes only      rho = 0.354  (p = 6.0e-12,  n = 356)
  The overall 0.725 is partly driven by the two separate up/down clouds;
  the within-direction values are the more conservative estimate.

  Positive = expression increases with disease severity.
  Negative = expression decreases with disease severity.
