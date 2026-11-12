# GSE225740 fixed-shortlist validation

Completed 7 November 2026. See `analysis_plan.md` for the analysis specification recorded before execution. No genes were reselected, reclustered or removed; no discovery analysis, manuscript or graph was changed.

## Primary findings

Across 87 staged patients (F0=27, F1=26, F2=15, F3=13, F4=6):

- 23/23 genes had the same sign of association with fibrosis severity as their original median-study correlation.
- 21/23 met the defined primary replication criterion: same direction and two-sided Spearman BH q<0.05 across exactly 23 hypotheses.
- KNG1: rho=-0.030623, BH q=0.778273; same direction but not statistically significant.
- SULT1E1: rho=-0.211752, BH q=0.0511883; same direction but just outside the primary threshold.
- No gene showed an opposite-direction association.

The 9,999-permutation sensitivity analysis yielded 22 concordant significant genes. The sole significance-classification change was SULT1E1 (permutation BH q=0.0491364). Its threshold crossing is method-sensitive and subject to Monte Carlo uncertainty; retain the primary 21/23 finding rather than reporting 22/23 as the headline or choosing a method based on this outcome. Report KNG1 and SULT1E1 alongside the other 21 genes.

## Interpretation limits

These results support replication of cross-sectional gene–fibrosis-severity associations in a separately recruited cohort supported by public provenance; individual-level non-overlap is not definitively verified. They do not establish causal roles, within-patient progression, drug efficacy or the complete five-cluster solution. The plotted stage profiles are descriptive, and several intermediate-stage fluctuations differ from discovery despite matching overall association directions. No formal equivalence or cluster-reproduction test was performed.

F4 has six patients. HTR7 and CACNA1C remain flagged for low expression; their nominally significant results should not erase that qualification. The association tests are unadjusted for age, sex or BMI because those individual covariates are not present in the downloaded phenotype file. Percentile bootstrap confidence intervals are pointwise, stratified by stage and not multiplicity-adjusted; they need not give the same threshold decision as BH q values.

## Files

- `validation_all_23_genes.csv`: complete primary/sensitivity results, directions, confidence intervals and low-expression annotations in frozen shortlist order.
- `stage_profiles_23_genes.csv`: original recorded profiles, validation log2CPM means and separately standardized profile shapes for all 23 genes and five stages.
- `association_comparison.pdf`: vector comparison of original median-study rho and validation rho with pointwise bootstrap intervals; PNG preview also provided.
- `stage_profiles_all23.pdf`: vector grid of all frozen original profiles and validation stage means; PNG preview also provided. Each five-stage vector is independently centred/scaled, so this shows shape rather than absolute expression or effect magnitude.
- `validation_summary.json`: counts, exact versions and source/script hashes.

## Reproduce and checks

From the repository root:

```bash
python independent_validation/scripts/validate_gse225740.py
```

Requires NumPy, pandas, SciPy and Matplotlib; executed versions are in the summary. Re-running rewrites generated validation outputs with fixed seeds (permutation 20261107; bootstrap 20261108). Keep the recorded plan and source inputs alongside results.

Verification: input gene/order/sample alignment assertions passed; all 23 primary correlations and their asymptotic p-values were independently recalculated from ranked expression and stages, with manual BH recalculation. Complete 23-row results and 115-row stage-profile table were confirmed. Both figures were visually inspected for readable labels and clipping.
