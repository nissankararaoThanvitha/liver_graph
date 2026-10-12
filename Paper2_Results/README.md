# Paper 2 — Team 2

Drug and therapeutic-target prioritisation, built on Paper 1's
progression-associated molecular evidence. Output folder for Team 2's analyses,
mirroring [`Paper1_Results/`](../Paper1_Results).

Each task has its own folder and a `README.txt` stating method, results and
caveats. Analysis code lives in [`scripts/`](../scripts), following the
convention Paper 1 settled on.

## Progress

| # | Task | Status | Output |
|---|---|---|---|
| 1 | Master progression-gene table | **done** | [`Task1/`](Task1) — 6,222 genes |
| 2 | Drug–gene extraction from the knowledge graph | not started | |
| 3 | Druggability comparison across progression groups | not started | |
| 4 | Drug coverage across progression genes | not started | |
| 5 | MetaPath implementation and testing | not started | |
| 6 | Target-prioritisation framework design | not started | |
| 7 | Drug action / direction evidence table | not started | |
| 8 | Final target and drug ranking | not started | |

## The gene set

The plan was written against **4,692** progression genes. That figure predates
the biopsy-pairing correction of 9–10 October 2026
([`BIOPSY_CORRECTION.md`](../BIOPSY_CORRECTION.md)). The current corrected set
is **6,222**, and that is what Paper 2 uses.

| | genes |
|---|---:|
| fibrosis-associated (fibrosis-only + both) | 3,845 |
| disease-associated (inflammation-only + both) | 4,199 |
| shared (both ladders) | 1,822 |
| **union** | **6,222** |

Verified against the live Neo4j graph on 12 October 2026.

## Standing constraints

- **Do not trim the graph.** Filter at read time, per edge type. The drugs with
  no existing liver indication are the repurposing space.
- **Keep the three progression classes distinct.** Never collapse them into a
  single "progression" category.
- **Paper 1's trajectory, transition, pathway and tier work covers only the
  3,845 fibrosis-associated genes.** The 2,377 inflammation-only genes have
  none of it, so any composite score with those components ranks them last for
  missing data rather than biology. Decide the rule before Task 6.
- **The graph records association direction and timing, not benefit.** It does
  not establish whether inhibiting or activating a gene helps.
- **Outputs are therapeutic hypotheses**, not proven anti-fibrotic treatments.
