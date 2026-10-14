# Task 7 — Drug action / direction evidence

Plan: *"For candidate drug-target relationships, determine whether the drug is
reported as an inhibitor, antagonist, agonist, activator, binder, or has
unknown/mixed action… Classify each relationship as reversal-consistent,
reversal-inconsistent, ambiguous, or unknown… this remains a hypothesis until
independently validated."*

Built by `scripts/paper2_task7_action_direction.py`, 12 October 2026.

## Files

| File | Rows | What it is |
|---|---:|---|
| `task7_action_direction_evidence.csv` | 4,984 | the required table |
| `task7_known_vs_unknown_direction.csv` | 8 | known vs unknown action direction |
| `task7_consistency_by_group.csv` | 7 | consistency × Paper 1 group |
| `task7_consistency_by_cluster.csv` | 5 | consistency × F0–F4 trajectory cluster |
| `task7_consistency_significance.csv` | 6 | is any group better than chance? |
| `task7_supporting.xlsx` | 4 sheets | action vocabulary · by transition · by tier · top Tier-1 |
| `task7_consistency_vs_null.png` | — | observed vs both baselines, per group |

## Scope — pharmacokinetic edges are excluded

The plan scopes this to *"candidate drug-target relationships"*. `ENZYME`,
`TRANSPORTER`, `CARRIER` and `SUBSTRATE` mean the gene metabolises or
transports the drug; there is no mechanism to be consistent or inconsistent
with.

```
8,948  drug-gene edges
3,964  pharmacokinetic   -> excluded, counted separately
4,984  drug-target relationships  <- this table
```

## Known versus unknown action direction

| | relationships | % |
|---|---:|---:|
| **Action direction known** (lowers or raises) | **1,005** | **20.2** |
|   …lowers the gene | 679 | 13.6 |
|   …raises the gene | 326 | 6.5 |
| **Unknown or mixed** | **3,979** | **79.8** |
|   …binder or mixed action | 21 | 0.4 |
|   …no direction recorded | 3,958 | 79.4 |

**Four fifths of drug-target relationships carry no usable direction.** Any
reversal logic runs on the remaining 1,005.

## The four-way classification

| Class | `reversal_class` | `reversal_class_with_trajectory` |
|---|---:|---:|
| unknown | 3,979 | 3,979 |
| **reversal-consistent** | **530** | **497** |
| **reversal-inconsistent** | **475** | **424** |
| ambiguous — rho and stage endpoints disagree | 0 | 84 |

Both columns ship. The first is the label from the association direction alone;
the second applies the trajectory rule below and is the one Task 6 reads.

### Two separate reasons a row cannot be classified

A relationship fails to earn a reversal label for either of two unrelated
reasons, and each gets its own column rather than being collapsed into one
word:

| flag | meaning | rows |
|---|---|---:|
| `drug_direction_known` = False | the vocabulary records no direction for the action | 3,979 |
| `gene_direction_conflict` = True | the gene's own direction is unresolved or contradictory | 8 |

**All eight gene-conflict rows are also drug-unknown rows** — every one carries
the action `TARGET`, which says a drug binds the gene and nothing about which
way. Describing those eight as "the drug's action is known perfectly well, it
is the gene that cannot be resolved" was wrong on the facts.

**Precedence:** the drug side is tested first, so those eight are `unknown`,
which is also how Task 2 classifies them. The two tables now agree.

`ambiguous` is therefore reserved for the third case, introduced below: a
relationship where the drug direction and the gene direction are both known but
the gene's two statements of direction disagree.

## Trajectory evidence changes the label

Cluster and transition sit on every row, but their presence alone says only
that a trajectory is on file. A rule has to compare them against something.

The reversal label is built on the **association** direction, the sign of rho.
The stage means carry a second and independent statement of which way the gene
moves: the sign of **F4 − F0**. Where they agree, the trajectory supports the
label. Where they disagree, the label rests on rho alone.

| `trajectory_support` | relationships |
|---|---:|
| trajectory supports | 4,601 |
| trajectory contradicts | 364 |
| no trajectory | 19 |

`reversal_class_with_trajectory` applies the rule: of the 364 contradicting
rows, **84 held a reversal label** and are now held at *"ambiguous — rho and
stage endpoints disagree"* instead of being counted as evidence either way.
Task 6's K component reads this column, so the rule changes the ranking rather
than decorating it.

## Evidence level, per edge

All **4,984** drug-target relationships carry per-edge provenance, read from
the recovered OptimusKG fields that Task 2 attaches to every row. Re-running
this script rebuilds them; no separate integration pass is required.

| level | relationships |
|---|---:|
| single-source | 3,957 |
| multi-source | 1,027 |
| with a reference URL | 1,025 |

**`multi-source` means two or more distinct asserting databases**, not two
assertions. `DRUG_BANK:TARGET;DRUG_BANK:TRANSPORTER` is one database speaking
twice and counts as single-source.

`Evidence_Source` names the asserting databases; `mechanisms_of_action` gives a
written mechanism where one exists, which is richer than the single `action`
token. A source count is a count of databases, not a grade of evidence quality:
databases reuse each other's underlying records, and only 1,025 of 4,984 rows
reach a retrievable reference at all.

## FINDING — no subgroup beats its own null once direction is preserved

**The naive baseline is wrong.** 68% of directional drugs *lower* their target,
so by chance alone a **rising** gene is reversal-consistent 67.6% of the time
and a **falling** gene only 32.4%. Comparing any group against 50% would
manufacture a result.

**And the null has to preserve progression direction.** Shuffling group labels
freely moves genes between rising and falling, which are the two populations
with different baselines by construction. A draw that lands extra rising genes
in a group inherits the 67.6% baseline and makes that group look enriched. The
permutation therefore shuffles only the **class** part of the label, and only
among genes sharing a direction, so every draw keeps the group's own baseline.
The question it answers is the one the claim makes: does this class do better
than other classes going the same way?

| group | n | observed | expected from vocabulary | permuted null | perm p | BH-q | survives |
|---|---:|---:|---:|---:|---:|---:|---|
| fibrosis-only / positive | 157 | 89.2% | 67.6% | 66.2% | 0.083 | 0.501 | ✗ |
| inflammation-only / positive | 165 | 61.8% | 67.6% | 65.5% | 0.739 | 0.842 | ✗ |
| shared / positive | 360 | 55.8% | 67.6% | 65.5% | 0.364 | 0.842 | ✗ |
| fibrosis-only / negative | 189 | 29.6% | 32.4% | 26.9% | 0.603 | 0.842 | ✗ |
| shared / negative | 98 | 20.4% | 32.4% | 27.0% | 0.587 | 0.842 | ✗ |
| inflammation-only / negative | 36 | 30.6% | 32.4% | 26.1% | 0.842 | 0.842 | ✗ |

**No group survives.** `fibrosis-only / positive` is the closest at p = 0.083
uncorrected, q = 0.50 across the six groups.

The choice of null is the whole result here. A null that mixes directions puts
this group's baseline at about 53%, against which 89.2% looks decisive; a null
that keeps direction fixed puts it at 66%, which is simply what rising genes
give. Only the second answers the question the group label asks.

### Why 89.2% is still not a finding

Those relationships cover only **32 genes**, and the distribution is top-heavy:

```
PTGS1 31 · CACNA1C 18 · KIT 12 · SCN4A 11 · PDE4D 7 · PDGFRA 7 · ALOX5 5
```

COX-1, an L-type calcium channel, a receptor kinase, a sodium channel, a
phosphodiesterase. These are the target classes pharmacology has spent fifty
years building **inhibitors** for. The group is enriched for genes that happen
to be classic inhibitor targets, and the corrected null absorbs most of that:
once a draw has to use rising genes, 66% consistency is simply what rising
genes give.

PDGFRA appears here with 7 inhibitors. This is the **same** nintedanib
relationship Paper 1 reports, reached through the same OptimusKG edges — it is
internal consistency, not an independent route to the same answer.

### The binomial columns are descriptive only

`binomial_p_descriptive` and `binomial_q_BH_descriptive` treat every
relationship as an independent draw. They are not: 4,984 relationships sit on
1,072 genes and 3,027 drugs, so one well-annotated gene contributes dozens of
correlated rows. BH does not repair that — it controls a family error rate
among tests that are each individually wrong. They are kept because they are
easy to check by hand, and no claim rests on them. `inference_basis` names what
does: the gene-level permutation within progression direction.

## By trajectory cluster

| Cluster | pattern | consistent | inconsistent | unknown |
|---|---|---:|---:|---:|
| C1 | early increase, then continues | 104 | 50 | 566 |
| C2 | late increase (largest F3→F4) | 171 | 116 | 774 |
| C3 | early rise, then plateau | **66** | **10** | 200 |
| C4 | mid decrease | 3 | 48 | 352 |
| C5 | late decrease (largest F3→F4) | 73 | 163 | 1,036 |

The rising clusters (C1–C3) run consistent; the falling ones (C4, C5) run
inconsistent — the same vocabulary asymmetry, now visible along the disease
trajectory. C4 is the starkest: 3 consistent against 48 inconsistent, because
almost nothing in the drug vocabulary *raises* a gene.

## What this table is for, and what it is not

Task 2 established that reversal consistency across **all** these relationships
sits at 52.7% against a 55.9% null, permutation p = 0.553 — indistinguishable
from chance overall, and robust to six different action-to-direction mappings.
Task 7 does not overturn that, and it does not find a subgroup that escapes it
either.

So a `reversal-consistent` label marks a relationship **worth looking at**, not
one that works. The plan says it first, and the repurposing handoff says it
more bluntly: the graph records association direction and timing, it does
**not** establish whether inhibition or activation is beneficial.

## Carried forward to Task 6

1. **No subgroup earns extra weight.** Nothing beats its own direction-
   preserving null, so mechanism consistency enters K as a flat binary fact and
   no group is up-weighted on the strength of a subgroup test.
2. **Never score against a 50% baseline.** The vocabulary's mix makes it 67.6%
   for rising genes and 32.4% for falling ones.
3. **79.8% of relationships have no direction.** A mechanism component applies
   to a fifth of the data and must not silently penalise the rest.
4. **Honour the trajectory rule downstream.** K reads
   `reversal_class_with_trajectory`, so the 84 relationships where rho and the
   stage endpoints disagree do not earn consistency credit.
5. **Internal agreement is not validation.** Where this table and Paper 1 agree
   on a relationship, they are reading the same OptimusKG edges.
