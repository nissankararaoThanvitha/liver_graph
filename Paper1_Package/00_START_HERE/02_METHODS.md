# Completed methodology

## 1. Collection and deposited expression parsing

Eight GEO studies and exact downloaded filenames are listed in06_PROVENANCE/DATA_SOURCES.md. Deposited matrices are parsed by matrix/GCT/tar branches; missing/non-numeric values removed, duplicate raw gene rows keep first, measured zeros retained. This is reanalysis of deposited counts/TPM, not a new alignment/quantification pipeline. Raw source downloads and the full acquisition chain are not supplied here.

## 2. Identifiers and clinical metadata

HGNC approved symbols, Entrez IDs, unambiguous previous symbols/aliases map to canonical version-stripped Ensembl IDs; non-HGNC Ensembl IDs pass through without annotation. Mapping failures are reported. _PAR_Y rows removed; distinct raw IDs collapsing to a gene are summed. The graph holds53,993 union genes;14,794 are measured in all eight studies. Gene category records the pilot categories, not complete HGNC biotypes.

Study-specific expression keys map to GSM via checked title/description/prefix rules. Clinical fibrosis labels, diagnosis provenance, patient identity and biopsy order are added beside raw fields. GSE135251/GSE162694 broad NAFLD is not treated as NASH. GSE130970 diagnosis is derived from steatosis/ballooning and requires clinical-definition review; GSE193066 has no usable disease diagnoses.

## 3. Measurement transformation

Library sums are calculated before mapping/filtering. TPM uses log2(TPM+1); other units use log2(CPM+1), including the unresolved GSE193066 unit. Expression is then standardised by within-study/gene mean and sample SD (ddof1); undefined SD gives0. No DESeq2/limma/edgeR or fitted batch-correction algorithm is used. Effect values are within-study SD units, not fold changes.

## 4. Shared repeat-biopsy policy

biopsy_policy.py selects repeat measurements before filtering any stage contrast. Same-stage repeats are averaged; differing stages retain biopsy1 only. There are28 same-stage and30 different-stage repeated patients. Stage means, discovery, trajectory bootstraps, stage contrasts, matched refits and LOSO use one observation per patient. Raw sample-demographics files continue to contain every original biopsy plus biopsy_number.

## 5. Progression discovery and stage summaries

Spearman within study correlates value_z with each axis; median rho summarises effects; Fisher combines p-values (clipped at10^-300); BH applies separately to retained tests on each axis. Require q<.05, all testable studies agreeing in direction, at least three testable studies. The fibrosis table tests14,794 genes; disease14,784 after testability filtering. Discovery has no minimum rho cutoff. Exported stage means average patients and rho is rounded to three decimals in downstream summary/scoring inputs.

The file diagnostic_both_q_significant.csv is a separate historical-style diagnostic: q significance on both axes plus matching median sign, without the unanimity filter. It is neither the selected shared set nor union. Define selected sets from the two complete progression tables.

## 6. Groups and trajectories

Task1 partitions selected genes into fibrosis-only, disease-only and shared, with direction. Task2 row-z-scores five patient-weighted stage means (ddof0); K-means with50 starts,seed42. Try k3–8;50 gene subsets of80% and50 patient bootstraps,10-start refits. Largest k with mean gene-subset ARI≥.95 is5 in the corrected run. Historical run selected6 under the rule and reported5 as an override; do not transfer that historical selection claim to current results.

A further100 patient bootstraps match centroids by Hungarian assignment. Membership confidence uses only own-cluster matches with r≥.5 and publishes denominators. Study-adjusted profiles use categorical stage+study OLS, then compare cluster/profile agreement.

## 7. Adjacent-stage contrasts

Fit value_z on binary higher-stage indicator plus study dummies, restricting to studies with both stages. Use one patient observation under the shared policy; no random choice between different-stage biopsies remains. OLS t test, BH across the selected fibrosis set within each contrast; substantial means q<.05 and|beta|≥.2. Power-matched refits use four studies,30 patients/stage,50 draws,seed42. Counts are within a preselected set; sampling and selection bias limit inference.

## 8. Local enrichment

MSigDB2024.1.Hs GO BP,KEGG legacy,Reactome,Hallmark; eligible background14,794 unique symbols. Intersect sets with background and retain10–500 members; group minimum5 genes. One-sided hypergeometric via gseapy; BH within group/database,q<.05. Six direction groups,five clusters,five cores at confidence≥.8. Groups below5 are untested, not tested-null.

## 9. Scores, shortlist and LOSO

P:2/1 at|rho|≥.4/.3. T:2/1 at|F4−F0|≥1/.5SD,0 if direction conflicts. X:2 if largest|beta| is substantial in full fit and reproducible with same sign/|beta|≥.2 in≥50% draws,1 for one condition. F:1 for fibrosis-only. B:2/1 for enriched membership in≥2/1 annotation databases via own group/cluster. Sum maximum9; Tier1≥7,Tier2≥5. These features share data and are not five independent validations.

Top25 remains five Tier1 genes per cluster, ranking total score then absolute rho. Alternative cluster-top-score list remains an unselected comparison. LOSO refits per-study correlations on the same biopsy rule, removes one of five staged studies and applies BH to all14,794 eligible genes before reporting Tier1. Selection is not repeated within a held-out clinical prediction design; this is internal robustness.

## 10. OptimusKG and mechanism subgraph

Gene–disease score≥.1; matched measured genes; symmetric interactions deduplicated; source drug indications/actions preserved. Eight node types/fourteen relationship types. Knowledge-loader MERGE does not remove obsolete edges automatically. Raw measurement CREATE loaders need full source exports; the core recovery is not suitable for reloading all measurements.

Pathway and BioProcess each attach directly to Gene. Test Tier1 enrichment against Ensembl background14,794 with BH over Tier1-reached mechanism nodes. Eligible mechanism size10–500,at least10 Tier1 members,q<.05. Rank byq; check Jaccard>.5 redundancy; select12. Draw genes reaching≥3 selected nodes plus shortlisted genes reaching any. No top25/top12 selection rule changed. Annotation connectivity is not causal validation.

