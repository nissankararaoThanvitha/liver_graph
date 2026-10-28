# Paper 2 — Task 3: druggability across progression-gene groups

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **6,222 genes**.
**Scope:** knowledge graph only (project scope decision). **Graph source:** Neo4j (live liver_kg, read-only).
Script: `Paper2_Results_Idea1/code/task3_druggability.py`.

## Key findings (definition B, pharmacological targets)
1. **Fibrosis-associated genes are over-represented among drug targets**: 16.6% vs 13.0% background (fold 1.30 vs degree-matched; permutation FDR 0.004). This holds beyond network connectivity.
2. **Inflammation-only genes are not**: 13.4% (fold 0.98; FDR 0.827). Fibrosis-only and shared genes are each more druggable than inflammation-only genes (pairwise FDR 0.028 and 0.002).
3. **The excess comes mainly from genes that FALL with fibrosis**: shared ⬇⬇ 22.7% (fold 1.85) and fibrosis-only ⬇ 19.3% (fold 1.55). Rising fibrosis-only genes are at background (12.8%), and rising shared genes are modestly enriched (15.9%, fold 1.19).
4. **Removing ENZYME/TRANSPORTER/CARRIER links does not change these conclusions** (compare A and B), although it removes many liver drug-metabolism genes (CYPs, ABC/SLC transporters) from the falling groups.
5. **Repurposing implication**: falling genes would need drugs that *raise* their activity (agonists/activators), which are rarer in the graph than inhibitors. This is examined in Task 7.

## Background used
`data/expression_analysis_core` is **not present** in this checkout, so the background is the **14,794 eligible genes** (all-eight-study analysis universe) in `Paper1_HighConfidence/10_loso_all_eligible_runs.csv`. All 6,222 progression genes lie inside it. Drug flags for progression genes match Task 2 exactly.

## Two definitions of "drug-connected"
- **A. Any drug**: ≥1 `Drug-[:ACTS_ON]->Gene` line. Background: 2,148 / 14,794 (14.5%).
- **B. Pharmacological target**: ≥1 line whose action is **not** ENZYME, TRANSPORTER or CARRIER. Background: 1,921 / 14,794 (13.0%).

Why B is needed: ENZYME/TRANSPORTER/CARRIER lines mostly say the gene **metabolises or moves the drug** (e.g. CYP1A2, CYP2C19, CYP2E1, ABCG2). They do not say the drug acts *on* the gene to change disease biology. Genes that **fall** with fibrosis include many such liver drug-metabolism genes:

| paper1_group | edges | pct_enzyme_transporter_carrier | top enzyme/transporter genes |
|---|---|---|---|
| fibrosis_only_negative | 2845 | 58.9 | ALB, CYP3A5, CYP2C8, SLCO1B1 |
| fibrosis_only_positive | 882 | 17.9 | ABCC1, PTGS1, ABCC5, NME2 |
| inflammation_only_negative | 322 | 40.4 | CYP1A1, SLC16A1, FPGS, CACNB2 |
| inflammation_only_positive | 1555 | 32.3 | CYP3A7, SLC15A1, SLC22A11, CYP1B1 |
| shared_discordant_fib_negative | 14 | 42.9 | UGT2B10, SCARB1 |
| shared_negative | 1772 | 71.5 | CYP1A2, CYP2C19, ABCG2, CYP2E1 |
| shared_positive | 1558 | 14.2 | ABCC4, PTGS2, SLCO2A1, DCK |

**Definition B is the one to use for repurposing.** A is reported for completeness and comparison with the plan.

## A. Any drug link

| Group | Genes | Connected | % (95% CI) | Drugs | OR (95% CI) | Fisher FDR | Matched exp. % | Fold vs matched | Perm FDR |
|---|---|---|---|---|---|---|---|---|---|
| All progression genes | 6,222 | 1,072 | 17.2 (16.3–18.2) | 3,027 | 1.45 (1.32–1.59) | 1.55e-14 | 14.7 | 1.17 | 0.004 |
| Fibrosis-associated (fibrosis-only + shared) | 3,845 | 717 | 18.6 (17.4–19.9) | 2,580 | 1.52 (1.38–1.68) | 2.01e-15 | 14.4 | 1.29 | 0.004 |
| fibrosis_only | 2,023 | 358 | 17.7 (16.1–19.4) | 1,794 | 1.32 (1.16–1.50) | 4.26e-05 | 14.2 | 1.25 | 0.004 |
| shared | 1,822 | 359 | 19.7 (17.9–21.6) | 1,761 | 1.53 (1.35–1.74) | 2.71e-10 | 14.6 | 1.35 | 0.004 |
| inflammation_only | 2,377 | 355 | 14.9 (13.6–16.4) | 1,202 | 1.04 (0.92–1.18) | 0.573 | 15.2 | 0.99 | 0.881 |
| fibrosis_only_positive | 1,040 | 142 | 13.7 (11.7–15.9) | 651 | 0.93 (0.77–1.11) | 0.525 | 14.3 | 0.96 | 0.799 |
| fibrosis_only_negative | 983 | 216 | 22.0 (19.5–24.7) | 1,482 | 1.73 (1.47–2.03) | 2.34e-10 | 14.1 | 1.56 | 0.004 |
| shared_positive | 1,408 | 247 | 17.5 (15.7–19.6) | 1,035 | 1.28 (1.11–1.49) | 0.002 | 14.8 | 1.18 | 0.010 |
| shared_negative | 384 | 105 | 27.3 (23.1–32.0) | 1,137 | 2.28 (1.79–2.88) | 1.34e-10 | 14.0 | 1.96 | 0.004 |
| shared_discordant_fib_negative | 30 | 7 | 23.3 (11.8–40.9) | 14 | 1.79 (0.65–4.33) | 0.284 | 14.3 | 1.63 | 0.405 |
| inflammation_only_positive | 2,042 | 309 | 15.1 (13.6–16.8) | 1,074 | 1.06 (0.93–1.21) | 0.525 | 15.3 | 0.99 | 0.881 |
| inflammation_only_negative | 335 | 46 | 13.7 (10.4–17.8) | 285 | 0.94 (0.67–1.29) | 0.754 | 14.2 | 0.96 | 0.881 |

Pairwise class comparisons (Fisher, BH-FDR):

| Comparison | %A | %B | OR (95% CI) | BH-FDR |
|---|---|---|---|---|
| fibrosis_only vs inflammation_only | 17.7 | 14.9 | 1.23 (1.04–1.44) | 0.021 |
| shared vs inflammation_only | 19.7 | 14.9 | 1.40 (1.19–1.65) | 1.71e-04 |
| fibrosis_only vs shared | 17.7 | 19.7 | 0.88 (0.74–1.03) | 0.115 |

## B. Pharmacological target only (recommended)

| Group | Genes | Connected | % (95% CI) | Drugs | OR (95% CI) | Fisher FDR | Matched exp. % | Fold vs matched | Perm FDR |
|---|---|---|---|---|---|---|---|---|---|
| All progression genes | 6,222 | 958 | 15.4 (14.5–16.3) | 2,407 | 1.44 (1.30–1.58) | 8.53e-13 | 13.2 | 1.17 | 0.004 |
| Fibrosis-associated (fibrosis-only + shared) | 3,845 | 639 | 16.6 (15.5–17.8) | 1,923 | 1.50 (1.35–1.67) | 3.43e-13 | 12.8 | 1.30 | 0.004 |
| fibrosis_only | 2,023 | 323 | 16.0 (14.4–17.6) | 1,225 | 1.33 (1.16–1.51) | 6.08e-05 | 12.6 | 1.27 | 0.004 |
| shared | 1,822 | 316 | 17.3 (15.7–19.1) | 1,166 | 1.49 (1.30–1.70) | 3.42e-08 | 13.1 | 1.33 | 0.004 |
| inflammation_only | 2,377 | 319 | 13.4 (12.1–14.8) | 874 | 1.05 (0.92–1.19) | 0.646 | 13.7 | 0.98 | 0.827 |
| fibrosis_only_positive | 1,040 | 133 | 12.8 (10.9–15.0) | 549 | 0.98 (0.81–1.19) | 0.966 | 12.7 | 1.01 | 0.955 |
| fibrosis_only_negative | 983 | 190 | 19.3 (17.0–21.9) | 847 | 1.67 (1.41–1.98) | 2.35e-08 | 12.4 | 1.55 | 0.004 |
| shared_positive | 1,408 | 224 | 15.9 (14.1–17.9) | 915 | 1.30 (1.11–1.52) | 0.001 | 13.3 | 1.19 | 0.014 |
| shared_negative | 384 | 87 | 22.7 (18.8–27.1) | 416 | 2.01 (1.55–2.57) | 2.97e-07 | 12.3 | 1.85 | 0.004 |
| shared_discordant_fib_negative | 30 | 5 | 16.7 (7.3–33.6) | 8 | 1.34 (0.40–3.57) | 0.699 | 12.9 | 1.29 | 0.827 |
| inflammation_only_positive | 2,042 | 276 | 13.5 (12.1–15.1) | 775 | 1.05 (0.92–1.21) | 0.646 | 13.9 | 0.97 | 0.827 |
| inflammation_only_negative | 335 | 43 | 12.8 (9.7–16.8) | 173 | 0.99 (0.70–1.37) | 1.000 | 12.6 | 1.02 | 0.955 |

Pairwise class comparisons (Fisher, BH-FDR):

| Comparison | %A | %B | OR (95% CI) | BH-FDR |
|---|---|---|---|---|
| fibrosis_only vs inflammation_only | 16.0 | 13.4 | 1.23 (1.03–1.46) | 0.028 |
| shared vs inflammation_only | 17.3 | 13.4 | 1.35 (1.14–1.61) | 0.002 |
| fibrosis_only vs shared | 16.0 | 17.3 | 0.91 (0.76–1.08) | 0.259 |

**Column guide:** % = observed drug-connected fraction (95% Wilson CI). OR/Fisher = group vs rest of background (2×2 Fisher's exact; conditional MLE odds ratio), BH-FDR across the 12 groups. Matched exp. % = mean of 1,000 random background gene sets with the same INTERACTS_WITH degree profile (10 deciles + a degree-0 bin, seed 42). Perm FDR = two-sided empirical p, BH across groups.

## Why degree matters (study bias)
Background genes with more known protein–protein interactions are more likely to have a known drug:

| degree_bin | genes | degree range | pct_any | pct_pharm |
|---|---|---|---|---|
| 0 | 571 | 0–0 | 6.8 | 5.8 |
| 1 | 1423 | 1–3 | 11.2 | 8.6 |
| 2 | 1422 | 3–6 | 12.1 | 9.5 |
| 3 | 1422 | 6–10 | 14.6 | 12.7 |
| 4 | 1422 | 10–15 | 14.3 | 12.5 |
| 5 | 1423 | 15–21 | 13.9 | 12.5 |
| 6 | 1422 | 21–28 | 13.3 | 11.8 |
| 7 | 1422 | 28–38 | 14.8 | 13.4 |
| 8 | 1422 | 38–53 | 14.1 | 13.2 |
| 9 | 1422 | 53–88 | 15.5 | 14.8 |
| 10 | 1423 | 88–5189 | 24.4 | 23.8 |

A raw difference can therefore just mean "better-studied genes". The degree-matched permutation removes this: a group counts as more or less druggable **beyond connectivity** only if its observed % lies outside its degree-matched null.

## Interpretation and caveats
- Percentages describe **representation among known drug targets in the knowledge graph**. They partly reflect which genes scientists have studied and drugged (DrugBank/Open Targets annotation bias), not biology alone.
- Druggability is not therapeutic relevance. A drug-connected gene is a *repurposing hypothesis entry point*, not evidence a drug would help.
- Groups are kept separate as in Paper 1. The 30 shared genes with discordant direction are reported on their own and are small (wide CIs).
