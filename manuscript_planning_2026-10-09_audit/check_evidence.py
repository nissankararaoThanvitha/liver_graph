from pathlib import Path
import pandas as pd,json,hashlib
def spearmanr(a,b): return pd.Series(list(a)).corr(pd.Series(list(b)),method="pearson") if False else pd.Series(list(a)).rank().corr(pd.Series(list(b)).rank())
R=Path(__file__).parent.parent;O=Path(__file__).parent/'audit';P=R/'Paper1_Package'
def read(s):return pd.read_csv(P/s)
checks=json.loads((O/'manifest_check.json').read_text());mf=pd.read_csv(P/'00_START_HERE/06_FILE_MANIFEST.csv').set_index('path')
for x in checks:
 b=(P/x['path']).read_bytes();x['matches_with_crlf']=hashlib.sha256(b.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()==mf.loc[x['path'],'sha256'];x['matches_with_lf']=hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()==mf.loc[x['path'],'sha256']
(O/'manifest_check.json').write_text(json.dumps(checks,indent=2)); print('Manifest',len(checks),'byte_matches',sum(x['hash_matches'] for x in checks),'CRLF_matches',sum(x['matches_with_crlf'] for x in checks),'unexplained',[x['path'] for x in checks if not any(x.get(k) for k in ['hash_matches','matches_with_crlf','matches_with_lf'])])
for s in ['02_TABLES/main/Table1_cohort.csv','02_TABLES/main/Table2_gene_groups.csv','02_TABLES/main/Table3_trajectory_clusters.csv','02_TABLES/main/Table4_stage_transitions.csv','02_TABLES/main/Table5_enrichment_counts.csv','03_RESULTS/Task2_trajectories/task2_bootstrap_shape_stability.csv','03_RESULTS/Task2_trajectories/task2_robustness.csv','02_TABLES/supplementary/TableS14_tier_cutoff_sensitivity.csv','02_TABLES/supplementary/TableS15_leave_one_score_out.csv','03_RESULTS/Task5_gene_prioritisation/09b_option_comparison.csv']:
 print('\n'+s+'\n'+read(s).to_string(index=False))
f=read('04_DATA/progression_genes/progression_fibrosis.csv');d=read('04_DATA/progression_genes/progression_disease.csv');b=read('04_DATA/progression_genes/progression_both.csv');g=read('04_DATA/gene_tables/genes_by_fibrosis_stage.csv');samples=read('04_DATA/harmonisation/nodes_sample_clinical.csv');sigf=f[(f.q_value<.05)&(f.n_studies==f.n_agree)];sigd=d[(d.q_value<.05)&(d.n_studies==d.n_agree)]
print('Computed',len(f),len(d),len(b),len(sigf),len(sigd),len(set(sigf.ensembl_id)&set(sigd.ensembl_id)),len(set(sigf.ensembl_id)|set(sigd.ensembl_id)))
print('demog_cols',list(samples));print('staged_unique_patients',samples[samples.fibrosis_stage.notna()].patient_id.nunique());print('first_biopsy_stage_counts',samples[(samples.fibrosis_stage.notna()) & (samples.biopsy_number != 2)].fibrosis_stage.value_counts().sort_index().to_dict());print('F0 diagnoses',samples[samples.fibrosis_stage==0].disease_group.fillna('missing').value_counts().to_dict())
print('category_gene_nodes',read('04_DATA/graph_nodes/nodes_gene.csv').category.fillna('').value_counts().to_dict())
shared=g[g.ladder=='both'];print('shared_corr',spearmanr(shared.fibrosis_rho,shared.inflammation_rho));print('within_up',spearmanr(shared.loc[(shared.fibrosis_rho>0)&(shared.inflammation_rho>0),'fibrosis_rho'],shared.loc[(shared.fibrosis_rho>0)&(shared.inflammation_rho>0),'inflammation_rho']));print('within_down',spearmanr(shared.loc[(shared.fibrosis_rho<0)&(shared.inflammation_rho<0),'fibrosis_rho'],shared.loc[(shared.fibrosis_rho<0)&(shared.inflammation_rho<0),'inflammation_rho']))
for s in ['02_TABLES/main/Table6_prioritised_genes.csv','03_RESULTS/Task5_gene_prioritisation/10_loso_summary.csv']:
 a=read(s);print(s,'cols',list(a));print(a.head(25).to_string(index=False) if len(a)==25 else a.select_dtypes('number').describe().to_string())
print('progression edge copies');
for s in ['04_DATA/graph_nodes/edges_my_progression.csv','04_DATA/knowledge_layer/edges_my_progression.csv']:
 a=read(s); print(s,len(a),a["rel"].value_counts().to_dict())
print('Background symbols',f.symbol.nunique(),f.symbol.isna().sum())
