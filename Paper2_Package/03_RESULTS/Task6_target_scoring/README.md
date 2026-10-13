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
**Deliberately degree-free.** The obvious K is "how many drugs act on this
gene", and every task so far has found degree misleading: Task 3 killed an
apparently significant result once connectivity was matched, Task 4 found
coverage *negatively* correlated with coherence (ρ = −0.268), and Task 5 found
raw path counts disagreeing with DWPC at ρ = 0.45 while DWPC itself promoted
proteasome and tubulin binders. A gene with one characterised inhibitor scores
the same as one with forty.

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

### The test
2,000 weight vectors drawn from a **Dirichlet(1,1,1,1,1)** — the uniform
distribution over the whole weight simplex, not small nudges around one choice.
The question is whether the ranking survives *any* reasonable weighting.

| class | genes | median ρ vs equal weights | 5th pct ρ | median top-50 retained | 5th pct |
|---|---:|---:|---:|---:|---:|
| fibrosis-only | 2,023 | 0.946 | 0.783 | **29 / 50** | 17 |
| shared | 1,822 | 0.923 | 0.810 | **31 / 50** | 16 |
| inflammation-only | 2,377 | 0.978 | 0.887 | **32 / 50** | 22 |

### Ablation — remove one component, see what moves

| removed | class | ρ vs full | top-50 kept |
|---|---|---:|---:|
| **F** | all three | **0.999–1.000** | **100%** |
| P | fibrosis-only | 0.969 | 54% |
| P | inflammation-only | 0.476 | 58% |
| T | fibrosis-only | 0.923 | 78% |
| K | fibrosis-only | 0.963 | 44% |
| K | inflammation-only | 0.871 | **18%** |
| B | fibrosis-only | 0.749 | 76% |

---

# Findings

### 1. F contributes nothing, by construction
Removing F changes the ranking **not at all** — ρ = 1.000, all 50 top genes
retained, in every class.

The reason is structural: F is *constant within a class* (1 for every
fibrosis-only gene, 0 for every other). Scoring within class — which the
missing-data problem forces — makes it a constant, and a constant cannot order
anything.

**F is not wrong, it is redundant under within-class scoring.** It should be
kept in the formula as documentation of why the classes are scored separately,
and recognised as carrying zero ranking information. Reporting it as a working
component would overstate the score's evidence base by a fifth.

### 2. The ranking is stable; the top-50 is not
Overall ordering holds well (median ρ ≈ 0.92–0.98). But a **median of only 29–32
of 50** top genes survive a random reweighting, and at the 5th percentile as few
as 16.

So: **rank bands are defensible, an exact top-50 is not.** Any shortlist drawn
from this should be described as "high-scoring under most weightings", with
`task6_stable_core.csv` — genes in the top 50 across ≥ 80% of random weightings
— as the defensible version.

### 3. The inflammation-only score is a two-component score
With T and B undefined and F constant, those 2,377 genes are ranked on P and K
alone. Removing K collapses their top-50 overlap to **18%** — the single
largest ablation effect anywhere in the table. Their ranking is close to "does
a drug exist for it", which is a much weaker claim than the four-component
score made for the other classes.

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
genes, and PDGFRA is Paper 1's own 9/9 gene and the Nintedanib case. Three
routes converging on the same genes is reassuring — though all three draw on
the same underlying data, so it is consistency, not independent validation.

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
