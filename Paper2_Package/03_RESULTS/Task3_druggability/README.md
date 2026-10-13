# Task 3 — Druggability across the progression groups

Plan: *"Compare fibrosis-only, inflammation-only, and shared genes. Also
examine positive and negative progression associations separately… Add an
enrichment/significance analysis comparing observed drug-connected genes with
an appropriate Paper 1-derived eligible-gene background. Report effect size and
BH-FDR… use a degree-aware permutation/null model."*

And: *"Do not collapse them into a single 'progression' category."*

Built by `scripts/paper2_task3_druggability.py` against **LiverDiseaseDB**,
database `neo4j`, 12 October 2026.

## Files

The per-gene table behind these numbers (all 14,794 eligible genes) is not
committed: it is 1.4 MB of intermediate working data that nothing downstream
reads. `scripts/paper2_task3_druggability.py` regenerates it.

| File | What it is |
|---|---|
| `task3_druggability_summary.csv` | the summary table the plan asks for |
| `task3_enrichment_tests.csv` | odds ratio, Fisher p, BH-q, degree-matched p |
| `task3_supporting.xlsx` | 1 sheet — `classic_druggable_sensitivity`, the confound check |
| `task3_druggability_by_group.png` | the bar plot |

## Two decisions behind the numbers

**Background = the 14,794 eligible genes**, the same background Paper 1's
enrichment used. All 6,222 progression genes sit inside it, so the comparison
set is the **8,572** eligible genes that are *not* progression-associated.
Using all ~20,000 human genes would inflate every result, because a gene absent
from these cohorts could never have been called progression-associated.

**Druggability counts therapeutic edges only.** Task 2 established that 44% of
drug–gene edges are pharmacokinetic — the gene metabolises or transports the
drug rather than being targeted by it. A percentage over all edges is partly
measuring liver drug metabolism. Both figures are in the summary table;
`percent` is therapeutic, `percent_ALL_edges` is everything.

## The summary table

**Two definitions are reported.** "Drug-connected" requires both a
non-pharmacokinetic action and a plausible therapeutic entity: 174 of the 958
drug-connected progression genes (18%) reach a mineral salt, cofactor or unnamed
accession and nothing else. The entity filter runs on **both arms**.

Background rate: **9.3% filtered** (was 11.2% unfiltered, 963 of 8,572).

| Group | Genes | Drug-connected | % | Unique drugs |
|---|---:|---:|---:|---:|
| fibrosis-only / positive | 1,040 | 133 | 12.8 | 549 |
| **fibrosis-only / negative** | 983 | 190 | **19.3** (filtered **14.3**) | 847 |
| inflammation-only / positive | 2,042 | 276 | 13.5 | 775 |
| inflammation-only / negative | 335 | 43 | 12.8 | 173 |
| shared / positive | 1,408 | 224 | 15.9 | 912 |
| **shared / negative** | 384 | 87 | **22.7** (filtered **17.2**) | 416 |
| shared / discordant | 30 | 5 | 16.7 | 8 |
| *background* | 8,572 | 963 | 11.2 (filtered **9.3**) | 2,047 |

By class, undivided: fibrosis-only **16.0%**, inflammation-only **13.4%**,
shared **17.3%**.

## Significance — and what survives a degree-aware null

A plain Fisher test is not enough here. Progression genes are on average better
studied than other genes, and better-studied genes have more of every kind of
edge, drug edges included. So each group is also compared against background
genes **matched on non-drug degree** (`ASSOCIATED_WITH`, `INTERACTS_WITH`,
`INVOLVED_IN`, `IN_PATHWAY`), 2,000 draws. Drug edges are excluded from the
matching so the null is not conditioned on the outcome being tested.

| Group | % | OR | BH-q | degree-matched null | p | survives |
|---|---:|---:|---|---:|---:|---|
| shared / negative | 22.7 | 2.32 | 2.0e-09 | 11.5 | 0.0000 | ✅ |
| fibrosis-only / negative | 19.3 | 1.89 | 2.1e-11 | 12.2 | 0.0000 | ✅ |
| shared / positive | 15.9 | 1.50 | 2.4e-06 | 13.2 | 0.0015 | ✅ |
| inflammation-only / positive | 13.5 | 1.24 | 6.5e-03 | 12.4 | 0.0560 | ✗ |
| fibrosis-only / positive | 12.8 | 1.16 | 1.8e-01 | 12.1 | 0.4950 | ✗ |
| inflammation-only / negative | 12.8 | 1.16 | 3.8e-01 | 10.8 | 0.2240 | ✗ |
| shared / discordant | 16.7 | 1.58 | 3.8e-01 | 13.0 | 0.5710 | ✗ |

Note how much work the degree-aware null does: `inflammation-only / positive`
has a BH-q of 0.0065 and looks significant, and then dies at p = 0.056 once
connectivity is matched. Reporting the Fisher result alone would have put a
false positive in the paper.

## FINDING — genes that go DOWN are more druggable than genes that go UP

The split is by **direction**, not by class:

```
decreasing:  shared 22.7%   fibrosis-only 19.3%
increasing:  shared 15.9%   fibrosis-only 12.8%
background                                11.2%
```

Both decreasing groups survive the degree-aware null at p < 0.001. The
inflammation-only class is the exception — it shows no direction effect
(13.5% up vs 12.8% down, neither surviving).

### Is it just pharmacology's favourite protein families?

The top drug-connected decreasing genes are **ADRA1A** (115 drugs), **HTR2A**
(106), **ESR1** (93), **AR** (73), **DRD1**, **MAOA/B** — adrenergic,
serotonergic, dopaminergic and nuclear receptors. These attract drug annotation
for reasons that have nothing to do with liver. The degree-aware null controls
for how *connected* a gene is, not for what *kind* of gene it is.

Tested directly by removing every classically druggable family (GPCRs, nuclear
receptors, ion channels, transporters, cytochromes, monoamine enzymes):

| Group | all genes | excluding classic families | background |
|---|---:|---:|---:|
| shared / negative | 22.7% | **20.2%** (OR 2.28, p = 3.4e-08) | 10.0% |
| fibrosis-only / negative | 19.3% | **16.5%** (OR 1.79, p = 1.1e-08) | 10.0% |

**The effect survives.** Those families are enriched among the decreasing
drug-connected genes (14.4% vs 6.4% of the increasing ones), but they account
for only a small part of the gap.

### What this does and does not mean

It means existing pharmacology has, by accident, accumulated more drugs against
the genes that **fall** as the liver scars than against the genes that rise.

It does **not** mean those drugs are useful here, for a reason worth stating
plainly: most drugs **inhibit** their target. A gene that is already falling is
one you would want to **restore**, not suppress further. High druggability of
the decreasing groups is therefore less actionable than the percentage makes it
look — and it is consistent with Task 2's finding that reversal-consistency
sits at chance level.

## Where this leaves the plan's question

The plan asks *"whether fibrosis-specific, inflammation-specific, or shared
progression programs differ in their representation among known drug targets."*

**They do — but the informative split is direction, not class.** All three
classes exceed the background, and the class-level spread (16.0 / 13.4 / 17.3)
is modest. The direction split is wider (22.7 vs 12.8 unfiltered) and is
where the surviving signal lives.

> Team 1's handover predicted a null result here, based on 18.4 / 18.6 / 16.4%
> measured on the pre-correction gene set over *all* drug edges. That prediction
> does not hold on the corrected 6,222-gene set with pharmacokinetic edges
> removed. The difference is the therapeutic/PK split, which Team 1 itself
> recommended making.

## Carried forward

1. **Report direction, not just class.** A class-only table hides the effect.
2. **Do not read druggability as actionability.** The decreasing groups are
   druggable in the sense that drugs exist against those proteins, not in the
   sense that those drugs would help.
3. **Keep the degree-aware null for Task 4.** It killed one apparently
   significant result here and will do the same for drug-coverage rankings.

## The entity filter, added after review

`percent` counts any therapeutic-action edge. `percent_usable` additionally
requires the drug to be a plausible therapeutic: not a mineral salt, nutrient,
cofactor, solvent or unnamed accession. Both columns are in
`task3_druggability_summary.csv`, and `task3_enrichment_tests.csv` carries the
Fisher test, BH-q and degree-matched null for **each** definition.

**What the filter costs.** The falling groups lose about 5 points each, which
is where the mineral salts sat. Three groups beat the degree-matched null on the
filtered definition; the class-level rollup `[class] inflammation-only` does not
(p = 0.081) and is not claimed.

**Why the filter is a heuristic and stays one.** Molecule type and clinical
phase were recovered from OptimusKG and do not discriminate: ZINC ACETATE is a
`Small molecule` at `max_phase 4.0`, because it genuinely is an approved small
molecule. The rule is name-based, it marks rather than deletes, and both numbers
are reported so a reader can disagree with it.
