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
| `task4_network_edges.csv` | 2,033 | — |
| `task4_supporting.xlsx` | 3 sheets | `coverage_by_group` · `flagged_non_therapeutic` · `specificity_trap` |
| `task4_coverage_vs_coherence.png` | — | why coverage is not quality |
| `task4_network.png` | — | coherent drugs and their targets, grouped by fibrosis process |

## Headline numbers

| | |
|---|---:|
| Drugs reaching ≥1 progression gene | **2,404** |
| …reaching ≥3 | 429 |
| …named, reaching ≥5 | 147 |
| Flagged as likely non-therapeutic | **726** |
| Network shipped | 376 drugs × 610 genes, 2,033 edges |

## FINDING — coverage and coherence pull in opposite directions

The plan asks whether a drug covers *a coherent programme* or *merely many
unrelated genes*. Two measures per drug answer it:

- **`dominant_class_fraction`** — largest share of a drug's progression targets
  falling in one class × direction group
- **`dominant_cluster_fraction`** — the same across F0–F4 trajectory clusters

Correlation between raw coverage and coherence: **−0.124**.

**Negative.** The drugs reaching the most progression genes cover the *least*
coherent programmes. Ranking by coverage actively selects promiscuity. The
plan's warning is not a caution to note and move past — it is the result.

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

## Filtering the drug vocabulary — what the graph cannot do

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
| **`likely_non_therapeutic`** | **726** | any of the above |

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
networkx. Restricted to named drugs reaching ≥3 progression genes: **376 drugs,
610 genes, 2,033 edges**.

Annotated with Paper 1 evidence as the plan requires — all four annotations it
names. Gene nodes carry `progression_class` (fibrosis-only / shared status),
`group` (positive / negative direction), `cluster` and `cluster_pattern`
(F0–F4 trajectory), and **`major_pathway`** (the major fibrosis-associated
process), plus `fibrosis_rho`, `inflammation_rho`, `largest_transition` and
`tier`; drug nodes carry coverage, total targets, specificity bound and
coherence; edges carry `Action_Mechanism`, `action_class` and
`mechanism_consistency`. So the network can be laid out by progression biology
rather than by database connectivity alone.

## Two gaps found on a re-read of the plan, and closed

Checked column by column against the plan on 12 October:

- **Per-cluster coverage was missing.** The plan asks for coverage "calculated
  separately for … important F0–F4 trajectory clusters", and only a single
  `dominant_cluster_fraction` existed. `n_cluster_C1` … `n_cluster_C5` are now
  on every drug.
- **The network lacked the pathway annotation.** The plan names four
  annotations; three were present and "major fibrosis-associated
  pathway/process" was not. Paper 1's gene table carries only a boolean per
  database, so the name is taken from Paper 1's own enrichment
  (`task4_top_pathways_per_group.csv`): for each gene, the most significant
  enriched term it is listed under. **341 of the 610 network genes** now carry
  one; the rest appear in no significant enriched term, which is a real absence
  rather than a lookup failure.

## Carried forward

1. **Do not rank candidates by coverage.** It is negatively correlated with
   coherence. If Task 6 uses a knowledge-graph component K, raw degree is the
   wrong quantity.
2. **Rank specificity by the Wilson bound, not the raw fraction**, or
   single-target drugs win.
3. **726 of 2,404 drugs should not be in a candidate list at all**, and 648 of
   those are unnamed entries that cannot be assessed without ChEMBL metadata.
4. **Coherence is the more useful lens**, and it surfaces TRAPIDIL, MARIMASTAT
   and GLYCYRRHIZIN — none of which the coverage ranking finds.
