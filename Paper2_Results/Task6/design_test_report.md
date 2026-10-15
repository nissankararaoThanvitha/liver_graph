# Task 6 design test run (equal weights)

> **Design test with equal weights (0.2 each).** After Paper 1 was confirmed final, equal weights were frozen for the final ranking; the final, stability-checked results are in `Final_ranking/`.

Gene set: corrected Paper 1 union of **6,222 genes** (the plan's 4,692 was the pre-correction count). Script: `Paper2_Results/code/task6_target_score_prototype.py`.

## Did it run?
Yes. All five components are in [0, 1] for all 6,222 genes, with no missing values after the documented rules. Paper 1 `n_databases` is reproduced for 99.2% of fibrosis genes by the B input (from the Task 5 prep term lists).

## Component distributions
| index | mean | 50% | min | max | share of genes = 0 |
|---|---|---|---|---|---|
| P | 0.523 | 0.471 | 0.156 | 1.0 | 0.0 |
| F | 0.519 | 0.667 | 0.0 | 1.0 | 0.382 |
| T | 0.35 | 0.381 | 0.0 | 0.993 | 0.382 |
| K | 0.044 | 0.0 | 0.0 | 0.898 | 0.829 |
| B | 0.206 | 0.0 | 0.0 | 1.0 | 0.59 |

## Component correlations (Spearman)
| index | P | F | T | K | B |
|---|---|---|---|---|---|
| P | 1.0 | 0.561 | 0.8 | 0.073 | 0.54 |
| F | 0.561 | 1.0 | 0.728 | 0.047 | 0.51 |
| T | 0.8 | 0.728 | 1.0 | 0.064 | 0.619 |
| K | 0.073 | 0.047 | 0.064 | 1.0 | 0.214 |
| B | 0.54 | 0.51 | 0.619 | 0.214 | 1.0 |

## Ablation (drop one component; remaining weights renormalised)
| variant | spearman_vs_full | kendall_vs_full | top50_overlap | median_abs_rank_shift | shortlist_median_rank | shortlist_in_top_500 |
|---|---|---|---|---|---|---|
| full (equal weights) | 1.0 | 1.0 | 50 | 0.0 | 247.0 | 18 |
| without P | 0.9594 | 0.8384 | 40 | 372.0 | 451.0 | 13 |
| without F | 0.9881 | 0.9324 | 34 | 240.0 | 146.0 | 19 |
| without T | 0.9852 | 0.9167 | 34 | 70.0 | 293.0 | 17 |
| without K | 0.9875 | 0.9469 | 24 | 99.5 | 249.0 | 16 |
| without B | 0.9552 | 0.8589 | 29 | 139.0 | 239.0 | 18 |
| without K and B | 0.9302 | 0.8045 | 10 | 247.0 | 389.0 | 14 |

## Weight sensitivity (Dirichlet, 1,000 draws, seed 42)
| dirichlet_alpha | draws | median_spearman_vs_equal | p05_spearman_vs_equal | median_top50_overlap | genes_in_top50_in_>=80%_of_draws | genes_ever_in_top50 |
|---|---|---|---|---|---|---|
| 1.0 | 1000.0 | 0.9669 | 0.9055 | 28.0 | 7.0 | 408.0 |
| 10.0 | 1000.0 | 0.9958 | 0.9844 | 41.0 | 29.0 | 173.0 |

α = 1: weights anywhere on the simplex (stress test). α = 10: weights near equal (plausible range).

## λ sensitivity (P scale for inflammation-only genes)
| lambda_inflammation_only | spearman_vs_full | top50_overlap | inflammation_only_in_top50 |
|---|---|---|---|
| 0.0 | 0.9765 | 50.0 | 0.0 |
| 0.5 | 1.0 | 50.0 | 0.0 |
| 1.0 | 0.9992 | 50.0 | 0.0 |

## Sanity check against Paper 1
Spearman between this prototype score and Paper 1's HighConfidenceScore (fibrosis genes): **0.871**. Expected to be positive but not 1: P, T and B reuse Paper 1 evidence (partly circular), while K is new and F is graded differently.

## First 10 genes under equal weights (design test; see Final_ranking/ for the final lists)
| Gene | progression_class | trajectory_cluster | P | F | T | K | B | TargetScore_equal_weights |
|---|---|---|---|---|---|---|---|---|
| BCL2 | fibrosis_only | C2 | 0.845 | 1.0 | 0.873 | 0.789 | 0.997 | 0.901 |
| CACNA1C | fibrosis_only | C2 | 0.982 | 1.0 | 0.867 | 0.8 | 0.787 | 0.887 |
| SRC | fibrosis_only | C1 | 0.908 | 1.0 | 0.817 | 0.706 | 0.998 | 0.886 |
| EPHA2 | fibrosis_only | C2 | 0.829 | 1.0 | 0.956 | 0.61 | 0.987 | 0.876 |
| PDGFRA | fibrosis_only | C2 | 0.973 | 1.0 | 0.816 | 0.718 | 0.864 | 0.874 |
| PIK3CG | fibrosis_only | C1 | 0.881 | 1.0 | 0.699 | 0.661 | 0.995 | 0.847 |
| PDGFRB | shared | C1 | 0.891 | 0.667 | 0.84 | 0.8 | 0.981 | 0.836 |
| ALDH2 | fibrosis_only | C5 | 0.936 | 1.0 | 0.729 | 0.56 | 0.938 | 0.833 |
| CXCR4 | shared | C2 | 0.979 | 0.667 | 0.856 | 0.681 | 0.98 | 0.833 |
| DPYD | fibrosis_only | C5 | 0.897 | 1.0 | 0.784 | 0.67 | 0.794 | 0.829 |
