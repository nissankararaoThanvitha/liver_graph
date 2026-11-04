# Unified drug–gene relationship schema — 28 October 2026

Completed and independently read back from the live graph. All 25,890 records now use ACTS_ON. The graph has 126,763 nodes, 35,138,047 relationships and 14 populated relationship types. The original 20,674 ACTS_ON records retained their internal IDs; 5,216 external records were recreated as ACTS_ON. Endpoint identifiers, every original property and record multiplicity were verified exactly. Other relationship-type counts are unchanged.

## Common fields
- unified_actions: nonempty source action/action_labels/external_action_label entries, semicolon-split, trimmed, uppercased and deduplicated within each record. No pharmacological synonym mapping or directional inference. Present on 25,430 records. Empty action information remains absent on 460 records.
- unified_sources: source entries from sources_direct, sources and external_action_sources, semicolon-split, trimmed and deduplicated. Present on all 25,890 records. Source aliases remain distinct; this is not a source-independence count.
- original_relationship_type: each original type, including EXTERNAL_ACTS_ON for the 5,216 converted records.
- migration_record_id: original Neo4j relationship element ID, linked to before.json and id_mapping.json. Internal IDs are database-local, not durable biological identifiers.
All original action, evidence, conflict, provenance, release, mechanism and other properties remain intact. Normalization is additive; existing code reading only action or sources_direct must switch to the common fields to retrieve all-source coverage. Parallel evidence records must not be interpreted as distinct drug–gene pairs.

## Backup and verification
before.json: complete endpoints, endpoint identifiers, labels and original properties for both types.
after.json: full post-migration readback.
id_mapping.json: original-to-current relationship element IDs.
verification.json: all checks passed.
backup_checksums.json: SHA-256 hashes of the JSON artifacts.
normalization_records.json: exact added fields per original record.

## Restoration
From the project root, invoke `python3 graph_relationship_unification_2026-10-28/migrate.py restore` only if restoration is wanted. It prompts for credentials and recreates the original external type, restores original properties on the retained records, and removes the added fields. Internal IDs of recreated relationships cannot be restored. Review current changes before restoration; it resets these records to the backed-up values. Restoration was prepared but NOT executed.

## Code and publication
Migration script is archived here; no transcriptomic analyses or drug-prediction analyses were rerun. The original external importer was not found in available repository branches and must be updated to emit ACTS_ON and the shared fields before reimporting, otherwise it could reintroduce EXTERNAL_ACTS_ON. No importer was invented or rerun. This limitation remains documented in the manuscript.

Active Overleaf main.tex and Supplementary Table S4 updated. Before/after source snapshots: Paper1_Manuscript/inline_layout/revision_2026-10-28/acts_on_unification/.
