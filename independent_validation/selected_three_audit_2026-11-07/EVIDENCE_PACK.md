# Audit of the three selected validation cohorts

Completed 7 November 2026. Scope: GSE225740, GSE213621 and GSE268273. Source expression was downloaded from GEO and analysed locally; the friend's supplied code/results, original discovery outputs, prior validation folders, live graph and manuscript were preserved. No commit, push or branch creation.

## Confirmed computational findings

All 3,845 frozen gene IDs, original symbols, tiers, clusters, original directions, fibrosis rho values and largest-transition labels agree between the supplied package and the discovery files. All source sample columns match clinical metadata bijectively. No nonfinite expression values or identical complete expression profiles were detected.

| Dataset | Source columns | Eligible patients | Deposited stage groups | Testable eligible universe |
|---|---:|---:|---|---:|
| GSE213621 | 368 | 299 | F0–F1:97; F2:107; F3–F4:95; 69 controls excluded | 13,358 |
| GSE225740 | 93 | 87 | F0:27; F1:26; F2:15; F3:13; F4:6; six missing-stage observations excluded | 13,790 |
| GSE268273 | 109 | 109 | F0:36; F1:41; F2:13; F3:14; F4:5 | 11,871 |

Source scale handling is supported: log2(FPKM+1) for deposited GSE213621 FPKM; log2(CPM+1) with library total before mapping for GSE225740; deposited normalized voom/log expression for GSE268273, without another count-based normalization. Five duplicate raw symbols in GSE213621 retain the first row as the supplied/discovery parsing policy; there are no duplicated raw rows in the other two. Eleven PAR_Y rows are dropped in GSE268273. Complete source and mapping records are preserved in the downloaded files and audit scripts.

The supplied pipeline was rerun using a separately archived HGNC snapshot. An independent reconstruction checked mapping/aggregation/transformation; each gene's Spearman rho and p-value across each entire testable eligible universe was recalculated using SciPy's scalar implementation, and BH recalculated using SciPy's FDR implementation. For all originally selected testable genes, source rho/p/q matched the friend's CSV within 1e-10 (maximum differences were below 1e-15). Testability sets also match exactly. All five gene-set direction percentages, replication percentages, effect-agreement statistics, score correlations and AUC point estimates match the supplied summary at its recorded precision. Monte Carlo random-set means and bootstrap endpoints may differ slightly with execution order/seed environment, without changing conclusions; stage-direction/replication/score permutation p-values matched in this rerun.

### Primary broad-universe results reproduced

| Cohort | Shortlist testable | Shortlist same direction | Shortlist concordant q<0.05 | Tier-1 testable | Tier-1 same direction | Tier-1 concordant q<0.05 | Opposite significant Tier-1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| GSE213621 | 19/23 | 19/19 | 15/19 | 387/447 | 382/387 | 312/387 | 0 |
| GSE225740 | 23/23 | 23/23 | 19/23 | 445/447 | 439/445 | 367/445 | 0 |
| GSE268273 | 18/23 | 18/18 | 16/18 | 366/447 | 356/366 | 272/366 | 0 |

BH is over each cohort's testable subset of the original 14,794-gene universe. These are computational associations, not proven mechanisms or clinical predictors.

Missing shortlist genes under these mapping/data rules: GSE213621 EPHA3, SULT1E1, KNG1, CYP2C19; GSE225740 none; GSE268273 CDC45, TREM2, HTR7, CACNA1C, PLPP4. Testability does not establish assay sensitivity for every low-expression gene.

### Targeted-family sensitivity, not interchangeable with broad-universe counts

| Cohort | Concordant significant shortlist | Concordant significant Tier-1 | Opposite significant Tier-1 |
|---|---:|---:|---:|
| GSE213621 | 15/19 | 336/387 | 0 |
| GSE225740 | 21/23 | 387/445 | 0 |
| GSE268273 | 17/18 | 295/366 | 1 |

Each fixed gene family is its own BH family here. The additional opposite Tier-1 result is LCP2 (rho −0.204846; targeted q=0.041171, broad q=0.095429). Do not combine targeted counts with broad-universe counts or retain a claim of no opposite genes under every correction scheme. Original GSE225740 targeted results therefore reconcile exactly with the friend's broader-correction results.

## Patient separation and recruitment evidence

Confirmed: compared the three eligible validation populations with each other, all eight discovery accessions, and the earlier GSE281797/GSE49541 validation accessions (36 pairwise records). No shared GSM was found. No shared BioSample/SRA experiment IDs were found where both datasets expose them. GSE225740 and GSE49541 lack those deposited identifiers, which is recorded as unassessable rather than a negative test. Identifiers come only from sample relation records, never platform gene annotation strings.

Primary evidence:

- **GSE213621:** [Chen et al., DOI 10.1016/j.jcmgh.2022.12.008](https://pmc.ncbi.nlm.nih.gov/articles/PMC9957752/), Human Liver Samples: Duke University Health System NAFLD Biorepository, IRB Pro00005368; 368 subjects, 299 NAFLD and 69 controls. The source also studies other species and public cohorts; only the deposited human bulk expression matrix is used here. GSE213623 is the associated superseries, not another independent patient cohort.
- **GSE225740:** [Powell et al., DOI 10.1038/s41467-023-37209-1](https://pmc.ncbi.nlm.nih.gov/articles/PMC10020163/), Patient selection: 93 clinical biopsies, Indiana University IRBs 1506218127 and 1011003025R008. The paper's separate multi-study meta-analysis is not being imported as new patient data.
- **GSE268273:** [García-Nieto et al., DOI 10.1016/j.jhepr.2024.101167](https://pmc.ncbi.nlm.nih.gov/articles/PMC11474426/), Study design/participants and transcriptomic subcohort: Santander/Marqués de Valdecilla study, recruitment described December 2018–December 2019; 69 IMID-associated MASLD and 40 control/classic-MASLD biopsies. Here 'control' means classic MASLD without IMID, not healthy liver. The individual 109 expression columns have deposited biopsy fibrosis labels.

Recruitment differs from that documented for the eight discovery cohorts (see the earlier `GSE225740_preprocessed/cohort_independence_audit.md`). This supports held-out recruitment, but cross-centre sample exchange or re-deposition cannot be definitively excluded without a donor crosswalk or genotype information. In particular GSE213621 and GSE49541 share the Duke biorepository provenance: no shared deposited IDs does **not** resolve whether they contain some of the same donors. GSE49541 is not one of the selected primary three, but must not be counted as definitively independent of GSE213621 if later combined. No authors were contacted.

## GSE268273 clinical heterogeneity checks

The primary article confirms all 109 transcriptomic cases meet MASLD criteria; 69 also have immune-mediated disease. Metadata distinguish IBD (42), psoriasis (14), hidradenitis (9), spondylitis (4), and classic NAFLD/NASH (40). These should not be called autoimmune hepatitis cases or healthy controls.

Independent additional sensitivity analyses, labelled exploratory:

| Population | Patients | Stage n F0/F1/F2/F3/F4 | Shortlist concordant significant, broad BH | Tier-1 concordant significant, broad BH |
|---|---:|---|---:|---:|
| IMID-NAFLD | 69 | 25/28/5/8/3 | 16/18 | 248/366 |
| Classic-NAFLD | 40 | 11/13/8/6/2 | 4/18 | 59/366 |
| Pooled, partial-rank adjusted for IMID status and sex | 109 | 36/41/13/14/5 | 16/18 | 278/366 |

All 18 shortlisted genes agree in direction within each subgroup. There is one opposite broad-significant Tier-1 gene within IMID-NAFLD. The smaller classic subgroup has fewer significant genes; different sample size and biology are possible factors, not demonstrated explanations. Partial rank correlation residualizes expression ranks and stage ranks against an intercept, binary IMID/classic and sex; uses t(df=n−4) and BH over the eligible universe. This is an added sensitivity, not the source paper's limma model and not comprehensive covariate adjustment (e.g. age/BMI/medications). Its p-values use an asymptotic approximation.

## Score/AUC verification and interpretation

Signed mean-z scores use frozen discovery directions, with no stage-based tuning of gene weights or sign selection. AUC is independently verified as P(score in advanced > score in mild), with half credit for ties, matching Mann–Whitney AUC. Separate stratified 2,000-bootstrap CIs were recalculated; their Monte Carlo endpoints are not expected to equal the original 1,000-bootstrap endpoints exactly.

| Cohort | Shortlist AUC | Independent bootstrap 95% CI | Tier-1 AUC | Independent bootstrap 95% CI |
|---|---:|---|---:|---|
| GSE213621 | 0.787629 | 0.720130–0.845147 | 0.820619 | 0.757352–0.876617 |
| GSE225740 | 0.838133 | 0.726887–0.930511 | 0.862959 | 0.763654–0.942403 |
| GSE268273 | 0.861928 | 0.771018–0.940550 | 0.864662 | 0.770284–0.943284 |

AUC uses mild F0–F1 versus advanced F3–F4, excluding intermediate F2. Denominators are 97/95 (GSE213621), 53/19 (GSE225740), and 77/19 (GSE268273). Stage associations use all staged patients; these different denominators must not be confused.

The friend uses population SD ddof=0; discovery `build_graph_all.py` uses sample SD ddof=1. In each cohort every gene has the same sample count, so changing this scales the entire score by one common positive constant and leaves these Spearman/AUC statistics unchanged. Normalization is fitted across all source columns before clinical exclusions, including the 69 healthy controls in GSE213621 and six unstaged samples in GSE225740. As a labelled sensitivity, re-standardizing only eligible staged patients changes shortlist AUC to 0.786218/0.837140/0.861928, respectively: little change here.

These are exploratory cohort discrimination scores, not a deployable classifier: validation-cohort mean/SD parameters are estimated from those same cohort expression profiles, no fixed clinical cutoff or calibration was validated, and no future progression outcome was tested. Bootstrap intervals are conditional on the calculated scores and do not represent independent clinical validation.

## Mapping provenance and reproducibility limitations

The original HGNC file/hash from the friend is unavailable. The nearby CausalKG file was inspected and found to be a different six-column resource, so it was not substituted. A fresh official HGNC complete-set snapshot was downloaded into this audit's source directory and its SHA-256 recorded. It contains 42,637 approved Ensembl-keyed entries versus 42,353 reported in the original run. It maps six extra raw symbol rows in GSE213621 and two extra Entrez rows in GSE225740, outside the testable analysis universe; all selected-gene results and universe sizes remain identical. This supports computational reproduction, but does not recover the historical original file identity or an official release date. Future work can use the newly archived, explicit snapshot.

The source GSE213621 SOFT processing text contains inconsistent mouse/human assembly statements ('mm10', 'hg39'), despite human organism, human gene symbols, human study description and the deposited human FPKM matrix. Do not repeat those assembly claims as verified methods. This audit starts from deposited processed values and does not independently align raw sequencing reads. GSE268273 normalized values likewise cannot reconstruct read-level QC or a raw-count pipeline.

The supplied script has no pinned dependency file or input checksums; a seed alone is insufficient for byte-identical random-set results because gene sets iterate as Python sets. The audit records sources, software, scripts and input hashes; the reproduction command fixes PYTHONHASHSEED=0 and BLAS threads. Independent deterministic scalar statistics provide the main numerical verification. Multiple gene-set permutation tests are exploratory and their p-values are not a separately multiplicity-adjusted confirmatory family. Random expression-matched sets do not additionally match cell type, coexpression, or discovery effect size. Stage permutations preserve gene dependence; that does not automatically prove their direction test is universally conservative.

## Important reporting limitation: cohort selection

These three cohorts were prioritized after their validation performance had already been observed. The audit does not convert that selection into a prespecified systematic search. Report the selection process transparently and do not claim these are an unbiased sample of every eligible cohort or conceal completed weaker adult-cohort results. No combined manuscript tables were created here and no earlier adult results were removed.

## Evidence and files

- `friend_package/`: supplied ZIP contents preserved unchanged; ZIP hash in manifest.
- `sources/`: deposited expression/metadata; official HGNC snapshot; download URLs and hashes.
- `reproduce_friend.py`, `reproduction_current_hgnc/`, `reproduction_run_log.txt`: isolated rerun of supplied code with explicit source paths.
- `audit_selected.py`, `audit_run_log.txt`: independent checks and subgroup/normalization sensitivities.
- `verified/sample_expression_QC.csv`, `stage_counts.csv`, `deposited_identifier_overlap.tsv`, `friend_gene_results_comparison.csv`.
- `verified/gene_set_summary_both_corrections.csv`: broad and targeted BH, including sensitivities; never silently mix columns.
- `verified/score_AUC_verification.csv`: point estimates, independently resampled CIs and normalization sensitivity.
- Full per-gene result and score CSVs include all failures, opposites and missing genes.
- `audit_manifest.json`: SHA-256 and software versions; source dates are retrieval metadata, not official release identifiers.

Reproduction environment: Python 3.12.3, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1; openpyxl 3.1.5 and et_xmlfile 2.0.0 were loaded from an isolated temporary dependency directory. No repository dependency files or existing environment packages were changed. If rerunning elsewhere, install compatible dependencies and update the temporary-dependency search path.

## Direct comparison with our earlier validation process

Completed after the user requested comparison of approaches. `compare_earlier_process.py` applies the earlier frozen discovery identifier map (unique Entrez/current exact symbol; Ensembl IDs version-stripped), original sample eligibility, source-unit-appropriate transformations and scalar two-sided Spearman tests. It reports both targeted and broad-universe BH rather than choosing a method based on its number of significant findings. Duplicate raw IDs follow the same declared discovery keep-first policy for this comparison.

- Every testable shortlisted and Tier-1 gene has the same rho and p under the earlier frozen-map and audited HGNC processes in all three cohorts (maximum absolute differences are numerical precision, below 1e-10). Testability sets and direction counts match.
- Earlier frozen mapping measures 13,107 eligible background genes in GSE213621 versus 13,358 with the archived HGNC mapping. The extra 251 are background genes; original shortlist/Tier-1 coverage is identical. Some other common background genes differ slightly when multiple legacy symbols are recovered/aggregated by HGNC. Therefore do not assert every background correlation is identical: maximum background rho difference is about 0.0163 and p difference 0.1506. The shortlist/Tier-1 comparison remains unchanged.
- GSE225740 and GSE268273 eligible universe sizes and gene statistics agree across the two mappings.
- Targeted BH yields shortlist 15/19, 21/23, 17/18 and Tier-1 336/387, 387/445, 295/366 for GSE213621/GSE225740/GSE268273, respectively. Broad BH yields 15/19, 19/23, 16/18 and 312/387, 367/445, 272/366 under either mapping. Targeted GSE268273 also has one significantly opposite Tier-1 gene (LCP2).

There is no known biological ground truth here that establishes one correction family as 'more accurate.' A larger replication count is not an accuracy estimate. The two families test different scoped hypotheses. For a unified broad validation of all original eligible genes and comparison across tiers, retain broad-universe BH as the main analysis and report fixed-shortlist/Tier-1 targeted BH as a clearly labelled secondary analysis. For future reruns, use the explicit archived HGNC snapshot for consistent mapping and improved documented coverage, without reselecting genes. The previous targeted results remain valid for their stated fixed-family question.

Files: `earlier_process_comparison/summary.csv`, `shared_gene_statistics_comparison.csv`, per-gene comparisons/mapping audits, and `earlier_process_comparison_log.txt`. The comparison does not overwrite primary outputs or manuscript text.
