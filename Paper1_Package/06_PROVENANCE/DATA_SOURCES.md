# Where every input came from

Full provenance for each external input, with the exact file taken. Nothing
in this project generated new human data; every analysis uses existing public
data, so no sample-size calculation or randomisation applies and the
available sample size is a constraint rather than a design choice.

---

## The eight expression studies

All from the NCBI Gene Expression Omnibus,
`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<accession>`.

**Two files were taken from each study:** the supplementary expression matrix
(listed below) and the **series matrix**, which carries the per-sample
clinical characteristics. Without the series matrix a sample is an anonymous
column.

| Study | Samples | Supplementary expression file taken |
|---|---|---|
| GSE126848 | 57 | `GSE126848_Gene_counts_raw.txt.gz` |
| GSE130970 | 78 | `GSE130970_all_sample_salmon_tximport_TPM_entrez_gene_ID.csv.gz` |
| GSE135251 | 216 | `GSE135251_RAW.tar` (per-sample files inside) |
| GSE162694 | 143 | `GSE162694_raw_counts.csv.gz` |
| GSE167523 | 98 | `GSE167523_Raw_gene_counts_matrix.txt.gz` |
| GSE193066 | 164 | `GSE193066_NAFLD.HUn164.gct.gz` |
| GSE240729 | 67 | `GSE240729_merged.counts.67samp.txt.gz` |
| GSE269412 | 262 | `GSE269412_DRX0FLO_rnaseq_count_mat.txt.gz` |

Total 1,085 samples from 1,027 patients. Compressed download size ~104 MB.

**Papers referenced while resolving clinical labels:** GSE193066 — PMID
35731891 (confirmed the 106-patient / 58-repeat-biopsy structure);
GSE269412 — *JCI Insight* 2025, PMID 39998893 (reports its cohort only in
aggregate, which is why that study carries no usable clinical labels).

---

## Gene identifier dictionary

**HGNC complete set** — `hgnc_complete_set.txt`, 16.2 MB, from
`https://www.genenames.org/download/archive/`.

Used by `02_map_gene_ids.py` to translate every symbol, Entrez ID and
Ensembl ID onto one canonical Ensembl gene ID with the version stripped.

---

## Knowledge graphs

**OptimusKG** — Harvard Dataverse, DOI `10.7910/DVN/IYNGEV`, 161 MB.
The source of the curated knowledge layer: diseases, drugs, pathways,
biological processes, phenotypes and the relationships between them.
Genes are identified by Ensembl ID, the same namespace this pipeline
standardises on, so the join needs no translation.

Underlying gene–disease association scores are Open Targets, carried through
OptimusKG. Links are kept at score ≥ 0.1 and the score is stored on every
edge.

---

## Gene sets for enrichment

**MSigDB v2024.1, human gene symbols**, from
`https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2024.1.Hs/`

Four collections, 5.7 MB total:

| File | Collection |
|---|---|
| `c5.go.bp.v2024.1.Hs.symbols.gmt` | GO Biological Process |
| `c2.cp.kegg_legacy.v2024.1.Hs.symbols.gmt` | KEGG legacy |
| `c2.cp.reactome.v2024.1.Hs.symbols.gmt` | Reactome |
| `h.all.v2024.1.Hs.symbols.gmt` | Hallmark |

**These are not shipped in this package.** The KEGG-derived sets may not be
redistributed. Download them from the URL above into `data/genesets/` before
re-running `task4_enrichment.py`.

A free MSigDB registration may be required. The version matters: MSigDB
2024.1 renamed some GO terms relative to earlier releases, which is itself a
documented finding in this project — see `00_START_HERE/04_LIMITATIONS.md` and the
note on name matching in `00_START_HERE/02_METHODS.md`.

---

## Software and recovered expression inputs

Historical upstream results documented Python3.13.7. Corrected analyses used Python3.12.14 with pandas2.3.3,numpy2.2.4,scipy1.16.3,scikit-learn1.7.2,matplotlib3.10.7,gseapy1.3.1. Baseline tested gene IDs/rhos/p/q and agreement counts reproduced before correction. Exact corrected environment is retained in biopsy_correction_2026-10-10/runtime_requirements.txt.

Graph at correction verification: Neo4j Enterprise2026.09.0. No raw expression or curated links were modified by the biopsy correction; only patient-derived progression links were updated with backup and verified identities/properties.

The recovered input is14,794 eligible genes across1,085 samples:16,051,490 value_z records, at data/expression_analysis_core. Every eligible sample/gene pair was verified. This is not the full32,471,042-measurement export. Do not reload all EXPRESSES edges from it. Download/recovery manifests and hashes are retained in the correction audit. MSigDB2024.1.Hs files were recovered from the documented URLs; local GMTs are excluded from version control/package redistribution.

---

## Ethics and data availability wording

No new human data were generated. All eight studies are publicly available
from GEO under their own accessions and their original consent and ethics
approvals. For the manuscript's data-availability statement: the accessions
above, plus a pointer to wherever the project repository is published.
