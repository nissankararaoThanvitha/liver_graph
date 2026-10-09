# Current project context

Corrected active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses221 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,688 fibrosis**, **4,018 disease**, **1,802 shared**, **5,904 union**. Tier1 has **491 genes**, with25 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with5 shortlisted genes shown.

Final purpose, clarified by the researcher: a graph for stage-informed drug repurposing to interrupt progression. Use the active root directories and Paper1_Package, not archived historical numbers.

Same-stage repeat biopsies are averaged; differing stages retain biopsy1 before all contrasts. Stage summaries and LOSO use the same independent-patient policy; LOSO BH uses14,794 eligible genes. Top25: five Tier1 genes per cluster, score then|rho|. Top12: enrichment-ranked mechanisms with existing eligibility/redundancy rules. Those selection rules are unchanged.

Raw expression/sample nodes and curated knowledge were preserved; current patient-derived links match corrected CSVs. The recovered analysis core is not a full measurement-load export. All missing metadata/unit/clinical-definition/causality questions remain explicit in04_LIMITATIONS.md.

Execute source scripts from root. Prioritisation order hc0→hc1→hc2→hc3→hc2→hc4. Never mix old intermediate files with a corrected run.
