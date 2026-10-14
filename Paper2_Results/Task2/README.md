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
| Retain original evidence and source information | ✅ **recovered 13 Oct 2026** — see below |
| Record mechanism/action exactly where present | ✅ stored verbatim, 23 distinct values |
| Otherwise mark the action as unknown | ✅ rule implemented — **it never fired**: all 8,948 edges carry an action, 0 marked unknown |
| Column: Drug | ✅ |
| Column: Drug ID | ✅ ChEMBL |
| Column: Gene | ✅ HGNC symbol |
| Column: Gene ID | ✅ Ensembl |
| Column: Relationship | ✅ `ACTS_ON` for all |
| Column: Action/Mechanism | ✅ |
| Column: Evidence/Source | ✅ per-edge, recovered 13 Oct: the asserting databases for all 8,948 rows |
| Column: Database ID | ✅ `ChEMBL:<drug>\|Ensembl:<gene>` — unique for all 8,948 rows |
| **Output:** complete drug-gene edge table | ✅ 8,948 rows |
| **Output:** genes with ≥1 drug connection | ✅ 1,072 |
| **Output:** total unique drugs, total relationships | ✅ 3,027 / 8,948 — 3,027 database entries = 3,020 parent compounds; see `task2_near_duplicate_drugs.csv` |
| **Output:** number and % with known action direction | ✅ 1,005 / 11.2% |
| **Output:** number and % reconcilable with Paper 1 direction | ✅ 1,005 / 11.2% |
| **Output:** …and the F0–F4 trajectory pattern where available | ✅ 804 available / 417 consistent |

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
| `task2_supporting.xlsx` | 5 sheets | `action_breakdown` (23) · `mechanism_consistency` (12) · `consistency_by_cluster` (10) · `mapping_sensitivity` (6) · `consistency_permutation_test` (1) |
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
| …of those, with an F0–F4 trajectory available | 804 | 9.0% |
| …of those, **consistent with** that trajectory | **417** | **4.7%** |

## Per-edge provenance — the column the graph alone could not fill

The graph stores one property on `ACTS_ON`, `action`, because
`build_optimuskg_layer.py` reads `properties` from every parquet and keeps it
only for `disease_gene`; for drug-gene edges it is read and discarded. The
evidence is in the source file all the same, and reading that file at the same
DOI recovers it for **8,948 of 8,948 edges**:

| column | content |
|---|---|
| `Evidence_Source` | `OptimusKG: DRUG_BANK;OPEN_TARGETS via FDA;PUBMED` |
| `Evidence_Level` | single-source · multi-source · conflicting |
| `relation_assertions` | `DRUG_BANK:TARGET ; OPEN_TARGETS:INHIBITOR` |
| `source_urls` | FDA label and EuropePMC links |
| `mechanisms_of_action` | *"Gamma-amino-N-butyrate transaminase inhibitor"* |

Only two databases assert these edges: **DrugBank** and **Open Targets**.

**It changes no result.** The single stored `action` per pair was checked
against the per-source assertions across all 36,611 source edges: only **15**
carry a direction not already stored, and **2** are flagged conflicting. The
11.2% directional figure stands.

## The original note, kept for the record

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
| **Evidence/Source** | ✅ recovered from OptimusKG's own source file |

Per-edge provenance was not loaded into the graph by
`build_optimuskg_layer.py`, which read `properties` and kept only `name` and
`relation`. A dataset-level statement would be the most the graph alone could
offer, and it would still beat a blank, which a reader takes as "no evidence
found".

**The source file carries more.** The OptimusKG parquets at DOI
`10.7910/DVN/IYNGEV` hold the per-edge evidence, which is written back onto the
`ACTS_ON` relationships and read from there by this task, so every one of the
8,948 rows names the databases asserting it — for example
`OptimusKG: DRUG_BANK;OPEN_TARGETS`. Only two sources assert drug-gene edges at
all: DrugBank and Open Targets.

The parquets are reachable: the download ids are recorded in `.gitignore` and
in `05_HOW_TO_VERIFY.md`, and `data/optimuskg/` is excluded from git only for
its size (33 MB), not because it is unavailable. Recovery 1 rebuilds
`data/optimuskg_recovered/` from them in about a minute.

**Depth is uneven, and the denominator matters.** A reference URL exists for
**1,028** of the 8,948 edges and a written mechanism for **1,030** — about
**11.5%**, or **20.6%** of the 4,984 therapeutic links. Across all 36,611
recovered OptimusKG evidence records the same fields reach 38%, but most of
those records are for edges outside Paper 2's gene set, so 38% is not the
figure for this table.

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
permutation p = 0.553
```

The observed value sits **inside** the null, and in fact slightly below its
mean. See `task2_consistency_null.png`.

**Does the conclusion depend on my action → direction mapping?** No. The
mapping is a judgement call, and a few members are genuinely arguable
(`STABILISER`, `DEGRADER`, `MODULATOR`, `BINDING_AGENT`), so every variant was
re-tested with its own null (`task2_mapping_sensitivity.csv`):

| mapping | consistent | null | p |
|---|---:|---:|---:|
| as published | 52.7% | 55.9% | 0.553 |
| STABILISER dropped | 53.3% | 56.1% | 0.740 |
| DEGRADER dropped | 52.8% | 55.9% | 0.770 |
| both arguable dropped | 53.4% | 56.1% | 0.731 |
| strict core only | 58.2% | 58.3% | 0.512 |
| INHIBITOR vs AGONIST only | 61.1% | 56.5% | 0.248 |

Restricting to cleaner pharmacology lifts the raw percentage to 61.1%, but it
also shrinks n and widens the null — **no variant beats its own null.** The
conclusion is a property of the data, not of my mapping table.

So **no enrichment of reversal consistency was detected under this null
model**. That is weaker than saying the two are uncorrelated, and it is what
the test supports. Drug action is not detectably aligned with
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

## Which direction each class is scored against

Mechanism consistency compares a drug's action against the gene's direction of
change. **The two classes use different ladders, and this is worth stating
plainly:**

| class | direction used |
|---|---|
| fibrosis-only | the fibrosis ladder, F0 to F4 |
| shared | the fibrosis ladder, F0 to F4 |
| **inflammation-only** | **the disease-group ladder**, control to NASH |

Inflammation-only genes have no fibrosis direction, so the disease-group
direction is used instead. That axis rests on 216 patients from three studies
against 610 for fibrosis, so those rows are built on thinner evidence.

**It changes nothing material.** Consistency is 52.7% over all 1,005 directional
links and **51.9%** over the 804 that exclude inflammation-only genes. Both sit
inside the same null, and the conclusion — no better than chance — is the same
either way.

## How the trajectory check is defined

The plan asks how many relationships reconcile with the Paper 1 direction **and,
where available, the F0–F4 trajectory pattern**. Those are two tests, and the
second needs a rule rather than a count of what is on file.

**The rule.** The trajectory's own direction is the sign of `F4 - F0`. An edge is
**trajectory-consistent** when the drug pushes against the way the gene actually
moves across the stages — the same logic mechanism consistency applies to the
rho direction, but using the stage endpoints instead.

| | edges |
|---|---:|
| reconciled with the rho direction | 1,005 |
| …of those, a trajectory is available | 804 |
| …of those, **consistent with that trajectory** | **417** |

Availability and consistency are reported separately because they answer
different questions: 804 relationships sit on a gene with a trajectory on file,
and 417 of those actually oppose it.

`trajectory_consistency` carries four values, not two. An edge whose action has
no recorded direction — every pharmacokinetic edge, and every therapeutic one
recorded only as `TARGET` — can neither oppose a trajectory nor agree with one,
so it reads **"no drug direction"** rather than being counted as inconsistent:

| `trajectory_consistency` | edges |
|---|---:|
| no drug direction | 7,943 |
| trajectory-consistent | 417 |
| trajectory-inconsistent | 387 |
| no trajectory | 201 |

### Where the two direction measures disagree

The rho direction and the sign of F4 − F0 are different quantities — a rank
correlation across five stages against the difference between the two end
stages — so they can disagree. Counting that needs both values present:
`NaN != "increasing"` is true in pandas, so comparing the columns directly
reports every row with a missing direction as a disagreement.

Done properly, they disagree on **576 of the 8,923 edges where both are known,
covering 112 genes — and none of those genes has a Paper 1 trajectory cluster.**
Every disagreement is on an inflammation-only gene, whose `gene_direction` comes
from the disease-group ladder (216 patients) while F0–F4 are fibrosis-stage
means (610 patients). Those are two different contrasts, so this is not a
trajectory conflict.

**Among the fibrosis-associated genes that actually have a trajectory, the two
measures agree on every edge.**

## Two limitations worth stating plainly

**693 drug entries use their identifier as their name.** Their `name` in
OptimusKG *is* their ChEMBL accession, so they cannot be judged, filtered or
reported by name. They are flagged, not deleted.

**A reference URL exists for only 1,028 relationships.** Every row carries source
attribution — which databases assert the edge — but that is not the same as a
supporting publication or label link, which about one row in nine has.
