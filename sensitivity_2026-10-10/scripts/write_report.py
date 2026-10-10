from pathlib import Path
import json,csv
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parents[1];s=pd.read_csv(D/'comparison_summary.csv');short=pd.read_csv(D/'shortlist_comparison.csv');net=pd.read_csv(D/'network_comparison.csv');details=json.loads((D/'membership_and_cluster_details.json').read_text());checks=json.loads((D/'verification_results.json').read_text());assert all(x['passed'] for x in checks)
def table(frame):
 cols=list(frame.columns);rows=['| '+' | '.join(cols)+' |','| '+' | '.join('---' for _ in cols)+' |'];rows.extend('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in frame.fillna('').itertuples(index=False,name=None));return '\n'.join(rows)
order=['baseline','labels_only','normalisation_only','combined'];sets={r:set(short[(short.run==r)&(short.scoring=='standard')].ensembl_id) for r in order};all_sets={}
for r in order:
 for mode in ['standard','without_F']:all_sets[r+'/'+mode]=set(short[(short.run==r)&(short.scoring==mode)].ensembl_id)
common=set.intersection(*sets.values());lookup=short.drop_duplicates('ensembl_id').set_index('ensembl_id').Gene.to_dict();common_names=sorted(lookup[g] for g in common);union=set.union(*all_sets.values())
# Per-gene score and membership across all main runs.
records=[]
for gid in sorted(union):
 row={'ensembl_id':gid,'Gene':lookup[gid]}
 for r in order:
  m=pd.read_csv(D/r/'Paper1_HighConfidence/01_master_table.csv').set_index('ensembl_id');hit=gid in m.index;row[r+'_shortlisted']=gid in sets[r];row[r+'_score']=m.loc[gid,'HighConfidenceScore'] if hit else np.nan;row[r+'_cluster']=m.loc[gid,'cluster'] if hit else '';row[r+'_confidence']=m.loc[gid,'membership_confidence'] if hit else np.nan
 records.append(row)
pd.DataFrame(records).to_csv(D/'candidate_stability.csv',index=False)
summary=s[['run','fibrosis_genes','disease_genes','shared','union','Tier1','shortlist_size','shortlist_retained_from_baseline','cluster_ARI_common_genes']]
report='''# Label and normalisation sensitivity comparison

This experiment compares alternatives without adopting new diagnoses or changing the active graph. All runs use the corrected biopsy rule, the same eligible gene universe, k=5, seeds, thresholds, P/T/X/F/B scoring, five-per-cluster shortlist quota and mechanism-selection rules.

## What was varied

- **Label sensitivity:** the five previously flagged GSE130970 samples have a blank disease_group and explicit unclassified-sensitivity provenance. Their fibrosis stages/raw histology remain unchanged. The remaining diagnoses are still derived and unverified.
- **Normalisation sensitivity:** only GSE193066 changes from current CPM-style rescaling to log2(deposited linear RLE counts+1), followed by the same gene/study standardisation over164 biopsies. The other seven expression inputs remain identical.
- **Combined sensitivity:** both changes, to separate the joint effect from each single change.
- **F-feature ablation:** set F=0 after each main run, keeping Tier1 cutoff7 and the same cluster quota. Its maximum score is8 rather than9, so this is a stricter feature-removal test. No thresholds were lowered to force25 candidates. B still uses group/cluster enrichment, so this is not a fully disease-label-independent prioritisation.

## Main results

'''+table(summary)+'''\n\nGene counts alone hide membership changes. Detailed added/removed Ensembl IDs, centroid matching and shortlist changes are in membership_and_cluster_details.json. Gene-level shortlist scores/confidence are in candidate_stability.csv.

## Shortlist changes relative to baseline

'''
for r in order[1:]:
 row=s[s.run==r].iloc[0];add=details[r]['shortlist_added'];removed=details[r]['shortlist_removed'];report+=f"### {r}\n\nRetains {int(row.shortlist_retained_from_baseline)} of the baseline25; produces {int(row.shortlist_size)} candidates under the unchanged quota.\n\nAdded: {', '.join(add) if add else 'none'}.\n\nRemoved: {', '.join(removed) if removed else 'none'}.\n\nClusters with fewer than five Tier1 candidates: {', '.join(details[r]['main_shortlist_shortages']) if details[r]['main_shortlist_shortages'] else 'none'}. No slots were filled by lowering criteria.\n\n"
report+=f"## Candidates shared across main runs\n\n**{len(common_names)} genes** are shortlisted in all four main runs: {', '.join(common_names) if common_names else 'none'}. This is robustness to these two specified perturbations, not an independently validated drug-target set. Stable association or scoring does not establish therapeutic direction or efficacy.\n\n"
report+='## Specificity-feature ablation\n\n'+table(s[['run','F_ablation_Tier1','F_ablation_shortlist_size','F_ablation_baseline_shortlist_retained','F_ablation_own_shortlist_retained']])+'\n\n'
for r in order:
 ab=details[r]['F_ablation'];report+=f"- {r}: {ab['tier1_genes']} Tier1 genes without F; {ab['shortlist_genes']} shortlisted. Clusters below five eligible genes: {', '.join(ab['clusters_below_five']) if ab['clusters_below_five'] else 'none'}.\n"
report+='\n## Clustering and internal robustness\n\n'+table(s[['run','cluster_ARI_common_genes','confident_cluster_genes','Tier1_LOSO_significant_all5','Tier1_LOSO_strong_all5']])+'''\n\nARI uses genes present in both selected sets and is invariant to cluster-label permutation; changed gene selection is reported separately. Centroid-matched correlations are saved, because similarly numbered clusters may represent different timing shapes. k=5 was held fixed; automatic k diagnostics remain available in each run.

LOSO applies BH over the full14,794 eligible genes, but tests internal robustness of already selected genes. Comparisons involve different Tier1 denominators. Direction retention is not independent validation. The stage contrasts/enrichment reuse discovery data and inherit selection and annotation limitations.

## Mechanism networks

'''+table(net)+'''\n\nA displayed network is a filtered Tier1 annotation subset. Genes absent from the selected twelve mechanisms may have other graph connections. Some unexpected cross-tissue labels may need biological review; enrichment alone is not a mechanism demonstration.

## Validation and active-state protection

'''+f"{len(checks)} comparison checks passed. Fresh baseline discovery and shortlist/Tier1 memberships reproduce the active outputs. Factorial invariants hold: label-only changes do not alter fibrosis discovery; normalisation-only changes do not alter disease discovery; the combined run matches the appropriate single-change axis results. Active-file hashes remain unchanged. No Neo4j writes were performed.\n\n"+'''## What this does and does not resolve

- Resolves how sensitive the implemented priorities are to the specified label abstention and normalisation alternatives.
- Does not recover original sample-level diagnoses, validate the other derived labels or establish a universally correct normalisation.
- Does not produce independently validated biomarkers, causal mechanisms or effective drugs.
- Does not automatically replace the baseline, active package or graph. A final strategy must be selected explicitly and documented; do not choose one to preserve preferred genes.

For a conservative primary analysis, selective abstention avoids presenting the five ambiguous cases as certain diagnoses, and preserving deposited RLE is a directly documented alternative. The measured comparison—not candidate preferences—should guide whether to adopt those choices, retain current processing with sensitivity disclosure, or narrow claims to fibrosis associations. F-dependent results and label-derived interpretation still require cautious wording.

## Files and commit checkpoints

Input preparation/protocol:input_preparation.json, PROTOCOL.md and source/runtime snapshots.

Main runs:baseline/, labels_only/, normalisation_only/, combined/ with full per-step logs and run_status.json.

Comparisons:comparison_summary.csv, candidate_stability.csv, shortlist_comparison.csv, network_comparison.csv, membership_and_cluster_details.json and verification_results.json.

F ablations:each run's F_ablation/ containing actual candidate counts, scores, confidence and regenerated networks.

Commit checkpoints are recorded in COMMIT_CHECKPOINTS.md. No commits were made automatically.
'''
(D/'SENSITIVITY_REPORT.md').write_text(report)
# Standalone scientific overview; membership matrix is exact, not inferred from diagrams.
labels=list(all_sets);genes=sorted(union,key=lambda g:lookup[g]);mat=np.array([[int(g in all_sets[k]) for k in labels] for g in genes]);fig,axes=plt.subplots(1,2,figsize=(13,max(6,.22*len(genes))),gridspec_kw={'width_ratios':[1,2]});ax=axes[0];x=np.arange(len(order));ax.bar(x-.18,s.set_index('run').loc[order,'Tier1'],width=.36,label='Standard score');ax.bar(x+.18,s.set_index('run').loc[order,'F_ablation_Tier1'],width=.36,label='Without F');ax.set_xticks(x,[r.replace('_','\n') for r in order]);ax.set_ylabel('Tier1 genes at unchanged cutoff7');ax.legend(fontsize=8);ax.set_title('Score sensitivity');ax=axes[1];im=ax.imshow(mat,aspect='auto',cmap='Blues',vmin=0,vmax=1,interpolation='nearest');ax.set_xticks(range(len(labels)),[k.replace('/','\n').replace('_',' ') for k in labels],rotation=60,ha='right',fontsize=8);ax.set_yticks(range(len(genes)),[lookup[g] for g in genes],fontsize=8);ax.set_title('Shortlist membership (blue = selected)');fig.tight_layout();fig.savefig(D/'shortlist_sensitivity.png',dpi=300,bbox_inches='tight');plt.close(fig)
print('Report written; candidates shared across main runs:',len(common_names),common_names)
