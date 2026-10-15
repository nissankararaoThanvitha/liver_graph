# Paper 2 — Task 5: MetaPaths from drugs to fibrosis-progression biology

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **6,222 genes**.
**Scope:** knowledge graph (read-only Neo4j) + Paper 1 results only. Drug → Gene steps use **pharmacological-target links** (no ENZYME/TRANSPORTER/CARRIER; Task 3). Drugs = the **2,407** Task 2 drugs with such a link to a progression gene (1,109 repurposing candidates, 559 on the main list; Task 4).
Script: `Paper2_Results/code/task5_metapaths.py`. Every Cypher statement: `metapath_queries.cypher`.

**MetaPaths show biological connectivity in the graph, not proof that a drug works.**

![Task 5 diagram](Task5_diagram.png)

## Definitions
See `metapath_definitions.csv`. Degree-normalised support for drug *d* and end node *e*: **DNS = paths(d,e) / √(deg(d) × deg(e))**, where deg(d) = pharmacological targets of *d* in the whole graph and deg(e) = genes on the end node (disease, pathway, process, term) or, for gene end nodes, pathways of the gene (M4/M5) or drugs of the gene (M6). DNS down-weights promiscuous drugs and huge pathways. DNS values are comparable **within** a MetaPath, not across MetaPaths (different end-node degrees).

## Results

| MetaPath | paths | unique drugs | unique genes | unique end nodes | degree-normalised support (sum) | mean DNS per pair | candidate drugs | main-list drugs |
|---|---|---|---|---|---|---|---|---|
| M1 Drug→Gene→LiverDisease | 24,497 | 1,921 | 437 | 61 | 712.59 | 0.0419 | 926 | 488 |
| M1f Drug→Gene→FibrosisSpectrumDisease | 3,164 | 844 | 82 | 10 | 143.84 | 0.0611 | 537 | 302 |
| M2 Drug→Gene→Pathway | 33,089 | 2,369 | 874 | 1,445 | 4725.4 | 0.1665 | 1,102 | 559 |
| M3 Drug→Gene→BioProcess | 131,177 | 2,406 | 948 | 5,284 | 16454.66 | 0.1421 | 1,109 | 559 |
| M4 Drug→Gene→Pathway←ProgressionGene | 1,058,939 | 2,394 |  | 3,888 | 215468.84 | 0.4902 | 1,105 | 558 |
| M5 Drug→Gene→Pathway←C1 gene | 184,201 | 2,272 |  | 561 | 38980.3 | 0.4771 | 1,061 | 539 |
| M5 Drug→Gene→Pathway←C2 gene | 249,499 | 2,252 |  | 814 | 53930.1 | 0.5201 | 1,060 | 534 |
| M5 Drug→Gene→Pathway←C3 gene | 43,870 | 1,979 |  | 147 | 9712.3 | 0.5602 | 967 | 481 |
| M5 Drug→Gene→Pathway←C4 gene | 62,456 | 2,012 |  | 251 | 11645.33 | 0.4825 | 925 | 458 |
| M5 Drug→Gene→Pathway←C5 gene | 121,510 | 2,307 |  | 612 | 26918.44 | 0.5219 | 1,079 | 543 |
| M6 Drug→F0→F1 transition gene | 926 | 740 | 136 | 136 | 137.73 | 0.1487 | 378 | 195 |
| M6 Drug→F1→F2 transition gene | 1,205 | 891 | 220 | 220 | 202.36 | 0.1679 | 437 | 220 |
| M6 Drug→F2→F3 transition gene | 1,471 | 845 | 184 | 184 | 168.2 | 0.1143 | 466 | 239 |
| M6 Drug→F3→F4 transition gene | 828 | 590 | 116 | 116 | 104.93 | 0.1267 | 360 | 209 |
| M7 GO_BP [graph node] | 26,126 | 2,226 | 714 | 753 | 2508.17 | 0.1098 | 1,056 | 545 |
| M7 GO_BP [graph proxy (approx.)] | 586 | 352 | 61 | 13 | 63.25 | 0.1178 | 117 | 47 |
| M7 GO_BP [Paper 1 gene list] | 10,073 | 1,205 | 360 | 187 | 514.3 | 0.0585 | 582 | 312 |
| M7 Reactome [graph node] | 5,314 | 1,547 | 389 | 115 | 452.97 | 0.1053 | 696 | 365 |
| M7 Reactome [graph proxy (approx.)] | 670 | 373 | 96 | 19 | 70.82 | 0.1272 | 94 | 36 |
| M7 Reactome [Paper 1 gene list] | 3,443 | 1,231 | 305 | 49 | 167.37 | 0.0594 | 599 | 307 |
| M7 KEGG [graph proxy (approx.)] | 131 | 116 | 26 | 3 | 15.18 | 0.1254 | 31 | 8 |
| M7 KEGG [Paper 1 gene list] | 4,339 | 828 | 244 | 83 | 293.92 | 0.0841 | 334 | 170 |
| M7 Hallmark [Paper 1 gene list] | 2,694 | 1,100 | 258 | 36 | 132.22 | 0.0535 | 483 | 246 |

"unique genes" = middle gene (for M4/M5 it is any pharmacological target, so it is not shown per row; 1,869 target genes sit in at least one pathway). M7 rows are split by database and by how the term reaches the graph: graph node (exact name), graph proxy (gene overlap, **approximate**), or Paper 1 gene list (no graph node).

### Stage-transition genes with drugs (M6)
| MetaPath | notes |
|---|---|
| M6 Drug→F0→F1 transition gene | 858 significant genes; 136 with a drug (125 rising / 11 falling at this step) |
| M6 Drug→F1→F2 transition gene | 1049 significant genes; 220 with a drug (76 rising / 144 falling at this step) |
| M6 Drug→F2→F3 transition gene | 1116 significant genes; 184 with a drug (115 rising / 69 falling at this step) |
| M6 Drug→F3→F4 transition gene | 781 significant genes; 116 with a drug (102 rising / 14 falling at this step) |

### Main-list drugs with the strongest fibrosis-spectrum disease support (M1f, DNS)
| Drug | targets | M1f paths | M1f DNS |
|---|---|---|---|
| INDEGLITAZAR | 4 | 21 | 0.905 |
| TESAGLITAZAR | 2 | 14 | 0.853 |
| MURAGLITAZAR | 2 | 14 | 0.853 |
| GW501516 | 2 | 14 | 0.853 |
| FENOFIBRIC ACID | 5 | 21 | 0.81 |
| INAMRINONE | 8 | 24 | 0.768 |
| ALEGLITAZAR | 3 | 14 | 0.697 |
| CIPROFIBRATE | 1 | 7 | 0.603 |
| FENOPROFEN | 4 | 14 | 0.603 |
| INT131 | 1 | 7 | 0.603 |

The top of this list is dominated by **PPAR agonists** (glitazars, fenofibric acid, GW501516). The graph reaches them through PPARA/PPARG/PPARD → fatty liver disease / NASH / cirrhosis. This is a plausible pattern, but **support is not efficacy**, and PPARA falls while PPARG/PPARD rise with fibrosis (see Example 1 and Task 7).

## Verification
Path counts computed in Python were re-computed **inside Neo4j** with aggregated Cypher (`crosscheck_python_vs_neo4j.csv`). All 8 checks match (M1, M2, M3, M4 and the four M6 transitions). LIMIT 5 test queries were run first for M1 and M4.

## Example subgraphs (quality checks, `examples/`)
1. **Example 1 (M1f), `example1_M1f.png`**: **INDEGLITAZAR** → PPARA ⬇ / PPARG ⬆ / PPARD ⬆ → 7 fibrosis-spectrum diseases. All three arrows are "agonist" (pushes ⬆). For PPARA, which falls with fibrosis, that is direction-consistent. For PPARG and PPARD, which rise, it is not. A good reminder that one drug can be consistent on one target and inconsistent on another.
2. **Example 2 (M7), `example2_M7_EMT.png`**: main-list drugs reaching the **Hallmark EMT** fibrosis program (no graph node, so Paper 1 gene list). Marimastat inhibits MMP2 (rising) and also links to MMP14; adapalene and pseudoephedrine reach JUN via "target" links of unknown direction. This shows that M7 works for KEGG/Hallmark terms, and that weak "unknown" links must not be over-read.
3. **Example 3 (M6), `example3_M6_PDGFRA.png`**: **PDGFRA**, a Paper 1 shortlist gene that rises and is significant at the **F2→F3 (q=2.5e-04)** step. 4 repurposing candidates act on it; ripretinib and amuvatinib are inhibitors (push a rising gene down), while fostamatinib and ponatinib links have unknown direction.

## Files
`metapath_definitions.csv`, `metapath_counts.csv`, `metapath_drug_scores.csv` (per-drug paths and DNS for every MetaPath, with candidate/main-list flags: input for the Task 6 K component), `M1_drug_disease_pairs.csv`, `M1f_drug_disease_pairs.csv`, `M7_drug_term_pairs.csv`, `crosscheck_python_vs_neo4j.csv`, `metapath_queries.cypher`, `examples/`.

## Caveats
- Raw path counts favour well-connected drugs and genes. Use DNS, and treat it as a supporting feature, not a ranking.
- M4/M5 count paths through *any* pharmacological target sharing a pathway with a progression gene, so they are broad by design.
- Gene–disease links include cancer-heavy liver terms. M1f restricts to the fibrosis spectrum (21 diseases).
- KEGG/Hallmark terms reach the graph mostly through Paper 1 gene lists. Graph proxies are approximate.
