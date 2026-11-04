# Rebuild repairs — 4 November 2026

Four repository-review issues addressed:

1. Added `scripts/unify_drug_schema.py` after the historical drug writer.
   Dry run by default; apply requires a new backup. Each relationship is
   converted separately, preserving endpoints/properties; no evidence is
   collapsed. Label cleanup and preservation checks are inside the same
   transaction. Already unified graphs require no changes.
2. Repaired `scripts/verify_against_neo4j.py`: correct workbook default,
   configurable paths/database, explicit original-annotation scope, full
   membership and duplicate checks. Expanded graph totals remain a separate
   verification task.
3. Added `scripts/prepare_analysis_core.py` and fresh-clone instructions.
   It streams a checksum-verified release ZIP into analysis-format files,
   rejects missing/duplicate/nonfinite observations, preserves zeros and
   refuses existing output folders. The original annotation layer can be
   recovered separately. Recovery is not raw-data reprocessing.
4. Updated active filenames/counts/instructions. MSigDB loading now requires
   `--apply`; its default writes CSVs only. Historical logs/results are retained.

Validation:

- 12 tests passed, including the five existing biopsy-policy tests and a
  real Neo4j Community 5.26.0 integration test. The latter used an empty
  temporary database on 127.0.0.1:17689, not a Desktop instance.
- Tested preservation of conflicting parallel action records, list properties,
  numeric zero, node properties and unrelated annotation edges; second-run
  behaviour; and rollback of a deliberately failed transaction.
- Tested expression recovery completeness, zero retention, refusal to overwrite,
  missing/duplicate/nonfinite inputs, metadata mismatch and annotation recovery.
- Tested the verifier's Cypher against the temporary database and its handling
  of duplicate memberships in a small fixture.
- Command help and source syntax checked. `git diff --check` passed.
- Calculation functions in high_confidence_genes.py, kg_subgraph.py and
  paper1_task4_enrichment.py were compared with HEAD after removing docstrings:
  unchanged. Only explanatory text/console wording changed in those scripts.
- No existing scientific results, final-run verification records or manuscript
  content were changed. The Desktop/liver_latest graph was not modified.
- The temporary server was stopped after testing. No release was published.

Limits: the complete 693 MB release ZIP was not reprocessed in this repair;
recovery was exercised with small fixtures in the exact export format. No new
whole-graph live verification or original-data analysis was run. The optional
integration test requires a deliberately empty temporary instance at the
hard-coded test port and TEST_NEO4J_URI=bolt://127.0.0.1:17689; it is skipped in
ordinary unit-test runs. Run `python -m unittest discover -s tests` in the
environment installed from requirements.txt.
