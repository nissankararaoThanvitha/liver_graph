# Commit checkpoints

These are suggestions requested by the researcher; no Git commits are made automatically. Commit only completed artifacts. Bulk expression and duplicate inputs are excluded via .gitignore; hashes and reproducible setup are retained.

1. Isolated input preparation and fixed protocol verified.
   `test: prepare isolated label and normalisation sensitivity inputs`
2. Fresh baseline reproduces current discovery, Tier1 membership and shortlist.
   `test: reproduce active baseline before sensitivity comparisons`
3. Label-only sensitivity completed.
   `test: complete sensitivity run excluding ambiguous disease labels`
4. Normalisation-only sensitivity completed.
   `test: complete preserved-RLE normalisation sensitivity run`
5. All four main runs completed; no quota was relaxed to force25.
   `test: complete label and normalisation factorial sensitivity runs`
6. Specificity-feature ablation, factorial checks and final comparisons verified.
   `test: compare candidate stability across label and normalisation sensitivities`

7. Primary strategy selected with rationale, claim boundaries and promotion requirements.
   `docs: select combined primary analysis and record evidence boundaries`

The combined standard run is now selected in manuscript_planning/PRIMARY_ANALYSIS_DECISION.md. The active package, source labels/results and live graph still contain the baseline pending verified promotion. The original diagnoses have not been recovered; sensitivity stability is not external validation or therapeutic efficacy.
