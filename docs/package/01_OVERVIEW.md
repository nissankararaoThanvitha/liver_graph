# Objective and completed outputs

Final combined active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses216 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,845 fibrosis**, **4,199 disease**, **1,822 shared**, **6,222 union**. Tier1 has **447 genes**, with23 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with4 shortlisted genes shown.

## Research objective

Build a stage-informed biomedical graph linking human liver expression to OptimusKG genes, diseases, drugs, pathways, biological processes and phenotypes, supporting the next team's stage-specific drug-repurposing analysis. Association, prioritisation and annotation are completed; therapeutic prediction/effectiveness remains downstream work.

## Clinical axes and sample units

Fibrosis is F0–F4. Disease-group ordering is control→NAFL→NASH. Broad NAFLD of unspecified subtype is excluded from that ordering. Five studies stage fibrosis; three provide varying disease labels. The full resource contains668 staged biopsies, but the corrected analysis gives each of610 staged patients one contribution. Stage-by-age/sex summaries use327 patients. Raw metadata and measurements remain intact.

## Current graph

Eight labels,126,244 nodes; 35,132,831 relationships expected from final exports; live verification status: True. Patient identity is a Sample property, not a Patient node. Curated gene/disease/drug/annotation relationships remain unchanged; 8,044 patient-derived progression links represent the final combined analysis. Five derived disease labels are unclassified; GSE193066 derived expression preserves deposited RLE normalisation. Raw expression values and curated knowledge are preserved. The graph is not trimmed to liver diseases only.

## Outputs

Task1 groups genes by qualifying axis/direction; Task2 clusters five stage profiles; Task3 models four adjacent-stage contrasts; Task4 performs local over-representation; Task5 scores genes, checks internal LOSO robustness and maps gene–mechanism connections. Top25 and top12 selection rules were not changed by the correction. Their input gene profiles/scores changed.

| cluster | cluster_name | n_genes | pct_of_fibrosis_genes | mean_F0 | mean_F1 | mean_F2 | mean_F3 | mean_F4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Early increase (F0→F1), then continued | 857 | 22.3 | -0.295 | -0.057 | 0.067 | 0.237 | 0.515 |
| 2 | Late increase (largest at F3→F4) | 1367 | 35.6 | -0.227 | -0.142 | -0.018 | 0.266 | 0.86 |
| 3 | Early rise, then plateau | 226 | 5.9 | -0.27 | -0.012 | 0.108 | 0.213 | 0.136 |
| 4 | Mid decrease (largest at F1→F2) | 397 | 10.3 | 0.161 | 0.182 | -0.075 | -0.26 | -0.279 |
| 5 | Late decrease (largest at F3→F4) | 998 | 26.0 | 0.184 | 0.195 | -0.034 | -0.259 | -0.658 |
