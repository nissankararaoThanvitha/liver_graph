# Adjacent-stage and pathway assessment plan

Recorded before this extension is executed, 7 November 2026. The previous gene/tier/cluster association findings are already known; this is an additional analysis, not preregistration.

## Adjacent-stage contrasts

Use frozen discovery gene identities and transitions. For every measurable, nonconstant gene among the original 3,845, fit OLS expression_z ~ intercept + higher-stage indicator separately for F0/F1, F1/F2, F2/F3 and F3/F4. z is the previously prepared within-cohort z score based on 93 deposited samples. In this single cohort, no study dummy is needed. Use the original pooled-variance OLS t test with n-2 df; beta is higher minus lower stage, in within-cohort SD units. No longitudinal interpretation or covariate adjustment. Mark a contrast untestable if its within-contrast residual variance is zero. BH separately over testable genes for each contrast, mirroring the original per-contrast family. Substantial = q<0.05 and |beta|>=0.2. Compare the same gene/contrast with the original result, counting replication among originally substantial, testable contrasts only. Save non-replication and opposite effects, missing genes and untestable contrasts.

Additionally test one frozen largest-transition hypothesis per original shortlisted gene. Extract the exact original Largest_transition, never choose its largest validation change. Apply BH across these 23 selected tests and compare beta direction against the original Transition_beta. Report as a separate correction family; do not mix with all-gene per-contrast rates. Missing or untestable comparisons are explicitly recorded, not zero scores. No power-matched refits are claimed.

## Independent-cohort functional enrichment

Do not re-enrich the unchanged discovery gene lists as if that were independent evidence. Instead test fibrosis Spearman associations anew in all available/nonconstant members of the original 14,794-gene eligibility background, apply BH across this cohort-wide family, then create validation up/down sets using q<0.05 and sign. No rho magnitude filter. Thus membership is determined by the new patients, not the original clusters or tiers.

Use the same local MSigDB 2024.1 GO BP, Reactome, KEGG legacy and Hallmark definitions. Background is the original eligibility universe intersected with measurable/nonconstant validation genes, using the original one-to-one Ensembl/symbol mapping. Restrict each term to this measurable universe and retain sizes 10–500 as originally. One-sided hypergeometric overrepresentation, BH within each direction x database over ALL retained terms (including zero overlaps, p=1; potentially more conservative than an overlap-only family). Minimum query size five. A term failing size restrictions is untestable, not a nonsignificant test.

Compare the frozen top annotations for the five original complete clusters from task4_top_pathways_per_group.csv (C1_all through C5_all), without selecting new top terms based on validation. Expected direction is the sign of the cluster's frozen median discovery rho. Report every original cluster/term pair and its availability, overlap count, validation enrichment and q, including failures. These tests evaluate broad fibrosis-associated biological themes, not independent validation of cluster membership, disease-group specificity, graph edges, causal mechanism or therapeutic action. Do not derive new disease-group labels from fibrosis.

Keep GMT files local; outputs contain term labels and summary statistics, not pathway membership lists or copies of restricted source files. Save source hashes, complete tables, vector PDF figures and limitations. No discovery results, graph or manuscript changes.
