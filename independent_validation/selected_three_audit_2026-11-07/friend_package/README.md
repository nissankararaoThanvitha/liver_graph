# Paper 1 external validation (7 Nov 2026)

The frozen Paper 1 gene lists (Top 23 shortlist, Tier 1 447, Tier 2 1,403, Tier 3 1,995, all 3,845) tested in four independent GEO cohorts. No gene was selected, re-ranked or refitted.

Run from the repository root: `python Paper1_Validation/code/validate_external.py`

## Cohorts (none is one of the eight Paper 1 studies)

| Cohort | Source | Staged patients used | Stages | Data file (GEO supplementary) | Transform |
|---|---|---|---|---|---|
| GSE213621 | Duke, NAFLD | 299 (69 controls left out) | F0–F1 97 · F2 107 · F3–F4 95 | `GSE213621_FPKMs_allsamples.txt.gz` | log2(FPKM+1) |
| GSE225740 | Indiana, NAFLD | 87 (6 without stage left out) | F0 27 · F1 26 · F2 15 · F3 13 · F4 6 | `GSE225740_NAFLD_RNA_counts.csv.gz` + `_phenotypes.csv.gz` | log2(CPM+1) |
| GSE268273 | Santander, NAFLD (incl. immune-mediated disease) | 109 | F0 36 · F1 41 · F2 13 · F3 14 · F4 5 | `GSE268273_EGN_RNAseq_Normalized_data.xlsx` | authors' limma-voom log2-CPM, kept |
| GSE276114 | Turkey/Sweden, MASLD 81 · viral 82 · alcohol 14 | 177 | F0–2 39 · F3 24 · F4 114 | `GSE276114_raw.count.txt.gz` | log2(CPM+1) |

Stages come from each series matrix. Files go in `data/raw_validation/<GSE>/` (git-ignored); download from `https://ftp.ncbi.nlm.nih.gov/geo/series/<GSEnnn>/<GSE>/suppl/` and `.../matrix/`.

Preprocessing is Paper 1's: same HGNC file and mapping code (`map_gene_ids.py`), first duplicate raw ID kept, `_PAR_Y` and unmappable IDs dropped, IDs mapping to one Ensembl gene summed, library size before mapping, z-score per gene within study. Genes tested: the 14,794-gene Paper 1 universe, where measured and non-constant. Details: `results/preprocessing_log.txt`.

## Tests (fixed before running)

1. **Direction:** % of genes whose Spearman rho with stage has the Paper 1 sign; p from 1,000 stage permutations.
2. **Replication:** % with BH q < 0.05 (over the testable universe) and the Paper 1 sign, vs 1,000 expression-matched random sets of non-selected genes.
3. **Effect agreement:** Spearman between Paper 1 rho and cohort rho.
4. **Score:** mean z of rising genes − mean z of falling genes; Spearman with stage (permutation p) and AUC advanced (F3–F4) vs mild (F0–F1; F0–2 in GSE276114), bootstrap 95% CI.

Seed 42, 1,000 permutations/bootstraps (smallest possible p = 0.001).

## Results (`results/validation_summary.csv`)

Same direction (%) / replicated at q < 0.05 (%) [matched random %] / score AUC advanced vs mild:

| Gene set | GSE213621 (n=299) | GSE225740 (n=87) | GSE268273 (n=109) | GSE276114 (n=177) |
|---|---|---|---|---|
| Top 23 | 100 / 78.9 [21.8] / 0.79 | 100 / 82.6 [20.0] / 0.84 | 100 / 88.9 [15.6] / 0.86 | 82.6 / 73.9 [33.3] / 0.82 |
| Tier 1 | 98.7 / 80.6 [20.7] / 0.82 | 98.7 / 82.5 [22.3] / 0.86 | 97.3 / 74.3 [15.1] / 0.87 | 94.9 / 80.5 [33.1] / 0.86 |
| Tier 2 | 94.0 / 60.0 [20.5] / 0.76 | 92.6 / 58.5 [21.7] / 0.84 | 90.2 / 52.2 [15.0] / 0.82 | 85.9 / 67.3 [32.7] / 0.85 |
| Tier 3 | 86.1 / 41.5 [19.8] / 0.72 | 78.7 / 39.1 [22.1] / 0.79 | 91.1 / 46.4 [14.9] / 0.80 | 74.4 / 48.5 [32.5] / 0.79 |
| All 3,845 | 90.4 / 52.6 [20.2] / 0.75 | 86.2 / 51.4 [21.9] / 0.82 | 91.5 / 51.8 [15.0] / 0.82 | 81.0 / 59.1 [32.7] / 0.83 |

- Replication beat matched random genes in every cohort and gene set (p ≤ 0.001, except Top 23 in the GSE276114 MASLD subgroup p = 0.002 and viral subgroup p = 0.011); the score rose with stage everywhere (p ≤ 0.001).
- Direction-agreement permutation p ≤ 0.024 in the three NAFLD cohorts; in GSE276114 0.03–0.05 for Tier 1, Tier 2 and all genes, and not significant for Top 23 (0.14) and Tier 3 (0.054). Co-expressed genes move together under permutation, which makes this test conservative.
- By cause (GSE276114): MASLD Tier 1 95.3% same direction, AUC 0.92; viral hepatitis Tier 1 80.5%, AUC 0.72 (CI 0.52–0.90); alcohol not testable (all 14 patients F3–F4).
- Genes tested in all four cohorts: Tier 1 318 (89.3% same direction in all four; 75.2% replicated in ≥ 3), Tier 2 1,022 (67.9%; 46.0%), Tier 3 1,507 (42.7%; 23.2%).
- Top 23: 8 replicated in all four cohorts (IL32, MME, ACADSB, TAX1BP3, F2, NFASC, PDGFRA, PLK3); 16 in ≥ 3; weakest LYZ, TREM2, KNG1 (1 each). Per gene: `results/validation_per_gene.csv`.

## Limits

- Stages are grouped in GSE213621 and GSE276114; few F4 patients in GSE225740 (6) and GSE268273 (5).
- GSE268273 provides only authors' normalised values (no counts); it covers 14,138 genes, so 5 of the Top 23 are not testable there.
- Cross-sectional cohorts: confirms association with stage, not causation.
