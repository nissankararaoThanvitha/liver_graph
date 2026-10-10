"""Remove only the F score, preserving fixed thresholds and selection quotas."""
from pathlib import Path
import json,sys,os,subprocess
import pandas as pd,numpy as np
D=Path(__file__).resolve().parents[1]
for name in ['baseline','labels_only','normalisation_only','combined']:
 run=D/name;out=run/'F_ablation';out.mkdir(exist_ok=False);m=pd.read_csv(run/'Paper1_HighConfidence/01_master_table.csv');m['F_original']=m.F;m['score_original']=m.HighConfidenceScore;m['F']=0;m['HighConfidenceScore']=m[['P','T','X','B']].sum(axis=1);m['tier']=np.select([m.HighConfidenceScore>=7,m.HighConfidenceScore>=5],['Tier 1 - high confidence','Tier 2 - moderate confidence'],default='Tier 3')
 assert (m.HighConfidenceScore<=m.score_original).all();tier=m[m.HighConfidenceScore>=7].copy();selected=tier.sort_values(['HighConfidenceScore','abs_rho'],ascending=[False,False]).groupby('cluster',group_keys=False).head(5).sort_values(['cluster','HighConfidenceScore','abs_rho'],ascending=[True,False,False]);assert set(tier.ensembl_id)<=set(pd.read_csv(run/'Paper1_HighConfidence/11_final_tier1_genes.csv').Ensembl_ID)
 m.to_csv(out/'01_master_table_without_F.csv',index=False);tier.to_csv(out/'tier1_without_F_master.csv',index=False)
 final=list((run/'Paper1_HighConfidence').glob('11_final_all_*_genes.csv'));assert len(final)==1;ft=pd.read_csv(final[0]);score=m.set_index('ensembl_id').HighConfidenceScore;ft['F_original']=ft.F;ft['Original_total_score']=ft.Total_score;ft['F']=0;ft['Total_score']=ft.Ensembl_ID.map(score);ft['Tier']=np.select([ft.Total_score>=7,ft.Total_score>=5],['Tier 1 - high confidence','Tier 2 - moderate confidence'],default='Tier 3')
 ft.to_csv(out/'all_genes_without_F.csv',index=False);ft[ft.Ensembl_ID.isin(tier.ensembl_id)].to_csv(out/'11_final_tier1_genes.csv',index=False);positions={gid:i for i,gid in enumerate(selected.ensembl_id)};short=ft[ft.Ensembl_ID.isin(selected.ensembl_id)].copy();short['__order']=short.Ensembl_ID.map(positions);short=short.sort_values('__order').drop(columns='__order');short.to_csv(out/'11_FINAL_shortlist_25_genes.csv',index=False)
 confidence=pd.read_csv(run/'Paper1_Results/Task2/task2_gene_clusters.csv');short.merge(confidence[['ensembl_id','membership_confidence','confidence_n_bootstraps']],left_on='Ensembl_ID',right_on='ensembl_id',validate='1:1').drop(columns='ensembl_id').to_csv(out/'shortlist_without_F_with_confidence.csv',index=False)
 quotas=tier.groupby('cluster').size().reindex(sorted(m.cluster.unique()),fill_value=0);info={'run':name,'F_removed':True,'maximum_score':8,'Tier1_cutoff':7,'tier1_genes':len(tier),'shortlist_genes':len(short),'tier1_available_per_cluster':quotas.to_dict(),'clusters_below_five':[k for k,v in quotas.items() if v<5],'rule_not_relaxed':True,'remaining_label_dependence':'B still uses group/cluster enrichment; removing F is not a fully disease-label-free analysis'};(out/'ablation_config.json').write_text(json.dumps(info,indent=2))
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(out/'matplotlib'))
 with (out/'network.log').open('w') as f:p=subprocess.run([sys.executable,str(run/'scripts/kg_subgraph.py'),'--out',str(out),'--results',str(run/'Paper1_Results')],cwd=run,stdout=f,stderr=subprocess.STDOUT,env=env)
 if p.returncode:print((out/'network.log').read_text()[-2000:]);raise SystemExit(p.returncode)
 print(json.dumps(info),flush=True)
