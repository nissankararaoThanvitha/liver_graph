# Frozen sensitivity protocol

Prepared10 October2026. No active labels, numerical results, scoring rules or graph relationships are changed by this experiment.

## Design

| Run | GSE130970 diagnosis labels | GSE193066 expression transform |
|---|---|---|
| baseline | Current derived labels | Current matrix-total/CPM-style rescaling,log2(+1),study/gene z |
| labels_only | Five flagged cases unclassified | Current transform |
| normalisation_only | Current labels | Deposited linear RLE counts,log2(+1),study/gene z |
| combined | Five flagged cases unclassified | Preserve RLE,log2(+1),study/gene z |

Unclassified means a blank disease_group with explicit sensitivity provenance; fibrosis stages and all raw fields remain unchanged. The cases are GSM3758028,GSM3758038,GSM3758039,GSM3758073,GSM3758074. The remaining labels are still derived and unverified; this is not recovery of the original diagnoses.

The alternate transform sums mapped aliases as before,uses the same14,794 eligible genes,standardises over the same164 GSE193066 biopsies with sample SD (ddof1),preserves zeros,and applies the already corrected biopsy policy only at analysis. The other seven studies are identical across runs.

## Fixed analyses

Use copied current source scripts and pinned core dependencies. Discovery eligibility,Spearman/Fisher/BH rules,biopsy selection,score thresholds,top25 cluster quotas and top12 mechanism rules are unchanged. Fit k5 in every run to make shape comparisons interpretable; report automatic k diagnostics separately,without silently choosing a different number. Compare clusters by both raw IDs and centroid-matched shapes if labels move.

Every main run includes discovery,patient exports,groups,clustering/bootstrap,transitions,matched refits,enrichment,scoring,full-universe LOSO,final shortlist,mechanism network and edge exports. Baseline will first be checked against the active output statistics/memberships.

## Specificity-feature ablation

For each main run,examine P+T+X+B with F set to0. Keep Tier1 cutoff7 unchanged (new maximum8); this is a labelled stricter ablation,not a new default method. Keep five-per-cluster shortlist quota,score then|rho|. If a cluster has fewer than five eligible genes,report fewer than25 candidates; never lower thresholds or add genes solely to fill slots. No change is made to the normal scoring functions.

Use the existing all-eligible LOSO calculations to assess any ablation-selected genes. If a network is computed for an ablation,it must use that ablation's actual Tier1 set and the same mechanism-selection rules.

## Outputs and interpretation

Report selected-gene counts and actual membership changes,shared/specific classifications,cluster ARI/shape matching/confidence,transition effect/count changes,enrichment changes,Tier1 overlap,shortlist overlap and per-gene scores/LOSO confidence. Compare the combined run both to baseline and to each single-change run.

Rank/gene-list stability is sensitivity evidence,not independent clinical or therapeutic validation. Do not choose a method because it yields preferred targets. Do not adopt or update the live graph before reviewing the comparisons and selecting a final strategy.

Source/input/runtime hashes,commands,logs and active-file preservation checks are saved. Bulk matrices and duplicate frozen inputs are excluded from Git; manifests make their identity explicit. Commit checkpoints: input preparation; verified main sensitivity runs; scoring ablation and final comparison.
