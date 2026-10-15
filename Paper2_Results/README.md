# Paper 2 — Knowledge-graph drug repurposing for liver fibrosis progression

Paper 2 uses the fibrosis-progression evidence from Paper 1 to prioritise therapeutic targets and existing drugs that could be repurposed. All analyses use the liver knowledge graph (Neo4j `liver_kg`, OptimusKG layer, read-only queries) and the final Paper 1 results only.

**Start with [`PAPER2_PROGRESS_REPORT.md`](PAPER2_PROGRESS_REPORT.md)**, which covers every task, the final ranking, the limitations and the next steps.

## Scope
- **In scope:** knowledge-graph drug repurposing. Existing drugs (clinical phase ≥ 2, not withdrawn, no recorded liver-disease use) linked to Paper 1 progression genes.
- **Out of scope** (project scope decision, 13 Oct 2026): transcriptomic drug-reversal analysis (LINCS/CMap), external databases and independent external validation.
- **Gene set:** the corrected Paper 1 union of **6,222 progression genes** (final combined version, 10 Oct 2026). Earlier planning documents cite 4,692, the pre-correction count.
- All outputs are **repurposing hypotheses**, not treatments or evidence of efficacy.

## Key results
| | |
|---|---|
| Progression genes with ≥ 1 drug in the graph | 1,072 / 6,222 (8,948 drug–gene links, 3,027 drugs) |
| Druggability, fibrosis-associated vs background | 16.6% vs 13.0% (1.30× a degree-matched null) |
| Repurposing candidates / mechanism-annotated main list | 1,109 / 559 |
| Candidates with ≥ 1 direction-consistent link | 315 |
| Stable targets (actionable / biology list) | 29 / 27 |
| Stable drugs in the top 25 | 19 |
| Independent audit | 86 / 86 checks pass |

## Layout
| Path | Contents |
|---|---|
| `PAPER2_PROGRESS_REPORT.md` | Full report with all diagrams |
| `AUDIT.md` | Independent checks of every result (re-run with `code/audit_tasks.py`) |
| `00_roadmap.png` | Task overview |
| `Task1/` | Master progression-gene table |
| `Task2/` | Drug–gene relationships from the graph, with evidence fields |
| `Task3/` | Druggability by Paper 1 group (Fisher's exact test, degree-matched permutation null) |
| `Task4/` | Drug coverage, repurposing candidates, candidate network (Cytoscape CSVs) |
| `Task5/` | MetaPath definitions, counts, Cypher queries, per-drug support, example subgraphs; `prep/` maps Paper 1 pathway terms to graph nodes |
| `Task6/` | Target-score framework and its equal-weight design test |
| `Task7/` | Drug action vs. progression direction for every link |
| `Task8/` | Shortlist-supported vs broad-evidence-only candidates |
| `Final_ranking/` | Final target and drug ranking: pre-registered rules, stable targets (biology and actionable lists), ranked candidates, evidence cards, ablation and stability |
| `code/` | Scripts that produce every file above |

Each `TaskN/` folder contains a `summary.md` and a diagram.

## Reproducing
Run from the repository root with the Paper 1 requirements installed and the Neo4j `liver_kg` database running. The Neo4j password is read from the `NEO4J_PASSWORD` environment variable.

```bash
python Paper2_Results/code/task1_master_gene_table.py
python Paper2_Results/code/task2_drug_gene_edges.py
python Paper2_Results/code/task3_druggability.py
python Paper2_Results/code/task4_drug_coverage.py
python Paper2_Results/code/task5_prep_pathway_map.py
python Paper2_Results/code/task5_metapaths.py
python Paper2_Results/code/task6_target_score_prototype.py
python Paper2_Results/code/task7_direction_consistency.py
python Paper2_Results/code/final_ranking.py
python Paper2_Results/code/diagrams.py
python Paper2_Results/code/task8_progress_report.py
python Paper2_Results/code/audit_tasks.py
```

All scripts are deterministic (fixed seeds); re-running them reproduces every output file byte for byte.

## Decisions to confirm
1. Druggability counts pharmacological-target links only (ENZYME, TRANSPORTER and CARRIER actions are excluded as drug-metabolism roles).
2. The liver-disease set is EFO "liver disease" plus descendants, minus 70 non-hepatic entries (malaria, gallbladder/ampulla tumours, erythropoietic porphyrias).
3. The primary candidate list keeps mechanism-annotated drugs only.
4. Targets are reported as two lists (biology and actionable), with equal weights frozen before the final ranking.

## Known data note
In the live graph, the `fibrosis_rho` property on Gene nodes predates the 10 Oct 2026 Paper 1 correction. Paper 2 does not use it; the `TRACKS_FIBROSIS` edges and the Paper 1 tables are current and agree exactly.
