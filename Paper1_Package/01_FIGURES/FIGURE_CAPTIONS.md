# Figure captions

Captions for every figure in this package, ready to paste. Main figures are in `main/`, supplementary in `supplementary/`. All are PNG at 300 dpi. The numbering is set in `build_paper1_package.py` and nowhere else, so figures cannot be renumbered in one place and not another.

## Figure 1

**Study design and analysis pipeline.**

Eight public GEO liver transcriptome studies parsed to a common long format, harmonised on the gene axis (identifier mapping to Ensembl) and the patient axis (fibrosis stage, disease group, patient identity), standardised within study, and loaded into a Neo4j property graph together with a curated knowledge layer. Every number shown on the figure is read from the committed outputs.

`Figure1_pipeline.png`

## Figure 2

**Overlap between the two progression ladders.**

Genes significantly associated with fibrosis stage and with disease group, giving the fibrosis-only (1,953), inflammation-only (1,047) and shared (1,692) partitions used throughout the paper.

`Figure2_ladder_overlap.png`

## Figure 3

**Agreement between ladders among shared genes.**

Fibrosis correlation against inflammation correlation for the 1,692 shared genes. The two clouds are concordantly rising and concordantly falling genes; one gene (GPD1) is discordant. Spearman rho = 0.725 overall, 0.453 within rising genes and 0.354 within falling genes.

`Figure3_shared_gene_agreement.png`

## Figure 4

**The five fibrosis trajectory shapes.**

Mean standardised expression of each cluster at fibrosis stages F0 to F4. Cluster names were assigned after clustering, from these curves; no gene was assigned to a pattern by hand.

`Figure4_trajectory_shapes.png`

## Figure 5

**Stage profiles of all 3,645 fibrosis-associated genes.**

Genes in rows grouped by cluster, stages F0-F4 in columns. Values are mean standardised expression per stage.

`Figure5_stage_heatmap.png`

## Figure 6

**Choice of cluster number.**

Silhouette score, gene-subsample stability and patient-bootstrap stability for k = 3 to 8. k = 5 is the largest k retaining a gene-subsample adjusted Rand index of at least 0.95.

`Figure6_choosing_k.png`

## Figure 7

**Comparison of the four stage transitions.**

Counts of substantially changing genes on the full data, the same counts under the power-matched design of 30 patients per stage, and the distribution of effect sizes. Equalising power isolates F3-F4 as the transition carrying the largest transcriptional change.

`Figure7_stage_transitions.png`

## Figure 8

**Hallmark process enrichment across groups and clusters.**

All significantly enriched Hallmark processes (FDR < 0.05) by gene group and trajectory cluster, tested against the 14,794-gene eligible background.

`Figure8_hallmark_enrichment.png`

## Figure 9

**Where the high-confidence fibrosis genes converge.**

The twelve mechanisms significantly over-represented among the 507 Tier 1 genes, with the genes reaching three or more of them plus every one of the final 25 reaching any: 46 genes, 12 mechanisms, 169 edges. Edges are INVOLVED_IN for biological processes (126) and IN_PATHWAY for pathways (43). Read the convergence as coming from Tier 1 as a whole, not from the final 25 -- see 05_LIMITATIONS.md.

`Figure9_mechanism_subgraph.png`

## Figure S1

**Every fibrosis gene's trajectory, by cluster.**

All 3,645 genes in grey with the cluster average overlaid, one panel per cluster. Shows the spread behind each averaged shape in Figure 4.

`FigureS1_all_gene_trajectories.png`

## Figure S2

**Distribution of change per transition.**

Per-transition distribution of expression change, at stage-mean level and at patient level.

`FigureS2_transition_deltas.png`

## Figure S3

**GO Biological Process enrichment across groups and clusters.**

Top five GO BP terms per group, FDR < 0.05, against the 14,794-gene background.

`FigureS3_enrichment_GO_BP.png`

## Figure S4

**Reactome enrichment across groups and clusters.**

Top five Reactome terms per group, FDR < 0.05, against the 14,794-gene background.

`FigureS4_enrichment_Reactome.png`

## Figure S5

**KEGG enrichment across groups and clusters.**

Top five KEGG terms per group, FDR < 0.05, against the 14,794-gene background.

`FigureS5_enrichment_KEGG.png`

## Figure S6

**Enrichment dot plot: fibrosis-only rising genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS6_dotplot_fibrosis_only_up.png`

## Figure S7

**Enrichment dot plot: fibrosis-only falling genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS7_dotplot_fibrosis_only_down.png`

## Figure S8

**Enrichment dot plot: inflammation-only rising genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS8_dotplot_inflammation_only_up.png`

## Figure S9

**Enrichment dot plot: genes rising on both ladders.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS9_dotplot_shared_up.png`

## Figure S10

**Enrichment dot plot: genes falling on both ladders.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS10_dotplot_shared_down.png`

## Figure S11

**Enrichment dot plot: cluster C1 (early increase), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS11_dotplot_C1_all.png`

## Figure S12

**Enrichment dot plot: cluster C1, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS12_dotplot_C1_core.png`

## Figure S13

**Enrichment dot plot: cluster C2 (late increase), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS13_dotplot_C2_all.png`

## Figure S14

**Enrichment dot plot: cluster C2, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS14_dotplot_C2_core.png`

## Figure S15

**Enrichment dot plot: cluster C3 (early rise, then plateau), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS15_dotplot_C3_all.png`

## Figure S16

**Enrichment dot plot: cluster C3, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS16_dotplot_C3_core.png`

## Figure S17

**Enrichment dot plot: cluster C4 (mid decrease), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS17_dotplot_C4_all.png`

## Figure S18

**Enrichment dot plot: cluster C4, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS18_dotplot_C4_core.png`

## Figure S19

**Enrichment dot plot: cluster C5 (late decrease), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS19_dotplot_C5_all.png`

## Figure S20

**Enrichment dot plot: cluster C5, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR. Tested against the 14,794-gene eligible background.

`FigureS20_dotplot_C5_core.png`

---

Every figure above is reproduced by the script named for it in `05_CODE/`; the numbers quoted in the captions come from the committed result tables in `03_RESULTS/`, not from memory.
