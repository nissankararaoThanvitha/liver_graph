# Task 5 — MetaPaths

Plan: *"Implement graph queries that connect drugs to the progression
biology… Record the exact graph schema and query logic so the analysis is
reproducible… Because raw path counts can favor highly connected nodes,
additionally report degree-normalized path support… Interpret MetaPaths as
evidence of biological connectivity, not as proof of drug efficacy."*

Built by `scripts/paper2_task5_metapaths.py` against **LiverDiseaseDB**,
database `neo4j`, 12 October 2026.

## Files

| File | What it is |
|---|---|
| `task5_metapath_definitions.csv` | the 7 metapaths, their schema, and why each is run |
| `task5_metapath_counts.csv` | paths, drugs, genes, terms — each capped and uncapped |
| `task5_top_drug_gene_dwpc.csv` | top 200 drug / progression-gene pairs by DWPC |
| `task5_example_subgraphs.csv` | worked paths for quality checking |
| `task5_supporting.xlsx` | `hub_terms` · `count_vs_dwpc_top100` |
| `task5_metapath_sizes.png` | path volume per metapath, capped vs uncapped |

## The seven metapaths

| id | metapath | schema |
|---|---|---|
| MP1 | D-G-Di | Drug –ACTS_ON→ Gene –ASSOCIATED_WITH→ Disease |
| MP2 | D-G-P | Drug –ACTS_ON→ Gene –IN_PATHWAY→ Pathway (Reactome) |
| MP3 | D-G-B | Drug –ACTS_ON→ Gene –INVOLVED_IN→ BioProcess (GO BP) |
| MP4 | D-G-P-G | Drug → Gene → Pathway ← **progression gene** |
| MP5 | D-G-B-G | Drug → Gene → BioProcess ← progression gene |
| MP6 | D-G-P-G[traj] | target restricted to the 3,845 trajectory-cluster genes |
| MP7 | D-G-P-G[trans] | target restricted to the 2,568 stage-transition genes |

MP1–MP4 are the plan's minimum; MP6 and MP7 are the two extensions it asks for.
Only therapeutic `ACTS_ON` edges are walked (12,341), never the pharmacokinetic
ones.

## Counts

| metapath | terms | paths | drugs | genes | terms used |
|---|---|---:|---:|---:|---:|
| MP1 D-G-Di | all | **3,496,420** | 3,694 | 2,267 | 11,665 |
| MP1 D-G-Di | 5–200 | 703,492 | 3,632 | 2,033 | 5,401 |
| MP2 D-G-P | all | 67,862 | 3,661 | 2,025 | 1,799 |
| MP2 D-G-P | 5–200 | 61,159 | 3,598 | 1,958 | 1,424 |
| MP3 D-G-B | all | 280,129 | 3,686 | 2,232 | 7,303 |
| MP3 D-G-B | 5–200 | 204,847 | 3,670 | 2,192 | 4,450 |
| **MP4 D-G-P-G** | all | 1,283,702 | 3,644 | 5,225 | 1,937 |
| **MP4 D-G-P-G** | 5–200 | **1,052,539** | 3,596 | 4,773 | 1,401 |
| MP5 D-G-B-G | all | **14,563,118** | 3,681 | 7,073 | 9,353 |
| MP5 D-G-B-G | 5–200 | 3,577,655 | 3,670 | 6,589 | 4,367 |
| MP6 D-G-P-G[traj] | 5–200 | 646,223 | 3,590 | 3,642 | 1,349 |
| MP7 D-G-P-G[trans] | 5–200 | 452,421 | 3,562 | 3,081 | 1,271 |

## FINDING 1 — Reactome is 11× cleaner than GO, and the cap proves it

Same metapath shape, different bridge:

```
MP4 via Reactome    1,283,702 paths
MP5 via GO BP      14,563,118 paths      11.3x more
```

And they respond to the size cap completely differently:

| bridge | uncapped | capped | removed by the cap |
|---|---:|---:|---:|
| Reactome (MP4) | 1,283,702 | 1,052,539 | **18%** |
| GO BP (MP5) | 14,563,118 | 3,577,655 | **75%** |

Three quarters of GO's paths run through terms outside 5–200 genes. Reactome
loses less than a fifth. **GO's volume is annotation breadth, not biology** —
`signal transduction` alone carries 616 progression genes and 1,683 drugs,
manufacturing 1,036,728 pairs by itself. Reactome is the primary bridge for
everything downstream, exactly as Team 1's handover advised.

## FINDING 2 — the disease axis is a dictionary

MP1 uncapped: **3,496,420 paths reaching 3,694 drugs.** There are only 4,212
drugs in the graph with any therapeutic target, so `Drug → Gene → Disease`
reaches **88% of the entire drug vocabulary**.

Its hubs are generic EFO upper-level terms, not diseases. MP1 is reported
because the plan lists it, and it is not a route to candidates.

## FINDING 3 — raw path count and DWPC disagree

> Spearman rank correlation between raw path count and DWPC: **0.454**

Not 0.9-something. Ranking by raw path count and ranking by degree-weighted
path count give substantially different orderings, so the plan's instruction to
report a degree-normalised measure was not a formality — raw counts were
misleading here.

**DWPC** (Degree-Weighted Path Count, Himmelstein & Baranzini 2015) downweights
every path by the degree of each node along it, raised to −w, with w = 0.4:

```
DWPC(source, target) = Σ over paths of  Π degree(node_i)^−0.4
```

A path through a hub contributes almost nothing; a path through a specific term
contributes nearly 1.

## FINDING 4 — DWPC has its own bias, and it is not subtle

The top 200 pairs by DWPC come from only **38 distinct drugs**, and the leaders
are all drugs that hit **multi-subunit protein complexes**:

| Drug | Its top targets | Complex |
|---|---|---|
| TILUDRONIC ACID | ATP6V1A, ATP6V1C1, ATP6V1B2, ATP6V1F… | V-ATPase |
| CARFILZOMIB / BORTEZOMIB | PSMB7, PSMA4, PSMD13, PSMD1… | proteasome |
| EPOTHILONE D / PATUPILONE | TUBB6, TUBB2B, TUBB1, TUBA1A… | tubulin |

Every subunit of a complex carries the same pathway annotations, so the
subunits form a dense mesh of short paths and DWPC rewards it heavily. This is
a property of how complexes are annotated, **not evidence that bisphosphonates
or proteasome inhibitors treat liver fibrosis**.

So: the cap fixes the hub problem, DWPC fixes what the cap misses, and **DWPC
introduces a complex-membership bias that neither fixes**. A ranking built on
DWPC alone would put a bone drug and two chemotherapies at the top of a liver
paper. Any use of these scores in Task 6 needs a complex-aware control, or the
component weighted low enough that it cannot drive the ranking.

## Reproducibility

Query logic is in the script and the schema is in
`task5_metapath_definitions.csv`. Two implementation notes that matter for
anyone re-running it:

**MP1's uncapped counts are aggregated server-side.** `ASSOCIATED_WITH` is 1.8
million edges; transferring it to count it would move the whole table to
produce four numbers. Only the capped slice (200,943 edges) is pulled.

**The uncapped 4-node counts are computed arithmetically, not by building the
table.** One GO term joins 616 genes to 1,683 drugs; materialising the hub
terms would mean hundreds of millions of rows to then count. Per term it is
exact: L_t drug-gene pairs on the left × R_t targets on the right, minus paths
whose source gene *is* the target gene — those are a one-hop fact already in
Task 2, not a metapath.

## Convergence on the important transition — the plan's second ask

Task 5 also says: *"test whether candidate drugs converge on genes involved in
the transitions identified as molecularly important in Paper 1."* MP7 restricts
targets to the 2,568 stage-transition genes, but the convergence test itself was
missing until 13 October. `scripts/paper2_task5_transition_convergence.py`
closes it.

Paper 1 Task 3 identified **F3→F4** as the molecularly important transition:
under equal statistical power it produced a median of 311 changing genes
against 0–2 for the earlier ones. So: do drugs reach those genes more often
than their number predicts?

| transition | genes | drug-connected | % | enrichment | BH-q | converges |
|---|---:|---:|---:|---:|---:|---|
| F0→F1 | 495 | 78 | 15.8 | 0.95 | 0.852 | no |
| F1→F2 | 611 | 116 | 19.0 | 1.14 | 0.202 | no |
| F2→F3 | 618 | 104 | 16.8 | 1.01 | 0.852 | no |
| **F3→F4** | 2,121 | 341 | 16.1 | **0.97** | 0.852 | **no** |

**No convergence anywhere**, against an overall rate of 16.6%. Drugs are no more
likely to reach the genes that move at the cirrhotic transition than any other.

That is the expected answer and worth stating: drug annotation has no reason to
know *when* in a disease a gene moves. It also means the stage at which a target
acts cannot be inferred from how drugged it is — the two are independent, which
is precisely why Paper 1's trajectory evidence adds something the graph does
not already contain.

## Carried forward

1. **Use Reactome, not GO**, as the bridge. 11× fewer paths and 4× less
   hub-driven.
2. **Never use raw path counts.** They disagree with DWPC at ρ = 0.45.
3. **Do not let DWPC drive a ranking on its own** — it promotes complex-targeting
   drugs structurally.
4. **MP1 is not a candidate route.** It reaches 88% of all drugs.
