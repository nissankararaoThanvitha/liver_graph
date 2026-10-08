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
The layer actually used, and the one loaded into the graph.

**PrimeKG** — Harvard Dataverse, DOI `10.7910/DVN/IXA7BM`, 937 MB.
Superseded and replaced; see `00_START_HERE/04_DECISIONS.md` §8 for the
table that decided it (0 drugs treating NASH/NAFLD/cirrhosis against 74/95/71).
Still required to reproduce Figure 9 as currently built — see
`00_START_HERE/05_LIMITATIONS.md` §14.

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
documented finding in this project — see `05_LIMITATIONS.md` §14 and the
note on name matching in `02_STAGE_BY_STAGE.md` stage 14.

---

## Software

Pinned in `05_CODE/requirements.txt`. The committed results were produced
with exactly these versions:

Python 3.13.7 · pandas 2.3.3 · numpy 2.2.4 · scipy 1.16.3 ·
scikit-learn 1.7.2 · matplotlib 3.10.7 · gseapy 1.3.1

Graph store: Neo4j Enterprise 2026.07.0 via Neo4j Desktop 2, store format
`block-block-1.1`, configured with a 1 GB heap and 512 MB page cache against
a 2.5 GB store. **No result in this package requires a running database.**

Link prediction only (not needed, and its model failed validation):
pykeen 1.11.1 · torch 2.14.0.

---

## Ethics and data availability wording

No new human data were generated. All eight studies are publicly available
from GEO under their own accessions and their original consent and ethics
approvals. For the manuscript's data-availability statement: the accessions
above, plus a pointer to wherever the project repository is published.
