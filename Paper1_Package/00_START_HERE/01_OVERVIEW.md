# Objective and completed outputs

Corrected active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses221 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,688 fibrosis**, **4,018 disease**, **1,802 shared**, **5,904 union**. Tier1 has **491 genes**, with25 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with5 shortlisted genes shown.

## Research objective

Build a stage-informed biomedical graph linking human liver expression to OptimusKG genes, diseases, drugs, pathways, biological processes and phenotypes, supporting the next team's stage-specific drug-repurposing analysis. Association, prioritisation and annotation are completed; therapeutic prediction/effectiveness remains downstream work.

## Clinical axes and sample units

Fibrosis is F0–F4. Disease-group ordering is control→NAFL→NASH. Broad NAFLD of unspecified subtype is excluded from that ordering. Five studies stage fibrosis; three provide varying disease labels. The full resource contains668 staged biopsies, but the corrected analysis gives each of610 staged patients one contribution. Stage-by-age/sex summaries use327 patients. Raw metadata and measurements remain intact.

## Current graph

Eight labels,126,244 nodes; 35,132,493 relationships at final correction verification. Patient identity is a Sample property, not a Patient node. Curated gene/disease/drug/annotation relationships remain unchanged; only7,706 patient-derived progression links were replaced. The graph is not trimmed to liver diseases only.

## Outputs

Task1 groups genes by qualifying axis/direction; Task2 clusters five stage profiles; Task3 models four adjacent-stage contrasts; Task4 performs local over-representation; Task5 scores genes, checks internal LOSO robustness and maps gene–mechanism connections. Top25 and top12 selection rules were not changed by the correction. Their input gene profiles/scores changed.

| cluster | cluster_name | n_genes | pct_of_fibrosis_genes | mean_F0 | mean_F1 | mean_F2 | mean_F3 | mean_F4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Early increase (F0→F1), then continued | 953 | 25.8 | -0.297 | -0.052 | 0.066 | 0.242 | 0.502 |
| 2 | Late increase (largest at F3→F4) | 1452 | 39.4 | -0.232 | -0.146 | -0.016 | 0.278 | 0.846 |
| 3 | Early rise, then plateau | 272 | 7.4 | -0.271 | -0.016 | 0.103 | 0.225 | 0.14 |
| 4 | Mid decrease (largest at F1→F2) | 322 | 8.7 | 0.194 | 0.175 | -0.084 | -0.248 | -0.356 |
| 5 | Late decrease (largest at F3→F4) | 689 | 18.7 | 0.173 | 0.208 | -0.023 | -0.246 | -0.699 |
