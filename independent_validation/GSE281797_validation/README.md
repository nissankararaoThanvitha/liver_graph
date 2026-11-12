# GSE281797: second held-out cohort assessment (F0–F3 only)

Completed 7 November 2026. This is a separate replication analysis with fixed original genes, tiers and cluster memberships. No discovery results, graph, manuscript, branch, commit or release was changed. The first validation cohort remains separately documented.

## Cohort suitability and independence

The [source paper](https://elifesciences.org/articles/109534), Overview and Ethics, describes Australian recruitment at The Avenue, Cabrini and Alfred Hospitals. The parent clinical cohort has 109 individuals; the deposited transcriptomic data used here contain 94 samples. The clinical provenance differs from the original eight cohorts and the Indiana GSE225740 cohort. Recruitment differences and deposited identifiers support separate cohorts, but cannot definitively establish patient identity non-overlap.

`deposited_identifier_overlap.tsv` records comparisons against all eight original accessions and GSE225740. GSE281797 has 94 GSM, 94 BioSample and 94 SRA experiment identifiers; no intersections were found with those available for the eight original studies. GSE225740 has 93 different GSMs but no public BioSample/SRA experiment IDs, so its latter two comparisons remain unassessable. No authors were contacted or donor-genotype matching performed.

All 94 samples have stages: F0=42, F1=26, F2=20, F3=6, F4=0. Diagnoses are MASL=53, MASH=11 and No Pathology=30. Six No Pathology samples carry deposited F1; diagnosis and histology fields were retained separately without forcing stage values. The pre-specified MASL/MASH-only sensitivity subset has 64 samples (18/20/20/6 across F0–F3).

## Preprocessing

- The deposited matrix has 60,668 rows and 94 columns, with no missing or negative values. Its 351,075 fractional entries were retained as estimated counts; they were not rounded to integers. The source reports RSEM quantification.
- Library denominators are totals of all deposited rows before identifier handling, following the discovery order. These are deposited count totals, not verified raw sequencing read counts.
- Removed 45 _PAR_Y rows from mapped expression, stripped Ensembl versions and retained 60,623 canonical gene identifiers without additional collapses. Retained all-zero genes in QC; constant genes are untestable, not zero-effect findings.
- Used log2(CPM+1) and per-gene cohort z scores over all 94 samples, ddof=1. No discovery expression data, batch correction, new clustering, expression-prevalence filtering or automatic outlier exclusions. All samples matched uniquely to GEO metadata by S-number keys.
- `preprocessed/` contains the normalized matrices, metadata, sample/gene QC and identifier audit. These are computational preprocessing checks, not full FASTQ quality control. The deposited TPM file was not treated as an independent dataset or selected as an alternative based on desired associations.

## Fixed gene-association results

Two-sided Spearman tests compare expression with the observed F0–F3 severity range. The shortlist and Tier 1 correction families are separate; concordant significance requires the original rho sign and within-family BH q<0.05.

| Population | Gene family | Testable | Same direction | Concordant significant | Opposite significant |
|---|---|---:|---:|---:|---:|
| Primary: all 94 | Shortlist | 23 | 21 | 14 | 0 |
| Primary: all 94 | Tier 1 | 447 | 399 | 161 | 4 |
| Sensitivity: MASLD-only 64 | Shortlist | 23 | 21 | 13 | 0 |
| Sensitivity: MASLD-only 64 | Tier 1 | 447 | 402 | 164 | 1 |

In the primary shortlist, CACNA1C and NFASC have opposite signs, neither significant. Of the remaining 21, seven do not meet corrected significance. All rows are preserved, including nonsignificant/discordant findings. Four primary Tier 1 genes have opposite significant associations: LIPG, SLC4A10, HEYL and JUN. Do not report all Tier 1 genes as validated.

The complete 3,845-gene family contains 3,842 testable genes; GSTA5, OR13C3 and HIGD1C are present but constant. The full-family q values are also provided and must not be mixed with shortlist/Tier 1 q values.

Across the two cohorts, 12/23 shortlisted genes have concordant significant primary associations in BOTH datasets, using each cohort's separate 23-test family. `shortlist23_two_cohort_comparison.csv` gives every gene, including genes significant in only one cohort. This is an intersection of separate tests, not a combined meta-analysis or a new shortlist. The cohorts cover different stage ranges (F0–F4 versus F0–F3), so differences in replication cannot be attributed solely to quality or power.

Descriptive QC flags differ by cohort: CDC45 reaches CPM>=1 in zero GSE281797 samples, TREM2 in six, and PLPP4 in 13. These genes were retained without outcome-based filtering. The first cohort's low-expression flags are not assumed to apply identically here.

## Frozen cluster patterns over F0–F3

| Cluster | Testable / original genes | Four-stage centroid shape r | Patient-score rho | Patient-score BH q (five tests) |
|---|---:|---:|---:|---:|
| C1 | 857 / 857 | 0.940 | 0.410 | 0.000099 |
| C2 | 1,367 / 1,367 | 0.992 | 0.262 | 0.0135 |
| C3 | 226 / 226 | 0.894 | 0.429 | 0.000081 |
| C4 | 397 / 397 | 0.428 | -0.053 | 0.614 |
| C5 | 995 / 998 | 0.896 | -0.278 | 0.0110 |

Centroids are compared using the same testable members and the original profiles truncated to F0–F3. Their four stage means are independently centred/scaled for shape visualization. These descriptive correlations do not formally validate the original five-cluster solution. C4 has fluctuating means, limited shape agreement and no supported monotonic score association. The other observed-range patterns agree more closely, but C2's defining F3–F4 change and C3's later plateau cannot be confirmed without F4. The cluster score is the equal-weight mean within-cohort z score; tests use patients, not genes, as units. Pointwise within-stage bootstrap intervals for raw mean scores are retained (2,000 draws, seed 20261110).

## Limitations and outputs

This is cross-sectional, unadjusted association replication, not within-patient progression, causal inference or therapeutic validation. F3 has six samples and F4 is absent. Clinical covariates are preserved in metadata, but covariate-adjusted associations were not run; primary analysis matches the previous validation approach. The pre-specified MASLD-only sensitivity is reported separately and does not replace the primary cohort definition.

- `shortlist23_primary_all94.csv`, `Tier1_primary_all94.csv`: fixed primary gene results.
- `shortlist23_sensitivity_MASLD64.csv`, `Tier1_sensitivity_MASLD64.csv`, `all3845_MASLDonly_64_sensitivity.csv`: complete sensitivity results, summarized in `gene_replication_summary.csv`.
- `all3845_primary_94.csv`: full fixed-master primary results, including untestable genes.
- `fixed_clusters_F0_F3.csv`, `fixed_cluster_stage_profiles_F0_F3.csv`, `fixed_cluster_patient_scores.tsv`: cluster results, stage means/intervals and patient scores.
- `shortlist23_stage_profiles_F0_F3.csv`: observed-stage shortlist means; no F4 extrapolation.
- `fixed_clusters_F0_F3.pdf`, `shortlist23_comparison.pdf`: vector figures, with PNG previews.
- `summary.json`: executed versions, input/script hashes and summary counts.

Run from the repository root:

```bash
python independent_validation/scripts/validate_gse281797.py
```

Requires NumPy, pandas, SciPy and Matplotlib; executed versions are recorded. Re-running rewrites this cohort's generated outputs. Checks independently recalculated all 3,842 primary correlations/p-values and manual BH for each family; metadata and matrix alignment were checked and both plots visually inspected. No analysis from the new cohort was used to rescore original genes or select a preferred population definition.
