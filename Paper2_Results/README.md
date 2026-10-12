# Current Paper2 results

Built on the final combined Paper 1 version of 10 October 2026. Eight human
liver transcriptome studies contain 1,085 samples from 1,027 patient IDs.
Fibrosis analysis uses 610 independent staged patients; the disease-group axis
uses 216 patients from three studies.

Progression genes: **2,023 fibrosis-only**, **2,377 inflammation-only**,
**1,822 shared**, **6,222 union**. The fibrosis-associated set is 3,845 and the
disease-associated set 4,199. Tier1 has 447 genes, with 23 shortlisted.

The Paper 2 plan was written against 4,692 progression genes. That figure
predates the biopsy-pairing correction of 9-10 October
([`BIOPSY_CORRECTION.md`](../BIOPSY_CORRECTION.md)); the corrected union is
6,222 and that is what Paper 2 uses throughout.

Use Task1 for the master gene table. Analysis code is in
[`scripts/`](../scripts), following the convention Paper 1 settled on.
`00_FILE_MANIFEST.csv` carries path, bytes and sha256 for every file here.

## Tasks

| # | Task | Status | Output |
|---|---|---|---|
| 1 | Master progression-gene table | **done** | [`Task1/`](Task1) — 6,222 genes, verified against the graph |
| 2 | Drug-gene extraction from the knowledge graph | **done** | [`Task2/`](Task2) — 8,948 edges, 1,072 genes, 3,027 drugs |
| 3 | Druggability comparison across progression groups | not started | |
| 4 | Drug coverage across progression genes | not started | |
| 5 | MetaPath implementation and testing | not started | |
| 6 | Target-prioritisation framework design | not started | |
| 7 | Drug action / direction evidence table | not started | |
| 8 | Final target and drug ranking | not started | |

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

## Graph

Instance **LiverDiseaseDB** (`dbms-1c965ecc-01bb-470f-86fa-237c81d9d40d`),
database `neo4j`, Neo4j 2026.09.0 Enterprise. This is a different instance from
the one used before 12 October; the earlier one no longer exists. Re-verify
with:

```bash
uv run --with neo4j --with pandas python scripts/paper2_task1_verify_against_neo4j.py
```
