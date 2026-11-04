# Drug layer added to the graph for Paper 2

Records of the three graph writes that added outside drug information to the Paper 1 graph. Each folder holds the exact table that was written, the write log (counts before and after), and an undo file. The writer scripts are in `scripts/`.

| Step | What was added | Writer | Folder |
|---|---|---|---|
| 0.4 | 5,216 drug–gene links from ChEMBL, DGIdb, GtoPdb and Open Targets; 519 new Drug nodes (21 Oct 2026) | `scripts/write_new_links_to_graph.py` | `new_drug_gene_links/` |
| 0.5 | Action direction (up/down) from GtoPdb, DGIdb and ChEMBL as `external_action_*` properties on 297 existing `ACTS_ON` links; no count change (21 Oct 2026) | `scripts/write_external_directions_to_graph.py` | `external_action_directions/` |
| 0.8 | 2,087 `TREATS` links: ChEMBL_37 indications of the drugs added in 0.4, for 138 drugs and 866 diseases already in the graph; 172 indications whose disease is not in the graph were skipped (3 Nov 2026) | `scripts/write_added_drug_indications_to_graph.py` | `added_drug_indications/` |

Source releases: GtoPdb 2026.3.1, DGIdb 5, ChEMBL REST API (Oct 2026), Open Targets Platform 26.09, ChEMBL_37 (`new_drug_gene_links/numbers.json`, the write logs).

All three writers do a dry run by default; `--apply` writes and `--undo` removes only what that script added. They need `NEO4J_PASSWORD` and use the Neo4j HTTP API at `127.0.0.1:7474`.

## Not in this folder

The tables here were produced by search scripts that query the source APIs and read the Paper 2 gene and drug–gene tables. Those scripts belong to the Paper 2 analysis and are in the Paper 2 repository (https://github.com/knarendrakumar187/Drug_Repurposing) under `Paper2_Results/code/`: `new_links_search.py`, `new_links_report.py`, `external_action_check.py` and `task4_added_drug_indications.py`.

## Final relationship schema

The historical writer creates `EXTERNAL_ACTS_ON` and `:Drug:ExternalDrug`.
Finish that import with `python scripts/unify_drug_schema.py` (dry run), then
`--apply --backup /path/outside/repo/drug-schema-before.json` on the intended
rebuild database. The migration preserves each relationship and its properties,
uses ACTS_ON for all drug links, and removes the auxiliary label without deleting
nodes. It checks preservation inside the transaction and does nothing on an
already unified graph. Historical logs remain unchanged as provenance. The
published graph release already contains the final schema.
