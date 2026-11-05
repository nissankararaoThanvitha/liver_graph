# Stage-resolved transcriptomic analysis of liver fibrosis

Code, result tables and graph exports for the paper *Stage-Resolved Transcriptomic Analysis Reveals Distinct Molecular Programs Associated with Liver Fibrosis Severity* (N. Thanvitha, V. Lakshmi Nikitha, K. Venkata Dinesh, Biswajit Maity, Ashmita Dey; Department of Computer Science and Engineering, SRM University-AP). Correspondence: Ashmita Dey, ashmita.de@srmap.edu.in.

Eight public human liver RNA-sequencing studies (1,085 samples; 1,027 recorded patients) are integrated at the patient level and linked to the OptimusKG biomedical knowledge graph. Within-study Spearman correlations with fibrosis stage (610 patients) and ordered control–NAFL–NASH labels (216 patients) are combined across studies. Fibrosis-associated genes are clustered by their F0–F4 profiles, adjacent stages are compared, and genes are prioritised with a nine-point score checked by leave-one-study-out and sensitivity analyses.

| Result | Value |
|---|---|
| Fibrosis-associated / disease-group-associated / shared / union genes | 3,845 / 4,199 / 1,822 / 6,222 |
| Stage-pattern clusters C1–C5 | 857 / 1,367 / 226 / 397 / 998 genes |
| Tier 1 genes / shortlist | 447 / 23 |
| Tier 1 genes significant in every LOSO refit | 442 |
| Knowledge-graph subgraph | 42 genes, 12 annotations, 154 connections |
| Graph | 126,480 nodes, 35,152,951 relationships, 8 entity types, 15 relationship types |

**[docs/PAPER1_MAP.md](docs/PAPER1_MAP.md) maps every section, figure and table of the paper to its code and result file.**

## Repository layout

| Folder / file | Contents |
|---|---|
| root `*.py`, `*.cypher` | Pipeline: parsing, gene-ID mapping, clinical labels, association analysis, the four analyses (`paper1_task1`–`task4`), graph building |
| `scripts/` | Prioritisation, LOSO, matched refits, knowledge-graph subgraph, graph additions, graph export and count checks |
| `Paper1_Results/` | Task 1 gene groups, Task 2 stage-pattern clusters, Task 3 adjacent-stage comparisons, Task 4 enrichment |
| `Paper1_HighConfidence/` | Scores, tiers, 23-gene shortlist, LOSO, sensitivity tables, knowledge-graph subgraph |
| `data/` | Processed inputs and association results the scripts read; graph-addition tables |
| `final_combined_2026-10-10/` | Record of the final run: selection, label/normalisation sensitivity, graph synchronisation checks |
| `label_audit_GSE130970_2026-10-10/`, `unit_audit_GSE193066_2026-10-10/` | Checks behind the GSE130970 labels and GSE193066 expression units |
| `docs/paper1/` | Overview, methods, statistics, limitations, how to verify, data dictionary |
| `docs/provenance/` | Data sources, rebuild steps, graph count verification |
| `docs/graph_export/` | Import guide and data terms for the graph release |
| `tests/` | Repeat-biopsy policy tests |

## Running it

Python 3.12 with the versions in `requirements.txt` (pandas 2.3.3, NumPy 2.2.4, SciPy 1.16.3, scikit-learn 1.7.2, matplotlib 3.10.7, GSEApy 1.3.1). Run every script from the repository root. Raw downloads (GEO, HGNC, OptimusKG, MSigDB) are not committed; [docs/provenance/DATA_SOURCES.md](docs/provenance/DATA_SOURCES.md) lists them and [docs/provenance/REBUILD.md](docs/provenance/REBUILD.md) gives fresh-clone input preparation and the order of the scripts. The graph ZIP can be converted into analysis inputs with `scripts/prepare_analysis_core.py`, without loading Neo4j. The result tables can be read without running anything or installing Neo4j.

```bash
pip install -r requirements.txt
python -m unittest discover -s tests
```

## Download the graph

The knowledge graph is available as a GitHub release, **without the KEGG pathways**. KEGG data may not be redistributed, so the release is not the complete graph:

- **Release page:** https://github.com/nissankararaoThanvitha/liver_graph/releases/tag/graph-export-2026-11-05
- **CSV files** (all nodes, relationships and properties, neo4j-admin import format): [liver_kg_graph_export_2026-11-05.zip](https://github.com/nissankararaoThanvitha/liver_graph/releases/download/graph-export-2026-11-05/liver_kg_graph_export_2026-11-05.zip)
- **Neo4j dump** (load with `neo4j-admin database load`, Neo4j 5.26 or newer): [liver_kg_2026-11-05.dump](https://github.com/nissankararaoThanvitha/liver_graph/releases/download/graph-export-2026-11-05/liver_kg_2026-11-05.dump)

| | Full graph | Release |
|---|---|---|
| Nodes | 126,480 | 126,294 |
| Relationships | 35,152,951 | 35,140,166 |
| Entity / relationship types | 8 / 15 | 8 / 15 |

Left out: 186 KEGG Pathway nodes, their 12,724 `IN_PATHWAY` links and the 61 `IMPLICATED_IN` links whose pathway is KEGG. With your own MSigDB download they can be added back with `scripts/add_msigdb_pathways.py` and `scripts/build_pathway_nafld_links.py`.

The release includes import instructions, constraints, a manifest with row counts and SHA-256 checksums, the count check and each source's terms. Use the data non-commercially, credit the sources, and share derived data under the same terms (OptimusKG is CC BY-NC-SA 4.0).

### How the graph was built

The graph integrates the expression layer, OptimusKG biological knowledge and the 8,044 progression links from this study. Drug nodes, drug molecular/clinical annotations and drug--gene/disease evidence are retained from OptimusKG. The graph also contains:

- 236 KEGG legacy and Hallmark pathways with 20,031 gene links from MSigDB 2024.1 (`data/graph_msigdb` holds the Hallmark rows; KEGG rows are not redistributed);
- 89 Pathway → NAFLD links supported by both this study's enrichment results and CTD (`data/graph_pathway_disease`).

The added graph memberships and pathway--NAFLD links were not inputs to the transcriptomic or original Reactome/GO graph-annotation analyses. `python scripts/verify_extended_graph_counts.py --live` checks the current counts; the saved verification is in `docs/provenance/extended_graph_verification.json`. Original drug coverage is 12,025 nodes, 20,674 `ACTS_ON` links and 57,601 `TREATS` links.

Earlier releases remain historical snapshots; use the release linked above for the current manuscript. Import the current release for the retained OptimusKG molecular/evidence properties; the primary processing commands rebuild the initial knowledge layer before metadata recovery.

The drug-repurposing study that uses this graph (Paper 2) is in its own repository: https://github.com/knarendrakumar187/Drug_Repurposing.

## Licence

Code: MIT ([LICENSE](LICENSE)). Data from outside sources keeps its own terms: GEO, OptimusKG (CC BY-NC-SA 4.0), MSigDB (KEGG-derived sets may not be redistributed), CTD and the upstream resources represented in OptimusKG. See [docs/graph_export/DATA_TERMS.md](docs/graph_export/DATA_TERMS.md).
