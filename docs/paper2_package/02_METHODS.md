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

**Provenance was recovered on 13 October 2026.** `build_optimuskg_layer.py`
reads `properties` from every OptimusKG parquet and keeps it only for
`disease_gene`; for drug-gene edges and drug nodes it was read and discarded.
Re-reading the same files at DOI `10.7910/DVN/IYNGEV` recovers, for all 8,948
edges: asserting databases, per-source relation claims, a conflict flag, FDA
and EuropePMC URLs on 38%, and a written mechanism of action.

## Task 3 — druggability

Background is the **14,794 eligible genes**, the same background Paper 1's
enrichment used; the comparison set is the 8,572 of those that are not
progression genes. Druggability counts **therapeutic edges only** — a
percentage over all edges would be partly measuring liver drug metabolism.

Each group is tested twice: Fisher against the background, and against
background genes **matched on non-drug degree** (`ASSOCIATED_WITH`,
`INTERACTS_WITH`, `INVOLVED_IN`, `IN_PATHWAY`), 2,000 draws. Drug edges are
excluded from the matching so the null is not conditioned on the outcome.

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

## Task 6 — target scoring

```
TargetScore(g) = [ Σ w·C ] / [ Σ w·1{C defined} ]     C ∈ {P, F, T, K, B}
```

P, F, T and B reuse Paper 1's frozen components rather than re-deriving them,
which keeps the score traceable. Only **K** is new, and it is deliberately
degree-free — two binary facts (a therapeutic drug acts on the gene; one of
them opposes its direction), never a drug count.

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
