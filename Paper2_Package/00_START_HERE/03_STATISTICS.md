# 3. Statistics

Every inferential claim in Paper 2, with the test behind it. Where a first
attempt was wrong, both the error and the correction are recorded — a reader
meeting the old figure elsewhere needs to know which to trust.

## Druggability across progression groups (Task 3)

**Two definitions are reported, because the first one was too loose.**

> **A reviewer's finding, 13 October.** "Drug-connected" originally counted any
> `ACTS_ON` edge whose action was not pharmacokinetic. That let zinc chloride,
> ATP and unnamed ChEMBL accessions make a gene druggable. **174 of the 958
> drug-connected progression genes — 18% — reach a flagged entity and nothing
> else.** The filter is now applied to **both arms**; cleaning one side only
> would manufacture an effect rather than measure one.

Background rate **9.3%** filtered (was 11.2% unfiltered).

| group | n | % published | **% filtered** | OR filtered | BH-q filtered | degree-matched p | survives |
|---|---:|---:|---:|---:|---|---:|---|
| shared / negative | 384 | 22.7 | **17.2** | 2.04 | 5.1e-06 | 0.0000 | ✅ |
| shared / positive | 1,408 | 15.9 | **14.1** | 1.62 | 3.2e-07 | 0.0000 | ✅ |
| fibrosis-only / negative | 983 | 19.3 | **14.3** | 1.64 | 4.3e-06 | 0.0000 | ✅ |
| inflammation-only / negative | 335 | 12.8 | 11.3 | 1.26 | 2.4e-01 | 0.0860 | ✗ |
| fibrosis-only / positive | 1,040 | 12.8 | 11.1 | 1.22 | 8.0e-02 | 0.2485 | ✗ |
| inflammation-only / positive | 2,042 | 13.5 | 10.9 | 1.20 | 3.8e-02 | 0.2575 | ✗ |

**The headline survives against the background, and the gap narrows.** All three
groups that beat the degree-matched null before still beat it with both arms
filtered. The falling groups lose the most — fibrosis-only / negative drops 5.0
points — which is exactly where mineral salts and cofactors were doing the work.

### Falling versus rising, tested directly

> **The "about 2×" claim was wrong, and not only because of the filter.** It
> compared each group against the *background*, then described the result as
> falling genes being twice as drug-connected as *rising* ones. Those are
> different comparisons. Asked directly, head to head within each class:

| class | rising | falling | ratio | Fisher p | significant |
|---|---:|---:|---:|---:|---|
| fibrosis-only | 11.1% | **14.3%** | **1.30×** | 0.027 | ✅ |
| shared | 14.3% | 16.9% | 1.19× | 0.196 | ✗ |
| inflammation-only | 11.0% | 11.3% | 1.03× | 0.851 | ✗ |

**The effect is real for fibrosis-only genes and about 1.3×, not 2×.** For the
shared class it does not reach significance head to head, although both of its
direction groups beat the background. The claim is now stated at that strength
and no higher. Unfiltered, the ratios are 1.51×, 1.42× and 0.95× — still not 2×.

Full table: `task3_falling_vs_rising.csv`, both definitions.

**One result did not survive.** The class-level rollup
`[class] inflammation-only` had a degree-matched p of 0.0205 unfiltered and
**0.0805 filtered**. It is no longer significant and is no longer claimed.

**Two nulls earn their place, not one.** `inflammation-only / positive` has a
filtered BH-q of 0.038 and looks significant until the degree-matched null puts
it at p = 0.26. Fisher alone would have put a false positive in the paper under
either definition.

**Confound tested, not assumed.** The decreasing groups are led by ADRA1A,
HTR2A, ESR1, AR, DRD1 and the monoamine oxidases — families that attract drug
annotation for reasons unrelated to liver. Removing every classically druggable
family leaves **20.2%** and **16.5%** against a 10.0% background (OR 2.29 and
1.79) on the unfiltered definition. The effect is smaller and it is not theirs.

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

Spearman **−0.268** (p = 0.001, 147 drugs) between progression-gene coverage and
class coherence, over drugs reaching ≥5 progression genes with non-therapeutic
entities removed. Negative: the widest-reaching drugs cover the least coherent
programmes.

> **A stale figure, corrected.** This was reported as **−0.124** in five
> documents and three scripts. No script computed it — it was carried by hand
> from an earlier Task 4 run, and it drifted when the coherence definition and
> the drug set changed. The task script now computes it and writes
> `task4_coverage_vs_coherence_correlation.csv`, so a stale value cannot
> survive a rerun. **The conclusion is unchanged and in fact stronger**: the
> correlation is more negative than was claimed, not less.

**The coherence measure matters, which one number hid.** Both measures were
computed; only the class-based one is significant:

| coherence measure | drug set | n | rho | p |
|---|---|---:|---:|---:|
| dominant **class** fraction | non-therapeutic removed | 147 | **−0.268** | 0.001 |
| dominant **class** fraction | named only | 173 | −0.320 | 1.8e-05 |
| dominant **cluster** fraction | non-therapeutic removed | 147 | −0.090 | 0.28 |
| dominant **cluster** fraction | named only | 173 | −0.059 | 0.44 |

The class-level claim holds on either drug set. The cluster-level one does not
hold at all, so the argument that coverage selects promiscuity should be made at
the level of progression class, not trajectory cluster.

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
