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
6,222. **Confirmed by the researcher on 12 October 2026: Paper 2 uses 6,222
throughout.** The plan's 4,692 no longer describes any committed gene set.

## Scope decision, 13 October 2026

The mentor's instruction: **"Repurposing not reversal"** and **"Focus only on
the knowledge graph."**

The Paper 2 plan put a transcriptomic drug-reversal analysis (LINCS / CMap)
before the final ranking, as an independent evidence layer. That is now **out
of scope**. Paper 2's evidence comes from the knowledge graph and Paper 1's
own results, and nothing else.

What this changes:

- **Task 8 is unblocked.** It was waiting only on the reversal layer.
- **The final evidence chain is six layers, not seven:** progression evidence,
  fibrosis specificity, F0-F4 trajectory, pathway/process context,
  knowledge-graph relationships, drug-target mechanism. The reversal layer is
  recorded as a stated limitation, not a gap to fill.
- **External resources stay out.** That includes ChEMBL molecule metadata, so
  the 648 drugs whose only name is an accession can be flagged but not
  resolved. Task 4 flags them; they cannot be filtered properly without data
  this project is not bringing in.

Note on wording: "reversal" here means the *transcriptomic* reversal analysis.
Task 7's `reversal-consistent` classification is a different thing -- it
compares a drug's recorded action with Paper 1's direction of travel, entirely
inside the knowledge graph -- and is retained.

Use Task1 for the master gene table. Analysis code is in
[`scripts/`](../scripts), following the convention Paper 1 settled on.
`00_FILE_MANIFEST.csv` carries path, bytes and sha256 for every file here.

## Tasks

| # | Task | Status | Output |
|---|---|---|---|
| 1 | Master progression-gene table | **done** | [`Task1/`](Task1) — 6,222 genes, verified against the graph |
| 2 | Drug-gene extraction from the knowledge graph | **done** | [`Task2/`](Task2) — 8,948 edges, 1,072 genes, 3,027 drugs |
| 3 | Druggability comparison across progression groups | **done** | [`Task3/`](Task3) — direction beats class; decreasing genes more druggable |
| 4 | Drug coverage across progression genes | **done** | [`Task4/`](Task4) — coverage vs coherence; 726 entities flagged |
| 5 | MetaPath implementation and testing | **done** | [`Task5/`](Task5) — 7 metapaths; Reactome 11× cleaner than GO; DWPC vs count ρ = 0.45 |
| 6 | Target-prioritisation framework design | **done** | [`Task6/`](Task6) — 5 components defined; F redundant within class; top-50 unstable |
| 7 | Drug action / direction evidence table | **done** | [`Task7/`](Task7) — 4,984 relationships; fibrosis-only rising genes 89% consistent |
| 8 | Final target and drug ranking | **done** | [`Task8/`](Task8) — band 1 is two genes: PDGFRA and CACNA1C |

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
