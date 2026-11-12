# Unused-cohort retrieval and validation screening

Screened: 7 November 2026. Status: dataset retrieval and feasibility screening only; no validation tests, gene re-selection, graph writes, or manuscript edits.

## Existing discovery data

The existing source-of-truth list is `data/graph/nodes_dataset.csv`, corroborated by `docs/provenance/DATA_SOURCES.md`: GSE126848, GSE130970, GSE135251, GSE162694, GSE167523, GSE193066, GSE240729 and GSE269412. None of the candidate accessions below is on that list.

The fixed candidate list for future testing is the existing `Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv`. Screening checked identifier presence, not association results. Candidate selection must not depend on whether this dataset reproduces the desired findings.

## Candidate assessment

Counts below are directly enumerated from downloaded GEO sample characteristics, except where explicitly labelled as a series-level statement. They describe deposited samples, not final analysis eligibility after expression QC. Do not assign missing stages or treat a healthy diagnosis as an observed F0 stage.

| Candidate | Deposited samples | Fibrosis stages in downloaded metadata | Intended use and limitation |
|---|---:|---|---|
| [GSE225740](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE225740) | 93 | F0=27; F1=26; F2=15; F3=13; F4=6; missing=6 | First candidate for full F0–F4 validation: 87 staged samples; all 23 shortlisted genes map to deposited Entrez identifiers using the retained project map. Counts and phenotype files downloaded. Raw reads are not provided because of participant privacy. Small F4 group limits precision. |
| [GSE281797](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE281797) | 94 | F0=42; F1=26; F2=20; F3=6; F4=0 | Complementary early/intermediate-stage assessment. Count and TPM matrices downloaded, all 23 shortlisted gene identifiers present. Includes 30 no-pathology, 53 MASL and 11 MASH samples. Cannot validate F3–F4 contrasts or cirrhosis patterns. |
| [GSE207310](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE207310) | 30 | F0=7; F1A=8; F1B=6; F1=1; F2=7; F3=1; F4=0 | Additional small cohort; counts deposited as per-sample files in RAW.tar (processed counts, not FASTQ). Any collapse of 1A/1B into F1 must be explicit. Only one F3 sample; no F4. |
| [GSE185051](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE185051) | 57 | All samples: F0=11; F1=37; F2=4; F3=5; F4=0 | Pediatric NAFLD (52) plus five adult normal controls: do not pool these as an age-comparable NAFLD stage series. Among the 52 NAFLD samples: F0=6, F1=37, F2=4, F3=5. Counts downloaded. Useful for secondary cross-age assessment rather than primary adult validation. |
| [GSE192959](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE192959) | 48 | F0=1; F1=1; F2=3; F3=16; F4=27 | RNA-seq GCT downloaded. Biopsies obtained at ablation of NAFLD-related HCC tumors. Mostly advanced fibrosis; severely underpowered early stages, with an HCC-related clinical context. From the same source publication/SuperSeries family as discovery GSE193066; separate accession is not proof of independent patients. |
| [GSE193080](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE193080) | 59 | F0=5; F1=20; F2=10; F3=14; F4=10 | GCT downloaded. Tumour-adjacent liver from NAFLD-related HCC surgical patients, not an uncomplicated NAFLD biopsy cohort. Same source publication family as GSE193066; only a qualified secondary assessment after provenance checks. |
| [GSE89632](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE89632) | 63 | F0=31; F1=14; F2=2; F3=4; F4=4; no stage field=8 | Microarray alternative. GEO reports 20 simple steatosis, 19 NASH and 24 healthy controls after nine QC exclusions. Stage counts above include controls; patient-only eligibility must be separately derived. Family SOFT includes processed expression tables. Probe annotation and alias mapping required. |
| [GSE239422](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE239422) | 125 | No fibrosis field in downloaded GEO characteristics | Metadata retrieved; raw/normalized count files are available, but not downloaded in this screen. Not currently eligible for fibrosis-stage validation without additional histology metadata. |
| [GSE49541](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE49541) | 72 | Series reports 40 F0–F1 and 32 F3–F4 | Microarray candidate for advanced-versus-mild replication. Do not infer exact individual F0/F1/F3/F4 labels from these pooled groups. SOFT and processed series matrix downloaded; no individual fibrosis-stage characteristic was recovered in the SOFT. |

## Independence audit

Downloaded current GEO SOFT records for all eight discovery accessions are retained in `original_cohort_metadata/` with their source URLs and SHA-256 hashes. Parsed sample metadata for downloaded candidate SOFT records are retained as `GSE*/sample_metadata.tsv`.

`candidate_inventory.tsv` records intersections of GSM, BioSample and SRX/ERX/DRX identifiers against the discovery metadata. No matching GSM identifiers were observed for candidates successfully parsed at screening. For GSE225740, BioSample and SRX identifiers are absent, so those comparisons are not assessable; their initial numeric zeros did not constitute evidence of non-overlap. This rules out identical deposited identifiers, not re-deposition or repeated enrollment of the same patient under different identifiers. Cohort recruitment centre, dates, source publication and any patient-level aliases must still be reviewed. No candidate has yet been certified as patient-independent. In particular, GSE192959 and GSE193080 share the source study family with GSE193066.

## Gene availability and provenance

`shortlist_identifier_coverage.tsv` records identifier-level coverage in downloaded matrices. It is not a statistical validation result or a detectability check. GSE225740 mapping uses the project's retained symbol-to-Entrez map; GSE281797 uses Ensembl/symbol identifiers. Direct symbol searches in the pediatric and GCT data find 22 of 23 current symbols; the unresolved PLPP4 symbol requires alias checking before calling it absent. All expression matrices need unit checks, sample matching, duplicate-ID handling and expression QC before analysis.

Files remain compressed as deposited. SHA-256 hashes, byte counts and public source URLs are retained in download manifests. No raw sequencing archives were requested. GSE207310's RAW.tar is an archive of processed per-sample count tables; archive contents were listed without extracting them.

## Proposed next step (not executed)

Prioritise GSE225740 for provenance/overlap confirmation and expression QC, followed by GSE281797 as a complementary F0–F3 cohort. Keep all original gene rankings and cluster assignments fixed. Define patient eligibility, preprocessing, hypotheses and multiplicity rules before testing associations. Report all measurable shortlist genes, including discordant and nonsignificant findings. An independent cohort test would evaluate transcriptional associations; it would not establish causality, longitudinal progression or drug efficacy.

## Retrieval completion

Nine unused accessions were screened. GEO family metadata were downloaded for all nine; processed expression data were retrieved for eight (GSE239422 metadata only). All requested downloads succeeded and compressed files were checked for readability. Original-discovery metadata were also downloaded for the overlap audit. `retrieved_files.tsv` consolidates source URLs, file sizes and SHA-256 checksums for all downloaded source files. No association or enrichment analyses were run.

## Subsequent preprocessing

GSE225740 has now been preprocessed separately in `../GSE225740_preprocessed/` (see its README). This update does not change the original screening observations or certify patient independence. No association tests have been run.

## GSE225740 cohort-provenance review

See `../GSE225740_preprocessed/cohort_independence_audit.md` and `cohort_overlap_checks.tsv` for the 7 November source-paper review. Distinct recruitment provenance is supported and no shared GSM was found; individual-identity non-overlap cannot be definitively established from anonymised records. The BioSample/SRX missingness correction is reflected in the inventory.

## Subsequent fixed-shortlist association analysis

Completed separately in `../GSE225740_validation/`: 23/23 concordant directions, 21/23 concordant significant primary tests (two-sided Spearman with BH over 23). KNG1 and SULT1E1 did not meet the primary significance threshold. Permutation sensitivity gave 22/23, with borderline SULT1E1 changing classification; the primary headline remains 21/23. All outcomes, low-expression caveats, cohort-independence qualification and plots are retained there. No reclustering, causal inference, longitudinal prediction or manuscript updates were performed.

## Subsequent frozen-tier/cluster assessment

See `../GSE225740_tier_cluster_validation/README.md`: 445/447 Tier 1 genes testable, 439 directionally concordant and 387 concordant significant under Tier 1 BH. Shared-family tier comparisons are separately reported. Fixed centroid shape correlations C1–C5: 0.960, 0.991, 0.743, -0.307 and 0.907; these describe five means and do not establish complete cluster replication. Original C4 pattern is not reproduced clearly. All original tiers/memberships remain unchanged.

## Subsequent transition and pathway checks

See `../GSE225740_transition_pathway_validation/README.md`: original exact stage contrasts replicate weakly under the per-contrast family; only 3/23 original shortlisted largest transitions meet the separate fixed-23 significance/effect threshold (IL32, TREM2, FABP5, all F0–F1). Fresh-cohort gene selection followed by the original annotation definitions supports 87/145 frozen cluster/term pairs; pair counts include repeated terms across clusters and do not establish mechanisms or cluster equivalence. Full positive/negative outcomes and limitations are retained. No original results, graph or manuscript edits.

## Second validation cohort (GSE281797)

Completed in `../GSE281797_validation/`. Australian recruitment and identifier checks support separate provenance, without definitive donor linkage. Primary all-94 results over F0–F3: shortlist 21/23 concordant directions, 14/23 concordant significant; Tier 1 399/447 concordant directions, 161/447 concordant significant, four opposite significant. MASLD-only sensitivity n=64: shortlist 13/23 concordant significant, Tier 1 164/447. No F4 exists. C4 pattern agreement remains weak; other four-stage centroid comparisons are descriptive, not proof of the full F0–F4 cluster solution. Twelve shortlist genes meet concordant significance in both cohorts. All original assignments and manuscript remain unchanged.

## GSE49541 grouped-severity validation, 2026-11-07

Confirmed: 72 deposited GC-RMA profiles (40 mild F0–F1, 32 advanced F3–F4). Primary mean-probe analysis: 22/23 shortlisted genes testable, 19 direction-concordant, 13 concordant BH-significant; TAX1BP3 unavailable. Tier-1: 439/447 testable, 397 concordant, 220 concordant BH-significant, zero opposite significant in either family. Median sensitivity yields 10 shortlisted and 175/433 Tier-1 concordant significant, so probe-summary dependence is material. No re-ranking or preferred probe selection. See `../GSE49541_validation/README.md`, full result CSVs, hash manifest and vector PDF.

Provenance: primary paper identifies Duke biorepository recruitment; records also list GSE31803, which must not be counted as another independent cohort. No shared GSM across the eight discovery and two prior validation cohorts. No BioSample/SRA IDs in candidate sample relations, so those overlap tests are unassessable. Platform gene names matching SAMD-like patterns are not sample identifiers. Distinct recruitment is supported, absolute donor nonoverlap is not established. Interpretation limited to grouped severity; no exact-stage, cluster-shape, longitudinal or wet-lab validation claim. Source paper: https://doi.org/10.1002/hep.26661 ; GEO https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE49541 .
