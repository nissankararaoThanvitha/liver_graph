# Paper 2: knowledge-graph drug repurposing for liver fibrosis progression

**Gene set:** corrected Paper 1 union of 6,222 progression genes (earlier plans cite 4,692, the pre-correction count).
**Scope:** knowledge graph (Neo4j `liver_kg`, built from OptimusKG) + final Paper 1 results. All outputs are repurposing hypotheses, not treatments.
Start with `PAPER2_PROGRESS_REPORT.md`; independent checks are in `AUDIT.md` (108 / 108 passed, 21 Oct 2026).

## Main results (graph + Paper 1 only)
| Folder | What it holds |
|---|---|
| `Task1/` | Master table of the 6,222 progression genes (`Paper2_progression_genes.csv`) |
| `Task2/` | All 8,948 drug–gene links from the graph (3,027 drugs, 1,072 genes) |
| `Task3/` | Druggability by Paper 1 group, with BH-FDR and degree-matched permutation tests |
| `Task4/` | Drug coverage, repurposing candidates (1,109; 559 mechanism-annotated), annotated drug–gene network |
| `Task5/`, `Task5_revised/` | MetaPath definitions, counts, degree-normalised support and queries (revised: biological-process path dropped, new drug–liver-disease pairs) |
| `Task6/` | Target-score framework, weight sensitivity and ablation |
| `Task7/`, `Task7_revised/` | Drug action vs. gene progression direction; revised version also uses pathway direction |
| `Task8/` | Candidates supported by the 23-gene shortlist vs. broad evidence only |
| `Final_ranking/` | Pre-registered target and drug ranking, stability analysis, evidence cards for the top 25 |
| `Graph_files/` | Four Excel edge files (gene–drug, gene–disease, drug–disease, gene–pathway) and the graph schema |
| `report_page/` | One-page HTML summary |
| `code/` | Scripts that reproduce every output (Neo4j password read from `NEO4J_PASSWORD`) |

## Extra layers from outside databases (kept separate, pending supervisor approval)
| Folder | What it holds |
|---|---|
| `External_action_check/` | Up/down direction for unknown graph links from ChEMBL, Guide to Pharmacology and DGIdb: 297 links filled (known direction 11.2% → 14.5%) |
| `Task7_external_layer/` | Task 7 re-counted with those extra directions |
| `New_drug_gene_links/` | New drug–gene links from GtoPdb 2026.3.1, DGIdb 5, ChEMBL and Open Targets 26.09: 5,216 curated links for approved / clinical-trial drugs, 319 genes get their first drug. Written to Neo4j as `EXTERNAL_ACTS_ON` with 519 new drug nodes (undo script in `graph_write/`). Raw API downloads are not in git; `code/new_links_search.py` fetches them again |

## Related folder
`../Paper2_Results_Idea1/` is a full rerun where only drugs already used for a **fibrosis-type** liver disease are excluded from the candidates (graph only, no diagrams). See its `IDEA1_CHANGES.md`: candidates 1,109 → 1,269, stable drugs on the main list 19 → 21.
