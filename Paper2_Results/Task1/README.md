# Task 1 — Master progression-gene table

Plan: *"Create the Paper-2 master progression-gene table. Start with all
progression-associated genes… Do not remove genes simply because they are not
already known drug targets."*

Nothing is filtered. All 6,222 progression genes are carried through.

Built by `scripts/paper2_task1_master_table.py` from
`Paper1_HighConfidence/00_all_progression_genes.csv`.

## Files

| File | Rows | What it is |
|---|---:|---|
| `Paper2_progression_genes.csv` | 6,222 | the master table |
| `task1_class_summary.csv` | 4 | counts per class, direction split per ladder |
| `task1_supporting.xlsx` | 4 sheets | `discordant_shared_genes` (30) · `discordant_vs_concordant` (2) · `stage_mean_verification` (40) · `stage_mean_check` (5) |
| `task1_class_composition.png` | — | classes and direction, per ladder |

## The gene count differs from the plan

The plan says 4,692. That predates the biopsy-pairing correction of 9–10
October 2026 (`BIOPSY_CORRECTION.md`), after which repeat biopsies are averaged
only when the fibrosis stage matches and biopsy 1 is retained otherwise. The
corrected union is **6,222**.

| | genes |
|---|---:|
| fibrosis-associated (fibrosis-only + both) | 3,845 |
| disease-associated (inflammation-only + both) | 4,199 |
| shared (both ladders) | 1,822 |
| **union** | **6,222** |

The script asserts every one of these and fails rather than writing a table
that disagrees with Paper 1.

> **Confirmed, 12 October 2026.** Substituting 6,222 for the plan's 4,692 was
> initially a judgement made here rather than an instruction. It has since been
> confirmed by the researcher, so Paper 2 uses 6,222 throughout and Task 6 can
> freeze weights against it. The plan's 4,692 is superseded, not ignored: it
> predates the biopsy-pairing correction and no longer describes any committed
> gene set.

## Class summary

Counted **per ladder**. A gene has a direction on each ladder it belongs to,
not one direction overall, so merging them would double-count.

| class | genes | % | fib ↑ | fib ↓ | infl ↑ | infl ↓ |
|---|---:|---:|---:|---:|---:|---:|
| fibrosis-only | 2,023 | 32.5 | 1,040 | 983 | — | — |
| inflammation-only | 2,377 | 38.2 | — | — | 2,042 | 335 |
| both | 1,822 | 29.3 | 1,408 | 414 | 1,438 | 384 |
| **union** | **6,222** | 100 | 2,448 | 1,397 | 3,480 | 719 |

Every column now sums to its own n: 1,040 + 983 = 2,023; 1,408 + 414 = 1,822;
2,448 + 1,397 = 3,845; 3,480 + 719 = 4,199.

The inflammation ladder is strongly skewed towards increases (3,480 vs 719);
fibrosis is closer to balanced (2,448 vs 1,397).

> **Corrected.** An earlier version counted a gene as increasing if *either*
> ladder said so, which made the shared row sum to 1,852 against 1,822 genes —
> the 30 contradictory genes fell into both columns.

## Verification — gene by gene, not count by count

Matching totals prove little: two sets of 6,222 genes can agree on size and
disagree on membership. Two scripts, both run 12 October 2026 against instance
**LiverDiseaseDB** (`dbms-1c965ecc-…`), database `neo4j`.

### `paper2_task1_verify_against_neo4j.py`

| Check | Result |
|---|---|
| gene **set** identical | 6,222, symmetric difference empty |
| `progression_class` vs the TRACKS edges | 6,222 agree |
| fibrosis rho / q / n_studies / direction | 3,845 agree, max diff 5.0e-05 |
| inflammation rho / q / n_studies / direction | 4,199 agree, max diff 5.0e-05 |
| gene symbols | 6,222 exact |

The 5e-05 residual is the CSV's four-decimal rounding. Direction is spelled
`rises`/`falls` in the graph and `increasing`/`decreasing` in Paper 1's CSVs;
that vocabulary difference is mapped before comparison.

### `paper2_task1_verify_stage_means.py`

The first script checked ten of sixteen columns and reported "reproduces the
live graph exactly" — true of what it checked, and silently untrue of **F0–F4**,
which it never compared. Gene nodes do not carry stage means, so they have to
be recomputed from `EXPRESSES` under the biopsy policy:

> same stage on every biopsy → average them · stages differ → keep biopsy 1

Recomputed for 40 genes stratified across the rho range:

| stage | genes | max abs diff |
|---|---:|---:|
| F0 | 40 | 0.000487 |
| F1 | 40 | 0.000479 |
| F2 | 40 | 0.000482 |
| F3 | 40 | 0.000489 |
| F4 | 40 | 0.000491 |

All within the four-decimal tolerance. The reconstruction independently lands
on **610 independent staged patients**, exactly the figure CLAUDE.md states —
580 patients consistent across biopsies, 30 with differing stages where biopsy
1 is kept, 30 samples discarded.

**PASS on both.**

## The 30 contradictory genes — and what they actually are

Paper 1 Task 1 reported **one** shared gene whose ladders point opposite ways
(GPD1). On the corrected data there are **thirty**, all decreasing with
fibrosis and increasing with inflammation. GPD1 is still among them.

Reported alone that looks like a finding. It is not:

| | genes | median \|fib rho\| | median \|infl rho\| | median fib q | median infl q |
|---|---:|---:|---:|---:|---:|
| **discordant** | 30 | **0.152** | **0.217** | **4.3e-03** | **6.0e-03** |
| concordant | 1,792 | 0.261 | 0.304 | 6.0e-09 | 1.4e-05 |

The discordant genes have roughly **half the effect size** and q-values **five
to six orders of magnitude weaker**. They sit just inside the significance
threshold on both ladders, which is exactly where a direction call is least
stable. The likeliest reading is borderline calls, not opposing biology —
helped by the disease axis resting on 216 patients from three studies against
610 for fibrosis.

Still carried forward: they cannot be given one direction, so Task 7 needs an
explicit rule if directional annotations are ever added for them. In Task 2
they did not bite — only 7 of the 30 have any drug edge and none is directional.

## Why the blank cells are not missing data

2,377 rows have no `fibrosis_rho` and 2,023 have no `inflammation_rho`. That is
what the class labels mean. These are structural blanks, must not be imputed,
and must not be read as measurement failure. F0–F4 are present for all 6,222.

## Carried warning for Task 6

Paper 1's trajectory, transition, pathway and tier work covers only the 3,845
fibrosis-associated genes. The 2,377 inflammation-only genes have none of it, so
a TargetScore with a trajectory (T) or pathway (B) component ranks them last
for **missing data, not biology** — while the plan requires the three classes
stay distinct. Decide the rule before Task 6 computes anything: normalise within
class, or score the classes separately.

`in_fibrosis_starting_set` is on every row so the affected genes stay findable.

## Columns

`Gene`, `Ensembl_ID`, `progression_class`, `fibrosis_rho`, `fibrosis_q_FDR`,
`fibrosis_direction`, `fibrosis_n_studies`, `inflammation_rho`,
`inflammation_q_FDR`, `inflammation_direction`, `inflammation_n_studies`,
`F0`–`F4`, `in_fibrosis_starting_set`.

## Not done here, on purpose

Trajectory cluster, stage-transition results and tier are not merged in. The
plan stages them as later refinement, and merging now would make the 2,377
inflammation-only genes look as though they failed a test they were never
eligible for. They are in `Paper1_HighConfidence/11_final_all_3845_genes.csv`,
joinable on `Ensembl_ID`.
