# Current project context

Final combined active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses216 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,845 fibrosis**, **4,199 disease**, **1,822 shared**, **6,222 union**. Tier1 has **447 genes**, with23 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with4 shortlisted genes shown.

Final purpose, clarified by the researcher: a graph for stage-informed drug repurposing to interrupt progression. Use the active root directories and Paper1_Package, not archived historical numbers.

Same-stage repeat biopsies are averaged; differing stages retain biopsy1 before all contrasts. Stage summaries and LOSO use the same independent-patient policy; LOSO BH uses14,794 eligible genes. Shortlist: up to five Tier1 genes per cluster (23 total), score then|rho|. Top12: enrichment-ranked mechanisms with existing eligibility/redundancy rules. Those selection rules are unchanged.

Raw expression values and curated knowledge were preserved; derived GSE193066 values and five derived disease labels were updated; current patient-derived links match corrected CSVs. The recovered analysis core is not a full measurement-load export. All missing metadata/unit/clinical-definition/causality questions remain explicit in04_LIMITATIONS.md.

Execute source scripts from root. Prioritisation order hc0→hc1→hc2→hc3→hc2→hc4. Never mix old intermediate files with a corrected run.
