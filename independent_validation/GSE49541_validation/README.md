# GSE49541: complementary grouped-severity validation

Completed 7 November 2026. The frozen shortlist, Tier-1 assignments, discovery analysis, live graph and manuscript were not changed. This is a third, public-cohort computational assessment, not wet-lab validation.

## Cohort and provenance

- 72 human NAFLD liver biopsies: 40 mild (F0–F1), 32 advanced (F3–F4). Individual stages and F2 are unavailable in the deposited labels.
- [GEO GSE49541](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE49541); [Moylan et al., Hepatology, DOI 10.1002/hep.26661](https://onlinelibrary.wiley.com/doi/abs/10.1002/hep.26661); [PubMed PMID 23913408](https://pubmed.ncbi.nlm.nih.gov/23913408/).
- The primary study describes prospectively collected Duke University Health System NAFLD Biorepository specimens. It distinguishes the 72 analysed discovery patients from a separate 17-patient validation cohort in its own study. Only the deposited 72 expression profiles are used here; the 17 are not added.
- GSE49541 sample records also list GSE31803: these are re-deposited specimens, not independent cohorts.
- No shared GSM with the eight original cohorts or the two analysed validation cohorts. GSE49541 has no sample-relation BioSample or SRA experiment identifiers, so comparisons of those identifiers are unassessable, not negative. Only sample relation fields are searched; platform gene names are excluded.
- Duke recruitment differs from the recruitment sources documented in the earlier provenance audit (Denmark, VCU/HemoShear, European EPoS, MGH/Bon Secours, Japanese cohorts, Dutch centres, Vanderbilt), and from Indiana GSE225740 and Melbourne GSE281797. This supports distinct recruitment but does not prove patient-level nonoverlap; donor genotypes/recruitment crosswalks are unavailable. The VCU/HemoShear collection provenance is less fully documented than other cohorts.

## Input handling

Source files remain in `../candidate_screening_2026-11-07/GSE49541/`. `summary.json` contains their SHA-256 hashes, the fixed gene-list/map hashes, script hash and software versions. `analysis_plan.md` was saved before group statistics, with subsequent numerical audit corrections explicitly marked.

The series matrix contains 54,675 unique probes and 72 unique sample columns; all values are finite, sample titles are unique, and there are no identical complete expression profiles. GEO processing is GC-RMA. Deposited values are already logarithmic (range 2.358–15.556); no second log, CPM, RNA-seq normalization or quantile normalization was applied. Array distributions are in `sample_distributions.pdf` and `preprocessed/sample_qc.tsv`. Raw CEL QC and detection-call analysis were not performed.

GPL570 annotation is embedded in the downloaded family SOFT; its rows show 6 October 2014 annotation dates. This retained table, rather than an invented current annotation version, is identified by the source hash. Probes require a single numeric Entrez ID that maps uniquely to an Ensembl ID in the original discovery gene map. There are 40,525 retained probes, 12,841 without a single Entrez ID, and 1,309 with an unmapped/ambiguous Entrez mapping. The complete audit includes excluded probes. Legacy probe specificity is not established merely by identifier matching.

Primary expression is the arithmetic mean of eligible log-scale probes per gene, with no group-based probe selection. Median of the same probes is a prespecified sensitivity analysis. Genes whose summary is constant (range ≤1e-10) are untestable; the tolerance is far below deposited 0.001 precision. The sensitivity can have more constant genes than the primary mean.

## Statistical analysis

Two-sided Welch tests compare advanced minus mild expression. Pointwise 95% Welch confidence intervals are reported. BH adjustment is separate for the testable shortlist and testable Tier-1 family, and is repeated separately for median sensitivity. Replication requires BH q<0.05 and a difference sign agreeing with the original median fibrosis-stage correlation. This comparison checks broad direction, not equality of effect sizes or stages. No extra minimum effect cutoff was imposed. Analyses are unadjusted; individual confounder adjustment cannot be reconstructed from these deposited covariates.

An independent check recalculated every tested contrast using SciPy Welch tests from the original matrix, recomputed BH manually, and verified all effect sizes, source hashes and unique sample profiles. One group may legitimately have zero variance where the other varies. Direct Welch–Satterthwaite formulas avoid misleading numerical warnings for such groups.

## Results

| Family and summary | Original genes | Testable | Same direction | Concordant q<0.05 | Opposite q<0.05 | Untestable |
|---|---:|---:|---:|---:|---:|---:|
| Shortlist, primary mean | 23 | 22 | 19 | 13 | 0 | 1 |
| Shortlist, median sensitivity | 23 | 22 | 18 | 10 | 0 | 1 |
| Tier-1, primary mean | 447 | 439 | 397 | 220 | 0 | 8 |
| Tier-1, median sensitivity | 447 | 433 | 369 | 175 | 0 | 14 |

Primary shortlist concordant significant genes: **IL32, EPHA3, NFASC, PLPP4, PDGFRA, FABP5, TYMS, OAT, F2, SLC38A4, CYP2C19, ACADSB, MME**.

TAX1BP3 has no eligible uniquely mapped probe. CACNA1C, PLK3 and CDC45 have opposite primary difference signs but are nonsignificant. Primary missing Tier-1 genes: APOBEC3H, GABRE, THSD1, ZC3H12A, PAH, ALKAL1, UBD and TAX1BP3. These are unavailable under the fixed annotation rule, not demonstrated replication failures.

The median sensitivity supports 10 shortlisted genes; EPHA3, PDGFRA and F2 lose significance. A total of 126 mapped Tier-1 genes have eligible probes with both positive and negative group differences, including potentially very small differences. `Tier1_probe_direction_audit.csv` reports all eligible probe effects and floor fractions, and `Tier1_probe_disagreement.csv` flags mixed signs. This warns of probe-summary dependence, not proof that all such genes are unreliable. No best-performing probe or summary was selected after looking at results.

## Interpretation and files

This is partial, cross-platform support for grouped fibrosis-severity associations. It does not validate exact F0–F4 patterns, adjacent-stage transitions, cluster shapes, patient progression, clinical prediction or causal mechanisms. Probe coverage is not equivalent to confirmed transcript detection. No claim that this satisfies a particular journal's independent-validation policy is made.

- `replication_summary.csv`: all primary and sensitivity denominators.
- `shortlist23_primary_mean.csv`, `Tier1_primary_mean.csv`: complete primary results including unavailable genes.
- Corresponding `sensitivity_median.csv` files: sensitivity results.
- `*_probe_coverage.csv`: eligible probe counts.
- `deposited_identifier_overlap.tsv`: all ten accession comparisons.
- `preprocessed/`: metadata, sample QC, mapping audit and gene expression summaries.
- `shortlist23_group_contrast.pdf`: vector plot; PNG preview also supplied.
- Run from the repository root using a Python environment with NumPy, pandas, SciPy and Matplotlib: `python independent_validation/scripts/validate_gse49541.py`.
