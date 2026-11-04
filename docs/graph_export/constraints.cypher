// Constraints and index of the original graph (Neo4j 2026.10.1, 3 Nov 2026).
CREATE CONSTRAINT bioprocess_id IF NOT EXISTS FOR (n:BioProcess) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT dataset_id IF NOT EXISTS FOR (n:Dataset) REQUIRE n.dataset_id IS UNIQUE;
CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (n:Disease) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT drug_id IF NOT EXISTS FOR (n:Drug) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT gene_id IF NOT EXISTS FOR (n:Gene) REQUIRE n.ensembl_id IS UNIQUE;
CREATE CONSTRAINT pathway_id IF NOT EXISTS FOR (n:Pathway) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT phenotype_id IF NOT EXISTS FOR (n:Phenotype) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT sample_id IF NOT EXISTS FOR (n:Sample) REQUIRE n.sample_id IS UNIQUE;
CREATE INDEX gene_symbol IF NOT EXISTS FOR (n:Gene) ON (n.symbol);
