# Stage-informed liver knowledge graph

Corrected active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses221 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,688 fibrosis**, **4,018 disease**, **1,802 shared**, **5,904 union**. Tier1 has **491 genes**, with25 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with5 shortlisted genes shown.

The final objective is to support the next team’s drug repurposing for interrupting disease progression at different stages. Curated biology from OptimusKG connects stage-associated genes to drugs, diseases, pathways and processes. No therapeutic efficacy or validated clinical stage predictor is established.

## Active files

- Paper1_Package: current data, methods, figures, tables and evidence boundaries.
- Paper1_Results: corrected Tasks1–4.
- Paper1_HighConfidence: corrected scores, shortlist, LOSO and network.
- data/progression_full and data/for_mentor: corrected association/group summaries.
- data/graph_full and data/graph_okg: current node/knowledge/progression CSVs.
- data/expression_analysis_core: core-only recovery for analysis; never use to replace all graph expression measurements.
- manuscript_planning: current inventory/workflow/evidence map/missing information.
- biopsy_correction_2026-10-10: verified correction audit, comparison and graph rollback snapshot.
- archives: checksum-verified recovery copy of superseded results/draft; excluded from Git by default.

## Rebuild and checks

Read docs/provenance/REBUILD.md. Run scripts from repository root with explicit outputs. Requirements cover Paper1; requirements-link-prediction.txt is optional and unrelated to the verified Paper1 results. Patient-policy tests are in tests/.

Historical Claude sessions under handover/ preserve rationale and rejected branches; their counts/method descriptions are not current results.
