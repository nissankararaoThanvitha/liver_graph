# 5. How to verify

Every number in Paper 2 can be re-derived. This says how, in the order the
pipeline runs.

## Prerequisites

- Neo4j instance **LiverDiseaseDB**, database `neo4j`, running on
  `bolt://127.0.0.1:7687`
- Python 3.13, `pandas numpy scipy matplotlib openpyxl neo4j pyarrow`
- Run every script from the repository root

Credentials are read from the local MCP server configuration, never from source.

## Run order

```bash
python scripts/paper2_task1_master_table.py
python scripts/paper2_task2_drug_gene_edges.py
python scripts/paper2_task3_druggability.py          # slow: 2,000 permutations
python scripts/paper2_task4_drug_coverage.py
python scripts/paper2_task5_metapaths.py             # slow: 36M-row joins
python scripts/paper2_task5_transition_convergence.py
python scripts/paper2_task6_target_score.py          # slow: 2,000 weightings
python scripts/paper2_task7_action_direction.py
python scripts/paper2_task8_final_ranking.py
python scripts/paper2_task2_robustness.py
python scripts/paper2_figures.py
python scripts/paper2_integrate_recovered_evidence.py   # LAST — see below
# the two recovery reports read the integrated columns, so they follow it
uv run --with neo4j --with pandas python scripts/paper2_recovery_optimuskg_report.py
uv run --with neo4j --with pandas python scripts/paper2_recovery_chembl_report.py
python scripts/paper2_manifest.py
```

`paper2_integrate_recovered_evidence.py` rewrites Task 2, 4 and 7 outputs in
place. **Re-running any of those task scripts drops the recovered columns**, so
run the integration again afterwards.

## The two recoveries

Kept separate on the mentor's instruction of 13 October — separate scripts,
separate directories, separate results folders. Neither reads the other's
outputs except in one direction: Recovery 2 needs Recovery 1's
`drug_metadata.csv` to know where OptimusKG is silent.

```bash
# fetch the two source files from DOI 10.7910/DVN/IYNGEV into data/optimuskg/
#   drug_gene.parquet  file id 14220895   (500 KB)
#   drug.parquet       file id 14220910   (33 MB)

# Recovery 1 -- OptimusKG's own discarded fields     -> data/optimuskg_recovered/
python scripts/paper2_recover_optimuskg_evidence.py
uv run --with neo4j --with pandas python scripts/paper2_recovery_optimuskg_report.py

# Recovery 2 -- ChEMBL, external                     -> data/chembl_recovered/
uv run --with pandas python scripts/paper2_fetch_chembl_gaps.py
uv run --with neo4j --with pandas python scripts/paper2_recovery_chembl_report.py
```

Neither data directory is committed (11 MB, regenerable in about a minute).

**Both report scripts are independent checks, not just summaries.** They
reproduce the limitation figures from the recovered files, against the graph's
own drug count: Recovery 1 lands on 9,036 SMILES of 12,025 and 1,163
accession-named drugs; Recovery 2 lands on 16 names and 0 structures added. If
those numbers move, the documents are stale.

**Watch the denominator.** ChEMBL's contribution reads as 2,638 structures
against OptimusKG's 18,640 raw records and **zero** against the 12,025 in the
graph, because 6,615 raw records never reached it. Measuring the raw file is how
this was first misreported. `recovery2_marginal_contribution.csv` gives all
three denominators side by side for exactly this reason.

## Independent checks

Two scripts exist only to try to break Task 1, and exit non-zero on failure:

```bash
python scripts/paper2_task1_verify_against_neo4j.py
python scripts/paper2_task1_verify_stage_means.py
```

The first compares the gene **set**, not just its size — two sets of 6,222 can
agree on count and disagree on membership — then every rho, q, n_studies,
direction and symbol. The second recomputes F0–F4 from `EXPRESSES` under the
biopsy policy, which the first never touched; it independently lands on 610
staged patients.

## Spot-checks you can run by hand

```cypher
// the gene set and its three classes -- expect 2,023 / 2,377 / 1,822
MATCH (g:Gene) WHERE (g)-[:TRACKS_FIBROSIS]->() OR (g)-[:TRACKS_INFLAMMATION]->()
WITH g, exists((g)-[:TRACKS_FIBROSIS]->())     AS f,
        exists((g)-[:TRACKS_INFLAMMATION]->()) AS i
RETURN CASE WHEN f AND i THEN 'shared' WHEN f THEN 'fibrosis-only'
            ELSE 'inflammation-only' END AS class, count(g) AS genes;

// drug-gene edges on progression genes -- expect 8,948 / 1,072 / 3,027
MATCH (g:Gene)-[:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->() WITH DISTINCT g
MATCH (dr:Drug)-[a:ACTS_ON]->(g)
RETURN count(a) AS edges, count(DISTINCT g) AS genes, count(DISTINCT dr) AS drugs;

// the showcase case
MATCH (d:Drug {name:'NINTEDANIB'})-[r:ACTS_ON]->(g:Gene {symbol:'PDGFRA'})
OPTIONAL MATCH (g)-[t:TRACKS_FIBROSIS]->()
RETURN r.action, round(t.rho,3) AS rho, t.n_studies;

// the same case with the recovered properties -- the whole evidence chain
// in one query, which was not possible before the 13 October write-back
MATCH (d:Drug {name:'NINTEDANIB'})-[r:ACTS_ON]->(g:Gene {symbol:'PDGFRA'})
RETURN d.node_id, d.molecule_type, d.max_phase, d.smiles_source,
       r.action, r.evidence_level, r.sources_direct, r.mechanisms_of_action;
// expect CHEMBL502835 / Small molecule / 4.0 / OptimusKG /
//        INHIBITOR / multi-source / DRUG_BANK;OPEN_TARGETS / PDGFR inhibitor

// recovered coverage -- expect 9,036 structures and 11,623 molecule types
MATCH (d:Drug)
RETURN count(d)                                        AS drugs,
       count(d.smiles)                                 AS with_smiles,
       count(d.molecule_type)                          AS with_type,
       count(d.recovered_name)                         AS with_name;

// every ACTS_ON edge should now name its asserting databases
MATCH ()-[r:ACTS_ON]->()
RETURN count(r) AS edges, count(r.sources_direct) AS attributed,
       count(r.source_urls) AS with_url;
```

The write-back is reversible. `paper2_write_recovered_to_graph.py --rollback`
removes exactly the properties it set and nothing else, returning the graph to
its pre-13-October state; re-running with `--apply` restores them. It refuses to
write at all if any target property already exists, so it cannot overwrite
Team 1's data or double-apply.

## Three traps that will bite

**Counting relationships.** Count **per type**. Counting all types in one query
times out against this server's 1 GB heap.

**Joining drugs to progression genes.** Put `WITH DISTINCT g` after matching
the progression genes, before joining drugs. Without it, shared genes are
counted twice and 8,948 becomes a false 12,107.

**Ordering by a nullable column.** `ORDER BY x DESC` puts NULLs **first** in
Neo4j, so a `LIMIT` returns rows with no value. Use
`ORDER BY (x IS NULL), x DESC`.

And one for disease selection: match on ontology ID or walk `PARENT_OF`, never
on name. Searching names for `nash` also returns
*"level of protein mago nashi homolog 2 in blood serum"*.

## Reproducibility

Random seeds are fixed at 42 throughout. Re-running a script reproduces its
output byte for byte — checked for Task 1, where the regenerated CSV carries an
identical SHA-256.

`00_START_HERE/06_FILE_MANIFEST.csv` lists path, size and SHA-256 for every
file in this package, so a reader can confirm their copy is the one the numbers
came from.
