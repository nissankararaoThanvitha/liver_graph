# Data dictionary

Every file in `04_DATA/`, with what its columns mean. Read the two
conventions first — they apply everywhere.

**`value_z`.** Almost every expression number in this package is `value_z`:
expression standardised per gene **within each study** to mean 0, SD 1. A
positive value means above average for that gene in that study. It does *not*
mean highly expressed. This standardisation is what makes eight cohorts
comparable; raw values are not comparable and are not used.

**Effect sizes are in standard deviations** of that gene within that study,
not in fold changes. There are no fold changes anywhere in this project.

---

## `gene_tables/` — the stage-wise gene tables

The deliverable set, restricted to the 4,692 progression genes. Values are
mean `value_z` per group.

**Shared columns in all four gene tables:**

| Column | Meaning |
|---|---|
| `ensembl_id` | canonical Ensembl gene ID, version stripped — the join key everywhere |
| `symbol` | HGNC gene symbol. Convenience only; **never join on it** |
| `fibrosis_rho` | cross-study Spearman correlation with fibrosis stage 0–4 (−1…+1). Blank if not significant on that ladder |
| `fibrosis_q` | BH-corrected q-value for that correlation |
| `inflammation_rho` | the same against control → NAFL → NASH |
| `inflammation_q` | its q-value |
| `n_studies` | how many studies the gene was tested in |
| `ladder` | `fibrosis_only`, `inflammation_only` or `both` |

| File | Extra columns | n behind it |
|---|---|---|
| `genes_by_fibrosis_stage.csv` | `stage_0` … `stage_4` | all **668** staged samples |
| `genes_by_disease_group.csv` | `control`, `obese`, `NAFL`, `NAFLD`, `NASH` | 592 labelled samples |
| `genes_by_stage_and_sex.csv` | `stage0_F`, `stage0_M` … `stage4_M` | **385** samples only |
| `genes_by_stage_and_age.csv` | `stage0_<30` … `stage4_60+` | **385** samples only |

**The age and sex tables rest on 385 samples, not 1,085** — three studies
only. Some cells are sparse by construction: there is no `stage4_<30` or
`stage4_30-39` column at all, because no patient in those bands reached F4.

`sample_demographics.csv` — one row per sample, 1,085 rows:

| Column | Meaning |
|---|---|
| `sample_id` | GEO accession (GSM…) |
| `patient_id` | the person. **Group by this, not `sample_id`** — 58 patients in GSE193066 were biopsied twice |
| `dataset_id` | the GEO series |
| `sex` | harmonised to `M` / `F`. Blank where not recorded (545 samples) |
| `age_years`, `age_band` | blank where not recorded (602 samples) |
| `fibrosis_stage` | integer 0–4, blank where the study never staged (417 samples) |
| `disease_group` | `control`, `obese`, `NAFL`, `NAFLD`, `NASH`, blank (493 samples) |

---

## `progression_statistics/` — the full statistics, significant or not

| File | Rows | What |
|---|---|---|
| `progression_fibrosis.csv` | 14,794 | every tested gene against the fibrosis ladder |
| `progression_disease.csv` | 14,794 | the same against the disease ladder |
| `progression_both.csv` | 6,986 | genes significant on at least one ladder, both sets of columns side by side (`_fib` / `_dis` suffixes) |

| Column | Meaning |
|---|---|
| `median_rho` | median of the per-study Spearman correlations — the headline effect size |
| `n_studies` | studies contributing to this gene |
| `n_agree` | how many agreed on the direction of change |
| `combined_p` | Fisher's combination of the per-study p-values |
| `q_value` | BH-corrected across all 14,794 genes |
| `min_rho`, `max_rho` | the per-study range. **The fastest check that a signal is not carried by one cohort** |

**These two files are also the tested universe**, which is the 14,794-gene
enrichment background. `len(progression_fibrosis.csv)` is the definitive
source for that number.

---

## `harmonisation/` — the audit trail of stages 2–5

| File | What it records |
|---|---|
| `_parse_summary.csv` | per study: genes, samples, identifier type, unit, measurements parsed |
| `gene_id_map.csv` | every raw identifier → canonical Ensembl ID, per dataset. The complete translation table |
| `_mapping_summary.csv` | per study: unique IDs, mapped, percentage, unmapped |
| `unmapped_genes.csv` | every identifier that failed to map (1,807 rows), with its dataset and type. **Nothing was silently dropped** |
| `sample_crosswalk.csv` | `dataset_id`, `sample_key` (the expression file's column name), `sample_id` (GSM accession) |
| `samples_metadata.csv` | the **raw** per-sample clinical fields as GEO supplied them, including `*_raw` severity columns and `raw_characteristics` |

`samples_metadata.csv` holds the un-harmonised labels. **Use
`gene_tables/sample_demographics.csv` for analysis** — querying
`fibrosis_stage_raw = '4'` here returns 29 of 35 cirrhosis samples and
reports no error.

---

## `knowledge_layer_optimuskg/` — the curated biology in the graph

The layer actually loaded into Neo4j. Node files are `node_id, name`; edge
files are `from_id, to_id, rel_type, score`.

| File | Rows | Becomes |
|---|---|---|
| `nodes_disease.csv` | 36,044 | Disease |
| `nodes_drug.csv` | 12,025 | Drug |
| `nodes_bioprocess.csv` | 12,203 | BioProcess |
| `nodes_phenotype.csv` | 8,666 | Phenotype |
| `nodes_pathway.csv` | 2,220 | Pathway |
| `edges_disease_gene.csv` | 1,832,441 | ASSOCIATED_WITH |
| `edges_gene_gene.csv` | 324,116 | INTERACTS_WITH |
| `edges_biological_process_gene.csv` | 157,081 | INVOLVED_IN |
| `edges_disease_phenotype.csv` | 149,960 | HAS_PHENOTYPE |
| `edges_pathway_gene.csv` | 46,751 | IN_PATHWAY |
| `edges_drug_disease.csv` | 43,636 + 722 | TREATS, OFF_LABEL_FOR |
| `edges_disease_disease.csv` | 28,919 | PARENT_OF |
| `edges_drug_gene.csv` | 20,674 | ACTS_ON — **carries the mode of action** (INHIBITOR, AGONIST, BLOCKER and 20 more) |
| `edges_my_progression.csv` | 6,384 | **TRACKS_FIBROSIS (3,645) and TRACKS_INFLAMMATION (2,739)** |

**`score` on gene–disease edges is the Open Targets association score.**
Links below 0.1 were not loaded; the score is kept on the edge so a query can
tighten further without a reload (`04_DECISIONS.md` §9).

**`edges_my_progression.csv` is the project's own contribution** — the only
edges here derived from these patients rather than imported.

## `knowledge_layer_primekg_superseded/` — PrimeKG, kept for one reason

The superseded layer. It ships **only** because
`hc4_kg_subgraph.py` reads it, so Figure 9 cannot be reproduced without it.
Node files are `node_id, name`; edge files are `from_id, to_id`, with no
score column.

**Do not use this layer for anything new.** See `05_LIMITATIONS.md` §14,
which this file exists to make checkable.

---

## `graph_nodes/` — the gene and dataset nodes

`nodes_gene.csv`, 53,993 rows:

| Column | Meaning |
|---|---|
| `ensembl_id` | the join key |
| `symbol`, `entrez_id` | convenience identifiers |
| `n_datasets` | **1–8: how many studies measured this gene** |
| `category` | gene class as carried from HGNC |

**`n_datasets` is load-bearing.** 39,199 genes are missing from at least one
study and 10,621 appear in exactly one. **Never average across genes without
checking it.** The progression analysis used only the 14,794 genes with
`n_datasets = 8`.

`gene_progression_scores.csv` — the compact form that went onto the Gene
nodes: `ensembl_id`, `fib_rho`, `fib_q`, `dis_rho`, `dis_q`.

`nodes_dataset.csv` — the eight studies.

---

## What is not here, and where it went

| Not shipped | Size | How to get it |
|---|---|---|
| `data/raw` | 104 MB | GEO — `06_PROVENANCE/DATA_SOURCES.md` has the exact filenames |
| `data/interim_full` | 197 MB | re-parse; `06_PROVENANCE/REBUILD.md` |
| `data/graph_full` | 2.1 GB | rebuild; needed only to re-run stages 12 and 14 |
| `data/graph_all` | 1.6 GB | superseded by `graph_full` |
| `data/primekg` | 937 MB | Dataverse DOI in `DATA_SOURCES.md` |
| `data/kg_triples`, `data/prediction` | 192 MB | the unresolved link-prediction strand |
| `data/genesets` | 5.7 MB | MSigDB — URL in `DATA_SOURCES.md`. **Not redistributable** (KEGG terms) |

No number in the paper is read directly from any of these. Every result is
traceable to a file that *is* here.
