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
| 3 | Druggability by group | Genes that **fall** with disease are ~2× more drug-connected; survives a degree-matched null |
| 4 | Drug coverage | Coverage and coherence correlate **−0.268**: counting targets selects promiscuity |
| 5 | MetaPaths | Reactome 11× cleaner than GO; raw path counts disagree with DWPC at ρ = 0.45 |
| 6 | Target scoring | Five components, one of which contributes nothing; exact top-50 not defensible |
| 7 | Action/direction | Mechanism consistency at chance overall; one subgroup beats its null |
| 8 | Final ranking | 30 candidates collapsing onto **two genes** |

## The headline result

The leading candidates reach exactly two targets:

- **PDGFRA** — 8 kinase inhibitors including **nintedanib**, already approved
  for *lung* fibrosis. Paper 1's only 9/9 gene, rho +0.42 in 5 of 5 studies,
  LOSO 5/5, independently flagged by Task 7. The convergence of three routes on
  one gene is the most defensible finding in either paper.
- **CACNA1C** — 22 calcium-channel blockers. Reaches the same band on the same
  measures, with a thinner biological story behind it.

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
