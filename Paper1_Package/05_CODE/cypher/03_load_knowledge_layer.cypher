// load_knowledge_layer.cypher
// =======================================================================
// Loads the curated knowledge layer and the project's own progression
// edges. This is the loader the pipeline never had.
//
// WHY IT EXISTS
// create_kg_constraints.cypher states that its constraints must exist
// "before the knowledge-layer edges are loaded", but no file loaded them --
// the layer was put in by hand. The consequence was undetectable until
// something compared the store against the CSVs: five relationship types,
// all of them touching Disease nodes, were short by 40,247 links in total,
// while the gene-disease links beside them were complete. Nothing could
// reload them, because nothing knew how.
//
// EVERY STATEMENT IS IDEMPOTENT
// MERGE, not CREATE, throughout. Running this file twice does not duplicate
// a single node or relationship, so it is safe to re-run after a partial
// load, and safe to run against a store that is only partly populated --
// which is exactly the situation it was written for.
//
// WHAT IT ASSUMES ALREADY EXISTS
//   Gene nodes, keyed on ensembl_id     (build_graph_all.py + its load)
//   the constraints in create_kg_constraints.cypher
// Gene nodes are MATCHed, never created: a knowledge edge pointing at a gene
// this project never measured should be dropped, not invented.
//
// HOW TO RUN
//   1. Copy data/graph_okg/*.csv and data/graph_full/edges_my_progression.csv
//      into Neo4j's import directory, under liverkg/.
//   2. Run create_kg_constraints.cypher first, if you have not.
//   3. Paste ONE statement at a time into Neo4j Browser and let each finish.
//      The `:auto` prefix is required -- CALL { } IN TRANSACTIONS is only
//      legal in an implicit transaction, which is what :auto provides.
//
// Statement 5 is the long one at 1.8M rows. Expect several minutes.
//
// AFTERWARDS
//   python verify_graph_counts.py --live
// which reconciles every relationship type against the CSVs and names any
// that is still short.
// =======================================================================


// ------------------------------------------------------------- 1/11 nodes
// Disease, 36,044
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/nodes_disease.csv' AS row
CALL { WITH row
  MERGE (d:Disease {node_id: row.node_id})
  SET d.name = row.name
} IN TRANSACTIONS OF 10000 ROWS;


// 2/11  Drug, 12,025
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/nodes_drug.csv' AS row
CALL { WITH row
  MERGE (d:Drug {node_id: row.node_id})
  SET d.name = row.name
} IN TRANSACTIONS OF 10000 ROWS;


// 3/11  BioProcess 12,203 · Pathway 2,220 · Phenotype 8,666
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/nodes_bioprocess.csv' AS row
CALL { WITH row
  MERGE (b:BioProcess {node_id: row.node_id})
  SET b.name = row.name
} IN TRANSACTIONS OF 10000 ROWS;

:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/nodes_pathway.csv' AS row
CALL { WITH row
  MERGE (p:Pathway {node_id: row.node_id})
  SET p.name = row.name
} IN TRANSACTIONS OF 10000 ROWS;

:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/nodes_phenotype.csv' AS row
CALL { WITH row
  MERGE (p:Phenotype {node_id: row.node_id})
  SET p.name = row.name
} IN TRANSACTIONS OF 10000 ROWS;


// --------------------------------------------------------- 4/11 gene-gene
// INTERACTS_WITH, 324,116. Both ends MATCHed.
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_gene_gene.csv' AS row
CALL { WITH row
  MATCH (a:Gene {ensembl_id: row.from_id})
  MATCH (b:Gene {ensembl_id: row.to_id})
  MERGE (a)-[:INTERACTS_WITH]->(b)
} IN TRANSACTIONS OF 20000 ROWS;


// ------------------------------------------------------ 5/11 gene-disease
// ASSOCIATED_WITH, 1,832,441 -- the longest statement here.
// The Open Targets score is kept on the edge so a query can tighten the
// evidence cut further without a reload. Links below 0.1 were already
// excluded when the layer was built.
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_disease_gene.csv' AS row
CALL { WITH row
  MATCH (g:Gene {ensembl_id: row.from_id})
  MATCH (d:Disease {node_id: row.to_id})
  MERGE (g)-[r:ASSOCIATED_WITH]->(d)
  SET r.score = toFloat(row.score)
} IN TRANSACTIONS OF 20000 ROWS;


// ------------------------------------------------------ 6/11 gene-process
// INVOLVED_IN, 157,081. The CSV says INTERACTS_WITH; the graph names it for
// what it is.
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_biological_process_gene.csv' AS row
CALL { WITH row
  MATCH (g:Gene {ensembl_id: row.from_id})
  MATCH (b:BioProcess {node_id: row.to_id})
  MERGE (g)-[:INVOLVED_IN]->(b)
} IN TRANSACTIONS OF 20000 ROWS;


// ------------------------------------------------------ 7/11 gene-pathway
// IN_PATHWAY, 46,751
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_pathway_gene.csv' AS row
CALL { WITH row
  MATCH (g:Gene {ensembl_id: row.from_id})
  MATCH (p:Pathway {node_id: row.to_id})
  MERGE (g)-[:IN_PATHWAY]->(p)
} IN TRANSACTIONS OF 20000 ROWS;


// --------------------------------------------------------- 8/11 drug-gene
// ACTS_ON, 20,674. The mode of action is kept on the edge: to lower a rising
// gene you need a drug that inhibits it, not one that activates it, and the
// untyped alternative cannot tell you which.
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_drug_gene.csv' AS row
CALL { WITH row
  MATCH (d:Drug {node_id: row.from_id})
  MATCH (g:Gene {ensembl_id: row.to_id})
  MERGE (d)-[r:ACTS_ON]->(g)
  SET r.action = row.rel_type
} IN TRANSACTIONS OF 20000 ROWS;


// ------------------------------------------------------ 9/11 drug-disease
// One file, three relationship types: TREATS 57,601 ·
// CONTRAINDICATED_IN 11,718 · OFF_LABEL_FOR 1,061.
// Three of the five types that were found short.
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_drug_disease.csv' AS row
WITH row WHERE row.rel_type = 'INDICATION'
CALL { WITH row
  MATCH (dr:Drug {node_id: row.from_id})
  MATCH (di:Disease {node_id: row.to_id})
  MERGE (dr)-[:TREATS]->(di)
} IN TRANSACTIONS OF 20000 ROWS;

:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_drug_disease.csv' AS row
WITH row WHERE row.rel_type = 'CONTRAINDICATION'
CALL { WITH row
  MATCH (dr:Drug {node_id: row.from_id})
  MATCH (di:Disease {node_id: row.to_id})
  MERGE (dr)-[:CONTRAINDICATED_IN]->(di)
} IN TRANSACTIONS OF 20000 ROWS;

:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_drug_disease.csv' AS row
WITH row WHERE row.rel_type = 'OFF_LABEL_USE'
CALL { WITH row
  MATCH (dr:Drug {node_id: row.from_id})
  MATCH (di:Disease {node_id: row.to_id})
  MERGE (dr)-[:OFF_LABEL_FOR]->(di)
} IN TRANSACTIONS OF 20000 ROWS;


// --------------------------------------------- 10/11 disease hierarchy and
// PARENT_OF 44,215 · HAS_PHENOTYPE 157,144. The other two that were short.
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_disease_disease.csv' AS row
CALL { WITH row
  MATCH (a:Disease {node_id: row.from_id})
  MATCH (b:Disease {node_id: row.to_id})
  MERGE (a)-[:PARENT_OF]->(b)
} IN TRANSACTIONS OF 20000 ROWS;

:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_disease_phenotype.csv' AS row
CALL { WITH row
  MATCH (d:Disease {node_id: row.from_id})
  MATCH (p:Phenotype {node_id: row.to_id})
  MERGE (d)-[:HAS_PHENOTYPE]->(p)
} IN TRANSACTIONS OF 20000 ROWS;


// ------------------------------------------- 11/11 the project's own edges
// TRACKS_FIBROSIS 3,681 · TRACKS_INFLAMMATION 4,018.
// The only edges here derived from these patients rather than imported, so
// they carry their own evidence: the cross-study median rho, the combined
// q, how many studies contributed, and the direction.
//
// Load from data/graph_full/edges_my_progression.csv, written by
// build_progression_edges.py. The copy inside data/graph_okg/ is an older
// one and should not be used.
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_my_progression.csv' AS row
WITH row WHERE row.rel = 'TRACKS_FIBROSIS'
CALL { WITH row
  MATCH (g:Gene    {ensembl_id: row.ensembl_id})
  MATCH (d:Disease {node_id: row.disease_id})
  MERGE (g)-[r:TRACKS_FIBROSIS]->(d)
  SET r.rho = toFloat(row.rho), r.q = toFloat(row.q),
      r.n_studies = toInteger(row.n_studies), r.direction = row.direction
} IN TRANSACTIONS OF 5000 ROWS;

:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_my_progression.csv' AS row
WITH row WHERE row.rel = 'TRACKS_INFLAMMATION'
CALL { WITH row
  MATCH (g:Gene    {ensembl_id: row.ensembl_id})
  MATCH (d:Disease {node_id: row.disease_id})
  MERGE (g)-[r:TRACKS_INFLAMMATION]->(d)
  SET r.rho = toFloat(row.rho), r.q = toFloat(row.q),
      r.n_studies = toInteger(row.n_studies), r.direction = row.direction
} IN TRANSACTIONS OF 5000 ROWS;


// =======================================================================
// VERIFY -- these need no :auto.
//
// Count per type, never all at once: the whole-graph count times out on a
// 1 GB heap, while a per-type count hits the count store and is instant.
//
//   MATCH ()-[r:TREATS]->()             RETURN count(r);   // 57,601
//   MATCH ()-[r:CONTRAINDICATED_IN]->() RETURN count(r);   // 11,718
//   MATCH ()-[r:OFF_LABEL_FOR]->()      RETURN count(r);   //  1,061
//   MATCH ()-[r:PARENT_OF]->()          RETURN count(r);   // 44,215
//   MATCH ()-[r:HAS_PHENOTYPE]->()      RETURN count(r);   // 157,144
//   MATCH ()-[r:TRACKS_FIBROSIS]->()    RETURN count(r);   //  3,681
//   MATCH ()-[r:TRACKS_INFLAMMATION]->() RETURN count(r);  //  4,018
//
// Or check the lot at once, from the shell:
//
//   NEO4J_PASSWORD=... python verify_graph_counts.py --live
//
// EXPECTED COUNTS, measured rather than assumed. scripts/
// expected_graph_counts.py checks every edge's endpoints against the node
// files and reports what a MATCH-based load can actually create:
//
//   INTERACTS_WITH       324,116      ACTS_ON               20,674
//   ASSOCIATED_WITH    1,832,441      TREATS                57,601
//   INVOLVED_IN          157,081      CONTRAINDICATED_IN    11,718
//   IN_PATHWAY            46,751      OFF_LABEL_FOR          1,061
//   HAS_PHENOTYPE        157,144      TRACKS_FIBROSIS        3,681
//   PARENT_OF             44,073      TRACKS_INFLAMMATION    4,018
//
// Every type loads complete except PARENT_OF, which lands at 44,073 rather
// than 44,215: 142 of its rows point at a disease id that is not a node in
// this layer. Those are dropped by the MATCH rather than invented, which is
// the behaviour wanted -- but it means a verification expecting the raw row
// count would report a false shortfall of 142. It is not a shortfall.
// =======================================================================
