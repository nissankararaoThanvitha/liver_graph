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

| Class | Relationships |
|---|---:|
| unknown | 3,971 |
| **reversal-consistent** | **530** |
| **reversal-inconsistent** | **475** |
| ambiguous | 8 |

`ambiguous` is reserved for the genes whose own direction is contradictory —
Task 1's 30 shared genes that fall with fibrosis and rise with inflammation.
Eight relationships touch them. The drug's action is known perfectly well; it
is the gene that cannot be resolved, which is a different thing from unknown.

## Evidence level — RECOVERED 13 October 2026

The section below was written when the graph was the only source. It is now
superseded: OptimusKG's own file carries the provenance, and all **4,984**
drug-target relationships have a real evidence level.

| level | relationships |
|---|---:|
| single-source | 3,957 |
| multi-source | 1,027 |
| with a reference URL | 1,025 |

`Evidence_Source` names the asserting databases; `mechanisms_of_action` gives a
written mechanism where one exists, which is richer than the single `action`
token.

## The original note, kept for the record

The plan asks to *"preserve the source and evidence level"*. `ACTS_ON` carries
**one** property, `action` — no evidence level, no reference, no assay, no
confidence. `load_knowledge_layer.cypher` sets `r.action = row.rel_type` and
nothing else.

Both columns are emitted with that stated explicitly
(`"not recorded - ACTS_ON carries 'action' only"`) rather than left blank,
because a blank reads as "none found" instead of "never recorded".

## FINDING — one group beats chance, and the baseline is not 50%

**The naive baseline is wrong.** 68% of directional drugs *lower* their target,
so by chance alone a **rising** gene is reversal-consistent 67.6% of the time
and a **falling** gene only 32.4%. Comparing any group against 50% would
manufacture a result.

Against the vocabulary's own mix, and then against a null that shuffles the
gene→group assignment at **gene** level (because edges on one gene are not
independent — the error Task 2 had to correct):

| group | n | observed | expected from vocabulary | gene-permuted null | perm p | survives |
|---|---:|---:|---:|---:|---:|---|
| **fibrosis-only / positive** | 157 | **89.2%** | 67.6% | 53.3% | **0.0010** | ✅ |
| shared / positive | 360 | 55.8% | 67.6% | 53.4% | 0.834 | ✗ |
| inflammation-only / positive | 165 | 61.8% | 67.6% | 53.1% | 0.399 | ✗ |
| fibrosis-only / negative | 189 | 29.6% | 32.4% | 53.4% | 0.029 | ✗ (below) |
| shared / negative | 98 | 20.4% | 32.4% | 53.2% | 0.035 | ✗ (below) |
| inflammation-only / negative | 36 | 30.6% | 32.4% | 56.0% | 0.346 | ✗ |

**Genes that rise with scarring *specifically* — not with inflammation — are
reversal-consistent 89% of the time.** That is the one group where the drugs
that exist point the right way more often than the vocabulary explains, and it
is also the most therapeutically interesting group: fibrosis-specific, rising,
and an inhibitor already exists.

### What it is not

Those 140 relationships cover only **32 genes**, and the distribution is top-heavy:

```
PTGS1 31 · CACNA1C 18 · KIT 12 · SCN4A 11 · PDE4D 7 · PDGFRA 7 · ALOX5 5
```

COX-1, an L-type calcium channel, a receptor kinase, a sodium channel, a
phosphodiesterase. These are the target classes pharmacology has spent fifty
years building **inhibitors** for. The honest reading is that this group is
enriched for genes that happen to be classic inhibitor targets — not that
inhibiting them treats fibrosis.

The gene-level permutation does rule out the simplest version of that objection
(PTGS1's 31 edges move as a block under the null, and the result survives), so
the enrichment is real. What it means biologically is not settled by this
table.

PDGFRA appears here with 7 inhibitors, which is the Nintedanib case from
Paper 1 arriving by an independent route.

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
sits at 52.7% against a 55.9% null, permutation p = 0.78 — indistinguishable
from chance overall, and robust to six different action-to-direction mappings.
Task 7 does not overturn that; it locates the one subgroup where the picture
differs.

So a `reversal-consistent` label marks a relationship **worth looking at**, not
one that works. The plan says it first, and the repurposing handoff says it
more bluntly: the graph records association direction and timing, it does
**not** establish whether inhibition or activation is beneficial.

## Carried forward to Task 6

1. **fibrosis-only / positive is the group to weight**, if mechanism consistency
   enters the TargetScore at all. It is the only one that beats its own null.
2. **Never score against a 50% baseline.** The vocabulary's mix makes it 67.6%
   for rising genes and 32.4% for falling ones.
3. **79.8% of relationships have no direction.** A mechanism component applies
   to a fifth of the data and must not silently penalise the rest.
4. **The signal is concentrated in 32 genes of classic inhibitor-target
   families.** Any weight given to it should be low enough that it cannot drive
   the ranking on its own.
