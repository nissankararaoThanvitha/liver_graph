# Updated live graph: proposed manuscript changes (28 October 2026)

Review only. No manuscript or graph mutations performed.

## Confirmed live observations
- Total nodes 126,763 versus manuscript snapshot 126,244: +519.
- Total relationships 35,138,047 versus 35,132,831: +5,216.
- Every original relationship-type count matches final_combined_2026-10-10/graph_verification.json. Equal counts do not establish exact edge/property identity.
- New EXTERNAL_ACTS_ON relationship type: 5,216 edges; 15 types in total.
- 519 nodes carry both Drug and ExternalDrug labels; 12,025 other Drug nodes, hence 12,544 Drug nodes total. Eight broad entity categories remain; ExternalDrug is an additional label on a Drug subset.
- New nodes account for 846 external drug-gene edges. Existing drugs (2,104 distinct) account for the other 4,370.
- Existing ACTS_ON edges: 20,674; all now carry evidence_level, n_sources, relation_assertions, relation_conflict and direct-source fields. Additional property coverage varies.
- Among 12,025 original Drug nodes: SMILES 9,036; molecule_type 11,623; max_phase 9,930; is_approved 9,902; has_been_withdrawn 11,623. Populated-field counts do not indicate the number approved, withdrawn or clinically effective.
- Added Drug subset has 224 nodes tagged approved and 295 clinical trial; status meaning and assignment procedure require import-document verification.
- External-edge release properties cite GtoPdb 2026.3.1, DGIdb 5 interactions downloaded October 2026, ChEMBL REST API October 2026, and Open Targets Platform 26.09. These are graph-recorded provenance strings, not independently verified source releases or import procedures.
- TRACKS_FIBROSIS (3,845) and TRACKS_INFLAMMATION (4,199) retain final_combined_2026-10-10 run identifiers.

## Proposed edits
1. Describe the original analysis snapshot separately from the enriched current resource; retain old counts explicitly dated/scoped, and report new totals for the enriched resource.
2. Add Drug/ExternalDrug subset semantics and EXTERNAL_ACTS_ON to graph Methods/schema, including separation from original ACTS_ON.
3. Add drug property recovery, source coverage and limitations; avoid claiming complete coverage, active clinical status or full provenance on every original edge.
4. Add a supplementary graph-extension summary (counts and populated-property coverage), with input hashes, import scripts, identifier matching, deduplication and conflict handling documented once recovered.
5. Add external resource citations following source/import verification. Source files/download records/import scripts for these later additions were not located in the current repository search.
6. Retain expression/association/clustering/prioritisation findings pending explicit dependency and membership checks. Counts alone do not revalidate the 42-gene/12-annotation/154-link subgraph.
7. Do not add therapeutic efficacy or drug-prediction claims; graph enrichment is resource extension evidence.
