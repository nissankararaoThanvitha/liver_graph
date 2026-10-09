> **Promoted to active paths:** Corrected outputs now live in the standard root data/, Paper1_Results/, Paper1_HighConfidence/ and rebuilt Paper1_Package/. Links under this audit directory are aliases to those active folders. Superseded results/draft are only in archives/previous_results_2026-10-10.tar.gz. This document records the correction run; use the active package for current methods and numbers.

# Biopsy correction and verified rerun

Completed 10 October 2026. The scientific purpose, clarified by the researcher, is to provide a stage-informed gene/biology knowledge graph for the next team’s drug-repurposing work aimed at identifying drugs that could interrupt progression. This run does not predict suitable drugs or demonstrate therapeutic efficacy.

## What changed

A shared rule now governs discovery, stage summaries, clustering robustness, stage contrasts, matched refits and LOSO:

- When a patient’s repeat biopsies have the same fibrosis stage, average their within-study standardised expression measurements and give that person one observation.
- When their stages differ, use biopsy 1 only. Biopsy 2 is excluded before selecting any stage comparison, so it cannot re-enter a later contrast.
- Raw expression and all sample records remain in the graph. The exclusion is an analysis decision, not deletion of biological source data.

GSE193066 contains 58 repeat-biopsy patients: 28 same-stage repeats averaged, and 30 different-stage second biopsies excluded. Discovery/analysis use 610 independent staged patients. Stage means now give each person one contribution rather than weighting repeat biopsies twice. Stage-by-age/sex summaries use 327 independent patients, compared with the original raw-sample coverage of 385.

LOSO also corrects significance over all 14,794 eligible genes in each omitted-study run, then reports the selected Tier1 genes. It no longer corrects only the selected shortlist-related family. This remains internal robustness of a selected set: it does not refit discovery/prioritisation within a fully held-out clinical prediction design, and is not external validation.

## Data recovery and baseline check

The missing analysis expression subset was recovered through read-only queries from liver_kg, database neo4j. All 1,085 samples and 14,794 common genes were recovered: 16,051,490 measurements. This is an analysis subset, not a replacement for the complete 53,993-gene expression export.

Live patient IDs, biopsy order, stage and study IDs matched the supplied clinical table. Each recovered sample has exactly one measurement for every eligible gene, with no missing endpoint or duplicated measurement.

Before correction, discovery was rerun using the old first-biopsy-only option on the recovered data. All tested gene IDs, median correlations, p-values, q-values and agreement counts reproduced the existing results within documented numerical tolerance. This verifies the recovery and baseline; it does not validate every biological interpretation.

Core dependency versions match the project pins. The available runtime is Python 3.12.14 rather than the documented original 3.13.7; the reproduced baseline establishes that this runtime difference did not alter the checked baseline discovery statistics. Full runtime dependencies are in runtime_requirements.txt.

## Results comparison

| Output | Original | Corrected |
|---|---:|---:|
| Fibrosis-associated genes | 3,681 | 3,688 |
| Disease-group-associated genes | 4,018 | 4,018 |
| Shared between the two selected sets | 1,815 | 1,802 |
| Union of selected genes | 5,884 | 5,904 |
| Tier1 score-qualified genes | 525 | 491 |
| Final balanced shortlist | 25 | 25 |
| Genes retained from original shortlist | — | 19 |
| Tier1 genes significant in every LOSO run | 521/525 | 488/491 |
| Tier1 genes retaining median absolute rho≥.30 in every LOSO run | 263/525 | 274/491 |

The fibrosis count rises by seven, but membership changes more than that: **87 genes enter and 80 leave**. Full ID/statistic comparisons are in fibrosis_membership_changes.csv and fibrosis_statistics_comparison.csv. Disease-axis membership is unchanged, as expected because the repeated-biopsy cohort has no usable disease-group labels.

The corrected Tier1 set retains 468 of the original 525 genes. LOSO summaries compare different selected sets and a corrected testing family; the counts should not be interpreted as a controlled estimate of improved validation performance.

Shortlist additions: DGAT2, DNAJC12, FCN2, ITGA2, SORD, TAX1BP3.

Shortlist removals: ADCY1, DAGLA, KCNN2, KNG1, NCAM2, STC1. Removal means they did not enter this balanced top-five-per-cluster rule; it does not establish biological irrelevance.

The updated shortlist_with_membership_confidence.csv includes bootstrap confidence and assessable denominators. Several shortlisted genes still have uncertain cluster timing. Score-qualified does not mean clinically validated or an established therapeutic target.

## Trajectories, contrasts and enrichment

Corrected five-cluster sizes: 953, 1,452, 272, 322 and 689. Confidently assigned members at confidence≥ 0.8: 32,803,1,96,511. In this rerun, the automatic largest-k rule at gene-subset ARI≥.95 **does select5**; k6 is below the threshold. This differs from the historical run where5 was an override. The corrected diagnostic figure states the reported and rule-selected values separately.

Full substantial-gene counts by adjacent transition: 1,197 ; 1,000 ; 1,086 ; 847. Matched medians: 0; 0; 1.5; 251.5. F3→F4 median absolute beta remains .3753 in the preselected set, with matched-count SD 411.5. The late comparison uses four studies under the first-biopsy rule because GSE193066’s first biopsies do not supply the F4 observation. These remain exploratory cross-sectional contrasts, not observed individual progression or unbiased whole-genome counts.

Enrichment was rerun using the exact documented MSigDB 2024.1.Hs GMT collections, downloaded into the isolated folder with URLs/checksums. The fresh result directory contains no residual skipped-output figures from the old package. C1 core 32 is now testable; C3 core 1 remains untestable; C4 core 96 has some significant terms. Old core conclusions must not be copied into the corrected manuscript.

The mechanism network was rebuilt on 491 Tier1 genes: 12 selected enriched mechanisms, 42 drawn genes,154 edges and 5 shortlist genes displayed. Its workbook uses the actual Tier1 count and identifies the subset correctly. Biological plausibility and annotation-dependent interpretation still need review.

## Live graph update

After all checks passed, only TRACKS_FIBROSIS and TRACKS_INFLAMMATION relationships were replaced atomically. The updater checked the current baseline membership and every endpoint before writing, saved a complete rollback snapshot, and compared every resulting identity and property against the corrected CSV.

Current graph: **3,688 TRACKS_FIBROSIS and 4,018 TRACKS_INFLAMMATION links**. Each carries rho, q, study count, direction, source, the biopsy-policy name and analysis-run identifier. Expression measurements, sample/gene nodes and curated OptimusKG relationships were not modified.

Backup: live_graph_before_progression_update.json. Post-update evidence: live_graph_after_progression_update.json and graph_update_verification.json. Credentials are obtained interactively and are not saved.

## Where to use the corrected outputs

The authoritative correction run is this directory, including data/progression_full, data/for_mentor, Paper1_Results and Paper1_HighConfidence. The original Paper1_Package, result directories and exported tables remain preserved as the earlier version. They are not the current source for manuscript numbers or the next team’s progression-gene shortlist.

The source scripts were updated to use biopsy_policy.py. Do not mix the corrected scripts with old intermediates. The isolated run commands and timings are in run_status.json; input hashes, source snapshots, logs and verification records remain here. The packaged copies were preserved and therefore still describe the earlier implementation.

## Verification and remaining limits

Five targeted policy tests pass, including shuffled biopsy order, missing first-biopsy order, unknown stages and prevention of second-biopsy re-entry. Integration checks confirm independent SciPy correlations for 20 genes in the repeat cohort, one-patient stage means, full-universe LOSO, corrected gene/cluster/edge memberships,25 unique score-qualified shortlist genes and preservation of original results. Graph verification confirms all 7,706 progression relationships and their properties.

This completes the biopsy-handling correction and affected reruns. It does not resolve the other independent manuscript issues: histology-derived diagnosis definition, original assay-unit documentation, confounding/cell composition, causal interpretation, therapeutic validation, original acquisition provenance or publication-ready manuscript prose.
