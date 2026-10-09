# Data dictionary

Every file in `04_DATA/`, and what its columns mean. Two conventions first —
they apply everywhere.

**`value_z`.** Almost every expression number here is `value_z`: expression
standardised per gene **within each study** to mean 0, SD 1. A positive value
means above average for that gene in that study. It does *not* mean highly
expressed. Raw values are not comparable across studies and are not used.

**Effect sizes are in standard deviations** of that gene within that study,
not fold changes. There are no fold changes in this project.

---

## `progression_genes/` — the inputs everything is built on

| File | Rows | What |
|---|---|---|
| `progression_fibrosis.csv` | 14,794 | every tested gene against the fibrosis ladder, pass or fail |
| `progression_disease.csv` | 14,784 | the same against the disease ladder |
| `progression_both.csv` | 5,755 | genes significant on at least one ladder |
| `genes_by_fibrosis_stage.csv` | 5,884 | the progression genes with mean expression at F0–F4 |
| `genes_by_disease_group.csv` | 5,884 | the same by disease group |
| `sample_demographics.csv` | 1,085 | one row per sample |

**Columns in the two progression files:**

| Column | Meaning |
|---|---|
| `median_rho` | median of the per-study Spearman correlations — the headline effect size |
| `n_studies` | studies contributing to this gene |
| `n_agree` | how many agreed on the direction |
| `combined_p` | Fisher's combination of the per-study p-values |
| `q_value` | BH-corrected across all 14,794 |
| `min_rho`, `max_rho` | the per-study range. **The fastest check that a signal is not carried by one cohort** |

**A gene counts as significant when `q_value < 0.05` AND
`n_agree == n_studies`.** Both conditions. `q < 0.05` alone returns about
10,900 genes; the published counts require every testing study to agree on
direction.

**These two files are also the tested universe**, which is the 14,794-gene
enrichment background.

---

## `gene_tables/` — the stage-wise tables

Values are mean `value_z` per group. Shared columns: `ensembl_id`, `symbol`,
`fibrosis_rho`, `fibrosis_q`, `inflammation_rho`, `inflammation_q`,
`n_studies`, `ladder` (`fibrosis_only` / `inflammation_only` / `both`).

| File | Extra columns | n behind it |
|---|---|---|
| `genes_by_fibrosis_stage.csv` | `stage_0` … `stage_4` | all **668** staged samples |
| `genes_by_disease_group.csv` | `control`, `NAFL`, `NAFLD`, `NASH`, `obese` | 592 labelled samples |
| `genes_by_stage_and_sex.csv` | `stage0_F` … `stage4_M` | **385 samples only** |
| `genes_by_stage_and_age.csv` | `stage0_<30` … `stage4_60+` | **385 samples only** |

Some age cells are absent by construction: no patient under 40 reached F4.

**`sample_demographics.csv`** — one row per sample:

| Column | Meaning |
|---|---|
| `sample_id` | GEO accession |
| `patient_id` | the person. **Group by this, not `sample_id`** |
| `sex` | harmonised to `M`/`F`; blank for 545 samples |
| `age_years`, `age_band` | blank for 602 samples |
| `fibrosis_stage` | integer 0–4; blank for 417 samples |
| `disease_group` | `control`, `NAFL`, `NAFLD`, `NASH`, `obese`, or blank |

**`NAFLD` means fatty liver disease of unstated subtype.** It is not a point
on the control → NAFL → NASH ladder, and those samples do not contribute to
the disease analysis. See `04_LIMITATIONS.md` §2.

---

## `harmonisation/` — the audit trail

| File | What it records |
|---|---|
| `_parse_summary.csv` | per study: genes, samples, identifier type, unit, measurements parsed |
| `gene_id_map.csv` | every raw identifier → canonical Ensembl ID. The complete translation table |
| `_mapping_summary.csv` | per study: unique IDs, mapped, percentage, unmapped |
| `unmapped_genes.csv` | every identifier that failed to map (1,807 rows). **Nothing was silently dropped** |
| `sample_crosswalk.csv` | `dataset_id`, `sample_key` (the expression file's column name), `sample_id` (GEO accession) |
| `samples_metadata.csv` | the **raw** clinical fields as GEO supplied them, including `raw_characteristics` |
| `nodes_sample_clinical.csv` | the **harmonised** clinical table — the one to use |

`samples_metadata.csv` holds the un-harmonised labels and is kept so every
translation is auditable. **Use `nodes_sample_clinical.csv` or
`sample_demographics.csv` for analysis** — a query against a raw severity
field returns 29 of the 35 cirrhosis samples and reports no error.

---

## `knowledge_layer/` — the curated biology

Node files are `node_id, name`; edge files are `from_id, to_id, rel_type,
score`.

| File | Rows | Becomes |
|---|---|---|
| `nodes_disease.csv` | 36,044 | Disease |
| `nodes_drug.csv` | 12,025 | Drug |
| `nodes_bioprocess.csv` | 12,203 | BioProcess |
| `nodes_phenotype.csv` | 8,666 | Phenotype |
| `nodes_pathway.csv` | 2,220 | Pathway |
| `edges_disease_gene.csv` | 1,832,441 | ASSOCIATED_WITH |
| `edges_gene_gene.csv` | 324,116 | INTERACTS_WITH |
| `edges_disease_phenotype.csv` | 157,144 | HAS_PHENOTYPE |
| `edges_biological_process_gene.csv` | 157,081 | INVOLVED_IN |
| `edges_drug_disease.csv` | 70,380 | TREATS, CONTRAINDICATED_IN, OFF_LABEL_FOR — split by `rel_type` |
| `edges_pathway_gene.csv` | 46,751 | IN_PATHWAY |
| `edges_disease_disease.csv` | 44,215 | PARENT_OF |
| `edges_drug_gene.csv` | 20,674 | ACTS_ON — **carries the mode of action** (INHIBITOR, AGONIST, BLOCKER and 20 more) |

**`score` on gene–disease edges is the Open Targets association score.**
Links below 0.1 were not loaded; the score is kept on the edge so a query can
tighten further without a reload.

This is the layer the mechanism network (Figure 9) is filtered from, which is
why that figure needs no database.

---

## `graph_nodes/`

**`nodes_gene.csv`**, 53,993 rows:

| Column | Meaning |
|---|---|
| `ensembl_id` | the join key |
| `symbol`, `entrez_id` | convenience identifiers |
| `n_datasets` | **1–8: how many studies measured this gene** |
| `category` | gene class from HGNC |

**`n_datasets` is load-bearing.** 39,199 genes are missing from at least one
study and 10,621 appear in exactly one. **Never average across genes without
checking it.** The progression analysis used only the 14,794 with
`n_datasets = 8`.

**`edges_my_progression.csv`** — 6,384 rows, the project's own contribution:
`TRACKS_FIBROSIS` (3,645) and `TRACKS_INFLAMMATION` (2,739), with the rho, q,
study count and direction on each edge. These are the only edges here derived
from these patients rather than imported.

**`gene_progression_scores.csv`** — the compact form: `ensembl_id`,
`fib_rho`, `fib_q`, `dis_rho`, `dis_q`.

---

## What is not here, and where it went

| Not shipped | Size | How to get it |
|---|---|---|
| `data/raw` | 104 MB | GEO — exact filenames in `06_PROVENANCE/DATA_SOURCES.md` |
| `data/interim_full` | 197 MB | re-parse; see `REBUILD.md` |
| `data/graph_full` | 2.1 GB | rebuild; needed only to re-run Tasks 2, 3 and hc1/hc3 |
| `data/genesets` | 5.7 MB | MSigDB. **Not redistributable** (KEGG terms) |

No number in the paper is read directly from any of these. Every result
traces to a file that *is* here.
