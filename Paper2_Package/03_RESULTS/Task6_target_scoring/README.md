# Task 6 — Target-prioritisation framework

Plan: *"Paper 2 should first rank therapeutic targets and only then rank
drugs. Define a transparent target-scoring framework now… Every component must
later be normalized and justified. Perform sensitivity analysis for weighting
choices rather than selecting arbitrary weights solely to obtain a desired
ranking… perform an ablation analysis showing how rankings change when
trajectory evidence, pathway evidence, knowledge-graph evidence, or other
components are removed."*

Built by `scripts/paper2_task6_target_score.py`, 12 October 2026.

## Files

| File | Rows | What it is |
|---|---:|---|
| `task6_target_scores.csv` | 6,222 | every gene, five components, score, rank within class |
| `task6_ablation.csv` | 15 | how far the ranking moves when each component is dropped |
| `task6_weight_sensitivity.csv` | 3 | stability across 2,000 random weightings |
| `task6_stable_core.csv` | 75 | genes that stay in the top 50 under almost any weighting |
| `task6_supporting.xlsx` | 2 sheets | component availability · component correlations |
| `task6_weight_stability.png` | — | top-50 survival, and the stable core |

---

# 1. Mathematical definition of every component

```
TargetScore(g) =  [ Σ_c w_c · C_c(g) ]  /  [ Σ_c w_c · 1{C_c(g) defined} ]
                  c ∈ {P, F, T, K, B}
```

All components are on **[0, 1]**, higher is better.

### P — progression evidence
```
fibrosis-associated g :  P(g) = P_paper1(g) / 2          P_paper1 ∈ {0,1,2}
inflammation-only   g :  P(g) = percentile_within_class( |inflammation_rho| )
```
`P_paper1` is Paper 1's frozen progression score: 2 if \|rho\| ≥ 0.40, 1 if
≥ 0.30, else 0. Inflammation-only genes have no fibrosis association to score,
so the same quantity is taken on the ladder they do sit on.

**Three things about P are departures from the plan's "strength, significance
and direction" component, and are stated rather than smoothed over.**

1. **Significance is eligibility, not score.** A gene reaches this table only
   by passing Paper 1's BH-adjusted threshold, so every gene scored here is
   already significant and q carries no further ranking information. P scores
   *strength* alone. A gene at q = 1e-40 and a gene at q = 0.049 with the same
   rho receive the same P.
2. **Direction is handled elsewhere.** It is not in P because direction is not
   a quality of the evidence; it enters through K, which asks whether a drug's
   action opposes the gene's direction of travel.
3. **The two calibrations are not comparable.** Fibrosis-associated genes get a
   coarse three-level cut on absolute rho, frozen by Paper 1 before Paper 2
   began; inflammation-only genes get a within-class percentile, because no
   frozen cut-point exists for the disease-group ladder and inventing one would
   be a Paper 2 decision dressed as a Paper 1 one. The consequence is that
   P = 0.5 means "rho between 0.30 and 0.40" in one class and "median of the
   class" in the other. **Scores are comparable within a class and not across
   classes**, which is also why the three lists are never merged.

### F — fibrosis specificity
```
F(g) = 1   if fibrosis-only
     = 0   if shared or inflammation-only
```
Paper 1's own definition, unchanged.

### T — trajectory and stage-transition evidence
```
fibrosis-associated g :  T(g) = ( T_paper1(g) + X_paper1(g) ) / 4
inflammation-only   g :  undefined
```
`T_paper1` scores \|F4 − F0\| (2 if ≥ 1.0 SD, 1 if ≥ 0.5, 0 if the direction is
wrong); `X_paper1` scores the largest stage jump (2 if real in the full fit
**and** reproducible in ≥ 50% of 50 equal-power redraws, 1 if one of the two).
The plan asks T to cover both trajectory and transition, so both are included.

### K — knowledge-graph evidence *(new in Paper 2)*
```
K(g) = 0.5 · 1{ a therapeutic drug acts on g }
     + 0.5 · 1{ some such drug's action opposes g's direction of travel }
```
**Carries no drug count.** The obvious K is "how many drugs act on this gene",
and every task so far has found degree misleading: Task 3 killed an apparently
significant result once connectivity was matched, Task 4 found coverage
*negatively* correlated with coherence, and Task 5 found raw path counts
disagreeing with DWPC at ρ = 0.45 while DWPC itself promoted proteasome and
tubulin binders. A gene with one characterised inhibitor scores the same as one
with forty.

**That is not the same as being degree-free.** K asks whether *any* usable
drug exists and whether *any* consistent relationship exists, and a
better-annotated gene has more chances to satisfy either. Measured against the same non-drug degree Task 3 matched on
(`K_degree_sensitivity` in the supporting workbook):

| non-drug degree | genes | median degree | % with any K credit |
|---|---:|---:|---:|
| Q1 least connected | 1,245 | 38 | 4.0 |
| Q2 | 1,244 | 76 | 6.5 |
| Q3 | 1,244 | 114 | 11.1 |
| Q4 | 1,244 | 169 | 14.1 |
| Q5 most connected | 1,245 | 330 | 27.4 |

Spearman **0.246** (p = 1.6e-86). The best-connected fifth of genes is nearly
**7×** more likely to earn K credit than the least. K is a binary
annotation-based component that removes the *count* of drugs, not the influence
of how well a gene has been studied.

### B — biological / pathway evidence
```
fibrosis-associated g :  B(g) = B_paper1(g) / 2          B_paper1 ∈ {0,1,2}
inflammation-only   g :  undefined
```
2 if the gene appears in enriched terms in ≥ 2 of GO BP / KEGG / Reactome /
Hallmark, 1 if in exactly one. Paper 1's four-database result, unchanged.

**Four of the five components are Paper 1's, reused rather than re-derived.**
Re-deriving them would create a second, differently-calibrated version of
validated work and break the traceability the plan asks for. Only K is new.

---

# 2. Normalisation and missing values

### Normalisation
Continuous inputs become **within-class percentiles**, not min-max. Min-max
would let one extreme rho compress everything else into the bottom of the
range, and these distributions are skewed. Paper 1's integer components are
divided by their maxima, which preserves the cut-points Paper 1 froze in
advance.

### Missing values — the real design decision
Paper 1's trajectory, transition, pathway and tier work covers only the **3,845**
fibrosis-associated genes. The **2,377** inflammation-only genes have none of it:

| class | P | F | T | K | B |
|---|---:|---:|---:|---:|---:|
| fibrosis-only | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| shared (both) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| **inflammation-only** | 1.00 | 1.00 | **0.00** | 1.00 | **0.00** |

Three options existed:

| | |
|---|---|
| impute the missing components | **rejected** — invents evidence |
| score 0 for missing components | **rejected** — that *is* the penalty: the 2,377 would rank last for missing data, not biology |
| **score within class, renormalising weights over available components** | **used** |

The denominator `Σ w_c · 1{defined}` renormalises so every class's score stays
on [0, 1]. **Genes are ranked only within their own class**, and the three
lists are never merged — which is also what the plan requires when it forbids
collapsing the classes into one "progression" category.

Consequence to state plainly: the inflammation-only score rests on **two**
effective components (P and K — see finding 1 below), the others on four. Those
rankings are not equally well-founded and must not be presented as if they
were.

---

# 3. Weight sensitivity and robustness

### Weights are not tuned
Equal weights (0.2 each) are the default because nothing in Paper 1 or Paper 2
justifies preferring one component yet, and the plan warns against *"selecting
arbitrary weights solely to obtain a desired ranking"*.

### Ties are admitted, not broken
The components are coarse — P and T take a handful of values, F, K and B take
two or three — so many genes share a score exactly. At equal weights the gene
sitting 50th is **tied with dozens of others**: 133 shared genes hold a top-50
score, 91 fibrosis-only, 50 inflammation-only.

Taking the literal first 50 would resolve those ties by row order, so shuffling
the file would change who is "in the top 50". Every top-N figure below is
therefore a **band**: all genes at or above the 50th score, ties included.
The band sizes are in `task6_weight_sensitivity.csv`
(`top50_band_at_equal_weights`), and retention is measured against the band.

### The test
2,000 weight vectors drawn from a **Dirichlet(1,1,1,1,1)** — the uniform
distribution over the whole weight simplex, not small nudges around one choice.
The question is whether the ranking survives *any* reasonable weighting.

| class | genes | band at equal weights | median ρ | 5th pct ρ | median band retained | 5th pct |
|---|---:|---:|---:|---:|---:|---:|
| fibrosis-only | 2,023 | 91 | 0.948 | 0.792 | **50 / 91** | 38 |
| shared | 1,822 | 133 | 0.924 | 0.815 | **84 / 133** | 34 |
| inflammation-only | 2,377 | 50 | 0.981 | 0.902 | **32 / 50** | 20 |

### Ablation — remove one component, see what moves

Band sizes change when a component is removed, so overlap is reported as a
percentage of the full-weight band, and a component that is constant inside a
class is marked as such: it cannot reorder that class at all, so any apparent
movement would be tie-breaking noise.

| removed | class | constant in class | ρ vs full | band kept |
|---|---|---|---:|---:|
| **F** | all three | **yes** | **1.000** | **100%** |
| P | shared | no | 0.926 | 44% |
| P | fibrosis-only | no | 0.968 | 66% |
| P | inflammation-only | no | 0.437 | 100% |
| T | fibrosis-only | no | 0.920 | 62% |
| K | shared | no | 0.964 | 63% |
| K | fibrosis-only | no | 0.968 | 62% |
| K | inflammation-only | no | 0.888 | **16%** |
| B | fibrosis-only | no | 0.736 | 52% |

Full table, all fifteen combinations: `task6_ablation.csv`.

---

# Findings

### 1. F contributes nothing, by construction
F is *constant within a class* — 1 for every fibrosis-only gene, 0 for every
other — and scoring within class, which the missing-data problem forces, makes
a constant unable to order anything. Removing it leaves ρ = 1.000 and the whole
band intact, in every class.

This is structural, not empirical: the ablation reports it because arithmetic
guarantees it, and `can_reorder_within_class` says so on the row. Resolving ties
by row order instead would show a little spurious movement here, which is one
reason the top-N band admits every tied gene.

**F is not wrong, it is redundant under within-class scoring.** It belongs in
the formula as documentation of why the classes are scored separately, and
carries zero ranking information. Reporting it as a working component would
overstate the score's evidence base by a fifth.

### 2. The ranking is stable; exact membership is not
Overall ordering holds well (median ρ ≈ 0.92–0.98). But only **55%, 63% and 64%**
of each class's top band survives a random reweighting, and at the 5th
percentile as little as a fifth.

So: **rank bands are defensible, an exact top-50 is not.** Any shortlist drawn
from this should be described as "high-scoring under most weightings".

### 3. The stable core is a threshold, not a quota
`task6_stable_core.csv` holds the genes that reach the top band under **at least
80% of the 2,000 weightings** — the same 2,000 the sensitivity table uses, so
both describe one experiment.

| class | genes meeting ≥ 80% | lowest frequency kept |
|---|---:|---:|
| shared | 16 | 0.952 |
| fibrosis-only | 15 | 0.850 |
| inflammation-only | 16 | 0.809 |

**47 genes**, not a fixed 25 per class. A quota would have filled the file to
75 rows whatever the frequencies were, admitting genes as low as 51% and making
a class with no stable members look as though it had twenty-five. The count per
class is itself a result: it says how much of each ranking is weighting-proof.

### 3b. The inflammation-only score is a two-component score
With T and B undefined and F constant, those 2,377 genes are ranked on P and K
alone. Removing K collapses their band overlap to **16%** — the single largest
ablation effect anywhere in the table. Their ranking is close to "does a drug
exist for it", which is a much weaker claim than the four-component score made
for the other classes. Removing P leaves 100% overlap only because the band
grows to 262 genes once P is gone, not because P does not matter.

### 4. The top of the list agrees with the rest of Paper 2
Fibrosis-only targets at equal weights:

| Gene | P | F | T | K | B | Score |
|---|---:|---:|---:|---:|---:|---:|
| **PDGFRA** | 1.0 | 1.0 | 1.00 | 1.0 | 1.0 | **1.00** |
| **CACNA1C** | 1.0 | 1.0 | 1.00 | 1.0 | 1.0 | **1.00** |
| MYC | 1.0 | 1.0 | 1.00 | 0.5 | 1.0 | 0.90 |
| TPM4 | 1.0 | 1.0 | 1.00 | 0.5 | 1.0 | 0.90 |
| SRC | 0.5 | 1.0 | 1.00 | 1.0 | 1.0 | 0.90 |

PDGFRA and CACNA1C score a perfect 1.00 on all five components. Both were
independently flagged in Task 7 as reversal-consistent fibrosis-only rising
genes, and **both are Paper 1 9/9 genes** — six genes reach 9, PDGFRA and
CACNA1C among them. Several routes converging on the same genes is reassuring,
though they all draw on the same underlying data, so it is consistency, not
independent validation.

---

## Carried forward to Task 8

1. **Do not present an exact top-N.** Use `task6_stable_core.csv` or report rank
   bands.
2. **Score within class, always.** Merging the three lists would rank the
   inflammation-only genes on two components against four.
3. **F is documentation, not evidence.** Four effective components, not five.
4. **Weights stay equal unless something justifies otherwise**, and any change
   must be re-run through the sensitivity analysis.
5. ~~The final ranking still needs the transcriptomic reversal layer.~~
   **Superseded 13 October 2026:** the mentor ruled transcriptomic reversal out
   of scope ("repurposing not reversal", "focus only on the knowledge graph").
   Task 8 proceeds on the six evidence layers that exist, with the reversal
   layer recorded as a limitation.

## Limitation — band 1 depends on recorded drug direction

**Band 1 depends on recorded drug direction.** PDGFRA and CACNA1C reach the top
band because each is a Paper 1 9/9 gene with a drug whose recorded action opposes
the gene's direction of change (K = 1.0). Three other 9/9 genes — MYC, PLK3 and
TPM4 — have a drug but no recorded direction (K = 0.5), so they rank in the next
band (score 0.9). TAX1BP3 has no drug (K = 0). Only 11% of drug–target
relationships carry a recorded direction, so this difference reflects
**annotation coverage, not evidence against these genes**. Candidate drugs for
them should be considered part of the wider repurposing space.
