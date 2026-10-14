# 3. Statistics

Every inferential claim in Paper 2, with the test behind it and the
assumptions it rests on.

## Druggability across progression groups (Task 3)

**Two definitions are reported throughout**, and neither establishes that a
gene is a good target:

| Definition | What it requires |
|---|---|
| therapeutic action | an `ACTS_ON` edge whose action is not `ENZYME`, `TRANSPORTER`, `CARRIER` or `SUBSTRATE` |
| **entity-filtered** (primary) | the above **and** the drug's name is not a mineral salt, nutrient, cofactor, solvent or bare ChEMBL accession |

The second condition matters — **172 of the 958 drug-connected progression
genes, 18%, reach a flagged entity and nothing else**. The filter is applied to
**both arms**; filtering one side alone would manufacture an effect rather than
measure one. It is a heuristic over names, so it marks rather than deletes, and
both columns ship.

Background rate **9.4%** filtered, 11.2% unfiltered.

| group | n | % action | **% filtered** | OR filtered | BH-q filtered | degree-matched p | exceeds null |
|---|---:|---:|---:|---:|---|---:|---|
| shared / negative | 384 | 22.7 | **16.9** | 1.96 | 2.2e-05 | 0.0005 | ✅ |
| fibrosis-only / negative | 983 | 19.3 | **14.3** | 1.61 | 1.2e-05 | 0.0005 | ✅ |
| shared / positive | 1,408 | 15.9 | **14.3** | 1.60 | 4.1e-07 | 0.0005 | ✅ |
| inflammation-only / negative | 335 | 12.8 | 11.3 | 1.23 | 2.8e-01 | 0.1124 | ✗ |
| fibrosis-only / positive | 1,040 | 12.8 | 11.1 | 1.20 | 1.2e-01 | 0.3223 | ✗ |
| inflammation-only / positive | 2,042 | 13.5 | 11.0 | 1.18 | 5.4e-02 | 0.3478 | ✗ |
| shared / discordant | 30 | 16.7 | 6.7 | 0.69 | 1.0e+00 | 0.5647 | ✗ |

**Enrichment against the background holds for three groups under both
definitions.** The falling groups lose the most to the filter — fibrosis-only /
negative drops 5.0 points — which is where the mineral salts and cofactors were.

### How the degree-matched null works, and its two limits

20 bins on non-drug degree rank; for each group gene a replacement is drawn from
its own bin; 2,000 draws. Drug edges are excluded from the matching so the null
is not conditioned on the outcome.

- **The per-bin count is always honoured.** Where a bin holds fewer background
  genes than the group needs, the draw is taken with replacement rather than
  shrinking, which would re-weight the null towards the bins that happen to be
  full. `matched_bins_short` and `matched_percent_resampled` report how often
  this happens; on this data they are **zero for every group**.
- **p never reports as zero.** It is `(r + 1) / (n + 1)` over 2,000 draws, so
  its floor is **0.0005**. That is the value the three surviving groups carry —
  it means "below the resolution of 2,000 draws", not "zero".
- `task3_gene_degrees.csv` ships every gene's degree, bin and drug counts, so
  the null can be reproduced from the delivered files.

### Falling versus rising, tested directly

Comparing each group against a shared background and comparing falling genes
against rising ones are different questions. The second is the one a direction
claim makes, so it is tested head to head within each class, with BH across the
three classes:

| class | rising | falling | ratio | Fisher p | BH-q | passes |
|---|---:|---:|---:|---:|---:|---|
| fibrosis-only | 11.1% | 14.3% | 1.30× | 0.027 | **0.082** | ✗ |
| shared | 14.3% | 16.9% | 1.19× | 0.196 | 0.294 | ✗ |
| inflammation-only | 11.0% | 11.3% | 1.03× | 0.851 | 0.851 | ✗ |

**No class passes correction on the primary definition**, so Paper 2 does not
claim that decreasing genes are more druggable than increasing ones. On the
unfiltered definition the ratios are 1.51×, 1.42× and 0.95×, and fibrosis-only
and shared do pass (BH-q 1.8e-04 and 4.4e-03) — the direction effect lives
entirely in the entities the filter removes.

Full table: `task3_falling_vs_rising.csv`, both definitions, both p and q.

**One rollup did not survive.** `[class] inflammation-only` has a degree-matched
p of 0.021 on the therapeutic-action definition and **0.127 filtered**. It is
not claimed.

**Two nulls earn their place, not one.** `inflammation-only / positive` has a
filtered BH-q of 0.054 and a therapeutic-action BH-q of 0.0065; the
degree-matched null puts it at p = 0.35. Fisher alone would have put a false
positive in the paper under either definition.

**Confound tested, not assumed.** The decreasing groups are led by ADRA1A,
HTR2A, ESR1, AR, CA2 and DRD1 — families that attract drug annotation for
reasons unrelated to liver. Classically druggable families are 20.3% of the
drug-connected decreasing genes against 10.7% of the increasing ones, and the
gap widens under the entity filter (25.0% against 11.3%). Removing those
families and re-testing against a background cleaned the same way leaves
**13.7%** (shared / negative) and **11.6%** (fibrosis-only / negative) against
an 8.2% background, OR 1.79 and 1.47. Enrichment above background survives;
the direction contrast does not, because shared / positive lands at 13.2% on the
same test.

## Mechanism consistency (Tasks 2 and 7)

Observed **52.7%** of 1,005 directional relationships.

A binomial test against 50% is invalid here: it would assume 1,005
independent observations, and a drug can hit several genes while a gene is hit
by several drugs, so the edges come in correlated blocks. The test is instead a
permutation shuffling direction at the **gene** level:

```
observed                 52.7%
null (10,000 permutations)  mean 55.9%,  95% range 45.6–66.5%
permutation p            0.553
```

The observed value sits inside the null and slightly below its mean. The test
is two-sided and centred on the **null mean**, not on 50%: the question is
whether the result differs from what this drug vocabulary gives for free, not
whether it differs from a coin flip.

**No enrichment of reversal consistency was detected under this null model.**

**The baseline is not 50%.** 68% of directional drugs lower their target and
68% of these genes rise, so the right-way pairing occurs 55.9% of the time by
accident. Any group compared against 50% would show a false result.

**Robust to the classification.** The action→direction mapping is a judgement
call, so six variants were tested, each against its own null. The strictest
raises the raw figure to 61.1% — and shrinks n, widening the null. **No variant
beats its own null.**

### No subgroup does either, once the null preserves direction (Task 7)

**The null has to keep progression direction fixed.** Rising and falling genes
have different consistency baselines by construction — 67.6% and 32.4% — so a
free shuffle of group labels lets a draw inherit the wrong baseline and makes
any group whose direction is over-represented look enriched. The permutation
shuffles only the **class** part of the label, and only among genes sharing a
direction.

| group | n | observed | vocabulary baseline | permuted null | p | BH-q |
|---|---:|---:|---:|---:|---:|---:|
| fibrosis-only / positive | 157 | 89.2% | 67.6% | 66.2% | 0.083 | 0.501 |
| inflammation-only / positive | 165 | 61.8% | 67.6% | 65.5% | 0.739 | 0.842 |
| shared / positive | 360 | 55.8% | 67.6% | 65.5% | 0.364 | 0.842 |
| fibrosis-only / negative | 189 | 29.6% | 32.4% | 26.9% | 0.603 | 0.842 |
| shared / negative | 98 | 20.4% | 32.4% | 27.0% | 0.587 | 0.842 |
| inflammation-only / negative | 36 | 30.6% | 32.4% | 26.1% | 0.842 | 0.842 |

`fibrosis-only / positive` is the closest at p = 0.083 uncorrected, q = 0.50
across the six. The choice of null decides this: mixing directions puts that
group's baseline near 53%, against which 89.2% looks decisive, while keeping
direction fixed puts it at 66% — which is simply what rising genes give.

Its 89.2% still covers only **32 genes**, led by PTGS1 (31), CACNA1C (18),
KIT (12), SCN4A (11) — the classes pharmacology has spent decades building
inhibitors for.

**The binomial columns are descriptive, not inferential.** 4,984 relationships
sit on 1,072 genes and 3,027 drugs, so they are not independent draws and BH
does not repair that. `inference_basis` on every row names the permutation as
what decides.

## Coverage versus coherence (Task 4)

Spearman **−0.328** (p = 3.3e-05, 154 drugs) between progression-gene coverage
and **class × direction** coherence, over drugs reaching ≥5 progression genes
with non-therapeutic entities removed. Negative: within that subset, the
widest-reaching drugs spread their targets across more class × direction groups.

The task script computes this correlation and writes
`task4_coverage_vs_coherence_correlation.csv`, so the value in the documents is
never carried by hand.

**The coherence measure matters.** Both measures are computed; only the
class-based one is significant:

| coherence measure | drug set | n | rho | p |
|---|---|---:|---:|---:|
| dominant **class** fraction | non-therapeutic removed | 154 | **−0.328** | 3.3e-05 |
| dominant **class** fraction | named only | 173 | −0.320 | 1.8e-05 |
| dominant **cluster** fraction | non-therapeutic removed | 154 | −0.102 | 0.21 |
| dominant **cluster** fraction | named only | 173 | −0.059 | 0.44 |

The class-level result holds on either drug set; the cluster-level one does not
hold at all. **So the claim is specific to that coherence definition and that
drug subset.** It does not generalise to coherence as such, it does not show
that wide-coverage drugs hit biologically unrelated programmes, and it says
nothing about drugs with fewer than five progression targets.

**Coherence itself is descriptive, not an enrichment statistic.** Its value
depends on target count and on how common each group is: a single-target drug
scores 1.000 automatically, and the groups are unequal in size, so a drug
choosing targets at random already scores well above chance. Nothing is compared
against a null matched for target count and group prevalence, so a high score is
a property of the target list, not evidence of unusually coherent targeting.

## MetaPaths (Task 5)

| | uncapped | capped 5–200 | removed |
|---|---:|---:|---:|
| MP4 via Reactome | 1,283,702 | 1,052,539 | **18%** |
| MP5 via GO BP | 14,563,118 | 3,577,655 | **75%** |

Membership counts terms that carry at least one valid path. A term can join
both sides and still support none, because every path through it has the source
gene equal to the target gene. **364 of MP4's 1,937 terms and 3,565 of MP5's
9,353** are excluded on that test.

Raw path count versus DWPC: Spearman **0.382**. The two orderings genuinely
disagree, so a degree-normalised measure was not a formality.

**DWPC is the published formula.** Each path is weighted by the product over
every *edge* of the two metaedge-specific degrees at its ends, raised to −0.4.
A three-edge path carries six factors, and the bridge term's degree enters
**twice** because the term lies on two edges. A four-factor shortcut counting
the term once ranks the same pairs at Spearman 0.897; only the published form is
used downstream, and `dwpc_4factor` ships beside it.

**Transition convergence — two null results, two different questions.**

*Direct connectivity, all fibrosis-associated genes.* Against an overall
drug-connection rate of 16.6%, the four transitions sit at 15.8 / 19.0 / 16.8 /
16.1 per cent, enrichment 0.95–1.14, nothing surviving BH. This tests drug
annotation, not candidates, and is not evidence that timing and drug
connectivity are independent — only that this comparison found nothing.

*Candidate drugs, by metapath.* The question the plan asks. Task 8's 30 leading
candidates against the 1,846 other ranked drugs, over MP7
(`Drug → Gene → Pathway ← transition gene`), on Paper 1's **substantial**
transition calls (2,568 genes, 781 at F3→F4), with a permutation over which
drugs carry the candidate label: **32.9% versus 30.9%, difference +2.0 points,
p = 0.380.** No convergence.

## Target-score robustness (Task 6)

**Ties are admitted, not broken.** The components are coarse, so the gene
sitting 50th shares its score with many others: at equal weights **133** shared
genes, **91** fibrosis-only and **50** inflammation-only hold a top-50 score.
Taking the literal first 50 would resolve that by row order, and shuffling the
file would change who is "in the top 50". Every top-N figure is therefore a
**band** — all genes at or above the 50th score — and retention is measured
against the band.

2,000 weightings from a Dirichlet(1,1,1,1,1) over the whole simplex:

| class | band at equal weights | median ρ | 5th pct | median band retained |
|---|---:|---:|---:|---:|
| fibrosis-only | 91 | 0.948 | 0.792 | 50 / 91 (55%) |
| shared | 133 | 0.924 | 0.815 | 84 / 133 (63%) |
| inflammation-only | 50 | 0.981 | 0.902 | 32 / 50 (64%) |

**Ordering is stable; exact membership is not.** Use rank bands, or
`task6_stable_core.csv`.

**The stable core is a threshold, not a quota.** A gene enters it by reaching
the band under at least **80%** of the same 2,000 weightings: 16 shared, 15
fibrosis-only, 16 inflammation-only, **47 genes** in all, lowest frequency kept
0.809. Taking a fixed 25 per class instead would fill the file to 75 rows
whatever the frequencies were, admitting genes as low as 51% and making a class
with no stable members look as though it had twenty-five.

**Ablation found a component that cannot rank.** Removing **F** changes the
ranking not at all — ρ = 1.000, the whole band retained, in every class —
because F is constant within a class and within-class scoring is what the
missing data forces. This is arithmetic, not an empirical finding, and
`constant_within_class` says so on the row. Four effective components, not five.

**K is binary, not degree-free.** It carries no drug count, so one inhibitor
scores the same as forty. It is still sensitive to how well a gene is studied,
because a better-annotated gene has more chances to satisfy either binary
condition: Spearman **0.246** against non-drug degree (p = 1.6e-86), and the
best-connected fifth of genes is nearly **7×** more likely to earn K credit than
the least. `K_degree_sensitivity` in the Task 6 workbook.

**P scores strength, not significance, and is calibrated differently per
class.** Significance is eligibility — every gene here already passed Paper 1's
BH threshold — so q carries no ranking information and P scores |rho| alone.
Direction enters through K instead. Fibrosis-associated genes use Paper 1's
frozen three-level cut on |rho|; inflammation-only genes use a within-class
percentile, because no frozen cut-point exists for the disease-group ladder.
**Scores are comparable within a class and not across classes**, which is also
why the three lists are never merged.
