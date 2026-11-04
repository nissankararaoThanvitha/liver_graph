## Results

### Integrated resource and cross-study gene associations

Eight human liver transcriptomic datasets comprised 1,085 samples from 1,027 recorded patient identifiers. After repeat-biopsy handling, the fibrosis analysis included 610 patient-level observations across five studies, while the ordered disease-group analysis included 216 observations across three studies. Gene harmonisation retained 53,993 measured genes, including 14,794 shared across all eight datasets.

Integration with OptimusKG and drug data from ChEMBL, DGIdb, GtoPdb and Open Targets produced a resource containing 126,763 nodes and 35,138,047 relationships. Direct queries verified 12,544 Drug nodes and 25,890 drug–gene relationships. Drug annotations were not inputs to the transcriptomic analyses.

Cross-study analysis identified 3,845 fibrosis-associated genes and 4,199 disease-group-associated genes. The sets shared 1,822 genes, with 2,023 selected only in the fibrosis analysis and 2,377 only in the disease-group analysis (Fig. 2A). Among shared genes, 1,408 showed positive associations on both axes and 384 showed negative associations on both; the remaining 30 showed opposite directions (Fig. 2B). These axis-specific categories describe statistical selection across different study populations rather than established biological specificity.

### Five expression patterns characterised fibrosis severity

The fibrosis-associated genes formed five clusters with distinct expression profiles across F0–F4 (Fig. 3). C1 contained 857 genes showing an early increase followed by continued elevation. C2 comprised 1,367 genes with a late increase, whereas C3 contained 226 genes showing an early rise followed by a plateau. Decreasing profiles comprised C4, with 397 genes showing a mid-stage decrease, and C5, with 998 genes showing a late decrease.

The five-cluster solution satisfied the predefined gene-subset stability criterion. Mean adjusted Rand index was 0.983 for gene-subset refits, compared with 0.592 for patient-bootstrap refits. Although average patterns were reproducible, individual assignments were less stable: 1,838 genes met the membership-confidence threshold of 0.8. Complete cluster-number diagnostics and membership results are provided in the Supplementary Information. These patterns represent cross-sectional differences between patients at different stages, rather than observed trajectories within individuals.

### Adjacent-stage contrasts and enrichment revealed distinct biological contexts

Study-adjusted comparisons identified 857 substantial expression differences between F0–F1, 1,048 between F1–F2, 1,116 between F2–F3 and 781 between F3–F4, using q < 0.05 and |β| ≥ 0.2 (Fig. 4A). F2–F3 had the largest number of substantial differences, while F3–F4 had the largest median absolute coefficient, at 0.352 within-study standard-deviation units. However, F3–F4 included only 34 F4 observations. Sample-size-matched refits produced markedly different counts and broad distributions, indicating sensitivity to patient composition and statistical power.

Functional enrichment distinguished immune, matrix-associated and metabolic annotations (Fig. 4B). Fibrosis-only increasing genes were enriched for T-cell activation and IL6–JAK–STAT3 signalling, while genes positively associated with both clinical axes were enriched for collagen formation and extracellular matrix organisation. The late-increasing C2 cluster was enriched for the Hallmark epithelial–mesenchymal transition set (q = 5.25 × 10⁻²⁷); C3 was enriched for E2F targets (q = 1.24 × 10⁻¹⁴). The late-decreasing C5 cluster was enriched for bile-acid and fatty-acid metabolism.

Enrichment depended partly on cluster-membership confidence, particularly for C4, whose full-cluster and confidence-core analyses shared no significant Reactome term. Complete enrichment results are provided in the Supplementary Information. These findings indicate annotation over-representation rather than demonstrated activation or suppression of biological processes.

### Multi-evidence prioritisation identified 23 representative candidates

The prioritisation framework identified 447 Tier 1 genes: 93 in C1, 262 in C2, seven in C3, three in C4 and 82 in C5. Selecting up to five qualifying genes per cluster yielded 23 candidates because C4 contained only three genes meeting the threshold (Fig. 5). PDGFRA, CACNA1C, TPM4, PLK3 and TAX1BP3 achieved the maximum score of nine. The complete candidate table is provided in the Supplementary Information.

Leave-one-study-out analysis retained statistical significance for 442 of the 447 Tier 1 genes across all five refits, while 247 retained an absolute median correlation of at least 0.30 throughout. All 23 shortlisted genes remained significant, and 18 retained the magnitude threshold. Nevertheless, shortlist membership confidence ranged from 0.38 to 0.99, indicating that high prioritisation scores did not ensure equally stable cluster assignments.

Sixteen candidates were retained across all four label/transformation configurations. Removing the fibrosis-only component while retaining the score threshold reduced the Tier 1 set to 286 genes and the shortlist to 21; this comparison also reduced the maximum achievable score. These analyses assess internal robustness and sensitivity, rather than independent validation.

### Knowledge-graph annotations contextualised prioritised genes

The filtered annotation network connected 42 Tier 1 genes to twelve selected pathway or biological-process annotations through 154 relationships. Enriched annotations included extracellular matrix organisation, cell–cell adhesion, angiogenesis, integrin interactions and PDGF signalling.

Four shortlisted genes appeared in this network: PDGFRA connected to five selected annotations, while EPHA3, NFASC and TREM2 each connected to one. The remaining displayed genes belonged to the wider Tier 1 set and each reached at least three annotations. The network therefore represents annotation sharing within a selected subset, rather than convergence across the complete shortlist. The full subgraph and enrichment statistics are provided in the Supplementary Information.
