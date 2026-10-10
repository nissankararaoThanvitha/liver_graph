# Primary analysis decision — 10 October 2026

## Selection and implementation status

Select `sensitivity_2026-10-10/combined/` with the standard P/T/X/F/B score as the primary exploratory analysis for manuscript preparation. This is a documented methodological selection; it has not yet been promoted to the canonical results, Paper1_Package, or live Neo4j graph. Those still contain the biopsy-corrected baseline. The selected run has completed all analysis stages and passed the comparison checks.

## Evidence-based rationale

1. **Abstain on five ambiguous disease labels.** GSM3758028, GSM3758038, GSM3758039, GSM3758073 and GSM3758074 have no confirmed original sample-level diagnoses and were flagged by the histology audit. Leave their disease_group blank with explicit provenance. Retain their measured histology and fibrosis stages for fibrosis analysis. This is selective abstention, not recovery of correct clinical diagnoses. All remaining GSE130970 disease labels must still be described as derived proxy groups.
2. **Preserve the deposited GSE193066 RLE scale.** The original matrix is linear DESeq2 RLE-normalised expression. Sum mapped aliases, use log2(expression+1), then the existing within-study/gene standardisation with sample SD over 164 biopsies. Avoid adding matrix-total rescaling to this deposited normalisation. This choice preserves the documented source processing; the sensitivity experiment does not establish that it is universally optimal. Other studies retain their existing processing.
3. **Preserve the established analysis and score rules.** Retain the corrected biopsy policy, 14,794-gene eligible universe, k=5, seed42, thresholds, full-universe LOSO correction, Tier1 cutoff7, five-per-cluster quota and twelve-mechanism selection. Retain F in the primary score for continuity of the specified prioritisation scheme. Its dependence on derived disease groups limits specificity interpretation; report the F-removal ablation as sensitivity evidence. B also depends on group enrichment, so removing F does not make the analysis label-independent.

These choices follow provenance and uncertainty handling, rather than whether preferred candidates remain selected. The decision is made after examining sensitivity results and must be described as post hoc; do not imply prospective registration.

## Selected results and wording

| Quantity | Combined standard run |
|---|---:|
| Fibrosis-associated genes | 3,845 |
| Disease-proxy-associated genes | 4,199 |
| Shared selected genes | 1,822 |
| Union | 6,222 |
| Tier1 genes | 447 |
| Balanced shortlist | 23 |
| Baseline shortlisted genes retained | 16 |
| Displayed mechanism genes / mechanisms / edges | 42 / 12 / 154 |
| Shortlisted genes represented in that network | 4 |

One cluster has only three qualifying Tier1 genes. Report an actual 23-gene shortlist; do not relax criteria or keep calling it a top25 result. The 16 genes shared across all four main runs are a sensitivity-stable subset, not independently validated targets.

Primary claims concern cross-sectional fibrosis-stage associations, expression patterns and graph-supported exploratory prioritisation. The disease axis uses derived proxy groups and is secondary contextual evidence. Do not claim clinically confirmed NAFL/NASH classification, fibrosis-specific mechanisms, longitudinal progression prediction, therapeutic direction, predicted effective drugs or demonstrated interruption of disease progression.

## Supporting analyses and manuscript placement

- **Methods:** deposited matrix units, alternate transform, selective abstention with all five accession IDs, unchanged biopsy policy, frozen scoring rules and actual cluster quotas. Explain that method selection followed the audit and sensitivity comparison.
- **Results:** combined standard-run results as primary after promotion; show actual shortlist counts and membership confidence. Distinguish disease proxies from fibrosis stages.
- **Supplement:** all four main runs, gene membership changes, the 16-gene intersection, cluster comparisons, full-universe LOSO and all four F ablations. The combined F ablation produces21 shortlisted genes with the unchanged cutoff; its maximum score8 makes that test stricter than the primary maximum9.
- **Discussion/limitations:** unrecovered diagnoses, remaining derived labels, published/GEO histology-count disagreement, internal rather than external validation, cross-sectional design, confounding and lack of therapeutic validation.

## Traceable sources

- `label_audit_GSE130970_2026-10-10/`: individual histology/label audit and the five flagged samples.
- `label_source_search_2026-10-10/SEARCH_RESULTS.md`: original supplements and repository search; no original individual diagnosis mapping recovered. The original supplement Table1 is aggregate evidence only.
- `unit_audit_GSE193066_2026-10-10/UNIT_AUDIT.md`: deposited units and reproduction of baseline processing.
- `sensitivity_2026-10-10/PROTOCOL.md`: frozen contrasts and analysis rules.
- `sensitivity_2026-10-10/comparison_summary.csv`, `shortlist_comparison.csv`, `network_comparison.csv`, `membership_and_cluster_details.json`: measured results.
- `sensitivity_2026-10-10/verification_results.json`: 51 passing checks; `combined/run_status.json`: completed stages; `results_manifest.json`: artifact hashes.

## Next implementation checkpoint

Promote the selected inputs, processing logic and completed combined outputs together, preserving a recoverable baseline. Refresh manuscript planning, tables, figures and package documentation against the new counts. Verify that the production workflow reproduces the selected run before replacing graph associations. A graph update must also reconcile the changed GSE193066 expression representation used downstream; changing only progression edges would leave an unexplained mismatch between stored expression and analysis. Keep the complete raw graph distinct from the recovered 14,794-gene core. No new numerical rerun or graph write was needed for this decision checkpoint.
