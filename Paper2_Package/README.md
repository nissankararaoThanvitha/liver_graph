# Paper 2 research package

Drug and therapeutic-target prioritisation, built on Paper 1's
progression-associated molecular evidence. All eight planned tasks complete,
13 October 2026.

Built on Paper 1's final combined version of 10 October 2026: eight human liver
transcriptome studies, 1,085 samples from 1,027 patients, **610 independent
staged patients** on the fibrosis axis and **216 from three studies** on the
disease-group axis.

Starting set: **2,023 fibrosis-only**, **2,377 inflammation-only**, **1,822
shared**, **6,222 union**. Paper 1 contributes 447 Tier-1 genes and a balanced
23-gene shortlist as a prioritisation layer.

## The result in three lines

Thirty leading candidates reach **two** targets: **PDGFRA** (8 kinase
inhibitors, including nintedanib, already approved for lung fibrosis) and
**CACNA1C** (22 calcium-channel blockers). PDGFRA is Paper 1's only 9/9 gene
and is reached independently by three routes. The candidate list is less
diverse than thirty names suggests, and says so.

**These are therapeutic hypotheses, not treatments.** Nothing here has been
tested in a cell. The graph records which direction a gene moves and when; it
does not establish that reversing it helps.

## Read in this order

| | |
|---|---|
| `00_START_HERE/01_OVERVIEW.md` | what was asked, what came back |
| `00_START_HERE/02_METHODS.md` | how each task was run, and the choices behind it |
| `00_START_HERE/03_STATISTICS.md` | every inferential claim, with its test — and the tests that were wrong first |
| `00_START_HERE/04_LIMITATIONS.md` | **read before drafting** |
| `00_START_HERE/05_HOW_TO_VERIFY.md` | how to re-derive every number |
| `00_START_HERE/06_FILE_MANIFEST.csv` | path, bytes, SHA-256 for every file here |

## Contents

| Folder | What is in it |
|---|---|
| `01_FIGURES/` | main and supplementary figures, with captions |
| `02_TABLES/` | the tables a manuscript would cite, with captions |
| `03_RESULTS/` | all eight tasks entire, plus the two recoveries, each with its own README |
| `05_CODE/` | pipeline, analysis, validation, recovery and figure scripts |
| `06_PROVENANCE/` | the biopsy correction and the project context file |

### The two recoveries

`03_RESULTS/` carries two folders that are not numbered tasks. They are the two
data-recovery jobs asked for on 13 October, and they are **deliberately kept
separate** — separate scripts, separate source directories, separate reports,
and a `*_source` column on every recovered field in the delivered tables.

| | source | what it added |
|---|---|---|
| `Recovery1_OptimusKG/` | OptimusKG's own discarded fields | per-edge provenance on all 8,948 edges; SMILES, molecule type and clinical phase for the graph's 12,025 drugs |
| `Recovery2_ChEMBL/` | the ChEMBL API, external | 25 field values across 2,404 drugs; **no structures, no result changed** |

Recovery 1 re-read the source the graph was already built from. Recovery 2 left
the knowledge graph. Pooling them would have hidden which source carried which
field, so neither folder cites the other's totals.

Each task's own README in `03_RESULTS/` states its method, its result and its
caveats, and is the authority for that task. These documents summarise; they do
not replace.

## Four things a reviewer will probably ask

**Was there independent validation?** No. The plan asked for it; it needs data
outside the knowledge graph, which the 13 October scope excludes. This is the
largest limitation.

**Is the ranking robust?** The ordering is; an exact top-N is not. Only 29–32
of a top-50 survive a random reweighting. Use bands or
`task6_stable_core.csv`.

**Does drug mechanism support the candidates?** Overall, no better than chance
— 52.7% against a 55.9% null, p = 0.78, stable across six classification
schemes. One subgroup beats its null, on 32 genes.

**Why only two targets?** Because that is what the evidence supports. Saying so
is more useful than a longer list that does not.

**Did anything come from outside the knowledge graph?** One thing, and it
changed nothing. Recovery 1 re-read OptimusKG's own discarded fields — the same
source the graph was built from. Recovery 2 queried ChEMBL, which is genuinely
external, and its entire contribution to the delivered analysis is 25 field
values across 2,404 drugs, no chemical structures, and no result altered.
Deleting `Recovery2_ChEMBL/` would leave every number in this package intact.

## A note on errors

Several analyses in this package were wrong on a first attempt: an invalid
significance test, a labelling bug that dropped 1,792 genes from a table, a
tie-break that reintroduced the promiscuity bias two tasks had measured, and a
sampling error that overstated what an external database would contribute.
Each is recorded with its correction rather than quietly fixed, in
`03_STATISTICS.md` and the task READMEs. A reader who met an earlier figure
elsewhere needs to know which to trust and why.
