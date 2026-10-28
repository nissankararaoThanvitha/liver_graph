// Paper 2 Task 5 (revised) — read-only Cypher used. $drugs = 3,027 drugs linked to progression genes;
// $prog = 6,222 progression genes; $liver = 161 liver diseases. MP3–MP5 and MP7 path counts are
// computed from the pulled edges by sparse matrix products; MP1–MP3 are re-counted in Neo4j.

// ---- TEST MP7 (LIMIT 5)
MATCH (d:Drug)-[:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)<-[:IN_PATHWAY]-(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND g.ensembl_id IN $prog AND x.node_id IN $liver AND t <> g
RETURN d.name, t.symbol, p.name, g.symbol, x.name LIMIT 5;

// ---- drug -> all targets
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE d.node_id IN $drugs
RETURN d.node_id AS drug, d.name AS drug_name, g.ensembl_id AS gene, g.symbol AS symbol, r.action AS action;

// ---- gene -> pathway
MATCH (g:Gene)-[:IN_PATHWAY]->(p:Pathway) RETURN g.ensembl_id AS gene, p.node_id AS pathway, p.name AS pathway_name;

// ---- progression gene -> liver disease
MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(x:Disease) WHERE g.ensembl_id IN $prog AND x.node_id IN $liver
RETURN g.ensembl_id AS gene, x.node_id AS disease, x.name AS disease_name, r.score AS score;

// ---- known drug -> liver disease uses
MATCH (d:Drug)-[r:TREATS|OFF_LABEL_FOR|CONTRAINDICATED_IN]->(x:Disease) WHERE d.node_id IN $drugs AND x.node_id IN $liver
RETURN d.node_id AS drug, x.node_id AS disease, type(r) AS relation;

// ---- COUNT MP1
MATCH (d:Drug)-[:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND g.ensembl_id IN $prog AND x.node_id IN $liver RETURN count(*) AS paths;

// ---- COUNT MP2
MATCH (d:Drug)-[:ACTS_ON]->(g:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs AND g.ensembl_id IN $prog RETURN count(*) AS paths;

// ---- COUNT MP3 (aggregated per pathway, minus T = P)
MATCH (d:Drug)-[:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs
WITH p, count(*) AS dt_pairs, sum(CASE WHEN t.ensembl_id IN $prog THEN 1 ELSE 0 END) AS self_pairs
MATCH (p)<-[:IN_PATHWAY]-(g:Gene) WHERE g.ensembl_id IN $prog
WITH p, dt_pairs, self_pairs, count(g) AS n_prog
RETURN sum(dt_pairs * n_prog - self_pairs) AS paths;

