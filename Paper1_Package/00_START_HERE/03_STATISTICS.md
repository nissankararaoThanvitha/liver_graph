# 3. Every statistic

One place for every test, with its unit of analysis, sample size,
multiple-testing correction, threshold and result — written so a Methods
section can be assembled without opening a script, and so any number in the
paper can be traced to the file it came from.

**Software**, pinned in `05_CODE/requirements.txt` and the versions these
results were produced with: Python 3.13.7, pandas 2.3.3, numpy 2.2.4,
scipy 1.16.3, scikit-learn 1.7.2, matplotlib 3.10.7, gseapy 1.3.1.

---

## 0. Conventions applying to every test below

| | |
|---|---|
| **Measured quantity** | `value_z` — expression standardised per gene within each study. Effect sizes are in standard deviations of that gene within that study. |
| **Unit of analysis** | the **patient**, never the sample. Each patient contributes once. |
| **Eligible gene set** | the **14,794** genes measured in all eight studies. This is the tested set and the enrichment background throughout. |
| **Multiple testing** | Benjamini–Hochberg FDR within each family of tests; the family is stated per test. |
| **Significance** | q < 0.05 unless stated otherwise. |
| **Cross-study rule** | statistics are computed **within each study** and then combined. Patients are never pooled across studies. |

---

## 1. Progression-gene identification

| | |
|---|---|
| **Test** | Spearman rank correlation of `value_z` against ladder position, **within each study** |
| **Why Spearman** | stages are ordered ranks whose spacing is not meaningful |
| **Combination** | per-study rho by **median**; per-study p by **Fisher's method** |
| **Inclusion** | **every study that tested the gene must agree on direction** |
| **n, fibrosis ladder** | 668 staged samples, 5 studies, collapsed to patients |
| **n, disease ladder** | 221 patients, 3 studies |
| **Genes tested** | 14,794 |
| **Correction** | BH across 14,794 genes, separately per ladder |
| **Result** | **5,884** progression genes: 3,681 fibrosis, 4,018 disease, 1,815 both |

Full statistics for all 14,794 genes, significant or not, are in
`04_DATA/progression_genes/`. `min_rho` and `max_rho` give the per-study
range — the fastest check that a signal is not carried by one cohort.

---

## 2. Agreement between the ladders

Spearman of fibrosis rho against inflammation rho among shared genes:
**0.657**, n = 1,815. Discordant genes: 13.

A correlation computed across both directions measures the separation between
the rising and falling clouds as much as the association within them; the
within-direction values in
`03_RESULTS/Task1_gene_groups/README.txt` are the conservative estimate.

---

## 3. Trajectory clustering

| | |
|---|---|
| **Input** | 3,681 fibrosis genes × 5 stage means |
| **Pre-processing** | each gene's stage means z-scored **across stages**, so clustering is on shape |
| **Algorithm** | K-means, 50 random initialisations |
| **k tested** | 3 to 8 |
| **Criteria** | silhouette; gene-subsample stability (50 reclusterings of 80% subsets); patient-bootstrap stability (50 resamples within study) |
| **Stability metric** | adjusted Rand index against the full-data clustering |
| **Reported** | **k = 5** — see `04_LIMITATIONS.md` §8 |
| **Shape reproducibility** | 100 patient bootstraps; each shape recovered at median correlation **0.96–0.996** |
| **Study-mix control** | profiles re-estimated as `value_z ~ stage + study`; median per-gene curve correlation **0.998**; reclustering gives **ARI 0.82** |

Stage sample sizes behind the means: **F0 152, F1 168, F2 186, F3 127,
F4 35.**

| k | Silhouette | Gene-subsample ARI | Patient-bootstrap ARI |
|---|---|---|---|
| 3 | 0.560 | 0.984 | 0.756 |
| 4 | 0.457 | 0.977 | 0.567 |
| **5** | **0.334** | **0.964** | **0.519** |
| 6 | 0.294 | 0.951 | 0.461 |
| 7 | 0.275 | 0.779 | 0.406 |
| 8 | 0.264 | 0.764 | 0.392 |

**Membership confidence.** Each bootstrap's clusters are matched to the main
ones by Hungarian assignment on centroid correlation. A gene is scored only
in the bootstraps where **its own cluster was matched soundly** (matched-pair
correlation ≥ 0.5); the per-gene denominator is published as
`confidence_n_bootstraps`. Scoring a gene against a bootstrap whose matching
failed measures the matching, not the gene.

---

## 4. Stage-transition analysis

| | |
|---|---|
| **Model** | `value_z ~ stage + study`, fitted on the patients of the two stages only |
| **Why `+ study`** | stages are compared **within** each study, so a difference in stage mix cannot create a false change |
| **Test** | t-test on the stage coefficient |
| **Correction** | BH **within each transition**, across 3,681 genes |
| **"Substantial"** | q < 0.05 **and** \|beta\| ≥ 0.2 SD |
| **Power-matched refit** | 50 refits per transition on the same study-balanced design of **30 patients per stage** |

| | F0→F1 | F1→F2 | F2→F3 | F3→F4 |
|---|---|---|---|---|
| Substantial genes | 1,197 | 1,145 | 1,127 | 934 |
| — increasing | 1,164 | 639 | 909 | 869 |
| — decreasing | 33 | 506 | 218 | 65 |
| Median \|beta\| | 0.189 | 0.185 | 0.221 | **0.375** |
| **Power-matched median** | **0** | **0** | **2** | **287** |

`|beta| ≥ 0.2 SD` is a conventional, not a unique, cutoff; the effect-size
panel does not depend on it.

---

## 5. Pathway enrichment

| | |
|---|---|
| **Test** | one-sided hypergeometric (over-representation), `gseapy.enrich`, run locally |
| **Background** | the **14,794** eligible genes — **not** the whole genome |
| **Gene-set restriction** | every set intersected with the background, then kept only if 10–500 genes remained |
| **Collection** | MSigDB v2024.1, human gene symbols |
| **Correction** | BH within each **group × database** |
| **Threshold** | FDR < 0.05 |
| **Verification** | one p-value recomputed from `scipy.stats.hypergeom` matched gseapy exactly |
| **Groups** | 6 ladder groups + 5 clusters (all genes) + 5 clusters (confident members), each separately |

Groups with fewer than five genes in the background are recorded as untestable
rather than reported as zero findings.

Reported columns: `overlap`, `set_size`, `gene_ratio`, `bg_ratio`,
`fold_enrichment`, and the genes responsible.

---

## 6. Evidence scoring and prioritisation

Not a hypothesis test — a ranking by agreement between five independent
measurements, each computed above. **All cutoffs were fixed as named
constants before any ranked list was inspected.**

| | Score | 2 points | 1 point | Reads from |
|---|---|---|---|---|
| **P** | Progression strength | \|rho\| ≥ 0.40 | ≥ 0.30 | §1 |
| **T** | Trajectory | \|F4 − F0\| ≥ 1.0 SD | ≥ 0.5 SD; 0 if direction conflicts | §3 |
| **X** | Transition | largest jump substantial in the full fit **and** reproducible in ≥ 50% of 50 draws | one of the two | §4 |
| **F** | Fibrosis specificity | — | fibrosis-only | §1 |
| **B** | Biological support | enriched in ≥ 2 of 4 databases | in 1 | §5 |

Total 0–9. **Tier 1 = 7–9 (525)** · Tier 2 = 5–6 (1,464) · Tier 3 = < 5
(1,692).

**Sensitivity**, measured and reported rather than used to choose: the Tier 1
boundary at 6 and at 8 (`TableS14`), the P thresholds one step tighter and
looser (`TableS16`), the T thresholds likewise (`TableS17`), and each score
dropped in turn with the ranking recomputed (`TableS15`).

**The power-matched analysis cannot carry significance.** At 30 patients per
stage with correction across 3,681 genes, genes significant in ≥ 50% of draws
number **0, 0, 0 and 292** across the four transitions. X therefore scores
**reproducibility** — did the jump stay large and keep its direction across
50 equal-power redraws — and the strict counts are carried as
`Matched_frac_significant_NOT_scored`, scoring nothing. The matched design
uses four studies, not five.

**Direction** is the sign of the cross-study fibrosis rho, cross-checked
against the F0→F4 endpoint difference and the assigned cluster shape. Two
genes disagree; both have a weak rho and a near-zero delta, and both are
flagged rather than relabelled.

### Leave-one-study-out

| | |
|---|---|
| **Runs per gene** | **5** — only five studies stage fibrosis |
| **Recomputed per run** | median rho and Fisher-combined q on the remaining four studies |
| **Reported** | direction kept · still significant · median \|rho\| ≥ 0.30 · largest % loss in rho |
| **Total runs** | 2,625 (525 × 5) |

| Measure | 5/5 | Lower |
|---|---|---|
| Direction kept | 525 | — |
| Still significant | **521** | 4 at 4/5 |
| Still strong (\|rho\| ≥ 0.30) | **263** | 85 at 3/5 · 101 at 2/5 · **76 at 0/5** |

Direction cannot fail for this gene set — see `04_LIMITATIONS.md` §9.

---

## 7. Mechanism enrichment on the graph

| | |
|---|---|
| **Test** | one-sided hypergeometric of the 525 Tier 1 genes against each pathway / biological-process node |
| **Background** | the same **14,794** genes as §5 |
| **Correction** | BH across nodes |
| **Eligibility** | node holds 10–500 background genes **and** reaches ≥ 10 Tier 1 genes |
| **Threshold** | q < 0.05 |
| **Ranking** | by q-value, not gene count |
| **De-duplication** | near-duplicates collapsed above Jaccard 0.5 of Tier 1 membership |
| **Kept** | top **12** of 85 passing all filters |
| **Drawn** | genes reaching ≥ 3 of the twelve, plus every shortlisted gene reaching any → **47 genes, 165 edges** |

Fold enrichments run 3.4–9.6× at q from 6 × 10⁻¹² to 5 × 10⁻⁹. Ranking by
gene count instead promotes terms appearing in almost any gene list, enriched
only 2–3×.

The full ranked node table is `TableS19`, sheet `3_all_mechanisms_ranked`.

---

## What was not done, and should not be claimed

- **No differential expression analysis.** No two-group comparison, no
  DESeq2/limma/edgeR, no log fold changes. Every result is a correlation or a
  model coefficient along an ordered stage ladder. Use "increasing /
  decreasing with stage".
- **No batch-correction algorithm.** Study effects are handled by
  standardising within study (§0) and by including `study` as a model term
  (§4).
- **No survival, outcome or longitudinal analysis.** The cohort is
  cross-sectional.
- **No validated predictive model.** No classifier, no AUC, no held-out test
  set.
