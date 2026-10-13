# Figure captions

**task2_action_classes.png** _(main)_

What the 8,948 drug-gene links are. Two of the four bars -- pharmacokinetic and direction-not-recorded -- carry no usable mechanism between them, leaving 1,005 links (11.2%) that state both that a drug acts on a gene and which way it pushes.

**task2_consistency_null.png** _(main)_

Mechanism consistency against its null. Observed 52.7% sits inside a null centred on 55.9%, permutation p = 0.78. The null is above 50% because 68% of directional drugs lower their target and 68% of these genes rise, so the right-way pairing is common by accident.

**task3_druggability_by_group.png** _(main)_

Druggability by progression group against an 11.2% background. Genes that fall as disease worsens are roughly twice as drug-connected as genes that rise. Starred groups survive a null matched on non-drug degree.

**task4_coverage_vs_coherence.png** _(main)_

Coverage against coherence, one point per drug. The widest-reaching drugs are the least coherent; the two measures correlate at -0.268 (p = 0.001), so ranking by target count selects promiscuity.

**task4_network.png** _(main)_

The most coherent drugs and the progression genes they reach, with genes grouped by their major fibrosis-associated process. MARIMASTAT's fan into the matrix metallopeptidases reads as one block rather than a coincidence of symbols.

**task5_metapath_sizes.png** _(supplementary)_

Path volume per metapath, with and without a 5-200 gene term cap. Capping costs Reactome 18% of its paths and GO 75%, which is the measure of how much of GO's volume is annotation breadth.

**task6_weight_stability.png** _(supplementary)_

Left: how little of a top-50 survives a random reweighting -- a median of 29 to 32 of 50. Right: the stable core, the genes holding their place across 80% of weightings.

**task7_consistency_vs_null.png** _(main)_

Reversal consistency per progression group against two baselines: what the drug vocabulary gives for free, and a gene-level permutation. Only fibrosis-only rising genes beat their own null.
