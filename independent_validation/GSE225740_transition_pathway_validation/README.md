# Adjacent-stage contrasts and pathway support in GSE225740

Completed 7 November 2026. The recorded plan is `../GSE225740_validation/transition_pathway_plan.md`. This is an extension after the earlier gene-association results were known, not prospective registration. All original genes, tiers, clusters and selected stage boundaries remain fixed. No graph or manuscript edits were made.

## 1. Exact adjacent-stage changes: limited statistical replication

The validation uses the original higher-minus-lower OLS contrast on within-cohort gene z scores. With one study, this is intercept + higher-stage indicator, equivalent to a pooled-variance two-sample t test. It is not a paired-biopsy test, a longitudinal transition or an age/sex/BMI-adjusted model. All observed patients at each of the two stages enter the contrast. The original substantial rule is retained: BH q<0.05 and |beta|>=0.2 SD units.

BH is applied separately across testable genes among the original 3,845 for each contrast. The replication denominator below includes only original substantial contrasts that are testable in validation; it is not the total number of validation-significant genes.

| Contrast | Patients lower / higher | Original substantial, testable | Same effect direction | Same direction + validation substantial |
|---|---:|---:|---:|---:|
| F0–F1 | 27 / 26 | 853 | 811 | 17 |
| F1–F2 | 26 / 15 | 1,033 | 550 | 0 |
| F2–F3 | 15 / 13 | 1,082 | 786 | 0 |
| F3–F4 | 13 / 6 | 767 | 749 | 0 |

Missing/untestable original substantial comparisons were 4, 15, 34 and 14 respectively. The full table preserves all 15,380 original gene/contrast rows, including comparisons not originally substantial, nonsignificant outcomes and missing observations. Results are also summarized for the frozen Tier 1 and shortlist subsets under the same per-contrast correction family.

A separate fixed-shortlist analysis tests exactly one ORIGINAL largest-stage comparison for each of the 23 genes and applies BH over those 23 tests. It does not select the largest change in validation. All 23 were testable; 18/23 had the original effect direction. Three met concordant significance and |beta|>=0.2:

| Gene | Frozen comparison | Validation beta (SD units) | BH q across 23 frozen tests |
|---|---|---:|---:|
| IL32 | F0–F1 | 0.977 | 0.003415 |
| TREM2 | F0–F1 | 1.098 | 0.000229 |
| FABP5 | F0–F1 | 1.180 | 0.000129 |

These results support some early-stage contrasts but do not confirm the original complete stage-boundary map. Failure to reach significance does not prove absence of change: sample sizes are smaller than discovery, later contrasts have very few patients and the per-contrast family is large. Conversely, reduced power cannot be assumed to explain every disagreement; F1–F2 directional agreement is also limited. Do not replace missing/nonsignificant effects with zero or alter the original tier/cluster assignments to improve replication. The earlier 21/23 overall severity-association result remains a distinct endpoint.

## 2. Functional enrichment: substantial, incomplete support for broad themes

To obtain new patient-derived evidence, genes were selected anew from validation associations, rather than re-enriching the unchanged discovery lists. The background was the intersection of the original 14,794-gene eligible universe with measurable, nonconstant validation genes: **13,790 genes**. BH-adjusted two-sided Spearman tests across that full family produced 4,416 increasing and 214 decreasing genes at q<0.05, without an additional rho threshold.

The same local MSigDB 2024.1 libraries were used (GO BP, KEGG legacy, Reactome and Hallmark). Each set was restricted to the measurable background and retained at 10–500 genes. One-sided hypergeometric tests were adjusted within each direction x database over all retained terms, including zero overlaps (p=1). This differs from overlap-only BH and is explicitly retained rather than silently matching only successful terms. Numbers tested per direction: GO BP=4,751; KEGG=183; Reactome=1,247; Hallmark=50. No disease-group labels were inferred and operational fibrosis-only specificity was not independently re-tested.

All original top terms for C1_all–C5_all were then compared in their frozen expected association direction. Of **145 cluster/term pairs**, all were testable and **87 were enriched** at validation q<0.05. Repeated terms across clusters are counted more than once in that pair total: there are 133 unique database/term combinations, of which 75 occur among the supported pairs. The 145 pairs overlap biologically and are not independent hypotheses or 145 distinct pathways.

Examples supported in validation include:

- Reactome extracellular matrix organization (q=3.13e-10), collagen degradation (q=0.000566), and integrin cell surface interactions (q=4.72e-6), in the increasing validation gene set.
- Hallmark inflammatory response (q=0.0274) in increasing genes; C1's specific top GO immune/adhesion terms did not pass despite support from other libraries.
- Cell-cycle-related annotations among C3's original top terms were partially supported, but this does not reproduce C3's original expression plateau.
- Fatty-acid, bile-acid and other metabolic themes in decreasing genes: support varied by exact term/library. For example, the Hallmark fatty acid metabolism term did not meet q<0.05 even though KEGG and Reactome fatty-acid metabolism did.

| Original cluster annotations | Enriched / tested pairs |
|---|---:|
| C1 | 17 / 40 |
| C2 | 35 / 40 |
| C3 | 6 / 25 |
| C4 | 3 / 5 |
| C5 | 26 / 35 |

These assess broad fibrosis-associated annotations in a new cohort, not cluster-specific pathway activity, complete replication of the five cluster memberships, graph-edge validation, causal mechanisms or therapeutic efficacy. In particular, support for C4-associated metabolic terms does not overturn the failure of its centroid pattern to reproduce. The same annotation databases are reused; only the patient-derived gene association evidence is new.

## Files, checks and reproduction

- `all_original_adjacent_contrasts.csv`: complete original/validation paired contrast results.
- `transition_replication_summary.csv`: all-gene, Tier 1 and shortlist subset summaries under the per-contrast family.
- `shortlist23_frozen_largest_transition.csv`: all 23 frozen-comparison results under the separate 23-test family.
- `validation_background_gene_associations.csv`: all 13,790 validation-background associations, including nonsignificant results.
- `validation_enrichment_all_terms.csv`, `validation_enrichment_significant.csv`: complete/supported ORA statistics; no gene-set membership lists.
- `frozen_cluster_top_pathways_comparison.csv`, `frozen_pathway_replication_summary.csv`: all frozen annotations, including nonsignificant comparisons.
- `transition_pathway_summary.pdf`: vector figure; PNG preview also provided. A dash means no original top term for that cluster/database combination.
- `summary.json`: input hashes, including the local GMT hashes, and script hash. Python/library environment is the same as in the preceding tier/cluster validation summary.

Run from repository root:

```bash
python independent_validation/scripts/validate_transitions_pathways_gse225740.py
```

The script reads the existing local GMT files and does not copy them or export membership lists. Keep any source-specific redistribution restrictions when sharing the project.

Verification: all four contrast p-value vectors independently matched SciPy pooled-variance t tests; all hypergeometric p values were recalculated and all eight ORA BH families checked. The complete 145-pair frozen comparison was verified and the figure visually inspected. Patient-identity non-overlap remains supported by provenance, not definitively verified; small F4 n, absent individual demographic covariates and cross-sectional design remain limitations.
