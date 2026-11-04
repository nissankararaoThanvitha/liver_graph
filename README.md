# Stage-informed liver knowledge graph

Final combined active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses216 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **3,845 fibrosis**, **4,199 disease**, **1,822 shared**, **6,222 union**. Tier1 has **447 genes**, with23 shortlisted. The network displays **42 genes**, **12 mechanisms**, **154 connections**, with4 shortlisted genes shown.

The final objective is to support the next team’s drug repurposing for interrupting disease progression at different stages. Curated biology from OptimusKG connects stage-associated genes to drugs, diseases, pathways and processes. No therapeutic efficacy or validated clinical stage predictor is established.

## Graph versions

| Version | Nodes | Relationships | Types | Record |
|---|---|---|---|---|
| Paper 1 final (10 Oct 2026) | 126,244 | 35,132,831 | 14 | final_combined_2026-10-10/graph_verification.json |
| Extended for Paper 2 (3 Nov 2026) | 126,999 | 35,160,254 | 15 | docs/provenance/extended_graph_verification.json |

The extended graph adds, on top of Paper 1 (nothing from Paper 1 is changed or removed):

- 519 Drug nodes and 5,216 drug–gene `ACTS_ON` links from ChEMBL, DGIdb, GtoPdb and Open Targets, plus action directions on 297 existing `ACTS_ON` links (data/graph_drug_layer);
- 236 KEGG legacy and Hallmark Pathway nodes with 20,031 `IN_PATHWAY` links, from the MSigDB 2024.1 files Paper 1 used for enrichment (data/graph_msigdb holds the Hallmark rows; KEGG rows are not redistributed);
- 89 Pathway → NAFLD `IMPLICATED_IN` links, kept only where Paper 1 enrichment (BH-FDR < 0.05, fibrosis groups) and CTD agree (data/graph_pathway_disease);
- 2,087 `TREATS` links from ChEMBL_37 indications for the added drugs (data/graph_drug_layer).

The Paper 2 drug-repurposing analysis that uses this graph is on the paper2-rerun-newgraph branch.

## Download the graph

The extended graph is available as a GitHub release, **without the KEGG pathways**. KEGG data may not be redistributed, so the release is not the complete graph:

- **Release page:** https://github.com/nissankararaoThanvitha/liver_graph/releases/tag/graph-export-2026-11-03
- **CSV files** (all nodes, relationships and properties, neo4j-admin import format): [liver_kg_graph_export_2026-11-03.zip](https://github.com/nissankararaoThanvitha/liver_graph/releases/download/graph-export-2026-11-03/liver_kg_graph_export_2026-11-03.zip)
- **Neo4j dump** (load with `neo4j-admin database load`, Neo4j 2026.10 or newer): [liver_kg_2026-11-03.dump](https://github.com/nissankararaoThanvitha/liver_graph/releases/download/graph-export-2026-11-03/liver_kg_2026-11-03.dump)

| | Full graph | Release |
|---|---|---|
| Nodes | 126,999 | 126,813 |
| Relationships | 35,160,254 | 35,147,469 |
| Entity / relationship types | 8 / 15 | 8 / 15 |

Left out: 186 KEGG Pathway nodes, their 12,724 `IN_PATHWAY` links and the 61 `IMPLICATED_IN` links whose pathway is KEGG. With your own MSigDB download they can be added back with scripts/add_msigdb_pathways.py and scripts/build_pathway_nafld_links.py.

The release includes import instructions (IMPORT.md), constraints, a manifest with row counts and SHA-256 checksums (MANIFEST.csv, SHA256SUMS.txt), the count check (VERIFICATION.json) and each source's terms (DATA_TERMS.md). Use the data non-commercially, credit the sources, and share derived data under the same terms (OptimusKG is CC BY-NC-SA 4.0). The export is made with scripts/export_graph.py and scripts/package_graph_release.py; their documents are in docs/graph_export.

## Active files

- Paper1_Package: current data, methods, figures, tables and evidence boundaries.
- Paper1_Results: corrected Tasks1–4.
- Paper1_HighConfidence: corrected scores, shortlist, LOSO and network.
- data/progression_full and data/for_mentor: corrected association/group summaries.
- data/graph_full and data/graph_okg: current node/knowledge/progression CSVs.
- data/expression_analysis_core: core-only recovery for analysis; never use to replace all graph expression measurements.
- manuscript_planning: current inventory/workflow/evidence map/missing information.
- data/graph_msigdb, data/graph_pathway_disease and data/graph_drug_layer: the graph extensions above, with write logs and undo files.
- final_combined_2026-10-10: final selection, sensitivity evidence and graph verification.
- biopsy_correction_2026-10-10: historical biopsy correction record; numerical results there are superseded.
- archives: checksum-verified recovery copy of superseded results/draft; excluded from Git by default.

## Rebuild and checks

Read docs/provenance/REBUILD.md. Run scripts from repository root with explicit outputs. Requirements cover Paper1; requirements-link-prediction.txt is optional and unrelated to the verified Paper1 results. Patient-policy tests are in tests/. `python scripts/verify_extended_graph_counts.py` checks the extended graph counts (add `--live` to compare with a running database).

## Licence

Code is released under the MIT licence (LICENSE). Data from outside sources keeps its own terms: OptimusKG, GEO, MSigDB (KEGG-derived sets have redistribution limits), CTD (cite CTD when using the pathway–NAFLD links), ChEMBL, DGIdb, GtoPdb and Open Targets.

Historical Claude sessions under handover/ preserve rationale and rejected branches; their counts/method descriptions are not current results.
