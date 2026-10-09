# Verify the current package

1. Recompute SHA-256 against00_START_HERE/06_FILE_MANIFEST.csv; all current files should match bytes exactly. The manifest excludes itself.
2. Filter progression_fibrosis/disease by q<.05 AND n_agree=n_studies. Compute intersections/unions rather than infer counts from filenames.
3. Check cluster-assignment IDs match the fibrosis selected set. Read confidence and confidence_n_bootstraps for individual genes.
4. Read Table6 and the mechanism workbook; the latter contains per-gene annotations, ranked mechanisms and displayed nodes/edges.
5. The correction audit under biopsy_correction_2026-10-10 records baseline reproduction, changed memberships, numerical tests, graph backup and post-update matching. Those are historical run records; active outputs now use the standard root directories.
6. Run pytest/unittest policy checks through tests/test_biopsy_policy.py from repository root. Rebuild commands are in06_PROVENANCE/REBUILD.md.

Full primary reprocessing cannot be done from this package alone: raw downloads, HGNC, original OptimusKG parquet and full expression-export assets are omitted. Packaged source copies retain repository-relative path assumptions; use the root scripts from the root checkout, or adapt paths explicitly. No database is needed to read the shipped analysis tables/network.

