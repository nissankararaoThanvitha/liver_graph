# Question on Step 9 — how to choose the final shortlist

Steps 1–8 are complete. The scoring rules were frozen before any ranked list
was looked at, as instructed.

**Result: 507 genes reached Tier 1 (HighConfidenceScore 7–9 out of 9).**

Before selecting the final set we examined the Tier 1 composition, as Step 9
asks. Two of your concerns are already satisfied; two are not.

## Already fine — no intervention needed

**Shared genes were not squeezed out.** Tier 1 is 54% shared (275) and 46%
fibrosis-only (232). Scoring fibrosis-specificity at 1 point rather than 2
kept it a tie-breaker.

**No single pathway dominates.** The most common enriched process among the
507 is Epithelial–mesenchymal transition at 10.8%, then ECM organization at
9.1%. Nothing approaches taking over, so the shortlist will not be "all
extracellular matrix" unless we create that ourselves.

## The problem — Tier 1 is very uneven across trajectory clusters

| Cluster | Pattern | Tier 1 genes | of all | % reaching Tier 1 |
|---|---|---|---|---|
| C1 | early increase, then continues | 103 | 927 | 11.1% |
| C2 | late increase, largest F3→F4 | **333** | 1,514 | 22.0% |
| C3 | early rise, then plateau | **6** | 197 | 3.0% |
| C4 | mid decrease | **5** | 309 | 1.6% |
| C5 | late decrease | 60 | 698 | 8.6% |

C2 alone is 66% of Tier 1. Consequently Tier 1 is 87% increasing genes
(442 vs 65 decreasing), and 75% of its genes make their largest change at
F3→F4.

This is partly real biology and partly our scoring. Two of the five scores
structurally favour late, well-studied genes: the trajectory score reads
F4 − F0 and so misses genes that rise early and plateau (C3 got 1 gene at
T=2 out of 197), and the pathway score depends on enrichment that C4 barely
has (10 significant terms in total, against 542 for C2). We have documented
both rather than tuned them away.

**If we simply take the top 25 by score, the final list will be almost
entirely C2: late-rising, increasing, well-annotated genes.**

## The question

Step 9 says to preserve diversity, and that "approximately 15–30 genes is
reasonable if supported by the data; do not force an exact number."

We are unsure how to weigh those two against each other here, so rather than
guess:

**Option A — balanced cells.** Take the top 5 Tier-1 genes from each cluster
(5 = what C4, the scarcest cluster, actually has). 25 genes, all five
trajectory patterns, both directions. C2 is capped at 5 despite having 333
qualifying genes; C3 and C4 contribute their entire Tier-1 membership.

**Option B — support-led, accepting a smaller or uneven set.** Within each
cluster take only the genes at that cluster's own top score, so each
cluster contributes as many as it genuinely supports and no more. This may
yield fewer than 25 overall, and an uneven split between clusters.

**Option C — score-led.** Take the strongest genes overall regardless of
cluster, and state plainly that the final set is predominantly late-stage
increasing biology.

We lean towards **A**, because it is the only one that guarantees the early
and decreasing programmes appear at all, and every selected gene still
clears the Tier-1 bar — the sampling changes, not the quality threshold.
But A does cap C2 arbitrarily, and B is closer to your "supported by the
data" wording.

**Which would you prefer? And is a final set smaller than 15 acceptable if
that is what the evidence supports?**

## Two limits worth knowing, whichever option you choose

**Leave-one-study-out will be 5 runs, not 8.** Only five of the eight studies
stage fibrosis (GSE130970, GSE135251, GSE162694, GSE193066, GSE240729); the
other three have no F0–F4 labels, so there is nothing to leave out. Robustness
will be reported as R = n/5.

**The power-matched analysis cannot carry significance.** We re-ran it per
gene. At 30 patients per stage with FDR across 3,645 genes, the number of
significant genes per draw is 0, 0, 0 and 297 for the four transitions —
scoring on it would have excluded every early-transition gene outright. We
therefore scored on reproducibility (did the jump stay large and keep its
direction across 50 equal-power redraws: 1,522 / 1,856 / 1,713 / 2,790 genes)
and carried the strict significance counts into the table as their own
column, scoring nothing.
