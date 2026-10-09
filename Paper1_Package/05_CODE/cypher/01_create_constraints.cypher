// create_kg_constraints.cypher
// ---------------------------------------------------------------------
// Run these FIVE lines in Neo4j Browser, one at a time.
// They are instant (no data is touched) but must exist before the
// knowledge-layer edges are loaded: without them every edge lookup
// scans all 17,080 Disease nodes instead of using an index.
//
// The MCP connection refuses schema commands, which is why these are
// here rather than run automatically.
// ---------------------------------------------------------------------

CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (d:Disease) REQUIRE d.node_id IS UNIQUE;

CREATE CONSTRAINT drug_id IF NOT EXISTS FOR (d:Drug) REQUIRE d.node_id IS UNIQUE;

CREATE CONSTRAINT pathway_id IF NOT EXISTS FOR (p:Pathway) REQUIRE p.node_id IS UNIQUE;

CREATE CONSTRAINT bioprocess_id IF NOT EXISTS FOR (b:BioProcess) REQUIRE b.node_id IS UNIQUE;

CREATE CONSTRAINT phenotype_id IF NOT EXISTS FOR (p:Phenotype) REQUIRE p.node_id IS UNIQUE;

// Also useful now that lookups by gene name are common:
CREATE INDEX gene_symbol IF NOT EXISTS FOR (g:Gene) ON (g.symbol);
