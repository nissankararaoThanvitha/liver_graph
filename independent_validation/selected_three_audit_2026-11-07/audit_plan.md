# Selected-three validation audit, 2026-11-07

Scope: independently review/reproduce GSE225740, GSE213621 and GSE268273 from deposited expression and clinical annotations; preserve frozen genes and all original results. Previous outcomes and selection of these three after inspecting validation results are known. This is a retrospective audit, not preregistration or an unbiased prospective cohort selection.

Audit source units, nonfinite/negative data as applicable, duplicated raw identifiers, mapping, sample crosswalks, source stage labels, exact duplicated patient profiles, and public deposited identifier overlap with the eight discovery and existing validation cohorts. Reproduce two-sided Spearman p-values and BH over each testable subset of the original 14,794-gene universe. Also report targeted BH within fixed shortlist and Tier-1 families, explicitly labelled, without selecting whichever method yields more hits. Grouped stages remain grouped.

Reproduce the frozen signed mean-z scores, direction/effect concordance, AUC and bootstrap method. Recheck complete sample records, missing genes, and clinically heterogeneous groups. Inspect IMID/classic NAFLD composition in GSE268273 and quantify subgroup robustness if enough stage variation. Clinical prediction, causality, exact-stage patterns and donor-level independence are not established by these computations.

The original friend HGNC snapshot/hash was not supplied. A separately downloaded HGNC snapshot is hashed and labelled; discrepancies due to mapping versions are reported, not silently overwritten. Do not claim an exact rerun unless original mapping and computational outputs support it. Frozen-discovery mapping can be used as a labelled comparator.

The friend package and current original outputs remain intact; audit material is isolated here. No branches, commits, pushes, live graph or manuscript modifications. Record all results and limitations, including the fact that the cohorts were prioritized after observing their performance.
