# GSE281797 second-cohort validation plan

Recorded before fibrosis-association tests in this cohort on 7 November 2026. Previous GSE225740 outcomes are known; this is not preregistration.

## Recruitment and eligible population

Source: Zhao et al., eLife, https://elifesciences.org/articles/109534, Overview of study, transcriptomics and Ethics. The parent cohort comprises 109 obese individuals recruited before bariatric surgery at The Avenue, Cabrini or Alfred Hospitals in Melbourne, Australia. The deposited RNA-seq matrix covers 94 samples, not all 109 individuals. Source protocols include Melbourne ethics ID 1851533 and hospital-specific approvals. Clinical collection differs from the documented discovery cohort sources (Denmark, VCU, European EPoS, MGH/Bon Secours, Japan, Netherlands, Vanderbilt) and the Indiana GSE225740 cohort. See GSE225740's prior independence audit for the original source comparisons. Distinct recruitment is supported, not identity-level proof.

Primary population: all 94 deposited samples with observed F0–F3 (42/26/20/6), including 30 labelled No Pathology, 53 MASL and 11 MASH. Preserve diagnosis and stage separately: six No Pathology samples have a deposited F1 grade; do not silently re-label or force F0. Predefined secondary population: 64 samples labelled MASL/MASH only (F0=18, F1=20, F2=20, F3=6), to assess whether results depend on including the No Pathology group. Report this separately, not as a replacement selected by outcome. No F4 inference, no F3–F4 test.

## Preprocessing

Use deposited GeneCount matrix as fractional estimated count values without rounding. Check finite/nonnegative data, sample keys, duplicates and zero totals. Compute normalization totals over ALL deposited rows, as in the discovery code. Drop _PAR_Y rows from gene mapping to avoid duplicate biological genes, strip Ensembl version suffixes, sum any remaining rows mapping to the same canonical Ensembl ID before log. Preserve all-deposited-row denominator; explicitly report mapping exclusions. This is a replication of the discovery order, not a claim that duplicate PAR rows are unique sequencing reads. All-zero genes remain documented but are untestable.

Apply log2(CPM+1), then within-cohort gene z scores over all 94 samples (ddof=1). Independent primary normalization uses no discovery samples. Gene identifiers are aligned directly by version-free Ensembl IDs to fixed master/shortlist IDs. Reuse retained symbol annotations where available; do not invent annotations for newly seen Ensembl IDs. Do not use the deposited TPM matrix as another independent cohort or choose normalization based on desired results. No low-expression exclusion or automatic outlier removal; preserve diagnostic flags.

## Fixed gene and cluster endpoints

- Use the unchanged original 23-gene shortlist, 447 Tier 1 genes and 3,845 cluster genes.
- Two-sided Spearman against F0–F3; BH separately across the testable shortlist, Tier 1 and full 3,845 families. Report testable denominator, sign concordance, concordant significant, opposite significant and nonsignificant outcomes. These are different multiplicity families. No rho>=0.3 cutoff is added. Missing/unvarying genes are untestable, not failed significance.
- Perform the same separately labelled gene association checks in the fixed MASL/MASH-only subset, with BH within each testable subset/family. Do not change primary findings based on sensitivity results.
- Keep original cluster memberships. Compare original centroid restricted to F0–F3 with validation means for the same measured/nonconstant member genes. Standardize each four-stage centroid separately for descriptive shape display; Pearson correlation of four means is not a formal pattern-equivalence test. Never extrapolate F4. Especially C2's defining F3–F4 late increase cannot be checked in this cohort.
- Test mean gene-z cluster scores against stage using patients as units; BH across five cluster scores. A score association is not confirmation of a specific nonlinear shape.
- Raw mean validation cluster-score stage intervals: 2,000 within-stage patient bootstraps, seed 20261110; pointwise, not simultaneous. Small F3 n=6 limits precision.
- No new tier scores, clustering, pathway tests, transition map or manuscript/graph changes in this task. Primary tests match prior validation; no experimental, causal or longitudinal claims.
