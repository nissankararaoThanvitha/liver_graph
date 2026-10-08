# Paper 1 — complete working package

Everything behind this paper, in one folder: the data as it arrived, every
step applied to it, every result, every statistic, every figure and table, and
the reasoning and limits of each. Nothing here depends on the machine it was
built on or on access to the original database.

**You should be able to write the manuscript from this folder alone, and
check any number in it without asking us anything.**

---

## What the project did, in three sentences

Eight public human liver transcriptome studies (1,085 biopsies from 1,027
patients) were harmonised onto one gene namespace and two clinical severity
ladders, then loaded into a knowledge graph alongside curated biology. Genes
whose expression tracks severity were identified **per study and then
combined**, never by pooling patients, giving 4,692 progression-associated
genes. Those genes were then grouped, their stage trajectories clustered,
every stage transition tested at patient level, their biology enriched, and
the fibrosis set re-ranked by how many independent kinds of evidence agree —
ending at 507 high-confidence genes and a prioritised 25.

---

## Reading order

Read these four in order. It takes about forty minutes and after it nothing
in the folder is mysterious.

| | File | What it gives you |
|---|---|---|
| 1 | `00_START_HERE/01_OVERVIEW.md` | The aim, the data, what was produced, where everything lives |
| 2 | `00_START_HERE/02_STAGE_BY_STAGE.md` | **The main document.** All fourteen stages: what we did, why, how, inputs, outputs, key numbers |
| 3 | `00_START_HERE/03_STATISTICS.md` | Every statistical test in the project: what was tested, n, the correction, the threshold, the result |
| 4 | `00_START_HERE/05_LIMITATIONS.md` | Every limit, stated plainly. Read before writing any claim |

Then, as needed:

| File | What it gives you |
|---|---|
| `00_START_HERE/04_DECISIONS.md` | The non-obvious choices and the evidence for each — settled, not open |
| `00_START_HERE/06_HOW_TO_VERIFY.md` | How to re-check any number, and how to re-run any stage |
| `00_START_HERE/07_FILE_MANIFEST.csv` | Every file with size and SHA-256, for checking the copy is intact |

---

## What is in the folder

```
00_START_HERE/     the six documents above, plus the file manifest
01_FIGURES/        main/ Figures 1-9, supplementary/ Figures S1-S20,
                   all 300 dpi PNG, plus FIGURE_CAPTIONS.md
02_TABLES/         main/ Tables 1-6, supplementary/ Tables S1-S17,
                   plus TABLE_CAPTIONS.md
03_RESULTS/        the five analyses in full, each with its own README.txt
                   recording method, thresholds and caveats
04_DATA/           every derived table needed to redo or check any analysis,
                   plus DATA_DICTIONARY.md
05_CODE/           all scripts in pipeline order, plus CODE_MAP.md and
                   requirements.txt with versions pinned
06_PROVENANCE/     where each dataset came from, and how to rebuild what is
                   too large to ship
07_REFERENCE_DRAFT/ an earlier draft of the paper, as reference only — see
                   its NOTE.md before using it
08_SESSION_HISTORY/ the working sessions in which the decisions were argued out
```

## Writing the manuscript from here

1. Captions are already written: `01_FIGURES/FIGURE_CAPTIONS.md` and
   `02_TABLES/TABLE_CAPTIONS.md`. Paste and edit.
2. Methods come from `00_START_HERE/02_STAGE_BY_STAGE.md` (what was done) and
   `03_STATISTICS.md` (the tests, in the detail a methods section needs).
3. Results numbers come from `02_TABLES/main/` and the `README.txt` in each
   `03_RESULTS/` folder. Those READMEs are the authoritative record of what
   each analysis did and what it does not support.
4. Before writing any claim, check it against `05_LIMITATIONS.md`. Several
   results are narrower than they first appear, and two are structurally
   unable to fail — they are marked.
5. `07_REFERENCE_DRAFT/` holds an earlier draft covering stages 9–13 only.
   It predates the stage 14 prioritisation work entirely. Read its
   `NOTE.md` first; treat it as a source of phrasing, not as a current
   draft.

## Two conventions to keep

**Say "increasing / decreasing with fibrosis stage", not "upregulated /
downregulated".** Up- and downregulated denote a two-group differential
expression comparison. This project measured correlation along an ordered
stage ladder, which is a different quantity. Every table carries a
`Direction` or `direction` column with the wording to use.

**Values are `value_z` unless stated otherwise** — expression standardised
per gene within each study. That standardisation is what makes eight cohorts
comparable; raw values are not comparable across studies and are not used.

---

## One thing that needs a decision, not just reading

`05_LIMITATIONS.md` §14 documents a provenance inconsistency in Figure 9: it
was built from the superseded PrimeKG knowledge layer rather than the
OptimusKG layer the graph actually holds. The fix is a path change and a
re-run, and both layers ship here so it can be done. **Resolve it before
submission**, and do not describe Figure 9 as coming from the project graph
until it is done.

---

Built by `05_CODE/build_paper1_package.py` from the committed analysis
outputs. Re-running that script rebuilds this folder from scratch, so it
cannot silently go stale.
