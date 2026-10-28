# Final ranking — pre-registered rules (written before ranks were computed)

Date: 21 Oct 2026. Paper 1: final combined version, 10 Oct 2026 (confirmed final by the Paper 1 team).

| Rule | Frozen value |
|---|---|
| paper1_version | final combined version, 10 Oct 2026 (confirmed final by the Paper 1 team) |
| target_components | P, F, T, K, B |
| biology_list | P, F, T, B |
| actionable_list | P, F, T, K, B |
| target_weights | equal (the default named in the Task 6 framework; not tuned) |
| drug_components | D1_target_relevance, D2_direction, D3_specificity, D4_graph_support |
| drug_weights | equal |
| drug_universe | Task 4 repurposing candidates (1,109); primary ranking = mechanism-annotated main list (559) |
| stability | 1,000 Dirichlet(alpha=10) weight draws, seed 42; stable = P(top-N) >= 0.8; N = 50 targets, 25 drugs |
| stress_test | Dirichlet(alpha=1) also reported |
| ablation | drop each component, renormalise; Spearman, Kendall, top-N overlap |
| never | no weight tuning after seeing ranks; no external data; no efficacy claims |

Component definitions: `Task6/target_score_framework.md` (targets) and the docstring of
`code/final_ranking.py` (drugs). The equal-weight Task 6 prototype was seen before this
freeze; equal weights were already named there as the default, and the stability analysis
below is the safeguard against relying on any single weight choice.
