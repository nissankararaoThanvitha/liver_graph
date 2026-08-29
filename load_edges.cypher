// load_edges.cypher
// -----------------------------------------------------------------------
// Loads the 23,340,664 EXPRESSES relationships of the full union graph.
//
// WHY THIS FILE EXISTS
// The MCP/driver connection wraps every query in an EXPLICIT transaction,
// and `CALL { ... } IN TRANSACTIONS` is only legal in an IMPLICIT one. So
// the batching that makes a 23M-row load possible cannot be issued that way.
// Neo4j Browser's `:auto` prefix runs a statement as auto-commit, which is
// implicit -- hence these statements are written for Browser.
//
// HOW TO RUN
//   1. Open Neo4j Browser and connect to the liver-kg database.
//   2. Paste ONE statement at a time (Browser runs one per execution) and
//      wait for it to finish before starting the next.
//   3. The `:auto` prefix is required. Without it you get:
//        "can only be executed in an implicit transaction"
//
// Expect a few minutes per statement. GSE269412 is the largest at 5.87M.
// Nodes and constraints are already loaded; this file only adds edges.
//
// If a statement fails partway, its committed batches remain. Re-running it
// would duplicate them -- delete that study's edges first with:
//   MATCH (s:Sample {dataset_id:'GSE135251'})-[r:EXPRESSES]->() DELETE r
// (run that as :auto ... IN TRANSACTIONS too if the count is large)
// -----------------------------------------------------------------------


// 1/8  GSE126848 -- 839,319 edges
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE126848.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// 2/8  GSE130970 -- 1,357,130 edges
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE130970.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// 3/8  GSE135251 -- 4,836,022 edges
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE135251.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// 4/8  GSE162694 -- 4,432,923 edges
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE162694.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// 5/8  GSE167523 -- 1,627,689 edges
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE167523.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// 6/8  GSE193066 -- 2,543,960 edges
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE193066.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// 7/8  GSE240729 -- 1,834,418 edges
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE240729.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// 8/8  GSE269412 -- 5,869,203 edges  (largest, slowest)
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE269412.csv' AS row
CALL { WITH row
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// -----------------------------------------------------------------------
// VERIFY (run after all eight; this one needs no :auto)
//   MATCH ()-[r:EXPRESSES]->() RETURN count(r);        // expect 23,340,664
//   MATCH (n) RETURN labels(n)[0], count(*);           // 53,993 / 1,085 / 8
// -----------------------------------------------------------------------
