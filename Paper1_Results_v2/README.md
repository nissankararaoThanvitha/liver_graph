# Paper 1 results — v2

A clean re-run of every analysis after three problems were found in the
inputs. **`Paper1_Results/` is untouched and remains the "before".** Nothing
in this folder overwrites it, so the two can be compared at every step.

## Why there is a v2

| | What was wrong | What changed |
|---|---|---|
| 1 | **Repeat biopsies were averaged across different stages.** 58 GSE193066 patients were biopsied twice; for 30 of them the stage moved between biopsies, so an averaged profile carried a label naming only one of the two stages. | First biopsy only. `find_progression_genes.py --repeat-policy first` |
| 2 | **112 GSE162694 samples were labelled NASH on no evidence.** GEO records only tissue, age, sex, fibrosis stage and NAS score for that study — no diagnosis at all. The code read the `_F0`–`_F4` suffix, which is a *fibrosis stage*, and called every one of them NASH. 35 of them sit at F0, with no scarring. | Relabelled **NAFLD**, which is what the source paper calls them and is true of all 112. They no longer sit on the control→NAFL→NASH ladder, because nobody knows which rung they belong on. |
| 3 | **The live Neo4j graph is missing 40,247 links** across five relationship types. | Documented. Affects no result — every analysis reads CSVs. |

Problem 2's original justification was circular: the labels were said to be
"cross-checked against `fibrosis_stage_raw` for all 143 samples". The suffix
*is* the fibrosis stage, so that check only ever confirmed `_F3` means stage
3. It never tested the diagnosis.

## What this did to the gene counts

| | v1 | v2 |
|---|---|---|
| **Fibrosis-associated** | 3,645 | **3,681** |
| fibrosis_only | 1,953 | 1,866 |
| inflammation_only | 1,047 | 2,203 |
| shared | 1,692 | 1,815 |
| **Total progression genes** | 4,692 | **5,884** |

**The headline set barely moved**, and more importantly it is stable: the
3,681 came out *identical* before and after fix 2 — the same genes, not just
the same count. Fibrosis stages were never in question, so nothing that
depends only on them changed.

**The split inside it did move.** 426 genes crossed between fibrosis_only
and shared, because that line is drawn by the disease test and the disease
test changed.

**Read the inflammation_only jump carefully.** It did not get stronger. The
disease ladder lost a study, so a gene now needs 3 studies to agree instead
of 4 — a lower bar on 221 patients instead of 364. More genes pass a weaker
test.

## `00_progression_genes/`

The inputs this entire re-run is built on.

| File | Rows | What |
|---|---|---|
| `progression_fibrosis.csv` | 14,794 | every gene tested against fibrosis stage, pass or fail |
| `progression_disease.csv` | 14,784 | the same against the disease ladder |
| `progression_both.csv` | 5,755 | genes significant on at least one ladder |
| `genes_by_fibrosis_stage.csv` | 5,884 | the progression genes with their mean expression at F0–F4 |
| `genes_by_disease_group.csv` | 5,884 | the same by disease group |
| `sample_demographics.csv` | 1,085 | one row per sample, with the corrected labels |

A gene counts as significant when **q < 0.05 and every study that tested it
agrees on the direction of change**. Both conditions, always.

## What the cohort actually supports

- **Fibrosis ladder — 668 samples, 5 studies.** The strong half. This is what
  the 3,681 genes rest on.
- **Disease ladder — 221 patients, 3 studies.** Weaker, and a third of it
  (GSE130970) uses labels derived from histology rather than stated by the
  study.
- **The two ladders overlap in one study, 78 samples.** So "shared" means a
  gene passed two tests run on largely different people — not that it was
  shown to track both things in the same patients.
- **F0 is not a control group.** Of 152 F0 samples, 46 are healthy controls,
  73 have fatty liver without scarring, and 5 have NASH without scarring.

## Still to come in this folder

Task 1 through Task 4, then the evidence scoring, the leave-one-study-out
validation and the gene shortlist — each with a comparison against its v1
counterpart.
