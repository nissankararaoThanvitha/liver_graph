# GSE49541 fixed-gene validation plan

Recorded 2026-11-07 before calculating group effects or p-values in this cohort.
The GSE225740/GSE281797 results are already known; this is not preregistration.

- Use deposited GC-RMA processed expression (already logarithmic), not RNA-seq CPM or a second log transform. Inspect all sample distributions and exact duplicate profiles; no outcome-driven exclusions.
- Use all 72 liver biopsies, with deposited mild F0–F1 (40) and advanced F3–F4 (32) labels. Do not impute individual stages.
- Read GPL570 annotation embedded in original GEO family SOFT. Retain probes with exactly one Entrez ID that maps uniquely to one Ensembl ID in the frozen discovery identifier map. Exclude multi-Entrez and ambiguous/unmapped probes. Do not use group differences to choose probes. Report annotation limitations and all missing genes.
- Primary gene expression: arithmetic mean of all eligible processed log-scale probes per Ensembl gene. Sensitivity: median of those same probes. These are alternative summaries of the same cohort, not independent validations.
- Test the fixed 23-gene shortlist and all 447 frozen Tier-1 genes; no gene reselection or scoring changes. Primary two-sided Welch t-test comparing advanced minus mild; 95% Welch CI for the unstandardized processed-log expression difference. BH separately across testable shortlist genes and testable Tier-1 genes. Concordant significant means q<0.05 and difference sign agrees with original median fibrosis rho. Missing/constant genes are untestable, not failures or assigned zero.
- Median-probe sensitivity repeats the same contrasts and separate BH families; report it without replacing primary results. Provide descriptive probe-wise direction disagreement, without selecting probes by significance.
- Compare deposited GSM, BioSample, SRA experiment IDs with eight discovery cohorts and two already analysed validation cohorts. Missing identifiers mean unassessable. Check primary source recruitment provenance; accession inequality alone cannot establish donor independence. GSE49541 is also deposited under GSE31803; these are not separate cohorts.
- No F0–F4 shape, adjacent-stage, progression prediction, clinical classification accuracy, or full cluster-pattern validation claims. Do not change graph, discovery outputs, manuscript, branch or commits.

Numerical audit clarification: variation uses a 1e-10 range tolerance, below the deposited 0.001 precision. Welch statistics use the explicit Welch–Satterthwaite formula; a constant group is permitted when the other group has variance. No floor-based exclusion is imposed. Identifier comparisons use sample relation fields only, excluding gene names such as SAMD3 in platform annotations. These audit corrections were made after the initial run and do not select genes by their results.
