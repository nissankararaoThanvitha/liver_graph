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

## Known gap: relationship type of the step 0.4 links

`write_new_links_to_graph.py` created the 5,216 links as a separate type, `EXTERNAL_ACTS_ON`, with new nodes labelled `:ExternalDrug`. The `--as-drug` run then gave those nodes the `Drug` label (`graph_write/relabel_log.json`). In the final graph the links are `ACTS_ON` relationships with `layer = 'external (Idea 4)'`, and `EXTERNAL_ACTS_ON` no longer exists. The Paper 2 Task 2 graph check (21 Oct 2026) counted 25,890 `ACTS_ON` links, 5,216 of them in that layer. The change of type was made directly in the database. No script or log for it is saved, but the change is recorded on the links themselves: every `ACTS_ON` link carries `original_relationship_type` (20,674 `ACTS_ON`, 5,216 `EXTERNAL_ACTS_ON`) and `migration_record_id`. The `ExternalDrug` label is also gone; the graph has eight node labels. Replaying step 0.4 from this folder gives `EXTERNAL_ACTS_ON` and a 16th type. Converting those links to `ACTS_ON`, keeping their properties, gives the final 15-type graph. The graph export in the GitHub release (see the root README) holds the final form directly.
