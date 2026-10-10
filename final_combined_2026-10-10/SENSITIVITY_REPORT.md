> Historical sensitivity comparison. The researcher selected the combined approach as final. Other run folders were removed after promotion; comparison evidence remains here and full outputs are in the verified recovery archive. Current outputs use canonical root paths.

# Label and normalisation sensitivity comparison

This experiment compares alternatives without adopting new diagnoses or changing the active graph. All runs use the corrected biopsy rule, the same eligible gene universe, k=5, seeds, thresholds, P/T/X/F/B scoring, five-per-cluster shortlist quota and mechanism-selection rules.

## What was varied

- **Label sensitivity:** the five previously flagged GSE130970 samples have a blank disease_group and explicit unclassified-sensitivity provenance. Their fibrosis stages/raw histology remain unchanged. The remaining diagnoses are still derived and unverified.
- **Normalisation sensitivity:** only GSE193066 changes from current CPM-style rescaling to log2(deposited linear RLE counts+1), followed by the same gene/study standardisation over164 biopsies. The other seven expression inputs remain identical.
- **Combined sensitivity:** both changes, to separate the joint effect from each single change.
- **F-feature ablation:** set F=0 after each main run, keeping Tier1 cutoff7 and the same cluster quota. Its maximum score is8 rather than9, so this is a stricter feature-removal test. No thresholds were lowered to force25 candidates. B still uses group/cluster enrichment, so this is not a fully disease-label-independent prioritisation.

## Main results

| run | fibrosis_genes | disease_genes | shared | union | Tier1 | shortlist_size | shortlist_retained_from_baseline | cluster_ARI_common_genes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 3688 | 4018 | 1802 | 5904 | 491 | 25 | 25 | 1.0 |
| labels_only | 3688 | 4199 | 1862 | 6025 | 484 | 25 | 25 | 1.0 |
| normalisation_only | 3845 | 4018 | 1768 | 6095 | 454 | 24 | 16 | 0.9126 |
| combined | 3845 | 4199 | 1822 | 6222 | 447 | 23 | 16 | 0.9126 |

Gene counts alone hide membership changes. Detailed added/removed Ensembl IDs, centroid matching and shortlist changes are in membership_and_cluster_details.json. Gene-level shortlist scores/confidence are in candidate_stability.csv.

## Shortlist changes relative to baseline

### labels_only

Retains 25 of the baseline25; produces 25 candidates under the unchanged quota.

Added: none.

Removed: none.

Clusters with fewer than five Tier1 candidates: none. No slots were filled by lowering criteria.

### normalisation_only

Retains 16 of the baseline25; produces 24 candidates under the unchanged quota.

Added: EPHA3, F2, KNG1, MME, NAAA, SLC38A4, SULT1E1, TPM4.

Removed: ADAMTSL2, AKR1D1, CLPX, CYP4F3, DGAT2, DNAJC12, FCN2, ITGA2, SORD.

Clusters with fewer than five Tier1 candidates: C4. No slots were filled by lowering criteria.

### combined

Retains 16 of the baseline25; produces 23 candidates under the unchanged quota.

Added: EPHA3, F2, KNG1, MME, SLC38A4, SULT1E1, TPM4.

Removed: ADAMTSL2, AKR1D1, CLPX, CYP4F3, DGAT2, DNAJC12, FCN2, ITGA2, SORD.

Clusters with fewer than five Tier1 candidates: C4. No slots were filled by lowering criteria.

## Candidates shared across main runs

**16 genes** are shortlisted in all four main runs: ACADSB, CACNA1C, CDC45, CYP2C19, FABP5, HTR7, IL32, LYZ, NFASC, OAT, PDGFRA, PLK3, PLPP4, TAX1BP3, TREM2, TYMS. This is robustness to these two specified perturbations, not an independently validated drug-target set. Stable association or scoring does not establish therapeutic direction or efficacy.

## Specificity-feature ablation

| run | F_ablation_Tier1 | F_ablation_shortlist_size | F_ablation_baseline_shortlist_retained | F_ablation_own_shortlist_retained |
| --- | --- | --- | --- | --- |
| baseline | 320 | 25 | 15 | 15 |
| labels_only | 321 | 25 | 15 | 15 |
| normalisation_only | 285 | 22 | 12 | 15 |
| combined | 286 | 21 | 12 | 14 |

- baseline: 320 Tier1 genes without F; 25 shortlisted. Clusters below five eligible genes: none.
- labels_only: 321 Tier1 genes without F; 25 shortlisted. Clusters below five eligible genes: none.
- normalisation_only: 285 Tier1 genes without F; 22 shortlisted. Clusters below five eligible genes: C4.
- combined: 286 Tier1 genes without F; 21 shortlisted. Clusters below five eligible genes: C4.

## Clustering and internal robustness

| run | cluster_ARI_common_genes | confident_cluster_genes | Tier1_LOSO_significant_all5 | Tier1_LOSO_strong_all5 |
| --- | --- | --- | --- | --- |
| baseline | 1.0 | 1443 | 488 | 274 |
| labels_only | 1.0 | 1443 | 481 | 275 |
| normalisation_only | 0.9126 | 1838 | 449 | 246 |
| combined | 0.9126 | 1838 | 442 | 247 |

ARI uses genes present in both selected sets and is invariant to cluster-label permutation; changed gene selection is reported separately. Centroid-matched correlations are saved, because similarly numbered clusters may represent different timing shapes. k=5 was held fixed; automatic k diagnostics remain available in each run.

LOSO applies BH over the full14,794 eligible genes, but tests internal robustness of already selected genes. Comparisons involve different Tier1 denominators. Direction retention is not independent validation. The stage contrasts/enrichment reuse discovery data and inherit selection and annotation limitations.

## Mechanism networks

| run | scoring | selected_mechanisms | displayed_genes | edges | shortlisted_genes_shown |
| --- | --- | --- | --- | --- | --- |
| baseline | standard | 12 | 42 | 154 | 5 |
| baseline | without_F | 12 | 34 | 127 | 6 |
| labels_only | standard | 12 | 42 | 154 | 5 |
| labels_only | without_F | 12 | 34 | 127 | 6 |
| normalisation_only | standard | 12 | 42 | 154 | 4 |
| normalisation_only | without_F | 12 | 29 | 122 | 5 |
| combined | standard | 12 | 42 | 154 | 4 |
| combined | without_F | 12 | 29 | 122 | 5 |

A displayed network is a filtered Tier1 annotation subset. Genes absent from the selected twelve mechanisms may have other graph connections. Some unexpected cross-tissue labels may need biological review; enrichment alone is not a mechanism demonstration.

## Validation and active-state protection

51 comparison checks passed. Fresh baseline discovery and shortlist/Tier1 memberships reproduce the active outputs. Factorial invariants hold: label-only changes do not alter fibrosis discovery; normalisation-only changes do not alter disease discovery; the combined run matches the appropriate single-change axis results. Active-file hashes remain unchanged. No Neo4j writes were performed.

## What this does and does not resolve

- Resolves how sensitive the implemented priorities are to the specified label abstention and normalisation alternatives.
- Does not recover original sample-level diagnoses, validate the other derived labels or establish a universally correct normalisation.
- Does not produce independently validated biomarkers, causal mechanisms or effective drugs.
- Does not automatically replace the baseline, active package or graph. A final strategy must be selected explicitly and documented; do not choose one to preserve preferred genes.

For a conservative primary analysis, selective abstention avoids presenting the five ambiguous cases as certain diagnoses, and preserving deposited RLE is a directly documented alternative. The measured comparison—not candidate preferences—should guide whether to adopt those choices, retain current processing with sensitivity disclosure, or narrow claims to fibrosis associations. F-dependent results and label-derived interpretation still require cautious wording.

## Files and commit checkpoints

Input preparation/protocol:input_preparation.json, PROTOCOL.md and source/runtime snapshots.

Main runs:baseline/, labels_only/, normalisation_only/, combined/ with full per-step logs and run_status.json.

Comparisons:comparison_summary.csv, candidate_stability.csv, shortlist_comparison.csv, network_comparison.csv, membership_and_cluster_details.json and verification_results.json.

F ablations:each run's F_ablation/ containing actual candidate counts, scores, confidence and regenerated networks.

Commit checkpoints are recorded in COMMIT_CHECKPOINTS.md. No commits were made automatically.
