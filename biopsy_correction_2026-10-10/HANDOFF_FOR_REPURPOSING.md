# Corrected evidence for the drug-repurposing team

Use the live liver_kg database and this directory's corrected results, identified by analysis_run=biopsy_correction_2026-10-10 on TRACKS relationships. The older Paper1_Package and original result folders were retained and contain superseded counts.

- Corrected gene associations: data/progression_full/progression_fibrosis.csv and progression_disease.csv. Select q < 0.05 AND n_agree=n_studies. Do not treat progression_both.csv as the shared or union set; that historical file has a different selection rule.
- Current stage-level gene profiles: data/for_mentor/genes_by_fibrosis_stage.csv, based on one observation per patient.
- Per-gene transitions: Paper1_Results/Task3/task3_all_genes_all_transitions.csv.
- Scores and full candidates: Paper1_HighConfidence/11_final_all_3688_genes.csv and 11_final_tier1_genes.csv.
- Balanced shortlist with timing uncertainty: Paper1_HighConfidence/shortlist_with_membership_confidence.csv.
- LOSO with eligible-universe correction: Paper1_HighConfidence/10_loso_all_eligible_runs.csv and 10_loso_summary.csv.
- Mechanism connections: Paper1_HighConfidence/12_KG_supplementary.xlsx; both pathways and GO processes attach directly to Gene.
- Verification/change record: CORRECTION_REPORT.md, comparison_summary.json, verification_results.json and graph_update_verification.json.

Drug–gene action annotations and disease treatment edges provide context, not demonstrated stage-specific treatment efficacy. Rising expression alone does not establish that inhibition is beneficial; falling expression does not prove activation is beneficial. Candidate predictions need direction-aware biological review, model/rule evaluation, and subsequent validation. No successful drug prediction or efficacy claim is produced by this correction.

No message was sent to the next team; this is a local handoff artifact.
