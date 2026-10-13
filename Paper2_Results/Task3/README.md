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

| File | What it is |
|---|---|
| `task3_druggability_summary.csv` | the summary table the plan asks for |
| `task3_enrichment_tests.csv` | odds ratio, Fisher p, BH-q, degree-matched null |
| `task3_falling_vs_rising.csv` | falling vs rising tested head to head |
| `task3_gene_degrees.csv` | every eligible gene with its non-drug degree, degree bin and drug counts |
| `task3_supporting.xlsx` | 2 sheets — `classic_druggable_sensitivity`, `classic_family_share` |
| `task3_druggability_by_group.png` | the bar plot |

`task3_gene_degrees.csv` is 1.4 MB and is committed on purpose: the degree bins
*are* the null model, so without it a reader can re-check the Fisher tests and
nothing else. With it, the degree-matched analysis can be reproduced from the
delivered files alone.

## Two decisions behind the numbers

**Background = the 14,794 eligible genes**, the same background Paper 1's
enrichment used. All 6,222 progression genes sit inside it, so the comparison
set is the **8,572** eligible genes that are *not* progression-associated.
Using all ~20,000 human genes would inflate every result, because a gene absent
from these cohorts could never have been called progression-associated.

**Two definitions of "has a drug", both reported.**

| Column | What it requires |
|---|---|
| `percent_ALL_edges` | any `ACTS_ON` edge at all |
| `percent` | the action is therapeutic, i.e. **not** `ENZYME`, `TRANSPORTER`, `CARRIER` or `SUBSTRATE` |
| `percent_usable` | the above **and** the drug passes the name-based entity filter |

Task 2 established that 44% of drug–gene edges are pharmacokinetic — the gene
metabolises or transports the drug rather than being targeted by it — so a
percentage over all edges is partly measuring liver drug metabolism.

Neither definition establishes that a gene is a *good* target. `percent` says a
non-metabolic drug edge exists; `percent_usable` adds that the drug's name does
not look like a mineral salt, nutrient, cofactor, solvent or bare accession.
That is a heuristic about names, not a judgement about therapeutic suitability.

172 of the 958 drug-connected progression genes (18%) reach a flagged entity and
nothing else, so the distinction changes the table rather than rounding it. The
filter runs on **both arms** — a background cleaned on one side only would
manufacture an effect rather than measure one.

## The summary table

| Group | Genes | Drug-connected | % | Filtered % | Unique drugs | Filtered |
|---|---:|---:|---:|---:|---:|---:|
| fibrosis-only / positive | 1,040 | 133 | 12.8 | 11.1 | 549 | 410 |
| **fibrosis-only / negative** | 983 | 190 | **19.3** | **14.3** | 847 | 638 |
| inflammation-only / positive | 2,042 | 276 | 13.5 | 11.0 | 775 | 555 |
| inflammation-only / negative | 335 | 43 | 12.8 | 11.3 | 173 | 150 |
| shared / positive | 1,408 | 224 | 15.9 | 14.3 | 912 | 737 |
| **shared / negative** | 384 | 87 | **22.7** | **16.9** | 416 | 340 |
| shared / discordant | 30 | 5 | 16.7 | 6.7 | 8 | 2 |
| *background* | 8,572 | 963 | 11.2 | **9.4** | 2,047 | 1,520 |

By class, undivided: fibrosis-only **16.0%**, inflammation-only **13.4%**,
shared **17.3%** (filtered: 12.7 / 11.0 / 14.7).

## Significance against the background

A plain Fisher test is not enough here. Progression genes are on average better
studied than other genes, and better-studied genes have more of every kind of
edge, drug edges included. So each group is also compared against background
genes **matched on non-drug degree** (`ASSOCIATED_WITH`, `INTERACTS_WITH`,
`INVOLVED_IN`, `IN_PATHWAY`), 2,000 draws. Drug edges are excluded from the
matching so the null is not conditioned on the outcome being tested.

On the primary, entity-filtered definition:

| Group | filtered % | OR | BH-q | degree-matched null | p | exceeds null |
|---|---:|---:|---|---:|---:|---|
| shared / negative | 16.9 | 1.96 | 2.2e-05 | 9.6 | 0.0005 | ✅ |
| fibrosis-only / negative | 14.3 | 1.61 | 1.2e-05 | 10.2 | 0.0005 | ✅ |
| shared / positive | 14.3 | 1.60 | 4.1e-07 | 11.2 | 0.0005 | ✅ |
| inflammation-only / positive | 11.0 | 1.18 | 5.4e-02 | 10.4 | 0.3478 | ✗ |
| inflammation-only / negative | 11.3 | 1.23 | 2.8e-01 | 9.0 | 0.1124 | ✗ |
| fibrosis-only / positive | 11.1 | 1.20 | 1.2e-01 | 10.2 | 0.3223 | ✗ |
| shared / discordant | 6.7 | 0.69 | 1.0e+00 | 11.5 | 0.5647 | ✗ |

The unfiltered columns are in `task3_enrichment_tests.csv` beside these.

### How the degree-matched null is computed, exactly

Every gene is placed in one of 20 bins by its rank on non-drug degree. For each
group gene, a replacement is drawn from that gene's own bin, so the draw carries
the group's connectivity profile and differs from it only in not being
progression-associated. 2,000 draws.

Two things are made explicit rather than left to the code:

- **The requested count per bin is always honoured.** A bin can in principle
  hold fewer background genes than a group needs — progression genes concentrate
  at the well-connected end, which is the thinnest part of the background — and
  taking only what the bin holds would re-weight the null towards the bins that
  happen to be full, at exactly the bins where matching matters. Where a bin
  cannot supply the count, the draw is taken with replacement, and the amount of
  resampling is reported in `matched_bins_short` and
  `matched_percent_resampled`. **On this data both are zero for every group**:
  no bin ever ran short, so no result here depends on that behaviour.
- **p is a finite-simulation estimate, not zero.** It is `(r + 1) / (n + 1)`
  over 2,000 draws, so the smallest value it can take is **0.0005**, and that is
  what the strongest groups report. A simulation cannot measure a probability
  smaller than it has draws, and `p = 0` would claim a precision the method does
  not have.

## FINDING — direction matters more than class, but the direction effect does not survive the filter

Three classes exceed the background and the class-level spread is modest
(16.0 / 13.4 / 17.3 unfiltered; 12.7 / 11.0 / 14.7 filtered). The wider contrast
is by **direction**:

```
unfiltered   decreasing:  shared 22.7%   fibrosis-only 19.3%
             increasing:  shared 15.9%   fibrosis-only 12.8%
             background                                11.2%

filtered     decreasing:  shared 16.9%   fibrosis-only 14.3%
             increasing:  shared 14.3%   fibrosis-only 11.1%
             background                                 9.4%
```

### Beating a shared background is not the same as differing from each other

Each group beating a common background does not establish that falling genes
differ from rising ones. `task3_falling_vs_rising.csv` runs the comparison the
sentence actually makes — falling against rising, head to head, within each
class, Fisher, BH across the three classes:

| Class | definition | rising % | falling % | ratio | p | BH-q | passes |
|---|---|---:|---:|---:|---:|---:|---|
| fibrosis-only | therapeutic action | 12.8 | 19.3 | 1.51 | 6.0e-05 | 1.8e-04 | ✅ |
| shared | therapeutic action | 15.9 | 22.7 | 1.42 | 3.0e-03 | 4.4e-03 | ✅ |
| inflammation-only | therapeutic action | 13.5 | 12.8 | 0.95 | 0.796 | 0.796 | ✗ |
| fibrosis-only | **entity-filtered** | 11.1 | 14.3 | 1.30 | 0.027 | **0.082** | ✗ |
| shared | **entity-filtered** | 14.3 | 16.9 | 1.19 | 0.196 | 0.294 | ✗ |
| inflammation-only | **entity-filtered** | 11.0 | 11.3 | 1.03 | 0.851 | 0.851 | ✗ |

**On the primary definition, no class passes.** The direction gap is real and
visible on the broader, unfiltered definition, and it does not survive once
mineral salts, cofactors and unnamed accessions are removed from both arms.

So the claim this task supports is the narrow one: **all three classes are
drug-connected above an eligible-gene background, and three of the seven
direction groups stay above a degree-matched null.** The claim it does *not*
support is that decreasing genes are more druggable than increasing ones. That
comparison is reported above and left unclaimed.

### Is it just pharmacology's favourite protein families?

The top drug-connected decreasing genes are **ADRA1A** (115 drugs), **HTR2A**
(106), **ESR1** (93), **AR** (73), **CA2** (65), **DRD1** (55) — adrenergic,
serotonergic, dopaminergic and nuclear receptors, plus a carbonic anhydrase.
These attract drug annotation for reasons that have nothing to do with liver.
The degree-matched null controls for how *connected* a gene is, not for what
*kind* of gene it is.

`classic_family_share` measures the overlap directly. Among drug-connected
genes, classically druggable families are **20.3%** of the decreasing set
against **10.7%** of the increasing set — and the gap widens under the entity
filter, to **25.0%** against **11.3%**, because the filter removes mineral salts
rather than receptors.

Removing every classic family (GPCRs, nuclear receptors, ion channels,
transporters, cytochromes, monoamine enzymes) and re-testing against a
background cleaned the same way:

| Group | filtered % | excluding classic families | background | OR | p |
|---|---:|---:|---:|---:|---:|
| shared / negative | 16.9 | **13.7** | 8.2 | 1.79 | 6.6e-04 |
| shared / positive | 14.3 | **13.2** | 8.2 | 1.71 | 1.1e-08 |
| fibrosis-only / negative | 14.3 | **11.6** | 8.2 | 1.47 | 8.7e-04 |
| fibrosis-only / positive | 11.1 | **9.8** | 8.2 | 1.22 | 8.8e-02 |

Enrichment above background survives for three of those four. The *direction*
contrast does not: with the classic families gone and the entity filter applied,
shared / negative (13.7%) and shared / positive (13.2%) are the same number.

### What this does and does not mean

It means that for the genes that change with liver scarring, drugs annotated
against those proteins exist more often than for comparable genes that do not
change — and that a sizeable part of that is which protein families pharmacology
has historically worked on.

It does **not** say which direction of intervention would help. These are
association results: a gene falling as fibrosis advances may be a driver worth
restoring, a consequence worth leaving alone, or a compensatory response worth
supporting, and a correlation with stage cannot tell those apart. Most drugs
inhibit their target, so a falling gene's drug list is in many cases pointing the
wrong way — but establishing that would need perturbation or causal evidence this
graph does not carry.

## Where this leaves the plan's question

The plan asks *"whether fibrosis-specific, inflammation-specific, or shared
progression programs differ in their representation among known drug targets."*

**All three are over-represented against the eligible background; they differ
from each other only modestly.** Fibrosis-only and shared stay above a
degree-matched null, inflammation-only does so only at the class level and on the
unfiltered definition. Direction is the wider contrast in the raw percentages but
does not reach significance once the entity filter is applied, so it is shown and
not claimed.

> Team 1's handover predicted a null result here, based on 18.4 / 18.6 / 16.4%
> measured on the pre-correction gene set over *all* drug edges. The ordering
> differs on the corrected 6,222-gene set with pharmacokinetic edges removed;
> the prediction that the three classes would not separate sharply holds.

## Carried forward

1. **Report direction alongside class.** A class-only table hides a contrast
   that is visible in the percentages, even though it does not reach
   significance on the primary definition.
2. **Do not read druggability as actionability.** These groups are druggable in
   the sense that drugs exist against those proteins, not in the sense that
   those drugs would help, and not in a direction this data can establish.
3. **Keep the degree-aware null for Task 4.** Degree alone accounts for most of
   the raw gap in several groups, and will do the same for drug-coverage
   rankings.
4. **Quote the filtered figure, or say which one is quoted.** The two
   definitions differ by up to 6 points, and the direction finding lives
   entirely in that gap.
