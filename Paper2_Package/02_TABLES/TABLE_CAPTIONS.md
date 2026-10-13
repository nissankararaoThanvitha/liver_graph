# Table captions

**Paper2_progression_genes.csv** _(main)_

The master table: 6,222 progression genes, both ladders' rho and q, progression class, and F0-F4 stage means. Nothing filtered.

**task1_class_summary.csv** _(main)_

Gene counts per progression class, with direction counted per ladder.

**task2_summary.csv** _(main)_

The drug-gene extraction in eight numbers. Drug count is given twice — database entries and parent compounds — because "unique drugs" is ambiguous and the two differ by 7.

**task3_druggability_summary.csv** _(main)_

Druggability per group: total genes, drug-connected genes, percentage, unique drugs.

**task3_enrichment_tests.csv** _(main)_

Odds ratios, Fisher p, BH-q and the degree-matched permutation p for each group.

**task4_top_drugs_by_coherence.csv** _(main)_

Drugs ranked by whether they hit a coherent programme rather than many unrelated genes. Read this before the coverage ranking.

**task4_top_drugs_raw_coverage.csv** _(supplementary)_

The top 50 by raw coverage, as the plan requires. Included to show why coverage is the wrong sort key.

**task5_metapath_definitions.csv** _(main)_

The seven metapaths, their schema, and why each is run.

**task5_metapath_counts.csv** _(main)_

Paths, drugs, genes and terms per metapath, capped and uncapped.

**task6_ablation.csv** _(main)_

How far the target ranking moves when each score component is removed. F moves it not at all.

**task6_weight_sensitivity.csv** _(main)_

Rank stability across 2,000 weightings drawn from the whole simplex.

**task6_stable_core.csv** _(main)_

Genes holding a top-50 place across most weightings -- the defensible alternative to a named top-50.

**task7_known_vs_unknown_direction.csv** _(main)_

Known versus unknown drug-action direction.

**task7_consistency_significance.csv** _(main)_

Reversal consistency per group against the vocabulary baseline and a gene-level permutation null.

**task8_leading_candidates.csv** _(main)_

The 30 leading candidates. Therapeutic hypotheses, not treatments.

**task8_evidence_summary.csv** _(main)_

Seven evidence layers by candidate: supports, missing, or out of scope.

**task8_shortlist_support.csv** _(main)_

How many candidates rest on Paper 1's 23-gene shortlist versus broader progression evidence.

**task2_drug_gene_edges.csv** _(supplementary)_

All 8,948 drug-gene relationships with recovered provenance. Large, but a candidate cannot be checked without it.

**task8_final_drug_ranking.csv** _(supplementary)_

All 1,920 ranked drugs, with score band, coherence and flags.
