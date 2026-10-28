# Paper 2 — Task 6: target-prioritisation framework

> **Status:** Paper 1 was confirmed final, and equal weights were frozen for the final ranking (`Final_ranking/PREREGISTRATION.md`). Final target lists: `Final_ranking/`.

**Purpose.** Rank therapeutic *targets* first, then drugs. Every component is traceable to a Paper 1 or Paper 2 output and lies in [0, 1].
**Universe:** the corrected Paper 1 union of **6,222 progression genes** (the plan's 4,692 was the pre-correction count).
**Scope:** knowledge graph + Paper 1 only; this is drug repurposing, not reversal (project scope decision).

$$\text{TargetScore}(g)=\frac{w_1P(g)+w_2F(g)+w_3T(g)+w_4K(g)+w_5B(g)}{\sum_i w_i},\qquad w_i\ge 0$$

## 1. Component definitions

| | Meaning | Definition (source columns) |
|---|---|---|
| **P** | Progression evidence: strength, significance, robustness of direction | Fibrosis genes: P = 0.5·pct(\|`fibrosis_rho`\|) + 0.2·pct(−log10 `fibrosis_q`) + 0.3·D. D = ½·[½ + ½·(sign(`fibrosis_min_rho`) = sign(`fibrosis_max_rho`))] + ½·[½·LOSO share still significant + ½·LOSO share direction kept] (`00_all_progression_genes.csv`, `10_loso_all_eligible_runs.csv`). Effect size dominates and q gets a small weight, because every gene already passed FDR < 0.05 (Paper 1 rationale). Inflammation-only genes: the same formula on `inflammation_rho`/`inflammation_q` (no LOSO), multiplied by λ = 0.5. Direction (rising/falling) is kept as a label: it decides which drug action is direction-consistent (Task 7), not how good a target is. |
| **F** | Fibrosis specificity | fibrosis_only = 1, shared (concordant) = 2/3, shared discordant = 1/3, inflammation_only = 0 (`progression_class`, `paper1_group`). This is a graded version of Paper 1's binary F, and it stays a bonus, never a filter. |
| **T** | F0–F4 trajectory and stage-transition evidence | Fibrosis genes: T = mean of T1 = pct(\|`delta_F0_F4`\|)·`delta_agrees`, T2 = `membership_confidence` (bootstrap cluster stability), T3 = pct(−log10 `transition_q`)·`matched_frac_reproducible` for the gene's largest stage jump (`01_master_table.csv`). The cluster label (C1–C5) is **not** scored, since no shape is "better". It is used for stage-stratified lists (top-k per cluster), as in Paper 1. |
| **K** | Knowledge-graph evidence (tractability) | Mean of K1 = pct(log1p pharmacological drugs), K2 = pct(log1p phase ≥ 2, non-withdrawn drugs), K3 = any multi-source drug link, K4 = any drug with known direction, K5 = max OptimusKG `ASSOCIATED_WITH` score to fibrosis-spectrum liver diseases, K6 = best Task 5 M1f degree-normalised support among the gene's drugs (`drug_gene_edges.csv` pharmacological links, `metapath_drug_scores.csv`, live graph). |
| **B** | Biological / pathway evidence | B = 0.5·(databases with a fibrosis-enriched term containing g)/4 + 0.5·pct(log1p number of such terms), over GO_BP, Reactome, KEGG, Hallmark terms enriched in fibrosis_only / shared / C1–C5 groups (`paper1_term_genes_long.csv`). This reproduces Paper 1 `n_databases` for 99.2% of fibrosis genes. |

pct(·) is the percentile rank in [0, 1] within the gene's own evidence set, using average ties.

## 2. Normalisation and missing values
- **Normalisation:** percentile ranks, which are robust to the skewed ρ, q and degree distributions and put every input on the same 0–1 scale. Binary inputs stay 0/1. OptimusKG association scores are already 0–1. Count inputs are log1p-transformed before ranking, and zero counts stay 0 ("no evidence earns no credit").
- **Structural zeros, not imputation.** Missing evidence is informative here, so nothing is imputed:
  - Inflammation-only genes have no fibrosis trajectory, so T = 0 and B (fibrosis terms) = 0.
  - A gene with no drug gets K1–K4 and K6 = 0, but can still earn K5 from disease association, which keeps undrugged (novel) targets visible.
  - Every row carries the raw counts so missingness can be audited.
- **λ (inflammation-only P scale)** is tested at 0, 0.5 and 1.

## 3. Ablation plan (before any final ranking)
Drop each component (and the pair K+B, giving a "knowledge-free" biology-only score), renormalise the remaining weights, and compare with the full score:
- Spearman and Kendall rank correlation;
- top-50 overlap;
- median absolute rank shift;
- median rank of the 23 Paper 1 shortlist genes.

Report a component as **driving** the ranking if removing it changes top-50 membership by > 20%.

## 4. Weight-sensitivity / robustness plan
- **Dirichlet weights:** 1,000 draws with seed 42 at α = 1 (anywhere on the simplex, a stress test) and α = 10 (near-equal, the plausible range).
- **Per gene:** median rank, 5th–95th percentile rank, and P(top-50).
- **Stable target:** P(top-50) ≥ 0.8 under α = 10.
- **Overall:** median and 5th-percentile Spearman versus equal weights.
- **Freezing rule:** weights are frozen only after Paper 1 is final, by a pre-registered rule (e.g. equal weights, or weights fixed before inspecting ranked lists). They are never tuned to obtain a desired ranking. Final reports give stable-target lists, not single-weight ranks. **Applied:** equal weights, frozen in `Final_ranking/PREREGISTRATION.md` before the final ranking.

## 5. What the design test (equal weights) showed
See `design_test_report.md`.
1. **P, F and T overlap** (Spearman 0.56–0.80), because they all describe fibrosis association. Consider merging P and T, or down-weighting them, so fibrosis strength is not counted three times.
2. **K is zero for 83% of genes,** so it acts like a druggability gate. Without K, top-50 overlap falls to 24. Recommendation: **report two lists**, a *biology score* (P, F, T, B) for novel targets and an *actionable score* (with K) for repurposing.
3. **Weights matter.** Under α = 1 only 7 genes stay in the top 50 in ≥ 80% of draws (29 under α = 10). This confirms that stable-target reporting is needed.
4. **Paper 1 sanity check:** Spearman 0.87 with Paper 1's HighConfidenceScore on fibrosis genes. That's consistent, but partly circular, because P, T and B reuse Paper 1 evidence.
5. **λ has no effect on the top 50,** because inflammation-only genes score 0 on F, T and B.

## 6. From targets to drugs (later, after Paper 1 is final and Task 7)
DrugScore(d) will combine the TargetScores of d's targets with direction-consistency (Task 7), progression_target_fraction (Task 4) and the Task 5 support. Shortlist-supported versus broad-evidence-only candidates will be reported separately. Outputs remain **repurposing hypotheses**.
