# How to verify the results

2. Filter progression_fibrosis/disease by q<.05 AND n_agree=n_studies. Compute intersections/unions rather than infer counts from filenames.
3. Check cluster-assignment IDs match the fibrosis selected set. Read confidence and confidence_n_bootstraps for individual genes.
4. Read the shortlist (Paper1_HighConfidence/shortlist_with_membership_confidence.csv) and the mechanism workbook (12_KG_supplementary.xlsx); the latter contains per-gene annotations, ranked mechanisms and displayed nodes/edges.
5. final_combined_2026-10-10 records the final run: selection, sensitivity configurations and graph synchronisation checks.
6. Run pytest/unittest policy checks through tests/test_biopsy_policy.py from repository root. Rebuild commands are in docs/provenance/REBUILD.md.

Full primary reprocessing needs the raw downloads, HGNC and the OptimusKG parquet files, which are not committed (sources in docs/provenance/DATA_SOURCES.md). Run scripts from the repository root. No database is needed to read the analysis tables or the network.

