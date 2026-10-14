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
| `task5_metapath_definitions.csv` | the 8 metapaths, their schema, and why each is run |
| `task5_metapath_counts.csv` | paths, drugs, genes, terms — each capped and uncapped |
| `task5_top_drug_gene_dwpc.csv` | top 200 drug / progression-gene pairs by DWPC |
| `task5_example_subgraphs.csv` | worked paths for quality checking |
| `task5_three_node_dwpc_top200.csv` | normalised support for MP1-MP3, top 200 per metapath |
| `task5_four_node_dwpc_top200.csv` | top 200 pairs by DWPC for every four-node metapath |
| `task5_mp7_reach_per_drug.csv` | per drug: MP7 reach and the share of it at F3->F4 — the input Test B runs on |
| `task5_transition_convergence.csv` | Test A, direct connectivity by transition |
| `task5_candidate_transition_convergence.csv` | Test B, candidate drugs by metapath |
| `task5_supporting.xlsx` | `hub_terms` · `count_vs_dwpc_top100` · `dwpc_formula_comparison` · `candidate_targets_by_transition` · `candidate_convergence_per_drug` |
| `task5_metapath_sizes.png` | path volume per metapath, capped vs uncapped |

## The eight metapaths

| id | metapath | schema |
|---|---|---|
| MP1 | D-G-Di | Drug –ACTS_ON→ Gene –ASSOCIATED_WITH→ Disease |
| MP2 | D-G-P | Drug –ACTS_ON→ Gene –IN_PATHWAY→ Pathway (Reactome) |
| MP3 | D-G-B | Drug –ACTS_ON→ Gene –INVOLVED_IN→ BioProcess (GO BP) |
| MP4 | D-G-P-G | Drug → Gene → Pathway ← **progression gene** |
| MP5 | D-G-B-G | Drug → Gene → BioProcess ← progression gene |
| MP6 | D-G-P-G[traj] | target restricted to the 3,845 trajectory-cluster genes |
| MP7 | D-G-P-G[trans] | target restricted to the 2,568 stage-transition genes |
| MP8 | D-G-P1-G | Drug → Gene → **Paper 1 significant fibrosis term** ← progression gene |

MP1–MP4 are the plan's minimum; MP6, MP7 and MP8 are the three extensions it
asks for. MP8 is the Paper 1 pathway/process refinement, kept as its own layer.
Only therapeutic `ACTS_ON` edges are walked (12,341), never the pharmacokinetic
ones.

## Counts

| metapath | terms | paths | drugs | genes | terms used | terms joining both sides | with no valid path |
|---|---|---:|---:|---:|---:|---:|---:|
| MP1 D-G-Di | all | **3,496,420** | 3,694 | 2,267 | 11,665 | — | — |
| MP1 D-G-Di | 5–200 | 703,492 | 3,632 | 2,033 | 5,401 | — | — |
| MP2 D-G-P | all | 67,862 | 3,661 | 2,025 | 1,799 | — | — |
| MP2 D-G-P | 5–200 | 61,159 | 3,598 | 1,958 | 1,424 | — | — |
| MP3 D-G-B | all | 280,129 | 3,686 | 2,232 | 7,303 | — | — |
| MP3 D-G-B | 5–200 | 204,847 | 3,670 | 2,192 | 4,450 | — | — |
| **MP4 D-G-P-G** | all | 1,283,702 | 3,642 | 5,050 | **1,573** | 1,937 | 364 |
| **MP4 D-G-P-G** | 5–200 | **1,052,539** | 3,596 | 4,773 | 1,401 | — | — |
| MP5 D-G-B-G | all | **14,563,118** | 3,681 | 6,997 | **5,788** | 9,353 | 3,565 |
| MP5 D-G-B-G | 5–200 | 3,577,655 | 3,670 | 6,589 | 4,367 | — | — |
| MP6 D-G-P-G[traj] | all | 796,200 | 3,636 | 3,803 | 1,487 | 1,777 | 290 |
| MP6 D-G-P-G[traj] | 5–200 | 646,223 | 3,590 | 3,642 | 1,349 | — | — |
| MP7 D-G-P-G[trans] | all | 559,349 | 3,609 | 3,199 | 1,377 | 1,591 | 214 |
| MP7 D-G-P-G[trans] | 5–200 | 452,421 | 3,562 | 3,081 | 1,271 | — | — |
| **MP8 D-G-P1-G** | all | 1,209,649 | 1,867 | 571 | 1,351 | 1,512 | 161 |
| **MP8 D-G-P1-G** | 5–200 | 1,184,125 | 1,865 | 566 | 797 | — | — |

### Membership counts only terms that carry a path

A term can join drugs on one side and progression genes on the other and still
support no valid path, because every path through it has the source gene equal
to the target gene — a one-hop fact already in Task 2, not a metapath. Those
terms are excluded from `unique_terms`, and the two right-hand columns show how
many were dropped: **364 of MP4's 1,937** and **3,565 of MP5's 9,353**. Counting
them as members would describe connectivity the metapath does not have.

## MP8 — the Paper 1 pathway/process layer, kept separate

The plan asks for the walk to be extended "using the major fibrosis-associated
pathways/processes identified in Paper 1". Paper 1 reports MSigDB term names and
the graph stores REACT:/GO_ accessions, so the two cannot be joined by
identifier. MP8 therefore takes **Paper 1's own significant terms as bridge
nodes**, with their own member genes as the edges, and reports them in a
separate row rather than mixed into the general graph layers.

1,512 fibrosis-associated significant terms (inflammation-only groups excluded),
covering 571 genes that carry a drug edge. It is a much narrower bridge than
Reactome — 1,867 drugs rather than 3,642 — and that is the point: it is the
connectivity Paper 1 found, not the connectivity the graph happens to have.

## FINDING 1 — Reactome carries a tenth of GO's paths, and responds differently to the cap

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

Three quarters of GO's paths run through terms outside 5–200 genes; Reactome
loses less than a fifth. `signal transduction` alone carries 616 progression
genes and 1,683 drugs, manufacturing 1,036,728 pairs by itself.

**What this does and does not say.** It says GO BP produces far more paths than
Reactome here, and that far more of them come from very large terms. It does
**not** establish that Reactome is "cleaner" or that GO connectivity "is not
biology" — GO BP has a larger vocabulary, a deeper hierarchy and broader
annotation coverage, and any of those alone would produce this pattern. The
measurable facts are volume and cap sensitivity; biological relevance is a
separate question this table cannot answer. Reactome is used as the primary
bridge downstream because it is the more selective one, which is a practical
choice, not a verdict on GO.

## FINDING 2 — the disease axis is a dictionary

MP1 uncapped: **3,496,420 paths reaching 3,694 drugs.** There are only 4,212
drugs in the graph with any therapeutic target, so `Drug → Gene → Disease`
reaches **88% of the entire drug vocabulary**.

Its hubs are generic EFO upper-level terms, not diseases. MP1 is reported
because the plan lists it, and it is not a route to candidates.

## FINDING 3 — raw path count and DWPC disagree

> Spearman rank correlation between raw path count and DWPC: **0.382**

Not 0.9-something. Ranking by raw path count and ranking by degree-weighted
path count give substantially different orderings, so the plan's instruction to
report a degree-normalised measure was not a formality — raw counts were
misleading here.

### DWPC as published

**DWPC** (Degree-Weighted Path Count, Himmelstein & Baranzini 2015) weights each
path by the product over every **edge** of the two metaedge-specific degrees at
its ends, raised to −w, with w = 0.4. A three-edge path therefore carries **six**
degree factors:

```
Drug -ACTS_ON->  Gene          deg_acts(drug)    · deg_acts(gene)
Gene -IN_PATHWAY-> Term        deg_path(gene)    · deg_path(term)
Term <-IN_PATHWAY- TargetGene  deg_path(term)    · deg_path(target)

w(path) = [ deg_acts(drug) · deg_acts(gene) · deg_path(gene)
            · deg_path(term)² · deg_path(target) ] ^ −0.4
```

The term's degree enters **twice**, because the term lies on two of the three
edges — which is precisely how DWPC penalises hub terms. `dwpc_4factor` carries
a simpler weighting that counts the term once and omits the source gene's
pathway degree; the two rank the same pairs at Spearman **0.897**, so the
distinction is not cosmetic. Only the published formula is used downstream.

### Normalised support for every tested path type

MP1–MP3 are two-edge metapaths and get their own DWPC on the same rule (four
degree factors), in `task5_three_node_dwpc_top200.csv`. Every four-node
metapath's top pairs are in `task5_four_node_dwpc_top200.csv`, and MP7 ships in
full as `task5_mp7_pairs.csv`, a 17 MB local intermediate that the convergence
addendum reduces to `task5_mp7_reach_per_drug.csv` — 1,876 rows, which is what
the permutation actually runs on and what ships.

## FINDING 4 — DWPC has its own bias, and it is not subtle

The leaders by DWPC are drugs that hit **multi-subunit protein complexes**:

| Drug | Its top targets | Complex |
|---|---|---|
| TILUDRONIC ACID | ATP6V1A, ATP6V1C1, ATP6V1B2, ATP6V0B… | V-ATPase |
| CARFILZOMIB / BORTEZOMIB | PSMB7, PSMA4, PSMD13, PSMD1… | proteasome |
| EPOTHILONE D / PATUPILONE | TUBB6, TUBB2B, TUBB1, TUBA1A… | tubulin |

Every subunit of a complex carries the same pathway annotations, so the subunits
form a dense mesh of short paths and DWPC rewards it heavily. This is a property
of how complexes are annotated, **not evidence that bisphosphonates or
proteasome inhibitors treat liver fibrosis**.

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
the transitions identified as molecularly important in Paper 1."*
`scripts/paper2_task5_transition_convergence.py` runs **two** tests, because
that sentence and the obvious first test are not the same question.

Paper 1 Task 3 identified **F3→F4** as the molecularly important transition:
under equal statistical power it produced a median of 311 changing genes
against 0–2 for the earlier ones.

### Test A — does drug annotation know when a gene moves?

Every fibrosis-associated gene against its largest transition, hypergeometric,
BH across the four:

| transition | genes | drug-connected | % | enrichment | BH-q | converges |
|---|---:|---:|---:|---:|---:|---|
| F0→F1 | 495 | 78 | 15.8 | 0.95 | 0.852 | no |
| F1→F2 | 611 | 116 | 19.0 | 1.14 | 0.202 | no |
| F2→F3 | 618 | 104 | 16.8 | 1.01 | 0.852 | no |
| **F3→F4** | 2,121 | 341 | 16.1 | **0.97** | 0.852 | **no** |

**No enrichment detected in direct connectivity**, against an overall rate of
16.6%. That is the expected answer: drug annotation has no reason to know *when*
in a disease a gene moves.

This is a test of **drug annotation against all fibrosis-associated genes**. It
is not a test of candidate drugs, it does not use the statistically supported
transition sets, and it walks direct edges rather than metapaths — so on its own
it cannot establish that timing and drug connectivity are independent. It says
only that this particular comparison found nothing.

### Test B — do the candidate drugs converge, through the metapath?

The plan's sentence names three things Test A does not have, so each is supplied
explicitly:

| what the plan names | what is used |
|---|---|
| candidate drugs | Task 8's 30 leading candidates, against the 1,846 other ranked drugs |
| transitions identified as molecularly important | Paper 1's **substantial** transition calls — 2,568 genes, 781 of them moving most at F3→F4 |
| converge on genes | MP7, `Drug → Gene → Pathway ← transition gene`, the metapath the plan names |
| a null | permuting which drugs carry the candidate label, so the null draws from the same reach distribution |

| measure | value |
|---|---:|
| candidate drugs | 30 |
| other ranked drugs | 1,846 |
| candidate mean share of reach at F3→F4 | **32.9%** |
| non-candidate mean share | 30.9% |
| difference | +2.0 points |
| permutation p (2,000 draws) | **0.380** |

**No convergence.** The candidates reach F3→F4 transition genes at essentially
the rate any ranked drug does. `task5_candidate_transition_convergence.csv`.

The two candidate targets land on either side of it — CACNA1C at F3→F4, PDGFRA
at F2→F3 — which is what a 2-point difference over 30 drugs looks like.

## Carried forward

1. **Use Reactome, not GO**, as the bridge — 11× fewer paths and far less
   cap-sensitive, which is a selectivity argument and not a claim about which
   vocabulary is biologically better.
2. **Never use raw path counts.** They disagree with DWPC at ρ = 0.38.
3. **Use the published six-factor DWPC.** The four-factor shortcut ranks pairs
   differently (ρ = 0.90) and under-penalises exactly the hub terms DWPC exists
   to penalise.
4. **Do not let DWPC drive a ranking on its own** — it promotes complex-targeting
   drugs structurally.
5. **MP1 is not a candidate route.** It reaches 88% of all drugs.
6. **Keep the Paper 1 layer separate.** MP8 is Paper 1's own enrichment used as
   a bridge; mixing it with general graph connectivity would make neither
   interpretable.
