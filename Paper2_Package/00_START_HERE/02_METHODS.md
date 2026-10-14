# 2. Methods

All analysis runs against the Neo4j instance **LiverDiseaseDB**
(`dbms-1c965ecc-01bb-470f-86fa-237c81d9d40d`), database `neo4j`, Neo4j
2026.09.0 Enterprise. Code is in `05_CODE/`.

## Scope

Set by the mentor on 13 October 2026: *"repurposing not reversal"*, *"focus
only on the knowledge graph."* Evidence comes from the graph and Paper 1's own
results. The transcriptomic drug-reversal layer the plan placed before the
final ranking is **out of scope**, and is carried in the Task 8 evidence summary
as a visible row rather than dropped.

## Task 1 — master gene table

Built from `Paper1_HighConfidence/00_all_progression_genes.csv`, unfiltered.
The script asserts the class counts (2,023 / 2,377 / 1,822) and both ladder
sets (3,845 / 4,199) and fails rather than write a table disagreeing with
Paper 1.

Structural blanks are not missing data: a fibrosis-only gene has no
inflammation rho because it was never significant on that ladder. They are not
imputed.

## Task 2 — drug–gene extraction

All `ACTS_ON` edges touching a progression gene, joined to Paper 1's class,
direction, rho, trajectory cluster and tier.

`ACTS_ON.action` holds OptimusKG's relation value, which is mostly not a
pharmacological direction:

| class | meaning |
|---|---|
| pharmacokinetic | `ENZYME`, `TRANSPORTER`, `CARRIER`, `SUBSTRATE` — the gene metabolises or transports the drug |
| non-directional | `TARGET`, `MODULATOR`, `BINDING_AGENT` |
| directional | inhibitor / antagonist / blocker / agonist / activator and modulators of known sign |

**Provenance was recovered on 13 October 2026, in two separate passes.** On the
mentor's instruction the two are kept apart throughout — separate scripts,
separate source directories, separate results folders, and a `*_source` column
on every recovered field in the delivered tables. They are different acts and a
reader needs to see which fields came from which.

**Recovery 1 — OptimusKG's own discarded fields.**
`build_optimuskg_layer.py` reads `properties` from every OptimusKG parquet and
keeps it only for `disease_gene`; for drug-gene edges and drug nodes it was read
and discarded. Re-reading the same files at DOI `10.7910/DVN/IYNGEV` recovers,
for all 8,948 edges: asserting databases, per-source relation claims and a
conflict flag, plus FDA and EuropePMC URLs and a written mechanism of action on
**11.5%** of them (20.6% of the 4,984 therapeutic links) — plus,
for the graph's 12,025 drugs, SMILES (9,036), molecule type (11,623) and
clinical phase (9,902). **This is not a new source**: it is the source the graph
was already built from, read more completely. Full report:
`03_RESULTS/Recovery1_OptimusKG/`.

**Recovery 2 — ChEMBL, an external database.** Queried for the gaps Recovery 1
left. Its contribution depends entirely on which drugs are counted, so it is
reported against three denominators:

| denominator | +SMILES | +names | +phases |
|---|---:|---:|---:|
| all 18,640 OptimusKG raw records | 2,638 | 938 | 688 |
| the graph's 12,025 Drug nodes | **0** | 16 | 28 |
| the 2,404 drugs in Task 4 | **0** | 8 | 17 |

Only the last row bears on the paper: **25 field values, no structures, no
result changed.** The drugs lacking a structure are precisely those that never
reach a progression gene — ChEMBL holds records for 2,654 of them and a
structure for none, because they are biologics, antibodies and mixtures no
SMILES can represent. Removing Recovery 2 entirely would change no result, which
is the cleanest available answer to whether it falls inside "focus only on the
knowledge graph". Full report: `03_RESULTS/Recovery2_ChEMBL/`.

**Both recoveries were written back into the graph on 13 October.** The data had
been recovered into CSVs but the graph itself still carried only what the
original load kept: `name` and `node_id` on Drug nodes, `action` on `ACTS_ON`.
`paper2_write_recovered_to_graph.py` adds the drug properties to the 12,025 Drug
nodes and the per-edge evidence to all 20,674 `ACTS_ON` relationships, each
recovered field accompanied by a `*_source` property so the two recoveries stay
separable in the graph as they are in the tables.

It is additive and reversible by construction: it refuses to run if any target
key already exists, so it cannot overwrite Team 1's data or its own earlier run;
it writes nothing without `--apply`; and `--rollback` removes exactly the keys it
sets. `name` and `action` are never touched — a recovered name is written to
`recovered_name` beside `name`, not over it. After the write, the Drug node and
`ACTS_ON` counts, `d.name` and `r.action` were confirmed unchanged, and both Task
1 verification scripts still pass.

**Nothing was written to Gene nodes.** No recovered field is gene-level, and
Gene properties are the one place in this graph where duplicating derived data
has already failed: `fibrosis_rho` sits on 3,645 Gene nodes while 3,845 carry a
`TRACKS_FIBROSIS` edge, and 191 have the property with no edge. Paper 2 reads the
edges throughout. That pre-existing divergence is Team 1's to resolve and is
untouched here.

## A naming convention, stated once

The shared class has two spellings in the delivered files, and the rule is
consistent: a `progression_class` or `target_class` column carries the master
table's raw value **`both`**; every group-style label — `group`, `set`, and the
Task 3 and Task 7 summaries — carries **`shared`**. They are the same 1,822
genes.

Both appear in `task4_network_nodes.csv`, on the same row, in neighbouring
columns. That is why this is written down rather than renamed: downstream code
matches on the raw value, and renaming it is precisely the change that once
produced `both / positive` where `shared / positive` was reported and dropped
1,792 genes from a table silently.

## Task 3 — druggability

Background is the **14,794 eligible genes**, the same background Paper 1's
enrichment used; the comparison set is the 8,572 of those that are not
progression genes. Druggability counts **therapeutic edges only** — a
percentage over all edges would be partly measuring liver drug metabolism — and
the primary definition additionally requires the drug itself to pass the entity
filter. Both columns are reported; neither is a claim about whether a gene is a
good target.

Each group is tested twice: Fisher against the background, and against
background genes **matched on non-drug degree** (`ASSOCIATED_WITH`,
`INTERACTS_WITH`, `INVOLVED_IN`, `IN_PATHWAY`), 2,000 draws. Drug edges are
excluded from the matching so the null is not conditioned on the outcome.

Genes are placed in 20 bins by degree rank, and each group gene's replacement
comes from its own bin. Where a bin holds fewer background genes than the group
needs, the draw is taken **with replacement** so the per-bin count is never
silently reduced — shrinking it would re-weight the null towards whichever bins
happen to be full. `matched_bins_short` and `matched_percent_resampled` report
how often that happens; on this data both are zero throughout. The permutation
p is `(r + 1) / (n + 1)`, so it never reports as zero and its floor at 2,000
draws is 0.0005. `task3_gene_degrees.csv` ships every gene's degree and bin so
the null can be reproduced.

A third test runs the comparison a *direction* claim actually makes: falling
versus rising, head to head within each class, BH-corrected across the three
classes (`task3_falling_vs_rising.csv`). Beating a shared background is weaker
evidence than beating each other, and the two give different answers here.

## Task 4 — drug coverage

Per drug: progression genes reached, broken out by class × direction and by
trajectory cluster. Two coherence measures separate *covers a programme* from
*covers a lot*.

Specificity is reported as the plan's raw fraction **and** a Wilson lower
bound, because 1,872 of 4,212 drugs with any target have exactly one, so the
raw fraction awards 1.000 for ignorance.

Non-therapeutic entities are **flagged, never deleted**: a name heuristic, a
bare-accession flag, and target-set containment at ≥95% (which caught
`CHEMBL1201279` sharing all 126 targets with zinc acetate). Molecule type and
clinical phase were recovered and **do not discriminate** — see
`04_LIMITATIONS`.

## Task 5 — MetaPaths

Seven metapaths: the four the plan lists as minimum, the two extensions it
asks for (targets restricted to trajectory-cluster and stage-transition genes),
and GO against Reactome for comparison. Therapeutic edges only.

Two countermeasures against hub inflation, both reported with and without:

1. **Term cap** — intermediates outside 5–200 genes dropped, the usual
   enrichment convention.
2. **DWPC** — Degree-Weighted Path Count (Himmelstein & Baranzini 2015), each
   path weighted by `Π degree(node)^−0.4`.

Uncapped four-node counts are computed arithmetically rather than materialised:
one GO term joins 616 genes to 1,683 drugs, and building the hub terms would
mean hundreds of millions of rows to count.

## What "has a drug" means, and where it is enforced

Found in review of Task 3 on 13 October and traced downstream the same day.
Three places ask whether a gene has a drug, and they must agree:

| | what it counts | filter |
|---|---|---|
| Task 3 druggability | genes per group with a drug | entity filter on **both** arms |
| Task 6 component K | `0.5 x [has a therapeutic drug]` | honours Task 7's entity flag |
| Task 7 summaries | what the drug vocabulary says | **deliberately unfiltered** |

Task 7 is the exception on purpose. Its question is what the knowledge source
asserts, not what a clinician could prescribe, so filtering there would answer a
different question. It carries `non_therapeutic_entity` on every row instead, and
Task 6 applies it.

**The effect of enforcing it in K: 176 genes lose drug credit** — the ones whose
only drug is a mineral salt, a cofactor or an unnamed accession. **The final
result does not move**: the same 30 candidates, the same two targets, the same
22/8 split, an identical target top-10 and 48 of 50 of the target top-50. PDGFRA
and CACNA1C keep K = 1.0, since real kinase inhibitors and calcium-channel
blockers were never the problem.

The rule itself lives in `paper2_drug_filters.py` and is imported by Tasks 3, 6
and 7, so the three cannot drift to different answers again — which is exactly
how the gap opened.

## Task 6 — target scoring

```
TargetScore(g) = [ Σ w·C ] / [ Σ w·1{C defined} ]     C ∈ {P, F, T, K, B}
```

P, F, T and B reuse Paper 1's frozen components rather than re-deriving them,
which keeps the score traceable. Only **K** is new: two binary facts — a
therapeutic drug acts on the gene, and one of them opposes its direction of
travel — never a drug count. Carrying no count is not the same as being
degree-free, and `K_degree_sensitivity` measures the difference (Spearman 0.246
against non-drug degree).

The consistency half of K reads Task 7's `reversal_class_with_trajectory`, so a
relationship whose association direction disagrees with its F4 − F0 endpoints
does not earn credit.

**Top-N membership is a band.** The components are coarse and scores tie
heavily, so "top 50" means every gene at or above the 50th score — 133, 91 and
50 genes by class — rather than the literal first fifty, which row order would
decide. The stable core applies the stated **80%** threshold over the same 2,000
weightings rather than taking a fixed count per class.

Continuous inputs become **within-class percentiles**, not min-max. Classes are
scored separately with weights renormalised over available components, because
Paper 1's trajectory and pathway work covers only the 3,845 fibrosis genes and
scoring the other 2,377 as zero would penalise them for missing data.

Weights are equal by default and tested across 2,000 Dirichlet draws from the
whole simplex, plus a component-by-component ablation.

## Task 7 — action and direction

Scoped to drug-**target** relationships; pharmacokinetic edges excluded and
counted separately. Four-way classification: reversal-consistent,
reversal-inconsistent, ambiguous (the gene's own direction is contradictory),
unknown.

## Task 8 — final ranking

Drugs are ranked by **the single best-supported target they reach**, never by a
sum or count. 51 drugs tie at the maximum, so ties break on coherence and the
*rate* of mechanism agreement — counts are reported and never sorted on.
Drugs sharing a best-target score form a **band**; order within a band is
weakly determined.
