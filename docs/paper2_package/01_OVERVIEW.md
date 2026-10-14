# 1. Overview

Paper 2 takes the progression-associated genes Paper 1 produced and asks which
medicines that already exist act on them. It is a drug-repurposing analysis
conducted entirely inside the project's knowledge graph.

**Status:** all eight planned tasks complete, 13 October 2026.

## What it rests on

Paper 1's final combined analysis of 10 October 2026. Eight human liver
transcriptome studies, 1,085 samples from 1,027 patients. The fibrosis axis
uses **610 independent staged patients**; the disease-group axis uses **216
patients from three studies** — a much smaller base, and relevant whenever an
inflammation result is quoted.

| Gene set | Count |
|---|---:|
| fibrosis-only | 2,023 |
| inflammation-only | 2,377 |
| shared (both ladders) | 1,822 |
| **union — the Paper 2 starting set** | **6,222** |
| fibrosis-associated (fibrosis-only + shared) | 3,845 |
| Tier 1, Paper 1's high-confidence set | 447 |
| Paper 1's balanced shortlist | 23 |

The Paper 2 plan was written against 4,692 genes. That figure predates the
biopsy-pairing correction of 9–10 October; the corrected union is 6,222, and
the researcher confirmed its use on 12 October.

## The eight tasks

| # | Task | Principal result |
|---|---|---|
| 1 | Master gene table | 6,222 genes, nothing filtered, verified gene by gene against the live graph |
| 2 | Drug–gene extraction | 8,948 links · 1,072 genes · 3,027 drugs; only 11.2% carry a usable direction |
| 3 | Druggability by group | All three classes exceed an eligible-gene background; three of seven direction groups also exceed a degree-matched null. Falling vs rising is 1.3× at most and fails BH correction (q = 0.082), so it is reported, not claimed |
| 4 | Drug coverage | Among drugs with ≥5 progression targets, coverage and class × direction coherence correlate **−0.328**; trajectory-cluster coherence shows no such relationship (−0.102, p = 0.21) |
| 5 | MetaPaths | Reactome carries a tenth of GO's paths and is far less cap-sensitive; raw path counts disagree with DWPC at ρ = 0.38 |
| 6 | Target scoring | Five components, one constant within class and so carrying no ranking information; scores tie heavily, so membership is reported as a band and the stable core as a threshold |
| 7 | Action/direction | Mechanism consistency at chance overall, and **no subgroup** beats a null that preserves progression direction |
| 8 | Final ranking | 30 candidates collapsing onto **two genes** |

## The endpoint this paper delivers, and the one the plan opened with

The Paper 2 plan asked for **transcriptomic drug-reversal evidence** before the
final ranking: signatures showing a drug moving the disease genes the other way.
That layer is **not** in this package. It was scoped out on the researcher's
"repurposing not reversal" decision, and the evidence summary records it as
`L7 transcriptomic reversal — out of scope` on all 30 candidates rather than as
a layer that was attempted and found empty.

So the endpoint delivered is narrower than the one the plan opened with, and it
should be described as what it is: **knowledge-graph-supported repurposing
hypotheses**, ranked on association, trajectory, pathway context and existing
drug–target annotation. Nothing here shows a drug reversing a disease signature.

**Independent validation has also not been performed.** Paper 1 and OptimusKG
are reused across every task, so agreement between tasks is internal
consistency, not confirmation. Where Task 7 and Paper 1 agree on the nintedanib
–PDGFRA relationship, they are reading the same OptimusKG edges. Adding a
genuinely independent layer needs data outside this graph; until then its
absence is limitation 1 and the largest one.

## The headline result

The leading candidates reach exactly two targets:

- **PDGFRA** — 7 kinase inhibitors including **nintedanib**, already approved
  for *lung* fibrosis. A Paper 1 9/9 gene, rho +0.42 in 5 of 5 studies, LOSO
  5/5, flagged by Task 7.
- **CACNA1C** — 23 calcium-channel blockers. **Also** a 9/9 gene, also 1.00 on
  all five Task 6 components, and marginally stronger on the progression
  statistics (rho +0.447, q 5.9e-21).

**The two are equivalent on this project's evidence.** Six genes score 9/9
(CACNA1C, MYC, PDGFRA, PLK3, TAX1BP3, TPM4), so a perfect Paper 1 score does not
separate them. PDGFRA is preferred because nintedanib already treats fibrosis in
another organ — an external fact, not a finding of this paper.

So the candidate list is, in substance, *"inhibit PDGFRA or block CACNA1C"* —
less diverse than thirty names suggests, and stated as such.

## What this paper does not claim

It does not demonstrate drug efficacy. It does not establish that inhibiting
either gene helps the liver — the graph records the direction a gene moves and
when, not whether reversing it is beneficial. No candidate has been tested in a
cell, let alone a patient.

Per the plan: **therapeutic hypotheses and prioritized candidate relationships,
not proven anti-fibrotic treatments.**

## Reading order

`02_METHODS` → `03_STATISTICS` → `04_LIMITATIONS` before drafting anything.
`05_HOW_TO_VERIFY` says how to re-run every number. Actual output files take
priority over any dated conversation.
