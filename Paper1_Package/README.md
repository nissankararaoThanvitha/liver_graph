# Paper 1 — complete working package

Everything behind this paper in one folder: the data, every step applied to
it, every result, every statistic, every figure and table, and the limits of
each. Nothing here depends on the machine it was built on or on access to a
database.

**You should be able to write the manuscript from this folder alone, and
check any number in it without asking us anything.**

---

## The work in three sentences

Eight public human liver transcriptome studies — **1,085 biopsies from 1,027
patients** — were harmonised onto one gene namespace and two clinical
severity ladders, then integrated with curated biological knowledge. Genes
whose expression tracks severity were identified **within each study and then
combined**, never by pooling patients, giving **5,884 progression-associated
genes** of which **3,681 track fibrosis**. Those genes were grouped, their
stage trajectories clustered, every stage transition tested at patient level,
their biology enriched, and the fibrosis set ranked by how many independent
kinds of evidence agree — ending at **525 high-confidence genes** and a
prioritised **25**.

---

## Reading order

Read these four in order. It takes about forty minutes, and afterwards
nothing in the folder is mysterious.

| | File | What it gives you |
|---|---|---|
| 1 | `00_START_HERE/01_OVERVIEW.md` | The aim, the cohort, what was produced, where everything lives |
| 2 | `00_START_HERE/02_METHODS.md` | **The main document.** Every stage: what was done, why, and what it produced |
| 3 | `00_START_HERE/03_STATISTICS.md` | Every statistical test: what was tested, n, the correction, the threshold |
| 4 | `00_START_HERE/04_LIMITATIONS.md` | What the results do and do not support. **Read before writing any claim** |

Then as needed:

| File | What it gives you |
|---|---|
| `00_START_HERE/05_HOW_TO_VERIFY.md` | How to re-check any number, and how to re-run any stage |
| `00_START_HERE/06_FILE_MANIFEST.csv` | Every file with size and SHA-256 |

---

## What is in the folder

```
00_START_HERE/      the documents above, plus the file manifest
01_FIGURES/         main/ Figures 1-9, supplementary/ S1-S21,
                    300 dpi PNG, with FIGURE_CAPTIONS.md
02_TABLES/          main/ Tables 1-6, supplementary/ S1-S19,
                    with TABLE_CAPTIONS.md
03_RESULTS/         the five analyses in full, each with its own README
04_DATA/            every derived table needed to check or redo any
                    analysis, plus DATA_DICTIONARY.md
05_CODE/            all scripts in pipeline order, plus CODE_MAP.md and
                    requirements.txt with versions pinned
06_PROVENANCE/      where each dataset came from, and how to rebuild what
                    is too large to ship
```

## Writing the manuscript from here

1. **Captions are written** — `01_FIGURES/FIGURE_CAPTIONS.md` and
   `02_TABLES/TABLE_CAPTIONS.md`. Paste and edit.
2. **Methods** come from `02_METHODS.md` (what was done) and
   `03_STATISTICS.md` (the tests, in the detail a Methods section needs).
3. **Results numbers** come from `02_TABLES/main/` and the `README.txt` in
   each `03_RESULTS/` folder.
4. **Before writing any claim, check `04_LIMITATIONS.md`.** Several results
   are narrower than they first appear, and two validation measures cannot
   fail by construction — they are marked.

## Three conventions to keep

**Say "increasing / decreasing with fibrosis stage", not "upregulated /
downregulated".** Up- and downregulated denote a two-group differential
expression comparison. This work measured correlation along an ordered stage
ladder, which is a different quantity arrived at by a different test. Every
table carries a `Direction` column with the wording to use.

**Values are `value_z`** — expression standardised per gene within each
study. That standardisation is what makes eight cohorts comparable; raw
values are not comparable across studies and are not used anywhere.

**The enrichment background is the 14,794 eligible genes**, not the whole
genome. This is the methodological point a reviewer is most likely to probe,
and the answer is that the background is the tested universe.

---

Built by `05_CODE/build_paper1_package.py` from the committed analysis
outputs. Re-running that script rebuilds this folder from scratch, so it
cannot silently go stale.
