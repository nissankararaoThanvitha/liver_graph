# Current claim-to-evidence map

| Finding | Source/locator | Manuscript placement | Boundary |
|---|---|---|---|
| Eight cohorts,1085 samples/1027 patient IDs;610 independent staged patients | Table1/clinical table;biopsy decision ledger | Methods,cohort Results,Figure1 | Raw resource counts differ from independent analysis n |
| Selected genes3845 fibrosis,4199 disease,1822 shared,6222 union | progression tables,q<.05 AND unanimity;Table2 | Results,Figures2–3 | Correlation/selection,not diagnosis or causal progression |
| Five cluster shapes857/1367/226/397/998 | Table3;TableS2/S5;Task2 outputs | Results,Figures4–6,S1 | Per-gene confidence/denominator and conditional matching matter |
| Adjacent contrasts and matched refits | Table4,TableS6/S7;Task3 | Results,Figure7,S2 | Preselected gene set,cross-sectional;F4 underpowered |
| Current group/core enrichment | Table5,TableS8–S10;Task4 all/per-run tables | Results,Figure8,supplementary panels | Read current core test status and per-group enrichment; annotations overlap |
|447 Tier1 and23 balanced candidates | Table6(confidence added),TableS11/S12,S14–S18 | Results/Methods,shortlist table | Complementary scoring,not validated drug targets |
|442/447 significant all five LOSO;247/447 retain effect bar | TableS13 plus all-eligible run table | Results/supplement robustness | Full-family correction;selected-set internal robustness,not external/nested validation |
|12 mechanisms,42 genes,154 edges,4 shortlist genes shown | TableS19 sheets1–6;Figure9 | Results/annotation network | Gene→Pathway and Gene→BioProcess are separate links;not causal mechanisms |
| Corrected live graph links | graph_nodes andknowledge_layer matching edge CSVs;graph update verification | Resource Results,data/code availability | Only patient-derived edges updated;raw/curated graph preserved |

Introduction requires verified primary sources on liver disease,prognosis,modern nomenclature,clinical staging and comparable graphs. Current annotations are not a substitute for a literature review. Drug prediction and therapeutic validation belong to downstream work.

Figures1–9 andS1–S21 are rebuilt/current. Empty enrichment panels explicitly distinguish tested-null from untested groups. Table6 includes confidence;TableS19 uses447 Tier1 rather than an old count in its sheet title. All displays still need final journal-size proof and biological interpretation before submission.

Current numerical statistics:

# Current statistics and test families

Final combined active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses216 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,845 fibrosis**, **4,199 disease**, **1,822 shared**, **6,222 union**. Tier1 has **447 genes**, with23 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with4 shortlisted genes shown.

## Trajectory sizes and confidence

| cluster | cluster_name | median_shape_corr | min_shape_corr | genes_confidence>=0.8 | n_genes |
| --- | --- | --- | --- | --- | --- |
| 1 | Early increase (F0→F1), then continued | 0.977 | 0.825 | 90 | 857 |
| 2 | Late increase (largest at F3→F4) | 0.996 | -0.426 | 806 | 1367 |
| 3 | Early rise, then plateau | 0.967 | -0.62 | 74 | 226 |
| 4 | Mid decrease (largest at F1→F2) | 0.968 | 0.756 | 126 | 397 |
| 5 | Late decrease (largest at F3→F4) | 0.993 | -0.374 | 742 | 998 |

## k diagnostics

| k | silhouette | stability_ARI_mean | stability_ARI_sd | patient_bootstrap_ARI_mean | patient_bootstrap_ARI_sd |
| --- | --- | --- | --- | --- | --- |
| 3 | 0.5874274548260973 | 0.981079066813464 | 0.0182811587200682 | 0.7912846310741619 | 0.0627296762171589 |
| 4 | 0.4378337161592175 | 0.970826783010548 | 0.017374617358458 | 0.6786661681134757 | 0.0806373554910996 |
| 5 | 0.3521700923761786 | 0.9834666794034416 | 0.0107295731534814 | 0.5919089483352878 | 0.0622922493704726 |
| 6 | 0.3167085315462095 | 0.8163589350097848 | 0.1716793476725813 | 0.5136759935239583 | 0.0727013446691447 |
| 7 | 0.2803957733778422 | 0.9343376240807432 | 0.045203963188876 | 0.4495038477806786 | 0.0478233247484487 |
| 8 | 0.2841160184125451 | 0.8676311443462404 | 0.1104395911485979 | 0.4257066006694372 | 0.0455258758492673 |

## Stage contrasts

| transition | n_F0 | n_F1 | studies_used | n_significant_q<0.05 | n_substantial | n_substantial_up | n_substantial_down | median_abs_beta | n_abs_beta>=0.2 | median_abs_delta_mean | n_F2 | n_F3 | n_F4 | matched_n_substantial_mean (n=30/stage) | matched_n_substantial_sd | matched_n_substantial_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F0→F1 | 152.0 | 160.0 | 5 | 858 | 857 | 822 | 35 | 0.1599 | 1522 | 0.125 |  |  |  | 12.42 | 67.6 | 0.0 |
| F1→F2 |  | 160.0 | 5 | 1049 | 1048 | 459 | 589 | 0.1862 | 1730 | 0.168 | 152.0 |  |  | 10.22 | 34.4 | 0.0 |
| F2→F3 |  |  | 5 | 1116 | 1116 | 792 | 324 | 0.2236 | 2165 | 0.213 | 152.0 | 112.0 |  | 77.02 | 154.2 | 1.0 |
| F3→F4 |  |  | 4 | 781 | 781 | 723 | 58 | 0.3518 | 2717 | 0.366 |  | 86.0 | 34.0 | 369.46 | 383.4 | 232.5 |

## Enrichment counts

| group | n_genes | GO_BP | KEGG | Reactome | Hallmark |
| --- | --- | --- | --- | --- | --- |
| fibrosis_only_up | 1040 | 356 | 30 | 17 | 7 |
| fibrosis_only_down | 983 | 68 | 19 | 23 | 5 |
| inflammation_only_up | 2042 | 141 | 6 | 206 | 11 |
| inflammation_only_down | 335 | 0 | 0 | 0 | 1 |
| shared_up | 1408 | 421 | 30 | 83 | 27 |
| shared_down | 384 | 86 | 24 | 11 | 4 |
| C1_all | 857 | 370 | 39 | 51 | 18 |
| C2_all | 1367 | 518 | 21 | 44 | 20 |
| C3_all | 226 | 87 | 2 | 28 | 3 |
| C4_all | 397 | 0 | 1 | 1 | 3 |
| C5_all | 998 | 162 | 32 | 45 | 5 |
| C1_core | 90 | 181 | 8 | 13 | 4 |
| C2_core | 806 | 324 | 5 | 40 | 21 |
| C3_core | 74 | 87 | 2 | 26 | 3 |
| C4_core | 126 | 0 | 0 | 1 | 0 |
| C5_core | 742 | 130 | 30 | 39 | 5 |

Core results and test status must be read from the current enrichment tables; groups with fewer than five genes are untested, not tested-null.

## LOSO

BH family14,794 eligible genes per omitted-study run. Tier1 reports2,235 gene/run records: 442/447 significant in all five refits; 247/447 retain median|rho|≥.30 in all five. Direction retention follows discovery consistency and is not an independent validation test.

## Selected graph mechanisms

| Mechanism_ID | mechanism | n_tier1_genes | fold_enrichment | q_value |
| --- | --- | --- | --- | --- |
| GO_0030198 | extracellular matrix organization | 27 | 7.77 | 1.056719036528773e-13 |
| GO_0098609 | cell-cell adhesion | 32 | 5.35 | 8.597685117371849e-12 |
| GO_0001525 | angiogenesis | 36 | 4.69 | 8.599051522770523e-12 |
| REACT:R-HSA-216083 | Integrin cell surface interactions | 20 | 8.38 | 1.076339087375278e-10 |
| GO_0030335 | positive regulation of cell migration | 32 | 4.62 | 2.779379358362056e-10 |
| REACT:R-HSA-3000178 | ECM proteoglycans | 18 | 8.76 | 5.653463072107831e-10 |
| REACT:R-HSA-9925563 | Developmental Lineage of Pancreatic Ductal Cells | 15 | 11.28 | 6.485206642148144e-10 |
| GO_0070374 | positive regulation of ERK1 and ERK2 cascade | 26 | 5.41 | 7.944906263589113e-10 |
| GO_0016477 | cell migration | 34 | 4.09 | 1.069674523599284e-09 |
| GO_0007229 | integrin-mediated signaling pathway | 20 | 6.75 | 3.715753984486238e-09 |
| REACT:R-HSA-6785807 | Interleukin-4 and Interleukin-13 signaling | 19 | 6.76 | 1.105684222848239e-08 |
| REACT:R-HSA-186797 | Signaling by PDGF | 12 | 12.81 | 1.283585189724749e-08 |

Displayed network42 genes+12 mechanisms,154 edges. Four of23 shortlisted genes appear; PDGFRA reaches5 selected mechanisms; EPHA3,NFASC,TREM2 reach one each.

Software: core dependency versions are those pinned in requirements; corrected run Python3.12.14. Baseline discovery reproduced the historical results under this runtime before correction. See the archived correction audit's runtime_requirements.txt for the exact installed environment.

