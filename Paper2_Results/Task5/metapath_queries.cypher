// Paper 2 Task 5 — every read-only Cypher statement used (run order).
// Parameters: $drugs = Task 2 drugs with a pharmacological link to a progression gene;
// $pk = ['ENZYME','TRANSPORTER','CARRIER']; $prog = 6,222 progression genes (Ensembl);
// $liver = Task 4 liver disease set (161 ids); $genes = significant transition genes.
// M4/M5 path counts are computed from the pulled edges by sparse matrix product and
// verified with the aggregated COUNT M4 statement below.

// ---- TEST M1
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog AND x.node_id IN $liver
RETURN d.name, g.symbol, x.name LIMIT 5;

// ---- TEST M4
MATCH (d:Drug)-[r:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)<-[:IN_PATHWAY]-(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog AND t <> g
RETURN d.name, t.symbol, p.name, g.symbol LIMIT 5;

// ---- drug -> pharmacological targets (all genes)
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk
RETURN d.node_id AS drug, g.ensembl_id AS gene, r.action AS action;

// ---- gene -> Reactome pathway
MATCH (g:Gene)-[:IN_PATHWAY]->(p:Pathway) RETURN g.ensembl_id AS gene, p.node_id AS node, p.name AS name;

// ---- gene -> GO biological process
MATCH (g:Gene)-[:INVOLVED_IN]->(b:BioProcess) RETURN g.ensembl_id AS gene, b.node_id AS node, b.name AS name;

// ---- gene -> liver disease
MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(x:Disease) WHERE x.node_id IN $liver
RETURN g.ensembl_id AS gene, x.node_id AS node, x.name AS name, r.score AS score;

// ---- gene pharmacological drug degree
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE g.ensembl_id IN $prog AND NOT r.action IN $pk
RETURN g.ensembl_id AS gene, count(DISTINCT d) AS deg;

// ---- liver disease gene degree
MATCH (g:Gene)-[:ASSOCIATED_WITH]->(x:Disease) WHERE x.node_id IN $liver RETURN x.node_id AS node, count(g) AS deg;

// ---- COUNT M1
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog AND x.node_id IN $liver
RETURN count(*) AS paths, count(DISTINCT d) AS drugs, count(DISTINCT g) AS genes, count(DISTINCT x) AS ends;

// ---- COUNT M2
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog
RETURN count(*) AS paths, count(DISTINCT d) AS drugs, count(DISTINCT g) AS genes, count(DISTINCT p) AS ends;

// ---- COUNT M3
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:INVOLVED_IN]->(b:BioProcess)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog
RETURN count(*) AS paths, count(DISTINCT d) AS drugs, count(DISTINCT g) AS genes, count(DISTINCT b) AS ends;

// ---- COUNT M4 (aggregated: per pathway, target pairs x progression members, minus T = P)
MATCH (d:Drug)-[r:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk
WITH p, count(*) AS dt_pairs, sum(CASE WHEN t.ensembl_id IN $prog THEN 1 ELSE 0 END) AS self_pairs
MATCH (p)<-[:IN_PATHWAY]-(g:Gene) WHERE g.ensembl_id IN $prog
WITH p, dt_pairs, self_pairs, count(g) AS n_prog
RETURN sum(dt_pairs * n_prog - self_pairs) AS paths;

// ---- COUNT M6 F0→F1
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $genes RETURN count(*) AS paths;

// ---- COUNT M6 F1→F2
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $genes RETURN count(*) AS paths;

// ---- COUNT M6 F2→F3
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $genes RETURN count(*) AS paths;

// ---- COUNT M6 F3→F4
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $genes RETURN count(*) AS paths;

