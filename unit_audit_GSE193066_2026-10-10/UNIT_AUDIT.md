# GSE193066 expression-unit audit

10 October 2026. This audit resolves the deposited units and checks the implemented transformation. Disease labels remain unchanged as requested. Active expression CSVs, analysis results and graph relationships were not modified.

## Finding

The deposited GCT is **DESeq2 RLE-normalised gene counts on a linear count-like scale**, not raw integer read counts, TPM or an already log-transformed matrix. The earlier `unknown` annotation reflects an incomplete provenance check; the depositor explicitly states the normalisation in GEO's data-processing fields.

Primary source: [GEO sample processing record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM5772654), Data processing and Supplementary_files_format_and_content. A first-biopsy record gives the same processing description: [GSM5772567](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM5772567). Fresh downloaded series metadata retain these fields in source_processing_fields.json.

Source context: [GSE193066](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE193066), tissue validation set1 in Fujiwara et al., Science Translational Medicine2022, DOI10.1126/scitranslmed.abo4474, PMID35731891, PMC9236162. It comprises106 patients and164 biopsies, including58 follow-ups in a selected high-risk group. This is source study context, not a new drug/clinical validation result for this project.

## Important terminology

RLE means Relative Log Expression **normalisation**. The name does not mean that the exported values have already undergone a log2 transformation. DESeq2 normalised counts are scaled counts; rlog/vst are different transformation operations. [Official DESeq2 documentation](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html), section on normalised counts and design variables.

## Downloaded matrix inspection

- File:GSE193066_NAFLD.HUn164.gct.gz, GCT version1.2.
- Declared and parsed dimensions:17,231 genes×164 samples.
- Non-numeric gene_id annotation column was excluded, matching the existing parser's numeric-column selection; it is not an expression sample.
- Values range0 to2,724,768.59; no negatives.
- Approximately90.34% of entries are non-integer; about9.66% are zeros.
- Deposited column sums range12,095,296.01 to20,542,686.84, median15,510,132.14. This is not a TPM table with sums near1million.

These numeric properties corroborate the source description of linear normalised counts. Distribution inspection alone would not identify RLE; that identification comes from the depositor.

Sources: downloaded GCT, source_manifest.json checksums and matrix_checks.json.

## What the existing project does

parse_expression.py marks GSE193066 as unit=`unknown`. build_graph_all.py treats every non-TPM input using:

1. Total deposited values per sample, before gene mapping/filtering.
2. Sum raw identifiers mapping to one Ensembl gene.
3. Rescale each mapped value by that sample total to1million, then log2(value+1).
4. Standardise each gene across the study's164 samples to mean0/sample SD1; fill undefined SD with0.

The source is already normalised, so this is **a further CPM-style rescaling of the deposited RLE counts**. It is a distinct normalisation choice and should not be described as simply preserving the depositor's RLE values.

All2,426,216 recovered eligible-gene/sample value_z records for GSE193066 were independently recomputed from the downloaded GCT, current gene map and sample crosswalk. Maximum absolute difference from active CSVs:3.153×10^-14. Thus the numerical transformation was reproduced; this does not certify that it is the preferred biological normalisation.

## Why this is not automatically an invalid double-log procedure

The matrix is on a linear count-like scale, so the log2(+1) step is not logging an already log-transformed matrix.

Under the usual one-size-factor-per-sample model, if deposited normalised count x_ij=c_ij/s_j, then:

x_ij / sum_i(x_ij) = c_ij / sum_i(c_ij).

Therefore a CPM-style rescaling cancels the source sample factor and changes the normalisation to a matrix-total/compositional scale. This is a conditional mathematical explanation, not recovery of unprovided raw counts or size factors. The denominator here is the deposited gene matrix, not proof of a complete original sequencing-library total.

Gene-wise z-scoring cannot undo arbitrary sample-specific factors, so it does not prove the two normalisations yield identical results.

## Descriptive comparison of sample rankings

Without rerunning discovery, compare within-gene sample ranks under current log-CPM-style processing versus log2(deposited normalised count+1):

- Across17,164 mapped canonical genes, median rank correlation is0.9667.
- The10th percentile is0.8855; minimum0.5964.
-2,356 genes have rank correlation below0.9.
- Among3,688 current fibrosis-associated genes,277 are below0.9.
- Across current top25 genes, correlations range0.8595–0.9972.

These are descriptive rank comparisons over all164 source biopsies, not fibrosis-stage correlations, hypothesis tests, final gene-list changes or patient-level sensitivity results. Preserve the corrected biopsy policy in any later method comparison. A ranking difference neither proves an existing finding wrong nor proves its final selection unchanged.

Artifacts:normalisation_rank_comparison.csv,shortlist_rank_comparison.csv,sample_column_sums.csv and matrix_checks.json.

## Recommended resolution

The input-unit question is resolved. A remaining method question is whether the manuscript should retain the implemented matrix-total/CPM-style scale or preserve the deposited RLE normalisation.

Before changing active results, run a separately labelled sensitivity comparison that changes only GSE193066's transform to log2(deposited RLE counts+1), followed by the same study/gene standardisation and shared biopsy policy. Keep all other cohorts, disease labels, eligibility, scoring, clustering and subgraph selection rules fixed. Compare per-study fibrosis correlations, selected genes, stage profiles, Tier1 and top25.

Do not select a method because it preserves preferred candidate genes. Choose a scientifically justified method with mentor/statistical review and document any differences. If the implemented approach is retained, describe its transformation exactly and correct the unit/provenance annotations.

This audit has not selected a replacement normalisation or altered the live graph. Original source size factors/raw count exports and exact preprocessing scripts were not retrieved; fresh metadata explicitly establish RLE and the available matrix supports direct sensitivity analysis.

## Source availability

GCT and series metadata downloaded successfully. Paper full-text XML retrieval through Europe PMC returned HTTP500; the indexed primary article was readable through web search. The input-unit conclusion does not depend on that failed XML request because the fresh GEO processing fields and actual matrix were directly inspected.
