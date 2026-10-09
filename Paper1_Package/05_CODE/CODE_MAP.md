# Current code map

Use root scripts from the repository root; source copies in05_CODE are for reproducibility review and retain path assumptions.

- pipeline01–06: expression parsing, ID mapping, crosswalk, clinical labels, union measurement build and OptimusKG integration.
- biopsy_policy.py: shared equal-stage mean/otherwise biopsy1 policy; locates explicitly named expression analysis core when present.
- pipeline07: Spearman/Fisher/BH discovery. Default same_stage_mean; first/average options retained only for historical comparison.
- pipeline08: independent-patient group summaries, retaining raw sample metadata with biopsy order.
- pipeline09: progression-edge generation from corrected selections.
- analysis: Task1groups; Task2profiles/k/bootstrap; Task3contrasts/matched refits; Task4local MSigDB enrichment; Figure1design.
- prioritisation: hc0union→hc1matched→hc2scores→hc3LOSO→hc2final→hc4network. Top25/top12 rules unchanged.
- validation: mapping/parse inspection, membership matching diagnosis, graph counts, exact mechanism memberships and version comparison. Historical recorded counts in the old verifier must not be treated as current live results; use--live.
- cypher: unique constraints; full-expression replacement (do not use the recovered core to reload); curated knowledge and patient-derived links.

The recovered14,794-gene expression subset is data/expression_analysis_core, distinct from a full expression-load export. All association/robustness scripts use that directory when available. Missing source assets are declared in provenance. Link prediction remains separate, previously failed work.

