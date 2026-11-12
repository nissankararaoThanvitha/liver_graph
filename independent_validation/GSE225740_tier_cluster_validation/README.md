# GSE225740: frozen-tier and cluster assessment

Completed 7 November 2026. No gene tiers, cluster assignments, shortlist, discovery files, graph or manuscript were changed. The analysis specification is retained in `../GSE225740_validation/tier_cluster_analysis_plan.md`; the previously completed 23-gene analysis remains separate.

## Tier 1 primary result

Of the original 447 Tier 1 genes, 445 mapped to the validation data and were nonconstant across the 87 staged samples. APOBEC3H (retained Entrez ID 164668) and SLC4A3 (6508) were unavailable: neither retained Entrez identifier occurs in the deposited matrix. They were not tested and must not be counted as nonsignificant biological findings.

Using the 445-test Tier 1 BH family:

| Outcome | Genes |
|---|---:|
| Same direction and BH q<0.05 | 387 |
| Same direction, not significant | 52 |
| Opposite direction, not significant | 6 |
| Opposite direction and significant | 0 |
| Untestable | 2 |

Thus 439/445 (98.7%) had concordant signs, and 387/445 (87.0%) had concordant significant associations. This is replication of unadjusted cross-sectional stage associations, not independent confirmation of every component of the P/T/X/F/B score.

## Fair comparison across tiers

To compare tiers using the same multiple-testing burden, a separate common BH family includes all 3,726 testable genes among the original 3,845. The rates below therefore differ from the Tier 1-only primary rate; do not mix denominators or quote 379 and 387 interchangeably.

| Frozen tier | Testable / original | Same direction | Same direction and common-family q<0.05 |
|---|---:|---:|---:|
| Tier 1 | 445 / 447 | 439 / 445 (98.7%) | 379 / 445 (85.2%) |
| Tier 2 | 1,373 / 1,403 | 1,271 / 1,373 (92.6%) | 855 / 1,373 (62.3%) |
| Tier 3 | 1,908 / 1,995 | 1,502 / 1,908 (78.7%) | 841 / 1,908 (44.1%) |

There were 0, 1 and 25 opposite-direction significant associations in Tiers 1, 2 and 3 respectively under the common family. The higher tier has greater observed replication, supporting the prioritisation descriptively. These are not randomized or matched tier groups; the result is not proof of calibrated predictive performance or a formal comparison adjusted for differences in original association strengths and expression levels.

## Fixed-cluster patterns

All original memberships were retained. Centroids compare the same measured/testable members in discovery and validation. No reclustering, cluster-number selection or ARI was performed.

| Cluster | Testable / original genes | Centroid shape correlation (five stages) | Interpretation |
|---|---:|---:|---|
| C1 | 845 / 857 | 0.960 | Similar overall increasing shape; exact transition timing is not confirmed |
| C2 | 1,321 / 1,367 | 0.991 | Very similar overall shape, including the prominent late rise |
| C3 | 213 / 226 | 0.743 | Partial shape agreement: the original rise/plateau differs from the validation late increase |
| C4 | 393 / 397 | -0.307 | Original decreasing centroid was not reproduced clearly; validation is fluctuating |
| C5 | 954 / 998 | 0.907 | Broadly similar decreasing shape, with an intermediate-stage difference |

Shape correlations are descriptive correlations of five mean values, not patient-level significance tests or proof of five-cluster reproduction. Each centroid is separately centred/scaled for the shape figure, so the plot is not comparing absolute expression magnitudes. Strong association of a cluster score with stage does not establish a particular nonlinear shape.

The patient-level fixed-cluster scores (equal-weight mean within-cohort gene z scores) had Spearman rho of 0.483, 0.518, 0.451, -0.047 and -0.223 for C1–C5 respectively; corresponding BH q across five scores was approximately 0.000005, 0.000001, 0.000019, 0.669 and 0.047. C4 has no supported monotonic score association; C5's is weaker despite its broadly similar five-stage mean shape.

## Limitations and reproducibility

- Stage counts are 27, 26, 15, 13 and 6 for F0–F4. Small F4 n and unequal stage sizes limit pattern precision. Pointwise within-stage patient-bootstrap intervals (2,000 resamples; seed 20261109) for unscaled validation centroid means are in `fixed_cluster_profiles.csv`; they are not simultaneous or equivalence intervals.
- HTR7/CACNA1C remain flagged for low expression. No expression-prevalence filter was selected after observing associations.
- The cohort-provenance review supports separate recruitment, but donor identity non-overlap cannot be definitively verified. No age/sex/BMI adjustment was possible from the deposited phenotype file. No causal, longitudinal, drug-efficacy or clinical-prediction validation was performed.
- For every original gene, `all3845_validation.csv` records availability and outcomes, including opposite and nonsignificant results. `tier1_all447_validation.csv` preserves all 447 original rows.
- `tier_comparison_common_family.csv`, `fixed_cluster_summary.csv`, `fixed_cluster_profiles.csv` and `fixed_cluster_patient_scores.tsv` contain the supporting summaries and patient-level scores.
- `fixed_cluster_shapes.pdf` and `tier_replication_comparison.pdf` are vector figures; PNG files are previews.
- `summary.json` records exact versions and input/script hashes.

Reproduce from the repository root with:

```bash
python independent_validation/scripts/validate_tiers_clusters_gse225740.py
```

Verification: independently recalculated all 3,726 associations with SciPy Spearman, manually checked BH for both 445-test and 3,726-test families, confirmed the previous 23 rho values were unchanged, and verified all five patient-level cluster tests. Both figures were visually inspected. Re-running rewrites generated expanded-validation outputs only.
