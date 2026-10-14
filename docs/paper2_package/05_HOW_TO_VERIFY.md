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

**One order, start to finish. Every script is self-contained: re-running any of
them rebuilds its own outputs, and no later pass is needed to restore columns.**

```bash
python scripts/paper2_task1_master_table.py
python scripts/paper2_task2_drug_gene_edges.py       # reads edge provenance from the graph
python scripts/paper2_task3_druggability.py          # slow: 2,000 permutations
python scripts/paper2_task4_drug_coverage.py         # reads drug chemistry from the graph
python scripts/paper2_task5_metapaths.py             # slow: 36M-row joins
python scripts/paper2_task7_action_direction.py      # before Task 6: K reads its output
python scripts/paper2_task6_target_score.py          # slow: 2,000 weightings
python scripts/paper2_task8_final_ranking.py
python scripts/paper2_task5_transition_convergence.py   # needs Task 8's candidates
python scripts/paper2_task2_robustness.py
python scripts/paper2_figures.py
uv run --with neo4j --with pandas python scripts/paper2_recovery_optimuskg_report.py
uv run --with neo4j --with pandas python scripts/paper2_recovery_chembl_report.py
python scripts/paper2_manifest.py
```

**Why that order and not another.** Three dependencies are real and the rest is
numbering:

| this | must run after | because |
|---|---|---|
| Task 6 | Task 7 | K reads `reversal_class_with_trajectory` |
| Task 8 | Task 6 | it ranks on `TargetScore` and the stable core |
| Task 5 convergence | Task 8 | Test B needs the candidate set |

**The recovered OptimusKG and ChEMBL fields live on the graph**, written back to
the `Drug` nodes and `ACTS_ON` relationships. Task 2 reads the edge provenance
and Task 4 the drug chemistry straight from there, so both carry those columns
on a plain re-run. `paper2_integrate_recovered_evidence.py` remains in the
repository as the fallback for a graph that has not had the write-back applied;
**it is not part of the run order and does not need to be run.**

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
those numbers move, the documents no longer match the data.

**Watch the denominator.** ChEMBL's contribution reads as 2,638 structures
against OptimusKG's 18,640 raw records and **zero** against the 12,025 in the
graph, because 6,615 raw records never reached it. The 12,025 is the drug
vocabulary Paper 2 ranks, so that is the figure the documents quote.
`recovery2_marginal_contribution.csv` gives all three side by side.

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

## Reproducing the degree-matched null

Task 3's null is the one result that cannot be checked from a summary table, so
`Paper2_Results/Task3/task3_gene_degrees.csv` ships every eligible gene with its
non-drug degree, its degree bin and its drug counts. The null is: for each group
gene, draw a replacement from its own bin out of the 8,572 non-progression
genes, 2,000 times, and take the fraction drug-connected.

```python
import pandas as pd, numpy as np
g = pd.read_csv("Paper2_Results/Task3/task3_gene_degrees.csv")
pool = g[g.progression_class == "NOT progression"]
sub = g[g.group == "shared / negative"]
bins = pool.groupby("degree_bin").Ensembl_ID.apply(list).to_dict()
conn = pool.set_index("Ensembl_ID").drug_connected_usable.to_dict()
rng, wanted = np.random.default_rng(42), sub.degree_bin.value_counts().to_dict()
draws = [np.mean([conn[x] for b, k in wanted.items()
                  for x in rng.choice(bins[b], k, replace=k > len(bins[b]))])
         for _ in range(2000)]
print(round(100 * np.mean(draws), 1))      # expect 9.6, against an observed 16.9
```

The per-bin count is honoured with replacement where a bin is short, rather than
shrinking the draw; `matched_bins_short` and `matched_percent_resampled` in
`task3_enrichment_tests.csv` report how often that was needed, and both are zero
for every group here. The reported p is `(r + 1) / (n + 1)`, so its floor is
0.0005 and it never prints as zero.

## Reproducing the two other simulations

**Task 7, the subgroup permutation.** `task7_action_direction_evidence.csv`
carries every relationship with its group, its reversal class and its
progression direction, which is everything the null needs: shuffle the CLASS
part of the group label among genes sharing a direction, 2,000 times, and
compare each group's observed consistency against its own draws.
`task7_consistency_significance.csv` reports the result with `permutations`, the
null mean and a `(r + 1) / (n + 1)` p-value, so the floor is 0.0005 and never
zero. The `binomial_*_descriptive` columns are not the basis of any claim;
`inference_basis` on each row names the permutation.

**Task 5, candidate convergence.** `task5_mp7_reach_per_drug.csv` holds, for
each of the 1,876 ranked drugs, its MP7 reach and the share of that reach
landing on supported F3→F4 transition genes, with `is_candidate` on the row.
Test B is a two-sample permutation over that one column:

```python
import pandas as pd, numpy as np
d = pd.read_csv("Paper2_Results/Task5/task5_mp7_reach_per_drug.csv")
v = d.share_at_target_transition.to_numpy()
n_c = int(d.is_candidate.sum())
obs = v[d.is_candidate].mean() - v[~d.is_candidate].mean()
rng = np.random.default_rng(42)
null = np.array([v[i[:n_c]].mean() - v[i[n_c:]].mean()
                 for i in (rng.permutation(len(v)) for _ in range(2000))])
c = null.mean()
print(round(obs, 4), (1 + int(np.sum(abs(null - c) >= abs(obs - c)))) / 2001)
# expect 0.02 and p around 0.38
```

The 194,393-row MP7 pair table this is derived from is a local intermediate and
is not shipped; `paper2_task5_metapaths.py` regenerates it in one run.

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
