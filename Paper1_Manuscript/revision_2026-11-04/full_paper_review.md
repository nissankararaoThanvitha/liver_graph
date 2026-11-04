# Review of current Overleaf paper — 4 November 2026

Project: https://www.overleaf.com/project/6aeadb061fca29e951a67537

Read-only review of the current main.tex, supp.tex and compiled main PDF (20 portrait pages). No manuscript changes or full analysis reruns were performed. Current source snapshots are full_audit_main_current.tex.txt and full_audit_supp_current.tex.txt in this directory. Commented-out abstract text was excluded from the review of active claims.

## Confirmed corrections

1. **Main and supplement authors disagree.** Main title page lists N. Thanvitha, V. Lakshmi Nikitha, K. Venkata Dinesh, Biswajit Maity and Ashmita Dey, with Ashmita Dey corresponding. Supplement page S1 lists only the original three authors and V. Lakshmi Nikitha corresponding. Synchronise the supplement with the author-approved main title page; confirm author order and email before submission.

2. **Incorrect comparison denominator, main PDF page 12.** The sentence compares confidence-core membership in Tier 1 with “other fibrosis-associated genes” as 71% versus 48%. From task2_gene_clusters.csv joined to 11_final_tier1_genes.csv: Tier 1 = 319/447 = 71.36%; other genes = 1,519/3,398 = 44.70%; all fibrosis-associated genes = 1,838/3,845 = 47.80%. Use 71% versus 45% for the stated comparison, or explicitly compare Tier 1 with the entire selected set and retain 48%.

3. **Sample matching does not establish equal power.** Results uses “remained prominent at equal power”; Discussion says matched refits “separated biological from power-driven differences”. Matching study composition and sample count does not equalise residual variability, effect sizes or power, and cannot isolate biology from all confounding. Describe persistence under the sample-size-matched design. Keep the existing F4 small-sample and repeated-draw caveats.

4. **The abstract makes LOSO retention ambiguous.** “447 Tier 1 genes (442 retained in every LOSO refit)” can imply that Tier 1 scoring was repeated. The documented outcome is 442 retaining association significance across five omission refits. Say “442 remained statistically significant in all five LOSO refits”. The saved table separately shows 247 retaining |rho| >= 0.30 in all five.

5. **C3 is not literally flat after F1.** Its pooled mean expression values are F0 -0.2697, F1 -0.0120, F2 0.1081, F3 0.2133, F4 0.1360. “Without further increase” is too absolute. Use an approximate shape description such as “early rise followed by a plateau” and avoid implying a tested absence of later differences. This wording occurs in the abstract, cluster table, Results, Discussion/Conclusions and supplement.

6. **The Introduction gap is too broad.** “These studies ... summarise progression as a contrast between categories” conflicts with the table's Separate F0–F4 ticks for Hoang and Govaere, and with the cited Ryaboshapkina study's histology-association analysis. Restrict this statement to studies using pooled contrasts and define the contribution as the specific combination of stage profiles, adjacent-stage analyses, prioritisation and graph context. Do not claim that all earlier studies lacked stage information.

## Discrepancies requiring reconciliation, not automatic replacement

7. **Effect-size count of 890 genes (main PDF page 8).** Filtering data/progression_full/progression_fibrosis.csv with q < .05, at least three studies and n_agree == n_studies reproduces 3,845 selected genes. Using its unrounded median_rho gives 889 with |rho| >= .30 and 165 with |rho| >= .40. Using the rounded task2_gene_clusters.csv yields 897 and 167. The manuscript's 890/165 therefore needs its exact source identified. Do not silently mix rounded scoring quantities with unrounded descriptive statistics. The median |rho| of 0.226 agrees.

8. **Piras comparison-table follow-up tick needs a precise definition.** The original study reports validated coexpression modules, GWAS/TWAS integration and network analyses. Identify the independent cohort or experiment qualifying it under the table's “External/experimental follow-up” heading. Internal network preservation and cross-study synthesis alone should not be presented as independent validation. Source: https://www.life-science-alliance.org/content/lsa/7/6/e202302517.full.pdf . This review does not automatically change the tick.

9. **New nesting result needs a retained supporting output.** The supplement figure reports 91.9% nesting; its visible cross-tabulation supports that arithmetic. The existing local robustness output supports ARI 0.901 and median profile correlation 0.999. Retain the exact k=3 recomputation output and script/configuration with the released result tables so the newer nesting claim can be independently reproduced; a figure alone is less traceable.

## Submission and traceability checks

- The current project explicitly uses a **Human Genomics** presentation, not the earlier Scientific Reports draft. It has a structured abstract, Methods before Results, Conclusions, and 20 main-PDF pages. Confirm the journal target before making further journal-specific formatting changes; do not apply the old draft-page target as a verified journal requirement.
- No AI-use disclosure was found in the active main text. Describe the actual Claude/Codex assistance and author verification, consistent with the publisher's current policy: https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation . Do not invent model versions or author review actions.
- Ethics is currently only “Not applicable.” A short explanation that this is a secondary analysis of public data would clarify the basis, provided the authors confirm the relevant data status and institutional requirements. Do not invent an ethics exemption or approval number.
- Conclusions describes public release of code/graph exports/outputs as a future priority, whereas the availability section says code and result tables are already on GitHub. Separate existing availability from any proposed future release of graph exports.
- The checksum manifest is now present in Overleaf and reproduced in Supplementary Methods. Its HGNC/OptimusKG coverage is expressly limited; newer MSigDB/CTD/ChEMBL inputs are not included. Do not describe this as a checksum manifest covering every input. Original acquisition dates and official release identifiers remain limited as disclosed.
- The current narrow availability statement (“Analysis code and result tables ...”) avoids the previous unsupported downloadable-full-graph claim. It does not itself distribute a KEGG source gene-set file. KEGG-derived enrichment results and pathway names are still discussed; this review is not a legal assessment of redistribution terms.
- Earlier repository checks found newer integration code on paper2-results, not all on main. A submission should identify the relevant branch/commit or release rather than leave readers to assume main reproduces every current graph addition. No repository publishing was performed in this review.

## Checks that passed

- Main source has no missing citation keys, unused bibliography entries or unresolved internal label keys. Compiled PDF text contains no unresolved “??” references.
- All 20 main pages are portrait. A rendered inspection of page 12 confirmed readable Figure 5/Table 4 and exposed the confidence-comparison sentence in the compiled document; this was not an exhaustive visual inspection of all plots at publication size.
- Supplement contains two numbered figures and six numbered tables; the main supplementary-content listing agrees. The asset named figS3_kg_subgraph.pdf is rendered as Figure S2; its filename alone does not make the numbering wrong. Table S6's reference to main Table 5 currently agrees with the main table order.
- Main and supplementary Table S4 agree on 126,999 nodes, 35,160,254 relationships, 15 relationship types, 12,544 drugs and 25,890 drug–gene links. The listed graph additions reconcile the earlier totals: +236 nodes and +22,207 relationships (20,031 + 89 + 2,087). These are document/record consistency checks, not a fresh live-database recount.
- Eligibility is explicit: fibrosis 610; ordered disease groups 45 + 73 + 98 = 216. The 12 ineligible obese-only samples are from GSE126848, not GSE167523.
- Core numerical checks reproduce 3,845 fibrosis-selected genes, 447 Tier 1 genes, cluster Tier 1 counts 93/262/7/3/82, 23 shortlisted genes, 442 significant in every LOSO refit and 247 strong in every refit.
- Adjacent-stage summary output agrees with the reported full-data sample counts, substantial-gene counts 857/1,048/1,116/781 and matched-refit means 12.42/10.22/77.02/369.46.
- Recounting the largest study-adjusted transitions agrees with the new cluster percentages: C2 1,287/1,367 = 94.15%; C3 165/226 = 73.01%; C4 229/397 = 57.68%.
- Existing robustness and bootstrap-shape tables support ARI 0.901, median per-gene profile correlation 0.999, centroid correlation range 0.967–0.996, 1,838 core genes and the per-cluster core counts.
- Primary-source spot checks confirmed the identity of Piras 2024, Yang 2026, Maiers 2026, Ryaboshapkina 2017, Verschuren 2024, Steinhauser 2025 and Younossi 2023 references. This is not a complete verification of every statement attached to all 51 references.

## Scope limit

This review identifies reporting errors and reproducibility gaps; it does not establish that every raw-data decision, model assumption, biological interpretation, external-source licence or live graph property is correct. No evidence here requires immediately rerunning the whole pipeline. Resolve the listed source/count discrepancies before asserting submission readiness.
