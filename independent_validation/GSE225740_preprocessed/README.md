# GSE225740: preprocessing for held-out cohort assessment

Preprocessing completed on 7 November 2026. This directory contains prepared expression and sample data, not validation findings. The subsequent source-paper review supports a separately recruited cohort, without definitive identity-level verification; see `cohort_independence_audit.md`. Absence of shared deposited identifiers alone does not establish independence.

## Reproduce

From the repository root, run:

```bash
python independent_validation/scripts/preprocess_gse225740.py
```

Requires Python with NumPy and pandas; exact executed versions and input/script SHA-256 hashes are in `preprocessing_summary.json`. Re-running rewrites only this generated output directory. Deposited source files remain in `../candidate_screening_2026-11-07/GSE225740/`.

## Procedure and decisions

1. Read the deposited 19,101-by-93 integer count matrix. Verify unique raw gene IDs, unique patient columns, finite nonnegative integer values and positive per-sample count totals. No missing values, duplicate gene IDs or identical expression columns were found.
2. Match all 93 matrix columns exactly to the phenotype table's patient IDs and the GEO metadata's description field. Check fibrosis, NAS and steatohepatitis fields agree between sources. Deposited technical replicates were already aggregated by the submitter; do not aggregate again. There are 93 unique recorded patient IDs, not independent confirmation of 93 unique people across publications.
3. Retain all 93 samples in the metadata. Exclude six with missing fibrosis stages only from stage-based matrices. The 87 eligible staged samples are F0=27, F1=26, F2=15, F3=13 and F4=6. Do not infer their missing stages from NAS or diagnosis.
4. Compute per-sample totals using all 19,101 deposited genes before any mapping. These are sums of the deposited count matrix, not verified sequencing-library read totals: low/unreported genes may have been filtered before deposition. The submitter's FASTQ files are unavailable.
5. Map Entrez IDs using the existing discovery project's retained `data/processed/gene_id_map.csv`. Use only unambiguous Entrez-to-Ensembl mappings. There were 17,917 mapped genes, no ambiguous mappings among measured genes and no mapping collisions. The 1,184 unmapped genes remain in the complete Entrez expression matrix, raw source file, mapping audit and normalization denominators; they are excluded only from Ensembl-indexed outputs. This is reuse of the retained mapping, not a claim to use a newly downloaded/current HGNC release.
6. Compute log2(CPM + 1), with CPM = deposited count / all-deposited-gene sample total × 1,000,000. Mapping collisions, if encountered in another input, would be summed before logarithms. This transformation follows `build_graph_all.py` for count inputs and is not DESeq2/RLE normalization or batch correction.
7. Calculate within-cohort gene z scores over all 93 deposited samples, using sample SD (ddof=1), before selecting the 87 staged samples. This matches the discovery workflow's study-level standardization order. Constant genes receive zero standardized values and retain a nonconstant flag; zero values must not be interpreted as evidence of no association. No discovery expression values enter this normalization.
8. Retain all mapped genes; do not filter genes or exclude samples based on outcome associations. `gene_qc.tsv.gz` records zero fractions, counts of staged samples with CPM ≥1, and whether expression varies across staged samples. These are descriptive diagnostics, not thresholds or validation outcomes.
9. Extract the existing fixed 23-gene shortlist by its original Ensembl IDs, preserving its order and identity. All 23 map and vary across the 87 staged samples. HTR7 reaches CPM ≥1 in only one staged sample and CACNA1C in eight; retain and disclose their low expression, and define any later testability/sensitivity rules before association testing. No shortlist gene was replaced or dropped.

## Output guide

- `sample_metadata_all.tsv`, `sample_metadata_staged.tsv`: all 93 and staged 87 samples.
- `samples_excluded_from_stage_analysis.tsv`: six missing-stage records and reasons.
- `sample_qc.tsv`: deposited-count totals, detected-gene counts, mapping fractions and duplicate-profile flags.
- `gene_mapping_audit.tsv.gz`, `gene_qc.tsv.gz`: mapping and expression-quality audit.
- `log2cpm_all_entrez_93.tsv.gz`: all deposited genes and 93 samples.
- `counts_mapped_staged_87.tsv.gz`, `log2cpm_mapped_staged_87.tsv.gz`, `zscore_mapped_staged_87.tsv.gz`: Ensembl-indexed staged matrices.
- `shortlist23_log2cpm_staged_87.tsv`, `shortlist23_zscore_staged_87.tsv`, `shortlist23_availability_qc.tsv`: fixed shortlist expression and descriptive availability.
- `preprocessing_summary.json`: dimensions, stage counts, QC, methods, versions and input hashes.

Preprocessing itself does not calculate association p-values, reproduction rates or stage-transition effects. The subsequent fixed-shortlist association analysis is documented separately in `../GSE225740_validation/README.md`. The discovery graph, original analyses and manuscript are unchanged.
