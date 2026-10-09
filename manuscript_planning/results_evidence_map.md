# Current claim-to-evidence map

| Finding | Source/locator | Manuscript placement | Boundary |
|---|---|---|---|
| Eight cohorts,1085 samples/1027 patient IDs;610 independent staged patients | Table1/clinical table;biopsy decision ledger | Methods,cohort Results,Figure1 | Raw resource counts differ from independent analysis n |
| Selected genes3688 fibrosis,4018 disease,1802 shared,5904 union | progression tables,q<.05 AND unanimity;Table2 | Results,Figures2–3 | Correlation/selection,not diagnosis or causal progression |
| Five cluster shapes953/1452/272/322/689 | Table3;TableS2/S5;Task2 outputs | Results,Figures4–6,S1 | Per-gene confidence/denominator and conditional matching matter |
| Adjacent contrasts and matched refits | Table4,TableS6/S7;Task3 | Results,Figure7,S2 | Preselected gene set,cross-sectional;F4 underpowered |
| Current group/core enrichment | Table5,TableS8–S10;Task4 all/per-run tables | Results,Figure8,supplementary panels | C3core1 untested; disease-only down tested with no terms; annotations overlap |
|491 Tier1 and25 balanced candidates | Table6(confidence added),TableS11/S12,S14–S18 | Results/Methods,shortlist table | Complementary scoring,not validated drug targets |
|488/491 significant all five LOSO;274/491 retain effect bar | TableS13 plus all-eligible run table | Results/supplement robustness | Full-family correction;selected-set internal robustness,not external/nested validation |
|12 mechanisms,42 genes,154 edges,5 shortlist genes shown | TableS19 sheets1–6;Figure9 | Results/annotation network | Gene→Pathway and Gene→BioProcess are separate links;not causal mechanisms |
| Corrected live graph links | graph_nodes andknowledge_layer matching edge CSVs;graph update verification | Resource Results,data/code availability | Only patient-derived edges updated;raw/curated graph preserved |

Introduction requires verified primary sources on liver disease,prognosis,modern nomenclature,clinical staging and comparable graphs. Current annotations are not a substitute for a literature review. Drug prediction and therapeutic validation belong to downstream work.

Figures1–9 andS1–S21 are rebuilt/current. S9 explicitly shows a tested-null enrichment result;S17 explicitly shows untested C3core1. Table6 includes confidence;TableS19 uses491 Tier1 rather than an old count in its sheet title. All displays still need final journal-size proof and biological interpretation before submission.

Current numerical statistics:

# Current statistics and test families

Corrected active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses221 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,688 fibrosis**, **4,018 disease**, **1,802 shared**, **5,904 union**. Tier1 has **491 genes**, with25 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with5 shortlisted genes shown.

## Trajectory sizes and confidence

| cluster | cluster_name | median_shape_corr | min_shape_corr | genes_confidence>=0.8 | n_genes |
| --- | --- | --- | --- | --- | --- |
| 1 | Early increase (F0→F1), then continued | 0.978 | 0.864 | 32 | 953 |
| 2 | Late increase (largest at F3→F4) | 0.996 | 0.948 | 803 | 1452 |
| 3 | Early rise, then plateau | 0.962 | 0.78 | 1 | 272 |
| 4 | Mid decrease (largest at F1→F2) | 0.961 | -0.74 | 96 | 322 |
| 5 | Late decrease (largest at F3→F4) | 0.991 | -0.603 | 511 | 689 |

## k diagnostics

| k | silhouette | stability_ARI_mean | stability_ARI_sd | patient_bootstrap_ARI_mean | patient_bootstrap_ARI_sd |
| --- | --- | --- | --- | --- | --- |
| 3 | 0.5471749740852124 | 0.9898852680109228 | 0.0080905017903522 | 0.7461986528119308 | 0.0370843963289989 |
| 4 | 0.4570698794024951 | 0.9775929165690715 | 0.0149523703477535 | 0.5590663072256323 | 0.0725023199426928 |
| 5 | 0.3320389786771027 | 0.96000734575419 | 0.0176872269654241 | 0.5153269898291009 | 0.0598684127391846 |
| 6 | 0.2921865660403158 | 0.9068214339786635 | 0.0511485212943671 | 0.4688551021163175 | 0.0466913205088611 |
| 7 | 0.2875609637143108 | 0.915514383551574 | 0.0316739007179199 | 0.4184619313126088 | 0.0516103699682386 |
| 8 | 0.2778694976935945 | 0.887588529894318 | 0.071396820491235 | 0.4038718792074401 | 0.0451844819171934 |

## Stage contrasts

| transition | n_F0 | n_F1 | studies_used | n_significant_q<0.05 | n_substantial | n_substantial_up | n_substantial_down | median_abs_beta | n_abs_beta>=0.2 | median_abs_delta_mean | n_F2 | n_F3 | n_F4 | matched_n_substantial_mean (n=30/stage) | matched_n_substantial_sd | matched_n_substantial_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F0→F1 | 152.0 | 160.0 | 5 | 1200 | 1197 | 1166 | 31 | 0.1888 | 1741 | 0.138 |  |  |  | 14.48 | 77.0 | 0.0 |
| F1→F2 |  | 160.0 | 5 | 1003 | 1000 | 550 | 450 | 0.1814 | 1599 | 0.161 | 152.0 |  |  | 10.94 | 35.5 | 0.0 |
| F2→F3 |  |  | 5 | 1086 | 1086 | 872 | 214 | 0.2246 | 2075 | 0.214 | 152.0 | 112.0 |  | 57.18 | 108.3 | 1.5 |
| F3→F4 |  |  | 4 | 847 | 847 | 791 | 56 | 0.3753 | 2738 | 0.363 |  | 86.0 | 34.0 | 406.44 | 411.5 | 251.5 |

## Enrichment counts

| group | n_genes | GO_BP | KEGG | Reactome | Hallmark |
| --- | --- | --- | --- | --- | --- |
| fibrosis_only_up | 1215 | 345 | 31 | 28 | 9 |
| fibrosis_only_down | 671 | 61 | 23 | 27 | 8 |
| inflammation_only_up | 1794 | 137 | 8 | 208 | 15 |
| inflammation_only_down | 422 | 0 | 0 | 0 | 0 |
| shared_up | 1460 | 393 | 30 | 87 | 26 |
| shared_down | 329 | 85 | 26 | 10 | 6 |
| C1_all | 953 | 377 | 48 | 65 | 18 |
| C2_all | 1452 | 486 | 23 | 57 | 20 |
| C3_all | 272 | 82 | 3 | 33 | 4 |
| C4_all | 322 | 15 | 4 | 5 | 6 |
| C5_all | 689 | 140 | 30 | 33 | 6 |
| C1_core | 32 | 65 | 1 | 0 | 0 |
| C2_core | 803 | 284 | 6 | 35 | 22 |
| C3_core | 1 | 0 | 0 | 0 | 0 |
| C4_core | 96 | 0 | 1 | 1 | 7 |
| C5_core | 511 | 129 | 29 | 25 | 5 |

C3 core has one gene and is untested. Zero entries for that core do not mean a null test. Other current core findings must be read from this table rather than earlier captions.

## LOSO

BH family14,794 eligible genes per omitted-study run. Tier1 reports2,455 gene/run records: 488/491 significant in all five refits; 274/491 retain median|rho|≥.30 in all five. Direction retention follows discovery consistency and is not an independent validation test.

## Selected graph mechanisms

| Mechanism_ID | mechanism | n_tier1_genes | fold_enrichment | q_value |
| --- | --- | --- | --- | --- |
| GO_0030198 | extracellular matrix organization | 27 | 7.07 | 1.162665179587812e-12 |
| GO_0001525 | angiogenesis | 38 | 4.51 | 7.273187557856588e-12 |
| GO_0030335 | positive regulation of cell migration | 35 | 4.61 | 3.497089442771115e-11 |
| GO_0098609 | cell-cell adhesion | 32 | 4.87 | 7.409231735728561e-11 |
| REACT:R-HSA-9925563 | Developmental Lineage of Pancreatic Ductal Cells | 16 | 10.96 | 2.100212274778178e-10 |
| REACT:R-HSA-3000178 | ECM proteoglycans | 19 | 8.42 | 2.494967025791799e-10 |
| GO_0007229 | integrin-mediated signaling pathway | 22 | 6.76 | 3.622415499952244e-10 |
| REACT:R-HSA-216083 | Integrin cell surface interactions | 20 | 7.63 | 3.622415499952244e-10 |
| GO_0016477 | cell migration | 36 | 3.94 | 7.128893887495718e-10 |
| GO_0007179 | transforming growth factor beta receptor signaling pathway | 21 | 6.66 | 1.362281830679808e-09 |
| GO_0070374 | positive regulation of ERK1 and ERK2 cascade | 26 | 4.93 | 5.201757681419712e-09 |
| REACT:R-HSA-8874081 | MET activates PTK2 signaling | 12 | 12.47 | 1.562982830805839e-08 |

Displayed network42 genes+12 mechanisms,154 edges. Five of25 shortlisted genes appear; ITGA2 reaches6 selected mechanisms and PDGFRA4; ADAMTSL2,NFASC,TREM2 reach one each.

Software: core dependency versions are those pinned in requirements; corrected run Python3.12.14. Baseline discovery reproduced the historical results under this runtime before correction. See the archived correction audit's runtime_requirements.txt for the exact installed environment.

