# 3. Every statistic in the project

One place for every test run, with its unit of analysis, sample size,
multiple-testing correction, threshold and result. Written so a methods
section can be assembled from it without opening any script, and so any
number in the paper can be traced to the file it came from.

**Software and versions** (pinned in `05_CODE/requirements.txt`; the
committed results were produced with exactly these): Python 3.13.7,
pandas 2.3.3, numpy 2.2.4, scipy 1.16.3, scikit-learn 1.7.2,
matplotlib 3.10.7, gseapy 1.3.1. Neo4j Enterprise 2026.07.0 held the graph
but no result depends on a running database.

---

## 0. Conventions that apply to every test below

| | |
|---|---|
| **Measured quantity** | `value_z` — expression standardised per gene within each study (mean 0, SD 1). Effect sizes are therefore in standard deviations of that gene within that study. |
| **Unit of analysis** | the **patient**, never the sample. Repeat biopsies are collapsed before any statistic (58 patients in GSE193066 were biopsied twice). |
| **Eligible gene set** | the **14,794** genes measured in all eight studies. This is the tested set and the enrichment background throughout. |
| **Multiple testing** | Benjamini–Hochberg false-discovery rate, applied within each family of tests (the family is stated per test below). |
| **Significance** | FDR q < 0.05 unless stated otherwise. |
| **Cross-study rule** | statistics are computed **within each study** and then combined. Patients are never pooled across studies. |

---

## 1. Progression-gene identification (stage 9)

| | |
|---|---|
| **Question** | does this gene's expression track position on this ladder? |
| **Test** | Spearman rank correlation of `value_z` against ladder position, computed **separately within each study** |
| **Why Spearman** | the stages are ordered ranks whose spacing is not meaningful; Pearson would impose a linear spacing the data does not support |
| **Combination across studies** | per-study rho combined by its **median**; per-study p-values combined by **Fisher's method** |
| **Inclusion rule** | gene kept only where **most studies agree on the direction** of change |
| **n (fibrosis ladder)** | 668 staged samples from 5 studies, collapsed to patients |
| **n (disease ladder)** | 592 labelled samples from 5 studies, collapsed to patients |
| **Genes tested** | 14,794 (measured in all 8 studies) |
| **Correction** | BH across the 14,794 genes, separately per ladder |
| **Threshold** | q < 0.05 |
| **Result** | **4,692** progression genes: 1,953 fibrosis-only, 1,047 inflammation-only, 1,692 both |
| **Full output** | `04_DATA/progression_statistics/progression_fibrosis.csv`, `progression_disease.csv`, `progression_both.csv` — all 14,794 genes with `median_rho`, `n_studies`, `n_agree`, `combined_p`, `min_rho`, `max_rho`, `q_value`, significant or not |

`min_rho` and `max_rho` are the per-study range and are the fastest way to
check that a gene's signal is not carried by one cohort.

---

## 2. Agreement between the two ladders (stage 10)

| | |
|---|---|
| **Test** | Spearman correlation of fibrosis rho against inflammation rho, among shared genes |
| **All shared genes** | rho = **0.725**, p = 2.9 × 10⁻²⁷⁶, n = 1,692 |
| **Rising genes only** | rho = **0.453**, p = 1.3 × 10⁻⁶⁸, n = 1,335 |
| **Falling genes only** | rho = **0.354**, p = 6.0 × 10⁻¹², n = 356 |

**Quote the within-direction values.** The 0.725 is inflated by the existence
of two separate clouds (concordantly rising, concordantly falling); a
correlation computed across both measures the separation between the clouds
as much as the association within them.

Discordant genes: **1** (GPD1). Output:
`03_RESULTS/Task1_gene_groups/task1_summary.csv`.

---

## 3. Trajectory clustering (stage 11)

| | |
|---|---|
| **Input** | 3,645 fibrosis-associated genes × 5 stage means |
| **Pre-processing** | each gene's five stage means z-scored **across stages**, so clustering is on curve shape, not magnitude |
| **Algorithm** | K-means, 50 random initialisations |
| **k tested** | 3 to 8 |
| **Selection criteria** | silhouette score; gene-subsample stability (50 reclusterings of random 80% gene subsets); patient-bootstrap stability (50 resamples of patients within study, stage means recomputed, reclustered) |
| **Stability metric** | adjusted Rand index against the full-data clustering |
| **Decision rule** | largest k with gene-subsample ARI ≥ 0.95 → **k = 5** |
| **Shape reproducibility** | 100 patient bootstraps; each of the five shapes recovered at median correlation **0.97–0.997** |
| **Study-mix control** | stage profiles re-estimated as `value_z ~ stage + study`; median per-gene correlation with plain stage means **0.998**; reclustering those gives **ARI 0.84** against the main clusters |
| **Per-gene stability** | `membership_confidence` = fraction of 100 bootstraps in which a gene keeps its cluster |

Stage sample sizes behind the means: **F0 152, F1 168, F2 186, F3 127, F4 35.**
F4 means are the noisiest by a wide margin.

| k | Silhouette | Gene-subsample ARI | Patient-bootstrap ARI |
|---|---|---|---|
| 3 | 0.560 | 0.981 | 0.754 |
| 4 | 0.461 | 0.968 | 0.564 |
| **5** | **0.338** | **0.957** | **0.526** |
| 6 | 0.291 | 0.932 | 0.464 |
| 7 | 0.280 | 0.795 | 0.423 |
| 8 | 0.258 | 0.757 | 0.367 |

**Disclose when writing this up:** silhouette alone favours k = 3, and the
ARI ≥ 0.95 rule was set after inspecting the k = 3–6 solutions. The reason is
stated in `03_RESULTS/Task2_trajectories/README.txt` and should be stated in
the paper: k = 3 and 4 merge visibly different shapes, k = 6 splits one
cluster into two near-identical halves.

Outputs: `task2_choosing_k.csv`, `task2_robustness.csv`,
`task2_bootstrap_shape_stability.csv`, `task2_gene_clusters.csv`.

---

## 4. Stage-transition analysis (stage 12)

| | |
|---|---|
| **Question** | for each gene and each adjacent stage pair, is there a change, how large, and where is it largest? |
| **Model** | `value_z ~ stage + study`, linear, fitted on the patients of the two stages only |
| **Why `+ study`** | stages are then compared **within** each study, so a difference in stage mix between studies cannot create a false change. Studies lacking either stage are excluded from that transition. |
| **Test** | t-test on the stage coefficient (beta) |
| **Correction** | BH **within each transition**, across 3,645 genes |
| **"Substantial"** | q < 0.05 **and** \|beta\| ≥ 0.2 SD |
| **Patient handling** | repeat biopsies at the same stage averaged (28 patients); a patient biopsied either side of a transition keeps one sample, drawn at random under a fixed seed (24 patients) |
| **Power-matched refit** | 50 refits per transition on the *same* study-balanced design of **30 patients per stage** (GSE130970 2, GSE135251 14, GSE162694 8, GSE240729 6) |

| | F0→F1 | F1→F2 | F2→F3 | F3→F4 |
|---|---|---|---|---|
| Patients (a / b) | 152 / 166 | 160 / 165 | 165 / 109 | 118 / 34 |
| Substantial genes | 1,165 | 1,175 | 1,117 | 936 |
| — increasing | 1,135 | 647 | 906 | 865 |
| — decreasing | 30 | 528 | 211 | 71 |
| Median \|beta\| | 0.188 | 0.189 | 0.221 | **0.378** |
| Genes \|beta\| ≥ 0.2 | 1,699 | 1,693 | 2,043 | 2,710 |
| **Power-matched median** | **0** | **0** | **2** | **311** |

**The comparison between transitions is the valid claim; the absolute counts
are not.** All four transitions use the same gene set, which was itself
selected for correlating with fibrosis stage in these data, so the counts are
inflated by selection. The ranking between transitions is unaffected because
the inflation is common to all four.

`|beta| ≥ 0.2 SD` is a conventional, not a unique, cutoff. The effect-size
panel of Figure 7 does not depend on it.

Outputs: `task3_transition_summary.csv`,
`task3_all_genes_all_transitions.csv` (every gene × transition with beta, se,
p, q, n), `task3_cluster_by_transition.csv`.

---

## 5. Pathway enrichment (stage 13)

| | |
|---|---|
| **Test** | one-sided hypergeometric (over-representation), `gseapy.enrich`, run locally |
| **Background** | the **14,794** cross-study-eligible genes — **not** all ~20,000 human genes |
| **Gene-set restriction** | every set first intersected with the 14,794, then kept only if 10–500 genes remained |
| **Sets tested** | GO BP 4,853 · KEGG legacy 183 · Reactome 1,279 · Hallmark 50 |
| **Collection** | MSigDB v2024.1, human gene symbols |
| **Correction** | BH within each **group × database** |
| **Threshold** | FDR < 0.05 |
| **Verification** | one p-value recomputed directly from `scipy.stats.hypergeom` matched gseapy exactly |
| **Groups tested** | 6 ladder groups + 5 clusters (all genes) + 5 clusters (high-confidence members only), each separately — never all 4,692 together |

**The background choice is not a detail.** Using the whole genome would
overstate enrichment for any term whose members are preferentially well
measured across studies, and it changes which terms reach significance. If a
reviewer asks one methodological question about stage 13, it will be this
one.

Reported columns: `overlap` (group genes in the set), `set_size` (set genes
in the background), `gene_ratio` = overlap / group size, `bg_ratio` =
set_size / 14,794, `fold_enrichment` = gene_ratio / bg_ratio, and the genes
responsible.

Counts per group are in `02_TABLES/main/Table5_enrichment_counts.csv`; every
tested term, significant or not, is in
`03_RESULTS/Task4_enrichment/enrichment_tables/<group>__<database>.csv`.

---

## 6. Evidence scoring and prioritisation (stage 14)

Not a hypothesis test — a ranking by agreement between five independent
measurements, each already computed above. **All cutoffs were frozen as named
constants before any ranked list was inspected.**

| | Score | 2 points | 1 point | Reads from |
|---|---|---|---|---|
| **P** | Progression strength | \|rho\| ≥ 0.40 | ≥ 0.30 | §1 |
| **T** | Trajectory | \|F4 − F0\| ≥ 1.0 SD | ≥ 0.5 SD; 0 if direction is wrong | §3 |
| **X** | Transition | largest jump substantial in the full fit **and** reproducible in ≥ 50% of 50 equal-power draws | one of the two | §4 |
| **F** | Fibrosis specificity | — | fibrosis-only (shared = 0) | §1 |
| **B** | Biological support | in enriched terms in ≥ 2 of 4 databases | in 1 | §5 |

Total 0–9. **Tier 1 = 7–9 (507 genes)** · Tier 2 = 5–6 (1,483) · Tier 3 = < 5
(1,655).

### Sensitivity, measured and reported rather than used to choose

| Tier 1 cutoff | Genes | Retains the frozen 507 |
|---|---|---|
| 6 | 1,111 | 100% |
| **7 (frozen)** | **507** | — |
| 8 | 135 | 26.6% |

| P thresholds | P=2 | P=1 | P=0 |
|---|---|---|---|
| 0.35 / 0.25 | 401 | 1,083 | 2,161 |
| **0.40 / 0.30 (frozen)** | **167** | **679** | **2,799** |
| 0.45 / 0.35 | 71 | 330 | 3,244 |

| T thresholds | T=2 | T=1 | T=0 |
|---|---|---|---|
| 0.8 / 0.4 | 2,068 | 1,313 | 264 |
| **1.0 / 0.5 (frozen)** | **1,361** | **1,783** | **501** |
| 1.2 / 0.6 | 767 | 2,059 | 819 |

### Leave-one-score-out: does any single score drive the ranking?

| Score dropped | Spearman vs full ranking | Top band retained (of 135) | Jaccard |
|---|---|---|---|
| P | 0.951 | **49** | **0.21** |
| T | 0.907 | 135 | 0.84 |
| X | 0.938 | 135 | 0.85 |
| F | 0.953 | 89 | 0.66 |
| B | 0.832 | 135 | 0.55 |

**Report this honestly.** Overall the ranking is robust to dropping any one
score (all Spearman ≥ 0.83). But at the top — the 135 genes scoring 8–9 —
removing P retains only 49. **The elite end of the ranking is more
effect-size-driven than "five kinds of evidence agree" implies.**

### Direction, and its cross-checks

Direction is the sign of the cross-study fibrosis rho, fitted across all 668
staged samples within study. The F0→F4 endpoint difference agrees for 3,641
of 3,645 genes (99.9%) and the cluster shape for 3,643. The four
disagreements — DNPH1, FST, SLC5A10, FUNDC2 — all have both a weak rho
(|rho| ≤ 0.18) and a near-zero delta, so these are two noise signals rather
than two strong signals in conflict. They are flagged in the tables and were
**not** relabelled.

### Leave-one-study-out validation

| | |
|---|---|
| **Runs per gene** | **5, not 8** — only five studies stage fibrosis (GSE130970, GSE135251, GSE162694, GSE193066, GSE240729). The other three carry no F0–F4 labels, so there is nothing to leave out. |
| **Recomputed per run** | median rho and Fisher-combined q on the remaining four studies |
| **Criteria reported** | direction kept · still significant · median \|rho\| still ≥ 0.30 · largest % loss in rho |
| **Total runs** | 2,535 (507 genes × 5) |

**One of these criteria cannot fail, and is labelled as such.** Every Tier 1
gene already has all five studies agreeing on direction, so dropping one
leaves four that still agree and the median keeps its sign **by arithmetic**.
All 507 score 5/5 on direction without anything being tested. The two
criteria that *can* fail are reported beside it:

- All 25 shortlisted genes keep direction **and significance** in all 5 runs.
- **19 of 25** also keep median |rho| ≥ 0.30; the six that dip land at
  **0.280–0.292** — grazing the line, not collapsing.
- `LOSO_max_pct_drop_in_rho` is the column that discriminates: MYC 2.6%,
  TREM2 2.7% against TPM4 27.6%, CACNA1C 37.3%. The direction test scores all
  four identically at 5/5.

### The power-matched analysis cannot carry significance — and does not

Measured, not assumed. At 30 patients per stage with FDR across 3,645 genes,
the number of genes significant in ≥ 50% of the 50 draws is **0, 0, 0 and
297** for F0→F1, F1→F2, F2→F3, F3→F4. Scoring X on significance would have
handed every available point to F3→F4 and excluded the three earlier
transitions outright.

**X therefore scores reproducibility** — did the jump stay large and keep its
direction across 50 equal-power redraws (1,522 / 1,856 / 1,713 / 2,790 genes)
— which answers the same question at this sample size, since whether a result
is a fluke depends on which patients were drawn. The strict significance
counts are carried in the master table as
`Matched_frac_significant_NOT_scored`, scoring nothing.

The matched design also uses **4 studies, not 5**: GSE193066 lacks patients at
some stage and cannot contribute an equal cell to every transition.

---

## 7. Mechanism enrichment on the graph (stage 14, Figure 9)

| | |
|---|---|
| **Test** | one-sided hypergeometric of the 507 Tier 1 genes against each pathway / biological-process **node of the graph** |
| **Background** | the same **14,794** genes as §5 |
| **Correction** | BH across nodes |
| **Eligibility** | node holds 10–500 background genes **and** reaches ≥ 10 Tier 1 genes |
| **Threshold** | q < 0.05 |
| **Ranking** | by q-value, not by gene count |
| **De-duplication** | near-duplicate nodes collapsed above **Jaccard 0.5** of Tier 1 membership (1 collapsed: Interleukin-4/13 signalling into cytokine-mediated signalling, Jaccard 0.65) |
| **Kept** | top **12** |
| **Drawn** | genes reaching ≥ 3 of the twelve, plus every one of the 25 reaching any → **46 genes, 169 edges, 58 nodes** |

| Mechanism | Tier 1 genes | Fold | q |
|---|---|---|---|
| Extracellular matrix organization | 56 | 7.46 | 8.5 × 10⁻³⁰ |
| Cell adhesion | 48 | 3.88 | 1.0 × 10⁻¹² |
| Inflammatory response | 41 | 4.00 | 3.6 × 10⁻¹¹ |
| Cytokine-mediated signaling pathway | 34 | 4.28 | 4.6 × 10⁻¹⁰ |
| Positive regulation of ERK1/ERK2 cascade | 28 | 5.17 | 4.6 × 10⁻¹⁰ |
| Integrin cell surface interactions | 20 | 7.39 | 8.1 × 10⁻¹⁰ |
| ECM proteoglycans | 18 | 7.72 | 3.7 × 10⁻⁹ |
| Angiogenesis | 31 | 4.27 | 3.7 × 10⁻⁹ |
| Integrin-mediated signaling pathway | 20 | 6.41 | 9.5 × 10⁻⁹ |
| Signaling by PDGF | 12 | 11.30 | 6.6 × 10⁻⁸ |
| Collagen fibril organization | 19 | 5.90 | 1.2 × 10⁻⁷ |
| Positive regulation of collagen biosynthetic process | 10 | 13.26 | 2.8 × 10⁻⁷ |

**Why rank by q and not count.** Count alone promotes "positive regulation of
gene expression", "negative regulation of apoptotic process" and
"positive/negative regulation of cell population proliferation" into the top
twelve — terms that appear in almost any gene list. They are significant here
too, but only 2.3–3.0× enriched against 3.9–13.3× for the twelve kept, and q
weighs size and fold together, so they fall away without a hand-picked fold
cutoff.

**Convergence, as measured** (see `05_LIMITATIONS.md` §7 before using these):

| | |
|---|---|
| Tier 1 genes reaching ≥ 1 of the twelve | **166** of 507 |
| Tier 1 genes reaching ≥ 3 | **39** |
| Pathways connecting ≥ 2 Tier 1 genes | 328 |
| Pathways connecting ≥ 3 Tier 1 genes | 163 |
| **Of the final 25**: reaching ≥ 1 of the twelve | **8** |
| **Of the final 25**: reaching ≥ 3 | **1** (PDGFRA) |
| Among the 25: pathways connecting ≥ 2 of them | 2 |
| Among the 25: pathways connecting ≥ 3 of them | **0** |

**Provenance caveat.** These nodes come from the superseded PrimeKG
knowledge layer, not from the OptimusKG layer that the graph itself holds --
see `05_LIMITATIONS.md` section 14.

Full ranked node table (4,034 nodes with fold, p, q and every filter flag):
`02_TABLES/supplementary/TableS17_knowledge_graph_connections.xlsx`, sheet
`3_all_mechanisms_ranked`. Two of the 507 Tier 1 genes have no
knowledge-graph connection at all, so per-gene connection sheets cover 505.

---

## What was *not* done, and should not be claimed

- **No differential expression analysis.** No two-group comparison, no
  DESeq2/limma/edgeR, no log fold changes. Every result here is a correlation
  or a model coefficient along an ordered stage ladder. Use "increasing /
  decreasing with stage", not "up/downregulated".
- **No batch-correction algorithm** (no ComBat or similar). Study effects are
  handled by standardising within study (§0) and by including `study` as a
  model term (§4). This is a deliberate choice: per-study standardisation
  cannot leak information between cohorts the way a fitted correction can.
- **No survival, outcome or longitudinal analysis.** The cohort is
  cross-sectional; the 58 repeat biopsies are treated as a
  pseudo-replication problem, not as a time series.
- **No validated predictive model.** Despite the aim being stage prediction,
  no classifier was trained, cross-validated or reported. This project
  delivers the stage-resolved gene sets a model would be built *from*.
- **No verified link prediction.** The pipeline exists; the first model
  failed its own validation. Treat any repurposing output as unverified.
