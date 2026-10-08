# About this folder — read before using the draft

`Paper1_draft_v1.docx` is an **earlier draft, kept as reference only.** It is
not the current state of the work and it is not a draft you should continue
from without reading this note.

## What it contains

Title block, Abstract, Introduction, Results 2.1–2.5, Methods 5.1–5.14,
Limitations, and placeholders. Line numbering is on, which makes commenting
easier.

Discussion, Conclusion and References are **deliberately empty**, marked as
placeholders. The supervisor said she would write Discussion and Conclusion
herself. Citation markers in the text read `[REF]` and mark the four places a
reference is needed: disease burden and transplantation; fibrosis stage as the
dominant prognostic feature; biopsy sampling variability and inter-observer
agreement; and biomedical knowledge graphs.

## What it is missing — the important part

**It covers stages 9–13 only. The entire stage 14 work is absent:** the five
evidence scores, the 507 Tier 1 genes, the prioritised 25, the
leave-one-study-out validation, and the mechanism subgraph (Figure 9). That
work is confirmed as part of Paper 1, so the draft is incomplete on a whole
section.

Consequences if you use it as a starting point:

- Its figures are numbered 1–8. Figure 9 in this package has no place in it
  yet. The numbering in `01_FIGURES/FIGURE_CAPTIONS.md` is authoritative.
- Its tables run to Table 4. This package numbers tables 1–6, and Table 1
  (the cohort table) does not exist in the draft at all.
- Its Limitations section lists four limitations. `05_LIMITATIONS.md` lists
  fifteen, several of which are substantive.
- It says nothing about the knowledge-layer provenance problem documented in
  `05_LIMITATIONS.md` §14.

## How to use it

**As a source of phrasing, not as a current draft.** The Methods sections
5.1–5.13 are accurate for the stages they cover and are worth reading before
writing your own. The Abstract and Introduction are serviceable but predate
stage 14 and under-sell the work.

**Write the manuscript from `00_START_HERE/` instead**, using this draft for
wording where it helps:

- what was done → `02_STAGE_BY_STAGE.md`
- the statistics for the Methods → `03_STATISTICS.md`
- justifications for method choices → `04_DECISIONS.md`
- the Limitations section → `05_LIMITATIONS.md`
- captions → `01_FIGURES/FIGURE_CAPTIONS.md`, `02_TABLES/TABLE_CAPTIONS.md`

## `make_manuscript.py`

The script that generated the draft. Every number in its Results comes from
the committed outputs rather than from memory, so the draft cannot silently
drift from the analysis. If you extend the draft, extending this script keeps
that property; editing the `.docx` directly loses it.

## `QUESTION_FOR_MENTOR.md`

The question that was put to the supervisor about how to choose the final
shortlist, with three options and the evidence for each. **It has been
answered** — option A, the top five Tier 1 genes per trajectory cluster, is
what was implemented and what `Table6_prioritised_25_genes.csv` holds. The
document is kept because it records the reasoning and the alternatives, which
belongs in the Methods justification for that choice.
