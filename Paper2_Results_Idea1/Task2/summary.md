# Paper 2 — Task 2: drug–gene relationships

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **6,222 genes** from Task 1.

**Source used:** Neo4j (live liver_kg, read-only). Query: `MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE g.ensembl_id IN $ids` (read-only).
Script: `Paper2_Results_Idea1/code/task2_drug_gene_edges.py`. Output: `drug_gene_edges.csv` (8,948 rows).

## Cross-check: Neo4j vs. CSV export

| Check | Result |
|---|---|
| Edges from source | 8,948 |
| Edges in edges_drug_gene.csv (same genes) | 8,948 |
| Counts match | YES |
| Identical drug–gene–action triples | YES |
| Duplicate drug–gene pairs | 0 |

## Headline numbers

| Measure | Value |
|---|---|
| Progression genes with ≥1 drug | 1,072 / 6,222 (17.2%) |
| Unique drugs | 3,027 (1,423 approved) |
| Total drug–gene relationships | 8,948 |
| Relationships with known direction (down/up) | 1,001 (11.2%) |
| …comparable with Paper 1 gene direction | 1,001 (11.2%) |
| …comparable with an F0–F4 trajectory cluster | 800 (8.9%) |
| 23-gene shortlist genes with ≥1 drug | 17 / 23 |

"Comparable" means the drug pushes the gene down or up **and** Paper 1 gives the gene a direction (fibrosis direction; inflammation direction for inflammation-only genes) or a trajectory cluster. Whether each comparison is direction-consistent is Task 7. A comparable relationship is a check of mechanism consistency, not proof that a drug would help (repurposing hypothesis only).

## Drug action direction

| Direction | Edges | % | Raw actions included |
|---|---|---|---|
| down | 679 | 7.6% | ALLOSTERIC_ANTAGONIST, ANTAGONIST, BLOCKER, DEGRADER, INHIBITOR, INVERSE_AGONIST, NEGATIVE_ALLOSTERIC_MODULATOR, NEGATIVE_MODULATOR |
| up | 322 | 3.6% | ACTIVATOR, AGONIST, OPENER, PARTIAL_AGONIST, POSITIVE_ALLOSTERIC_MODULATOR, POSITIVE_MODULATOR, STABILISER |
| mixed | 28 | 0.3% | BINDING_AGENT, MODULATOR, RELEASING_AGENT, SUBSTRATE; or sources disagree (down vs up) |
| unknown | 7,919 | 88.5% | CARRIER, ENZYME, TARGET, TRANSPORTER |

Raw action counts: TARGET 3,958, ENZYME 2,241, TRANSPORTER 1,225, CARRIER 495, INHIBITOR 470, AGONIST 216, ANTAGONIST 135, POSITIVE_ALLOSTERIC_MODULATOR 68, BLOCKER 62, MODULATOR 19, STABILISER 16, POSITIVE_MODULATOR 12, NEGATIVE_ALLOSTERIC_MODULATOR 5, RELEASING_AGENT 4, PARTIAL_AGONIST 4, ACTIVATOR 3, OPENER 3, SUBSTRATE 3, BINDING_AGENT 2, DEGRADER 2, ALLOSTERIC_ANTAGONIST 2, INVERSE_AGONIST 2, NEGATIVE_MODULATOR 1.
Edges flagged `relation_conflict` by OptimusKG: 0.

## By progression class

| Class | Genes | Genes with drug | % | Unique drugs | Edges |
|---|---|---|---|---|---|
| fibrosis_only | 2,023 | 358 | 17.7% | 1,794 | 3,727 |
| shared | 1,822 | 359 | 19.7% | 1,761 | 3,344 |
| inflammation_only | 2,377 | 355 | 14.9% | 1,202 | 1,877 |

(Statistics comparing these groups are Task 3.)

## Evidence level

| Evidence level | Edges |
|---|---|
| single-source | 7,855 |
| multi-source | 1,093 |

## What the source does and does not contain (honest notes)

- **Present on every Neo4j edge:** consolidated action, per-source assertions (`relation_assertions`), contributing sources (`sources_direct`: DrugBank, Open Targets, etc.), number of sources, evidence level (single-/multi-source), conflict flag.
- **Present only on some edges:** mechanism-of-action text, literature URLs (PubMed/Europe PMC), indirect sources.
- **Not available:** a per-source record or accession ID for each assertion. `Database_ID` is therefore the stable pair `ChEMBL drug ID | Ensembl gene ID`. There is also no quantitative affinity/potency, and no dose or tissue context.
- The CSV export (`edges_drug_gene.csv`) keeps only drug, gene and action; its `score` column is empty for drug–gene edges. The extra evidence fields come from Neo4j only.
- Action labels such as TARGET, ENZYME, TRANSPORTER and CARRIER describe what the gene product is for the drug, not whether the drug switches it down or up. They are counted as **unknown direction**.
