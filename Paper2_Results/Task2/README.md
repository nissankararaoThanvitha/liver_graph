# Task 2 — Drug–gene relationships from the knowledge graph

Plan: *"For every progression gene, extract all connected drugs... For each edge
retain the original evidence and source information. Where the knowledge source
contains mechanism/action information, record it exactly; otherwise mark the
action as unknown."*

Built by `scripts/paper2_task2_drug_gene_edges.py` against instance
**LiverDiseaseDB** (`dbms-1c965ecc-…`), database `neo4j`, 12 October 2026.

## Does this match the plan? — line by line

| Plan asks for | Status |
|---|---|
| Extract all connected drugs for every progression gene | ✅ 8,948 edges, all 6,222 genes queried |
| …from **CausalKG**/OptimusKG | ⚠️ **CausalKG does not exist in this project.** The knowledge layer is OptimusKG (`data/graph_okg`). PrimeKG is superseded and kept only as `data/graph_primekg_superseded` for the comparison that justified the switch. Source used: OptimusKG |
| Retain original evidence and source information | ❌ **not available per edge** — see below |
| Record mechanism/action exactly where present | ✅ stored verbatim, 23 distinct values |
| Otherwise mark the action as unknown | ✅ rule implemented — **it never fired**: all 8,948 edges carry an action, 0 marked unknown |
| Column: Drug | ✅ |
| Column: Drug ID | ✅ ChEMBL |
| Column: Gene | ✅ HGNC symbol |
| Column: Gene ID | ✅ Ensembl |
| Column: Relationship | ✅ `ACTS_ON` for all |
| Column: Action/Mechanism | ✅ |
| Column: Evidence/Source | ⚠️ dataset-level only, stated explicitly in the cell |
| Column: Database ID | ✅ `ChEMBL:<drug>\|Ensembl:<gene>` — unique for all 8,948 rows |
| **Output:** complete drug-gene edge table | ✅ 8,948 rows |
| **Output:** genes with ≥1 drug connection | ✅ 1,072 |
| **Output:** total unique drugs, total relationships | ✅ 3,027 / 8,948 |
| **Output:** number and % with known action direction | ✅ 1,005 / 11.2% |
| **Output:** number and % reconcilable with Paper 1 direction | ✅ 1,005 / 11.2% |
| **Output:** …and the F0–F4 trajectory pattern where available | ✅ 804 / 9.0% |

Two notes on interpretation:

**Database ID** is listed beside Drug ID in the plan, so it is meant to be
something other than a copy of it. There is no edge-level identifier in the
graph — the loader `MERGE`s the relationship and stores only `action` — so it
is filled with the namespaced pair, which states which vocabulary each side is
in and is a stable join key for the relationship itself.

**"Reconcilable with the Paper 1 direction"** is computed on *drug-target*
relationships only. Pharmacokinetic edges are excluded, because a gene that
metabolises a drug has no mechanism to be consistent or inconsistent with.

## Files

| File | Rows | What it is |
|---|---:|---|
| `task2_drug_gene_edges.csv` | 8,948 | the complete edge table |
| `task2_summary.csv` | 7 | the counts the plan asks for |
| `task2_action_breakdown.csv` | 23 | every action value, classified |
| `task2_mechanism_consistency.csv` | — | consistency × progression class |
| `task2_consistency_by_cluster.csv` | — | consistency × F0–F4 trajectory pattern |
| `task2_mapping_sensitivity.csv` | 6 | consistency under 6 action→direction mappings |
| `task2_consistency_permutation_test.csv` | 1 | the valid test, replacing the binomial |
| `task2_action_classes.png` | — | what the 8,948 edges actually are |
| `task2_consistency_null.png` | — | observed consistency against its null |

## Was mode of action lost when the graph was loaded?

**No — checked, not assumed.** `load_knowledge_layer.cypher` does
`MERGE (d)-[r:ACTS_ON]->(g) SET r.action = row.rel_type`, which keeps **one**
edge per drug–gene pair. Had the source listed a pair twice with different
actions, the later row would have silently overwritten the earlier one and the
directional share would be an undercount.

The source file is in the repo at
`Paper1_Package/04_DATA/knowledge_layer/edges_drug_gene.csv`:

```
source rows                   20,674
distinct drug-gene pairs      20,674
pairs with >1 action row           0
rows lost to MERGE overwrite       0
```

Nothing was overwritten. **11.2% is exact, not a floor.** Re-checked by
`scripts/paper2_task2_robustness.py`.

## The required counts

| Measure | Value | % of relationships |
|---|---:|---:|
| Progression genes in the master table | 6,222 | |
| **Progression genes with ≥1 drug connection** | **1,072** | 17.2% of genes |
| **Total unique drugs** | **3,027** | |
| **Total drug–gene relationships** | **8,948** | 100% |
| Relationships with known action direction | 1,005 | **11.2%** |
| Reconcilable with Paper 1 progression direction | 1,005 | **11.2%** |
| …of those, also carrying an F0–F4 trajectory pattern | 804 | 9.0% |

## One column the graph cannot fill

`ACTS_ON` carries **exactly one** property, `action`. The loader
(`load_knowledge_layer.cypher`, block 8/11) does `SET r.action = row.rel_type`
and nothing more, and `build_optimuskg_layer.py` only ever carried
`from_id / to_id / rel_type / score` out of the source parquet — with `score`
empty for every edge type except `disease_gene`.

So of the columns the plan asks for:

| Column | Status |
|---|---|
| Drug, Drug ID, Gene, Gene ID | available |
| Relationship | `ACTS_ON` for all 8,948 |
| Action/Mechanism | available, recorded exactly as stored |
| Database ID | drug ChEMBL id; gene side is the Ensembl id |
| **Evidence/Source** | **not available per edge** |

Per-edge provenance was never loaded into the graph. `Evidence_Source` is
therefore filled with the dataset-level statement
`"OptimusKG (Harvard Dataverse DOI 10.7910/DVN/IYNGEV); per-edge evidence not
loaded"` rather than left blank, so nobody later reads a blank cell as "no
evidence found". Recovering true per-edge evidence means re-parsing the
OptimusKG parquet, which is not in this repository.

## Action is not the same thing as direction

`action` holds OptimusKG's relation value. Most of it is not a pharmacological
direction at all:

| Class | Edges | % | What it means |
|---|---:|---:|---|
| therapeutic — non-directional | 3,979 | 44.5% | `TARGET`, `MODULATOR`, `BINDING_AGENT`. A real target, effect direction unrecorded |
| **pharmacokinetic** | **3,964** | **44.3%** | `ENZYME`, `TRANSPORTER`, `CARRIER`, `SUBSTRATE`. The gene **metabolises or transports** the drug — it is *not* a therapeutic target |
| therapeutic — lowers | 679 | 7.6% | inhibitor, antagonist, blocker, degrader, inverse agonist, negative modulators |
| therapeutic — raises | 326 | 3.6% | agonist, activator, opener, releasing agent, stabiliser, positive modulators |

**44% of the table is drug metabolism, not drug targeting.** In a liver study
that is a systematic bias and not noise: the cytochromes live in the liver and
their expression genuinely changes as it fails, so they appear among
progression genes while telling you nothing therapeutic. Any druggability or
coverage figure computed over all 8,948 edges is measuring liver drug
metabolism. Tasks 3 and 4 must use the therapeutic subset and report the
pharmacokinetic one separately.

## Mechanism consistency — the early check the plan asks for

A relationship is called **reversal-consistent** only when the drug's action
opposes the direction the gene moves in as disease worsens:

| | |
|---|---|
| gene rises with disease + drug lowers it | reversal-consistent |
| gene falls with disease + drug raises it | reversal-consistent |
| same direction as the disease | reversal-inconsistent |
| action non-directional | unknown |
| action pharmacokinetic | not-applicable |

| Result | Edges |
|---|---:|
| unknown | 3,979 |
| not-applicable | 3,964 |
| **reversal-consistent** | **530** |
| **reversal-inconsistent** | **475** |

Sanity check: `NINTEDANIB → PDGFRA`, `INHIBITOR`, gene increasing,
rho +0.417, cluster "Late increase (largest at F3→F4)" → **reversal-consistent**.
The known showcase case lands where it should.

### FINDING — consistency is not distinguishable from chance

530 consistent of 1,005 is **52.7%**.

> **The binomial test first reported here (p = 0.088) was invalid.** It assumed
> 1,005 independent observations. They are not independent: a drug can hit
> several genes and a gene is hit by several drugs, so the edges come in
> correlated blocks. Replaced with a permutation test that shuffles direction
> labels at the **gene** level, moving each gene's whole set of edges together
> and preserving the clustering under the null.

```
observed                       52.7%
null (gene-level shuffle, 10,000 permutations)
  mean 55.9%, 95% range 45.6% – 66.5%
permutation p = 0.778
```

The observed value sits **inside** the null, and in fact slightly below its
mean. See `task2_consistency_null.png`.

**Does the conclusion depend on my action → direction mapping?** No. The
mapping is a judgement call, and a few members are genuinely arguable
(`STABILISER`, `DEGRADER`, `MODULATOR`, `BINDING_AGENT`), so every variant was
re-tested with its own null (`task2_mapping_sensitivity.csv`):

| mapping | consistent | null | p |
|---|---:|---:|---:|
| as published | 52.7% | 55.9% | 0.778 |
| STABILISER dropped | 53.3% | 56.1% | 0.740 |
| DEGRADER dropped | 52.8% | 55.9% | 0.770 |
| both arguable dropped | 53.4% | 56.1% | 0.731 |
| strict core only | 58.2% | 58.3% | 0.512 |
| INHIBITOR vs AGONIST only | 61.1% | 56.5% | 0.248 |

Restricting to cleaner pharmacology lifts the raw percentage to 61.1%, but it
also shrinks n and widens the null — **no variant beats its own null.** The
conclusion is a property of the data, not of my mapping table.

So on this evidence drug action is **essentially uncorrelated** with
progression direction. That is not a defect — these drugs were developed for
other diseases and there is no reason their mechanisms should align with liver
progression. But it means:

**Mechanism consistency cannot by itself rank candidates.** It is one weak
evidence layer among several, exactly as the plan frames it — *"an early
mechanism-consistency check without treating it as therapeutic proof"* — and
the repurposing handoff is blunter still: the graph records association
direction and timing, it does **not** establish whether inhibition or
activation is beneficial.

Per gene rather than per edge (edges are not independent — one drug hits many
genes), of the 202 genes with at least one directional edge: 111 are wholly
consistent, 62 wholly inconsistent, 29 mixed.

## The 30 contradictory genes did not bite — yet

Task 1 found 30 shared genes that fall with fibrosis but rise with
inflammation, and flagged that they cannot be given one direction. In this
table only **7 of the 30** have any drug edge at all (14 edges), and **none of
those 14 is directional** — 8 non-directional, 6 pharmacokinetic.

So no edge had to be classified `ambiguous`, and the contradiction does not
affect any number above. It is still live for Task 7: if directional
annotations are added later, those genes need an explicit rule rather than a
default.

## Columns

`Drug`, `Drug_ID` (ChEMBL), `Gene`, `Gene_ID` (Ensembl), `Relationship`,
`Action_Mechanism`, `Evidence_Source`, `Database_ID`, `action_class`,
`progression_class`, `gene_direction`, `fibrosis_rho`, `inflammation_rho`,
`Cluster`, `Cluster_pattern`, `Largest_transition`, `Tier`,
`in_fibrosis_starting_set`, `mechanism_consistency`.

Paper 1 evidence is joined on `Gene_ID`. `Cluster`, `Cluster_pattern`,
`Largest_transition` and `Tier` are blank for genes outside the 3,845
fibrosis-associated set — structural, not missing data.

## Carried forward

1. **Split therapeutic from pharmacokinetic before counting anything** in
   Tasks 3 and 4. 44% of these edges are metabolism.
2. **Only 11.2% of relationships carry a usable direction.** Any
   direction-aware analysis runs on ~1,000 edges, not ~9,000, and the unknown
   bucket must be reported as the majority it is.
3. **Mechanism consistency is at chance level.** Do not build a narrative on
   it, and do not weight it heavily in the Task 6 TargetScore without saying
   so.
