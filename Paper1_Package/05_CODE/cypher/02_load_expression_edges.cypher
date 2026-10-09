// reload_expression.cypher
// =======================================================================
// Replaces the 23,340,664 EXPRESSES edges with the 32,471,042 rebuilt from
// the parse that KEEPS measured zeros.
//
// WHY
// The original parse ran with --drop-zeros, so a gene that read 0 in a
// patient had no edge at all. That is not neutral: the missing values track
// the disease. IL6 is detected in 10% of stage-1 patients and 64% of
// stage-4, so deleting zeros deletes exactly the switching-on that IS the
// progression signal. Re-running without the flag recovered 17,218,924
// measurements and surfaced 514 more progression genes -- among them TREM2
// (scar-associated macrophages, a current NASH drug target), CXCL8, CXCL1,
// CCL20, MMP9, LOXL1 and CIDEC. Every one of those is a gene that is OFF in
// a healthy liver, which is why every one of them was invisible before.
//
// The gene, sample and dataset nodes are unchanged (still 53,993 / 1,085 /
// 8), and the progression links and OptimusKG knowledge layer have already
// been updated. This file only swaps the expression edges.
//
// HOW TO RUN
//   1. Open Neo4j Browser, connect to the liver-kg database.
//   2. Run the statements below ONE AT A TIME, waiting for each to finish.
//   3. The `:auto` prefix is required -- CALL { } IN TRANSACTIONS is only
//      legal in an implicit transaction, and Browser's :auto provides one.
//
// Step 1 is a delete of 23.3M relationships and is the slowest; expect
// several minutes. Steps 2-9 load ~3-9 minutes each. Nothing is lost if a
// statement is interrupted: re-run step 1 until it reports 0 deleted, and
// re-run any load whose study shows a short count in the verification query.
// =======================================================================


// ---- 1/9  DELETE the old expression edges -----------------------------
// Run this repeatedly until it reports 0 rows deleted.
:auto MATCH ()-[r:EXPRESSES]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 50000 ROWS;


// ---- 2/9  GSE126848 -- 1,017,051 edges --------------------------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE126848.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// ---- 3/9  GSE130970 -- 1,480,830 edges --------------------------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE130970.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// ---- 4/9  GSE135251 -- 9,049,104 edges  (large) -----------------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE135251.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// ---- 5/9  GSE162694 -- 4,530,669 edges --------------------------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE162694.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// ---- 6/9  GSE167523 -- 2,077,600 edges --------------------------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE167523.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// ---- 7/9  GSE193066 -- 2,814,896 edges --------------------------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE193066.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// ---- 8/9  GSE240729 -- 2,809,042 edges --------------------------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE240729.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// ---- 9/9  GSE269412 -- 8,691,850 edges  (largest, slowest) ------------
:auto LOAD CSV WITH HEADERS FROM 'file:///liverkg/edges_GSE269412.csv' AS row
CALL (row) {
  MATCH (s:Sample {sample_id: row.sample_id})
  MATCH (g:Gene   {ensembl_id: row.ensembl_id})
  CREATE (s)-[:EXPRESSES {value_raw: toFloat(row.value_raw),
                          value_log: toFloat(row.value_log),
                          value_z:   toFloat(row.value_z)}]->(g)
} IN TRANSACTIONS OF 50000 ROWS;


// =======================================================================
// VERIFY -- no :auto needed. Expect 32,471,042 in total.
//
//   MATCH (s:Sample)-[r:EXPRESSES]->()
//   RETURN s.dataset_id AS study, count(r) AS edges ORDER BY study;
//
//   GSE126848  1,017,051      GSE167523  2,077,600
//   GSE130970  1,480,830      GSE193066  2,814,896
//   GSE135251  9,049,104      GSE240729  2,809,042
//   GSE162694  4,530,669      GSE269412  8,691,850
// =======================================================================
