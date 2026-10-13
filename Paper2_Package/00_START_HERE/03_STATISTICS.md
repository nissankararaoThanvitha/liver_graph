# 3. Statistics

Every inferential claim in Paper 2, with the test behind it. Where a first
attempt was wrong, both the error and the correction are recorded — a reader
meeting the old figure elsewhere needs to know which to trust.

## Druggability across progression groups (Task 3)

Background rate **11.2%** (963 of 8,572 eligible non-progression genes).

| group | n | % | OR | BH-q | degree-matched p | survives |
|---|---:|---:|---:|---|---:|---|
| shared / negative | 384 | 22.7 | 2.32 | 2.0e-09 | 0.0000 | ✅ |
| fibrosis-only / negative | 983 | 19.3 | 1.89 | 2.1e-11 | 0.0000 | ✅ |
| shared / positive | 1,408 | 15.9 | 1.50 | 2.4e-06 | 0.0015 | ✅ |
| inflammation-only / positive | 2,042 | 13.5 | 1.24 | 6.5e-03 | 0.0560 | ✗ |
| fibrosis-only / positive | 1,040 | 12.8 | 1.16 | 1.8e-01 | 0.4950 | ✗ |
| inflammation-only / negative | 335 | 12.8 | 1.16 | 3.8e-01 | 0.2240 | ✗ |

**The degree-aware null earns its place.** `inflammation-only / positive` has a
BH-q of 0.0065 and looks significant, then dies at p = 0.056 once connectivity
is matched. Fisher alone would have put a false positive in the paper.

**Confound tested, not assumed.** The decreasing groups are led by ADRA1A,
HTR2A, ESR1, AR, DRD1 and the monoamine oxidases — families that attract drug
annotation for reasons unrelated to liver, and which a degree-matched null does
not control for. Removing every classically druggable family leaves **20.2%**
and **16.5%** against a 10.0% background (OR 2.29 and 1.79). The effect is
smaller and it is not theirs.

## Mechanism consistency (Tasks 2 and 7)

Observed **52.7%** of 1,005 directional relationships.

> **An invalid test, corrected.** The first version used a binomial against
> 50% and reported p = 0.088. It assumed 1,005 independent observations; a drug
> can hit several genes and a gene several drugs, so the edges come in
> correlated blocks.

Replaced with a permutation shuffling direction at the **gene** level:

```
observed                 52.7%
null (10,000 permutations)  mean 55.9%,  95% range 45.6–66.5%
permutation p            0.778
```

The observed value sits inside the null and slightly below its mean.

**The baseline is not 50%.** 68% of directional drugs lower their target and
68% of these genes rise, so the right-way pairing occurs 55.9% of the time by
accident. Any group compared against 50% would show a false result.

**Robust to the classification.** The action→direction mapping is a judgement
call, so six variants were tested, each against its own null. The strictest
raises the raw figure to 61.1% — and shrinks n, widening the null. **No variant
beats its own null.**

### One subgroup does (Task 7)

| group | n | observed | vocabulary baseline | gene-permuted null | p |
|---|---:|---:|---:|---:|---:|
| **fibrosis-only / positive** | 157 | **89.2%** | 67.6% | 53.3% | **0.0010** |
| shared / positive | 360 | 55.8% | 67.6% | 53.4% | 0.834 |
| fibrosis-only / negative | 189 | 29.6% | 32.4% | 53.4% | 0.029 *(below)* |

Caveat stated with the result: those 140 relationships cover **32 genes**, led
by PTGS1 (31), CACNA1C (18), KIT (12), SCN4A (11) — the classes pharmacology
has spent decades building inhibitors for. The gene-level permutation rules out
the simplest objection; what it means biologically is not settled here.

## Coverage versus coherence (Task 4)

Spearman **−0.124** between progression-gene coverage and coherence, over named
drugs reaching ≥5 genes. Negative: the widest-reaching drugs cover the least
coherent programmes.

## MetaPaths (Task 5)

| | uncapped | capped 5–200 | removed |
|---|---:|---:|---:|
| MP4 via Reactome | 1,283,702 | 1,052,539 | **18%** |
| MP5 via GO BP | 14,563,118 | 3,577,655 | **75%** |

Raw path count versus DWPC: Spearman **0.454**. The two orderings genuinely
disagree, so a degree-normalised measure was not a formality.

**Transition convergence — a null result.** Against an overall drug-connection
rate of 16.6%, the four transitions sit at 15.8 / 19.0 / 16.8 / 16.1 per cent,
enrichment 0.95–1.14, nothing surviving BH correction. F3→F4 — the transition
Paper 1 found carries 311 genes under equal power — sits at 0.97. Drug
annotation has no reason to know *when* in a disease a gene moves.

## Target-score robustness (Task 6)

2,000 weightings from a Dirichlet(1,1,1,1,1) over the whole simplex:

| class | median ρ vs equal weights | 5th pct | median top-50 retained |
|---|---:|---:|---:|
| fibrosis-only | 0.946 | 0.783 | 29 / 50 |
| shared | 0.923 | 0.810 | 31 / 50 |
| inflammation-only | 0.978 | 0.887 | 32 / 50 |

**Ordering is stable; an exact top-50 is not.** Use rank bands, or
`task6_stable_core.csv`.

**Ablation found a dead component.** Removing **F** changes the ranking not at
all — ρ = 1.000, all 50 retained, in every class — because F is constant within
a class and within-class scoring is what the missing data forces. Four
effective components, not five.
