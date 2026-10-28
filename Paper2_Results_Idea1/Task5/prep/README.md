# Task 5 preparation: linking Paper 1 pathways to the knowledge graph

**Gene set note:** uses the corrected 6,222-gene union (the plan's 4,692 was the pre-correction count).
**Scope:** knowledge graph + Paper 1 only (project scope decision); no external pathway resources.
**Graph source:** Neo4j (live liver_kg, read-only). Graph members: 46,751 Gene→Pathway (Reactome) and 157,081 Gene→BioProcess (GO BP) lines.

## The problem
Paper 1 enrichment used four collections (GO BP, Reactome, KEGG, Hallmark). The graph holds only GO BP (`BioProcess`) and Reactome (`Pathway`). KEGG and Hallmark terms have no graph node of their own.

## The fix (two matching steps, best first)
1. **name**: identical normalised name, same collection (GO→BioProcess, Reactome→Pathway).
2. **gene_overlap_proxy**: the graph node whose progression-gene members best overlap the term's Paper 1 genes (Jaccard ≥ 0.5, ≥ 5 shared genes). This is how KEGG/Hallmark terms reach the graph. Proxies are labelled and must be reported as approximate.

Fuzzy (character-similarity) name matching was tried and **rejected**: it paired different biology (e.g. "catabolic" with "metabolic", "type II" with "type III" interferon, "amide" with "amine").

Terms that stay unlinked are still usable: `paper1_term_genes_long.csv` holds their Paper 1 gene lists, so MetaPath M7 can test Drug → Gene ∈ term directly.

## Coverage of the 1,903 significant Paper 1 terms

| Database | Exact name | Gene-overlap proxy | Not linked (Paper 1 genes only) | Total | Linked to graph |
|---|---|---|---|---|---|
| GO_BP | 1162 | 21 | 203 | 1386 | 1183 (85.4%) |
| Hallmark | 0 | 0 | 41 | 41 | 0 (0.0%) |
| KEGG | 0 | 11 | 87 | 98 | 11 (11.2%) |
| Reactome | 243 | 50 | 85 | 378 | 293 (77.5%) |

**Result:** 1,487 / 1,903 terms (78.1%) are linked to a graph node. **1,903 / 1,903 terms are usable in MetaPaths**, because unlinked terms fall back to their Paper 1 gene lists (Drug →ACTS_ON→ Gene ∈ term).
KEGG and Hallmark sets rarely match one Reactome/GO node closely, because they are broad, mixed collections. That is expected, not an error. Their nearest graph node and Jaccard are still recorded (`nearest_*` columns) for transparency.

## Best KEGG/Hallmark proxies (top 10)

| Paper 1 term | Graph node | Jaccard | Shared genes |
|---|---|---|---|
| KEGG_PROTEASOME | Proteasome assembly (REACT:R-HSA-9907900) | 0.76 | 19 |
| KEGG_AMINOACYL_TRNA_BIOSYNTHESIS | tRNA aminoacylation for protein translation (GO_0006418) | 0.706 | 12 |
| KEGG_PRIMARY_BILE_ACID_BIOSYNTHESIS | Synthesis of bile acids and bile salts via 7alpha-hydroxycholesterol (REACT:R-HSA-193368) | 0.692 | 9 |
| KEGG_ASTHMA | antigen processing and presentation of peptide or polysaccharide antigen via MHC class II (GO_0002504) | 0.636 | 7 |
| KEGG_ONE_CARBON_POOL_BY_FOLATE | tetrahydrofolate interconversion (GO_0035999) | 0.625 | 5 |
| KEGG_AUTOIMMUNE_THYROID_DISEASE | antigen processing and presentation of peptide or polysaccharide antigen via MHC class II (GO_0002504) | 0.583 | 7 |
| KEGG_PEROXISOME | Peroxisomal protein import (REACT:R-HSA-9033241) | 0.581 | 25 |
| KEGG_MISMATCH_REPAIR | Mismatch repair (MMR) directed by MSH2:MSH6 (MutSalpha) (REACT:R-HSA-5358565) | 0.545 | 6 |
| KEGG_ALLOGRAFT_REJECTION | antigen processing and presentation of peptide or polysaccharide antigen via MHC class II (GO_0002504) | 0.538 | 7 |
| KEGG_GRAFT_VERSUS_HOST_DISEASE | antigen processing and presentation of peptide or polysaccharide antigen via MHC class II (GO_0002504) | 0.5 | 7 |

## Files
- `paper1_term_to_graph_map.csv`: one row per Paper 1 term → graph node, match type, score, and `use_in_metapaths`.
- `paper1_term_genes_long.csv`: Paper 1 term → progression gene (symbol + Ensembl), per group.
- `graph_pathway_process_nodes.csv`: all graph Pathway/BioProcess nodes with total and progression-gene member counts.
- `mapping_coverage.csv`: the coverage table above.

Note: Paper 1 gene lists contain only the progression genes in each term (the enrichment overlap), not the full pathway membership. Full membership is available only for graph-linked terms.
