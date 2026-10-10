# Final analysis selected by the researcher

On 10 October 2026 the researcher selected the combined approach as the final
analysis and requested removal of the alternative sensitivity-run folders.

The final approach excludes five flagged GSE130970 samples from the disease
axis by marking their derived disease groups unclassified. Fibrosis stages
and original histology are retained. The remaining 73 diagnoses remain
histology-derived; the source search did not recover individual author labels.

GSE193066 uses its deposited linear DESeq2 RLE-normalised counts, sums mapped
gene aliases, applies log2(count+1), then standardises within gene across all
164 biopsies using sample SD. There is no CPM rescaling for this study.

The established biopsy policy, eligible gene universe, seed42, k=5, scoring,
Tier1 cutoff7 and mechanism selection remain unchanged. The main final score
includes F; the without-F experiment remains historical sensitivity evidence.

| Final output | Count |
|---|---:|
| Fibrosis-associated genes | 3,845 |
| Disease-group-associated genes | 4,199 |
| Shared genes | 1,822 |
| Selected union | 6,222 |
| Tier1 genes | 447 |
| Balanced shortlist | 23 |
| Tier1 by cluster C1–C5 | 93 / 262 / 7 / 3 / 82 |
| Displayed network | 42 genes, 12 mechanisms, 154 edges |
| Shortlisted genes shown | EPHA3, NFASC, PDGFRA, TREM2 |

C4 contains only three qualifying Tier1 genes, so its quota is not filled by
lowering the threshold. Existing numerical filenames containing `25` describe
the original selection target; their final row count is23.

Canonical outputs are root Paper1_Results, Paper1_HighConfidence,
data/progression_full, data/for_mentor and the rebuilt Paper1_Package.
The retained comparison tables and protocol in this directory document the
choice; alternative run outputs are only in the checksum-verified local
archives/pre_combined_final_2026-10-10.tar.gz recovery archive.

Graph synchronisation status and checks are recorded in promotion_status.json
and graph_verification.json. These must be checked before using the live graph.
The graph update changes only GSE193066 derived expression properties, the five
derived disease labels, and the two progression relationship types. Raw values,
sample identity and curated biological/drug relationships are preserved.

These association, annotation and internal robustness analyses supply a
resource for downstream drug repurposing. No drug efficacy or causal disease
mechanism has been demonstrated.
