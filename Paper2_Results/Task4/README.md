# Task 4 — Drugs connected to multiple progression genes

Plan: *"For each drug calculate the number of progression-associated genes to
which it is connected… calculate coverage separately for fibrosis-only
positive, fibrosis-only negative, shared positive, shared negative, and
important F0–F4 trajectory clusters. This will reveal whether a drug covers a
coherent progression program or merely many unrelated genes."*

And twice over: ***"This is candidate generation only. Do not describe a
high-degree drug as the best therapeutic candidate."***

Built by `scripts/paper2_task4_drug_coverage.py`, therapeutic edges only.

## Files

| File | Rows | What it is |
|---|---:|---|
| `task4_drug_coverage.csv` | 2,404 | every drug reaching ≥1 progression gene, with per-group **and per-cluster** coverage |
| `task4_top_drugs_raw_coverage.csv` | 50 | top 50 by raw coverage, as the plan asks |
| **`task4_top_drugs_by_coherence.csv`** | 50 | **ranked by coherence instead of count — read this one first** |
| `task4_network_nodes.csv` | 986 | bipartite network, annotated with Paper 1 evidence |
| `task4_network_edges.csv` | 2,085 | — |
| `task4_supporting.xlsx` | 3 sheets | `coverage_by_group` · `flagged_non_therapeutic` · `specificity_trap` |
| `task4_coverage_vs_coherence.png` | — | why coverage is not quality |
| `task4_network.png` | — | coherent drugs and their targets, grouped by fibrosis process |

## Headline numbers

| | |
|---|---:|
| Drugs reaching ≥1 progression gene | **2,404** |
| …reaching ≥3 | 429 |
| …named, reaching ≥5 | 147 |
| Flagged as likely non-therapeutic | **696** |
| Network shipped | 387 drugs × 611 genes, 2,085 edges |

## FINDING — coverage and coherence pull in opposite directions

The plan asks whether a drug covers *a coherent programme* or *merely many
unrelated genes*. Two measures per drug answer it:

- **`dominant_class_fraction`** — largest share of a drug's progression targets
  falling in one class × direction group
- **`dominant_cluster_fraction`** — the same across F0–F4 trajectory clusters

Correlation between raw coverage and coherence, measured by the task script
rather than carried by hand, on drugs reaching **≥ 5** progression genes:

| coherence measure | drug set | n | Spearman ρ | p |
|---|---|---:|---:|---:|
| **class × direction** | non-therapeutic entities removed | 154 | **−0.328** | 3.3e-05 |
| class × direction | named drugs only | 173 | −0.320 | 1.8e-05 |
| trajectory cluster | non-therapeutic entities removed | 154 | −0.102 | 0.207 |
| trajectory cluster | named drugs only | 173 | −0.059 | 0.438 |

**The relationship holds for class coherence and not for cluster coherence.**
Drugs reaching the most progression genes spread those targets across more
class × direction groups, so ranking by coverage selects against that particular
kind of focus. The same drugs are **not** measurably less focused by F0–F4
trajectory cluster — that correlation is weak and not significant.

So the supported claim is narrow: **among drugs with at least five progression
targets, wider coverage goes with lower class × direction coherence.** It is not
a statement about coherence in general, it does not establish that
wide-coverage drugs hit biologically unrelated programmes, and it says nothing
about drugs with fewer than five targets, who are excluded precisely because
their coherence is undefined or trivially perfect.

### What the coherence score is, and is not

`dominant_class_fraction` is the largest share of a drug's progression targets
falling in one class × direction group. It is **descriptive**: its value depends
on how many targets the drug has and on how common those groups are among
progression genes, not only on whether the drug is focused.

A single-target drug scores 1.000 automatically. A two-target drug scores at
least 0.5. And the largest group is large to begin with — the class × direction
groups are not equal in size — so a drug picking targets at random already
scores well above chance. **Nothing here is compared against a null matched for
target count and group prevalence**, so a high coherence score is a feature of
the drug's target list, not evidence that the drug targets a programme more
coherently than expected. Treating it as enrichment would need that matched
reference first.

## The top-50 lists, and why there are two

Top by raw coverage, as asked:

| Drug | Genes | All targets | Coherence |
|---|---:|---:|---:|
| FOSTAMATINIB | 131 | 302 | 0.34 |
| CHEMBL1201279 | 50 | 125 | 0.46 |
| ZINC ACETATE | 49 | 124 | 0.47 |
| ZINC CHLORIDE | 41 | 97 | 0.44 |
| GLUTAMIC ACID | 33 | 61 | 0.30 |

One promiscuous kinase inhibitor, two zinc salts, an amino acid, and an unnamed
ChEMBL entry. Filtering the flagged entities out of that list leaves FOSTAMATINIB, then
PHENETHYLISOTHIOCYANATE, CANNABIDIOL, NABIXIMOLS, ASPIRIN, TILUDRONIC ACID,
SPIRONOLACTONE, MINOCYCLINE, ZONISAMIDE, CAFFEINE — filter
`task4_drug_coverage.csv` on `likely_non_therapeutic` to reproduce it.

Still not a candidate list. It is what "most targets" looks like.

### Reading the coherent end instead

Named drugs reaching ≥5 genes, ranked by coherence:

| Drug | Genes | Coherence | Why it is interesting |
|---|---:|---:|---|
| FLUOCINOLONE ACETONIDE | 6 | 0.83 | corticosteroid |
| **GLYCYRRHIZIN** | 6 | 0.67 | licorice derivative, used for chronic hepatitis in Japan |
| **TRAPIDIL** | 8 | 0.63 | **PDGF antagonist** — the PDGFRA axis |
| **MARIMASTAT** | 10 | 0.60 | **MMP inhibitor** — matrix remodelling, the core of fibrosis |
| AMLODIPINE | 5 | 0.60 | calcium channel blocker |

Three of the top five have a defensible route to liver fibrosis biology, where
the raw-coverage list has none. The full ranking is `task4_top_drugs_by_coherence.csv`. **This is a better
place to start than the coverage ranking** — and it is still candidate generation, not evidence.

## The specificity measure needed fixing before it could be used

The plan asks for *progression-target fraction = progression targets / all
known targets*, "as a supporting feature and not as a standalone therapeutic
score". That caveat is doing heavy lifting:

> **1,872 of 4,212 drugs with any target have exactly one.**

So every single-target drug whose one target is a progression gene scores a
perfect **1.000**, outranking a characterised inhibitor with 6 of 10 targets in
the set. Ranking on the raw fraction ranks ignorance.

Both are reported. `progression_target_fraction` is the plan's measure;
`progression_fraction_lower95` is the Wilson lower bound, which prices in the
denominator — 1/1 scores 0.21, 6/10 scores 0.31. **Use the bound to rank; keep
the fraction because the plan asks for it.** The `specificity_trap` sheet lists
the drugs the raw fraction would promote.

**What the Wilson bound is doing here, and what it is not.** Wilson assumes the
numerator is a binomial draw from the denominator. A drug's recorded target list
is not a random sample of its true pharmacological repertoire: it is whatever
has been assayed and curated, and both are biased towards well-studied targets.
So the number is **not** a validated confidence bound on true specificity. It is
used for one narrow purpose — penalising a small denominator — and it does that
correctly because it is monotone in the denominator. Where it enters a ranking,
it enters as a denominator-sensitive ordering device, not as a probability
statement about the drug.

## Molecule type and clinical phase — recovered, and a negative result

Team 1's instruction was to *filter on molecule type and clinical phase*. Those
fields were recovered from OptimusKG's own drug nodes. **They do not work for
this.**

| | |
|---|---|
| All 70 name-flagged entries | `molecule_type = "Small molecule"` |
| ZINC ACETATE, ZINC CHLORIDE | `max_phase = 4.0`, `is_approved = True` |

They genuinely *are* approved small molecules, so the classification has
nothing to separate. A filter built on it flags **one** drug where the name
heuristic flags 70.

What does discriminate, for inorganics, is chemistry: a formula with no carbon
is not an organic therapeutic. `flag_inorganic` catches ZnCl₂, MgSO₄, Na₂SO₄,
AlCl₃, CaCl₂ and NO — **certain where it fires, and it caught nothing the name
heuristic had missed.** It cannot reach the organic nutrients (ATP, FAD,
glutamic acid all contain carbon), so the crude name rule stays beside it.

**SMILES are available for all 2,404 drugs in this table** — recovered from the
same source.

ChEMBL was then queried for the drugs OptimusKG leaves short, and **added
nothing for this project**: 0 structures and 16 names across our 12,025 drugs.
Of the 2,989 drugs with no OptimusKG structure, ChEMBL holds a record for 2,654
and has no structure for any of them — they are biologics, antibodies and
mixtures that no SMILES can represent. A 60-drug pilot had suggested ChEMBL
would fill 57 of 59; that pilot sampled all 18,640 OptimusKG records rather
than the 12,025 this project uses, and overstated the benefit. Earlier statements in this repository that the project has no
chemical structures were wrong; `canonical_smiles` was read at build time and
discarded.

## The original note, kept for the record

Team 1's handover says to filter on molecule type and clinical phase before any
coverage ranking. **The graph cannot do that.** Drug nodes carry exactly two
properties, `node_id` and `name` — no modality, no phase, no molecule type. So
the filter is a heuristic, and it **flags rather than deletes**: every drug
stays in the table with the reason visible.

| Flag | Drugs | How |
|---|---:|---|
| `flag_name` | 70 | salts, elements, vitamins, cofactors, simple metabolites |
| `flag_unnamed` | 648 | the name is only a ChEMBL accession — unjudgeable |
| `flag_duplicate` | 27 | ≥95% of targets contained in a flagged drug's target set |
| **`likely_non_therapeutic`** | **696** | any of the above |

The duplicate rule earns its place: `CHEMBL1201279` shares **all 126** of its
targets with ZINC ACETATE, so it is the same entity under another accession.
No name rule would have caught it, and it sat at number two on the raw list.

**648 unnamed entries is the larger problem** and nothing here solves it --
though Task 8 measures how far it reaches: none of them enters band 1 or the
leading candidates, and the best sits at band 3.
Doing this properly needs ChEMBL molecule metadata, which this project does not
have. **Settled 13 October 2026:** the mentor's instruction to focus only on
the knowledge graph puts external resources out of scope, so these 648 stay
flagged and unresolved. Any candidate list must carry that caveat.

## The bipartite network

`task4_network_nodes.csv` / `task4_network_edges.csv`, for Cytoscape, Gephi or
networkx. Restricted to named drugs reaching ≥3 progression genes: **387 drugs,
611 genes, 2,085 edges**.

Annotated with Paper 1 evidence as the plan requires — all four annotations it
names. Gene nodes carry `progression_class` (fibrosis-only / shared status),
`group` (positive / negative direction), `cluster` and `cluster_pattern`
(F0–F4 trajectory), and **`major_pathway`** (the major fibrosis-associated
process), plus `fibrosis_rho`, `inflammation_rho`, `largest_transition` and
`tier`; drug nodes carry coverage, total targets, specificity bound and
coherence; edges carry `Action_Mechanism`, `action_class` and
`mechanism_consistency`. So the network can be laid out by progression biology
rather than by database connectivity alone.

## Two columns the plan asks for that are easy to miss

- **Per-cluster coverage.** The plan asks for coverage "calculated separately
  for … important F0–F4 trajectory clusters", which a single
  `dominant_cluster_fraction` does not answer. `n_cluster_C1` … `n_cluster_C5`
  are on every drug.
- **The network carries the pathway annotation.** The plan names four
  annotations, and "major fibrosis-associated pathway/process" is one of them.
  Paper 1's gene table carries only a boolean per database, so the name comes
  from Paper 1's **complete** significant-enrichment results
  (`task4_all_significant.csv`, 3,945 terms covering 3,929 symbols) — not its
  per-group top table, which keeps only 456 leading terms and would leave a gene
  blank whenever its enrichment sits below the top of its group.

  **503 of the 611 network genes** carry a term; 108 appear in no significant
  enriched term at all. `pathway_annotation` states which of the two a blank
  means, because absence of annotation and absence of enrichment are different
  facts. The representative term is the most significant one listing that gene —
  lowest q, ties broken by fold enrichment and then term label, so it does not
  depend on row order — and `major_pathway_q` carries its q-value.

## Carried forward

1. **Do not rank candidates by coverage.** It is negatively correlated with
   coherence. If Task 6 uses a knowledge-graph component K, raw degree is the
   wrong quantity.
2. **Rank specificity by the Wilson bound, not the raw fraction**, or
   single-target drugs win.
3. **696 of 2,404 drugs should not be in a candidate list at all**, most of
   them unnamed entries that cannot be assessed without ChEMBL metadata.
4. **Coherence is the more useful lens**, and it surfaces TRAPIDIL, MARIMASTAT
   and GLYCYRRHIZIN — none of which the coverage ranking finds. It remains a
   descriptive feature, not an enrichment claim, until it is compared against a
   null matched for target count and group prevalence.
5. **Quote the coherence definition with the correlation.** Class × direction
   coherence falls with coverage; trajectory-cluster coherence does not.
