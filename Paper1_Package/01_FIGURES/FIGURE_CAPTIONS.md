# Figure captions

Captions for every figure, ready to paste. Main figures are in `main/`, supplementary in `supplementary/`. All are PNG at 300 dpi.

## Figure 1

**Study design and analysis pipeline.**

Eight public GEO liver transcriptome studies parsed to a common long format, harmonised on the gene axis (identifier mapping to Ensembl) and the patient axis (fibrosis stage, disease group, patient identity), standardised within study, and integrated with a curated knowledge layer. Every count shown is read from the committed outputs at draw time.

`Figure1_study_design.png`

## Figure 2

**Overlap between the two progression ladders.**

Genes significantly associated with fibrosis stage and with disease group, giving the fibrosis-only, inflammation-only and shared partitions used throughout.

`Figure2_ladder_overlap.png`

## Figure 3

**Agreement between ladders among shared genes.**

Fibrosis correlation against inflammation correlation for genes significant on both ladders. The two clouds are concordantly rising and concordantly falling genes.

`Figure3_shared_gene_agreement.png`

## Figure 4

**The five fibrosis trajectory shapes.**

Mean standardised expression of each cluster at fibrosis stages F0 to F4. Cluster names were assigned after clustering, from these curves; no gene was assigned to a pattern by hand.

`Figure4_trajectory_shapes.png`

## Figure 5

**Stage profiles of all fibrosis-associated genes.**

Genes in rows grouped by cluster, stages F0-F4 in columns. Values are mean standardised expression per stage.

`Figure5_stage_heatmap.png`

## Figure 6

**Selection of the cluster number.**

Silhouette score, gene-subsample stability and patient-bootstrap stability for k = 3 to 8. See 04_LIMITATIONS.md for the basis of the k = 5 choice, which must be stated in the Methods.

`Figure6_choosing_k.png`

## Figure 7

**Comparison of the four stage transitions.**

Numbers of substantially changing genes on the full data, the same counts under the power-matched design of 30 patients per stage, and the distribution of effect sizes. Equalising power isolates F3-F4 as the transition carrying the largest transcriptional change.

`Figure7_stage_transitions.png`

## Figure 8

**Hallmark process enrichment across groups and clusters.**

All significantly enriched Hallmark processes (false-discovery rate below 0.05) by gene group and trajectory cluster, tested against the eligible-gene background.

`Figure8_hallmark_enrichment.png`

## Figure 9

**Mechanisms shared by the high-confidence fibrosis genes.**

The twelve mechanisms significantly over-represented among the Tier 1 genes, with the genes reaching three or more of them and every shortlisted gene reaching any. Read the convergence as a property of Tier 1 as a whole, not of the shortlist -- see 04_LIMITATIONS.md.

`Figure9_mechanism_network.png`

## Figure S1

**Every fibrosis gene's trajectory, by cluster.**

All genes in grey with the cluster average overlaid, one panel per cluster. Shows the spread behind each averaged shape in Figure 4.

`FigureS1_all_gene_trajectories.png`

## Figure S2

**Distribution of change per transition.**

Per-transition distribution of expression change, at stage-mean level and at patient level.

`FigureS2_transition_deltas.png`

## Figure S3

**GO Biological Process enrichment across groups and clusters.**

Top five GO BP terms per group at FDR < 0.05.

`FigureS3_enrichment_GO_BP.png`

## Figure S4

**Reactome enrichment across groups and clusters.**

Top five Reactome terms per group at FDR < 0.05.

`FigureS4_enrichment_Reactome.png`

## Figure S5

**KEGG enrichment across groups and clusters.**

Top five KEGG terms per group at FDR < 0.05.

`FigureS5_enrichment_KEGG.png`

## Figure S6

**Enrichment dot plot: fibrosis-only increasing genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS6_dotplot_fibrosis_only_up.png`

## Figure S7

**Enrichment dot plot: fibrosis-only decreasing genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS7_dotplot_fibrosis_only_down.png`

## Figure S8

**Enrichment dot plot: inflammation-only increasing genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS8_dotplot_inflammation_only_up.png`

## Figure S9

**Enrichment tested with no significant terms: inflammation-only decreasing genes.**

Tested 422 genes; no terms at FDR < 0.05 in the four collections.

`FigureS9_dotplot_inflammation_only_down.png`

## Figure S10

**Enrichment dot plot: genes increasing on both ladders.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS10_dotplot_shared_up.png`

## Figure S11

**Enrichment dot plot: genes decreasing on both ladders.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS11_dotplot_shared_down.png`

## Figure S12

**Enrichment dot plot: cluster C1 (early increase), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS12_dotplot_C1_all.png`

## Figure S13

**Enrichment dot plot: cluster C1, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS13_dotplot_C1_core.png`

## Figure S14

**Enrichment dot plot: cluster C2 (late increase), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS14_dotplot_C2_all.png`

## Figure S15

**Enrichment dot plot: cluster C2, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS15_dotplot_C2_core.png`

## Figure S16

**Enrichment dot plot: cluster C3 (early rise, then plateau), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS16_dotplot_C3_all.png`

## Figure S17

**Enrichment not tested: cluster C3, high-confidence members only.**

Not tested: 1 confidently assigned gene(s), below the minimum of five.

`FigureS17_dotplot_C3_core.png`

## Figure S18

**Enrichment dot plot: cluster C4 (mid decrease), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS18_dotplot_C4_all.png`

## Figure S19

**Enrichment dot plot: cluster C4, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS19_dotplot_C4_core.png`

## Figure S20

**Enrichment dot plot: cluster C5 (late decrease), all genes.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS20_dotplot_C5_all.png`

## Figure S21

**Enrichment dot plot: cluster C5, high-confidence members only.**

Top five terms per database. x = gene ratio, point size = number of genes, colour = -log10 FDR.

`FigureS21_dotplot_C5_core.png`

---

Each figure is produced by the script named for it in `05_CODE/`, and the numbering is set in one place in `build_paper1_package.py`.
