# Current main-branch availability audit

Public heads checked with git ls-remote. Main: 565863549d7f2cde147d022b51f0dc65495b4ea3; latest paper2-results: e413951ceffff6bc92912100156005e11139a04c. Temporary filtered fetch used for latest branch tree; working repository not changed.

## Confirmed missing from main but present on paper2-results
- scripts/add_msigdb_pathways.py
- scripts/build_pathway_nafld_links.py
- data/graph_msigdb/nodes_pathway_msigdb.csv
- data/graph_msigdb/edges_pathway_gene_msigdb.csv
- data/graph_msigdb/unmatched_symbols_msigdb.csv
- data/graph_pathway_disease/edges_pathway_nafld.csv
- data/graph_pathway_disease/pathway_nafld_all_candidates.csv

## Missing release materials
- No public Git tags returned by git ls-remote --tags.
- No root code LICENSE/COPYING file found in main.

## Present but needing improvement
- Core association, clustering, transition, enrichment, prioritisation and LOSO code exists. Result tables, package manifests, requirements, source documentation and rebuild instructions exist.
- README and REBUILD omit the latest two integration scripts; REBUILD describes unavailable reference inputs and recovery-only execution. The excluded expression core is not itself downloadable from main.
- A final graph-count verification file matching 126,999 nodes, 35,160,254 relationships and 15 types should accompany the release; the archived correction verification is not evidence of those additions.
- Do not classify all 325 branch-only files as required for Paper 1: many are Paper 2 drug-ranking outputs.
- Absence of full graph exports is intentional under the proposed code-and-result-tables availability statement.
