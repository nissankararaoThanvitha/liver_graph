#!/usr/bin/env python3
"""Frozen-tier and cluster validation: no discovery reassignment or gene selection."""
from pathlib import Path
import os,json,hashlib,platform
os.environ.setdefault('MPLCONFIGDIR','/tmp/liver-validation-matplotlib')
import numpy as np
import pandas as pd
from scipy.stats import rankdata,t,spearmanr,false_discovery_control
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/'independent_validation/GSE225740_preprocessed'
OUT=ROOT/'independent_validation/GSE225740_tier_cluster_validation'
MASTER=ROOT/'Paper1_HighConfidence/11_final_all_3845_genes.csv'
TIER1=ROOT/'Paper1_HighConfidence/11_final_tier1_genes.csv'
PLAN=ROOT/'independent_validation/GSE225740_validation/tier_cluster_analysis_plan.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scaled(v):return (v-v.mean())/v.std(ddof=0) if v.std(ddof=0)>0 else np.full_like(v,np.nan)
def main():
 OUT.mkdir(exist_ok=True)
 frozen=pd.read_csv(MASTER)
 t1=pd.read_csv(TIER1)
 assert len(frozen)==3845 and frozen.Ensembl_ID.is_unique and len(t1)==447
 assert set(t1.Ensembl_ID)==set(frozen.loc[frozen.Tier.str.startswith('Tier 1'),'Ensembl_ID'])
 meta=pd.read_csv(PRE/'sample_metadata_staged.tsv',sep='\t',dtype={'patient_id':str})
 log=pd.read_csv(PRE/'log2cpm_mapped_staged_87.tsv.gz',sep='\t',index_col=0)
 z=pd.read_csv(PRE/'zscore_mapped_staged_87.tsv.gz',sep='\t',index_col=0)
 qc=pd.read_csv(PRE/'gene_qc.tsv.gz',sep='\t',index_col=0)
 ids=meta.patient_id.tolist();stage=meta.fibrosis_stage.to_numpy(float)
 assert ids==log.columns.tolist()==z.columns.tolist() and len(ids)==87
 table=frozen[['Gene','Ensembl_ID','Tier','Cluster','Cluster_pattern','Fibrosis_rho','Direction']].copy().rename(columns={'Fibrosis_rho':'discovery_median_study_rho','Direction':'discovery_direction'})
 table['available']=table.Ensembl_ID.isin(log.index)
 table['testable']=False
 for i in table.index[table.available]:table.loc[i,'testable']=log.loc[table.loc[i,'Ensembl_ID']].nunique()>1
 table['unavailable_reason']=np.where(~table.available,'unmapped_in_validation',np.where(~table.testable,'constant_expression',''))
 valid=table.index[table.testable];ens=table.loc[valid,'Ensembl_ID']
 x=log.loc[ens].to_numpy(float)
 ranks=rankdata(x,axis=1);ranks-=ranks.mean(axis=1,keepdims=True)
 yr=rankdata(stage);yr-=yr.mean()
 rho=(ranks@yr)/np.sqrt((ranks*ranks).sum(axis=1)*(yr*yr).sum())
 pval=2*t.sf(np.abs(rho*np.sqrt((len(stage)-2)/(1-rho*rho))),df=len(stage)-2)
 assert np.isfinite(rho).all() and np.isfinite(pval).all()
 table.loc[valid,'validation_rho']=rho;table.loc[valid,'validation_p_two_sided']=pval
 table.loc[valid,'validation_q_common_BH']=false_discovery_control(pval,method='bh')
 ti=table.index[table.testable & table.Tier.str.startswith('Tier 1')]
 table['tier1_primary_q_BH']=np.nan
 table.loc[ti,'tier1_primary_q_BH']=false_discovery_control(table.loc[ti,'validation_p_two_sided'].to_numpy(),method='bh')
 table['same_direction']=pd.Series(pd.NA,index=table.index,dtype='boolean')
 table.loc[valid,'same_direction']=np.sign(rho)==np.sign(table.loc[valid,'discovery_median_study_rho'])
 table['common_family_status']='untestable'
 d=table.loc[valid,'same_direction'].astype(bool)
 sig=table.loc[valid,'validation_q_common_BH']<.05
 table.loc[valid,'common_family_status']=np.where(sig&d,'concordant_significant',np.where(sig,'opposite_significant',np.where(d,'concordant_not_significant','opposite_not_significant')))
 table['tier1_primary_status']='not_in_tier1'
 table.loc[table.Tier.str.startswith('Tier 1'),'tier1_primary_status']='untestable'
 td=table.loc[ti,'same_direction'].astype(bool);ts=table.loc[ti,'tier1_primary_q_BH']<.05
 table.loc[ti,'tier1_primary_status']=np.where(ts&td,'concordant_significant',np.where(ts,'opposite_significant',np.where(td,'concordant_not_significant','opposite_not_significant')))
 means=np.array([x[:,stage==k].mean(axis=1) for k in range(5)]).T
 original=frozen.loc[valid,['F0','F1','F2','F3','F4']].to_numpy(float)
 table.loc[valid,'profile_shape_Pearson_5points']=[np.corrcoef(a,b)[0,1] if a.std()>0 and b.std()>0 else np.nan for a,b in zip(original,means)]
 table.loc[valid,'n_staged_cpm_ge_1']=qc.loc[ens,'n_staged_cpm_ge_1'].to_numpy()
 table['preflagged_shortlist_low_expression']=table.Gene.isin(['HTR7','CACNA1C'])
 table.to_csv(OUT/'all3845_validation.csv',index=False,float_format='%.12g')
 table[table.Tier.str.startswith('Tier 1')].to_csv(OUT/'tier1_all447_validation.csv',index=False,float_format='%.12g')
 def summary_group(label,g):
  v=g[g.testable];same=v.same_direction.astype(bool)
  return {'group':label,'original_n':len(g),'available_n':int(g.available.sum()),'testable_n':len(v),'unavailable_n':int((~g.available).sum()),'constant_n':int((g.available&~g.testable).sum()),'same_direction_n':int(same.sum()),'same_direction_fraction_testable':float(same.mean()),'concordant_significant_common_BH_n':int((v.common_family_status=='concordant_significant').sum()),'concordant_significant_common_BH_fraction_testable':float((v.common_family_status=='concordant_significant').mean()),'opposite_significant_common_BH_n':int((v.common_family_status=='opposite_significant').sum()),'median_abs_rho':float(v.validation_rho.abs().median()),'median_profile_shape_r':float(v.profile_shape_Pearson_5points.median()),'positive_profile_shape_r_fraction':float((v.profile_shape_Pearson_5points>0).sum()/v.profile_shape_Pearson_5points.notna().sum())}
 tiers=pd.DataFrame([summary_group(k,g) for k,g in table.groupby('Tier',sort=True)])
 tiers.to_csv(OUT/'tier_comparison_common_family.csv',index=False,float_format='%.12g')
 clusters=[];profiles=[];scores=pd.DataFrame(index=ids);rng=np.random.default_rng(20261109)
 for c in ['C1','C2','C3','C4','C5']:
  g=table[table.Cluster==c];v=g[g.testable];es=v.Ensembl_ID
  score=z.loc[es,ids].mean(axis=0).to_numpy();scores[c]=score
  sr=spearmanr(score,stage)
  vm=np.array([score[stage==k].mean() for k in range(5)])
  dm=frozen.set_index('Ensembl_ID').loc[es,['F0','F1','F2','F3','F4']].mean(axis=0).to_numpy()
  row=summary_group(c,g);row.update({'cluster_score_rho':float(sr.statistic),'cluster_score_p':float(sr.pvalue),'centroid_shape_Pearson_5points':float(np.corrcoef(dm,vm)[0,1]),'discovery_largest_absolute_step':int(np.argmax(np.abs(np.diff(dm)))),'validation_largest_absolute_step':int(np.argmax(np.abs(np.diff(vm))))})
  clusters.append(row)
  for k in range(5):
   group=score[stage==k];bs=group[rng.integers(0,len(group),size=(2000,len(group)))].mean(axis=1);lo,hi=np.percentile(bs,[2.5,97.5])
   profiles.append({'Cluster':c,'stage':k,'n_patients':len(group),'n_genes':len(es),'validation_mean_score':vm[k],'validation_mean_score_CI95_low':lo,'validation_mean_score_CI95_high':hi,'discovery_centroid_recorded_units':dm[k],'discovery_centroid_shape_z':scaled(dm)[k],'validation_centroid_shape_z':scaled(vm)[k]})
 clusters=pd.DataFrame(clusters);clusters['cluster_score_q_BH5']=false_discovery_control(clusters.cluster_score_p.to_numpy(),method='bh')
 clusters.to_csv(OUT/'fixed_cluster_summary.csv',index=False,float_format='%.12g');profiles=pd.DataFrame(profiles);profiles.to_csv(OUT/'fixed_cluster_profiles.csv',index=False,float_format='%.12g')
 scores.index.name='patient_id';scores.to_csv(OUT/'fixed_cluster_patient_scores.tsv',sep='\t',float_format='%.12g')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
 fig,axes=plt.subplots(2,3,figsize=(11,7),sharex=True,sharey=True)
 for i,c in enumerate(['C1','C2','C3','C4','C5']):
  ax=axes.flat[i];p=profiles[profiles.Cluster==c];cr=clusters.iloc[i]
  ax.plot(range(5),p.discovery_centroid_shape_z,'s--',color='#64748b',markersize=4,label='Frozen discovery centroid')
  ax.plot(range(5),p.validation_centroid_shape_z,'o-',color='#166d8d',markersize=4,label='Validation centroid')
  ax.set_title(f'{c}: {int(cr.testable_n)}/{int(cr.original_n)} genes\nShape r = {cr.centroid_shape_Pearson_5points:.2f}',fontsize=11)
  ax.set_xticks(range(5),['F0','F1','F2','F3','F4']);ax.tick_params(labelbottom=True);ax.axhline(0,color='#aaaaaa',lw=.7);ax.grid(alpha=.15)
 axes.flat[5].axis('off');handles,labels=axes.flat[0].get_legend_handles_labels();axes.flat[5].legend(handles,labels,loc='upper left',fontsize=10)
 axes.flat[5].text(.02,.50,'Fixed memberships; no reclustering.\nShape correlations use five stage means.\nF0–F4: 27 / 26 / 15 / 13 / 6 patients.\nNot a profile-equivalence test.',transform=axes.flat[5].transAxes,va='top',fontsize=10)
 fig.supxlabel('Fibrosis stage (cross-sectional)');fig.supylabel('Within-centroid standardized stage mean');fig.tight_layout(rect=(.025,.025,1,1));fig.savefig(OUT/'fixed_cluster_shapes.pdf',bbox_inches='tight');fig.savefig(OUT/'fixed_cluster_shapes.png',dpi=180,bbox_inches='tight');plt.close(fig)
 fig,ax=plt.subplots(figsize=(7,4.8));xx=np.arange(3);w=.35
 ax.bar(xx-w/2,tiers.same_direction_fraction_testable*100,w,label='Same direction',color='#88a8ba')
 ax.bar(xx+w/2,tiers.concordant_significant_common_BH_fraction_testable*100,w,label='Same direction + common BH q < 0.05',color='#197c61')
 ax.set_xticks(xx,['Tier 1','Tier 2','Tier 3']);ax.set_ylabel('Percentage of testable genes');ax.set_ylim(0,110);ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,1.20));ax.grid(axis='y',alpha=.15)
 for i in range(3):ax.text(i,103,f'n = {tiers.testable_n.iloc[i]}',ha='center',fontsize=9)
 fig.tight_layout();fig.savefig(OUT/'tier_replication_comparison.pdf',bbox_inches='tight');fig.savefig(OUT/'tier_replication_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
 tier1=table[table.Tier.str.startswith('Tier 1')]
 summary={'tier1_original_n':447,'tier1_available':int(tier1.available.sum()),'tier1_testable':len(ti),'tier1_primary_status_counts':tier1.tier1_primary_status.value_counts().to_dict(),'tier1_unavailable_genes':tier1.loc[~tier1.available,'Gene'].tolist(),'common_family_n':len(valid),'tier_comparison':tiers.to_dict(orient='records'),'fixed_cluster_summary':clusters.to_dict(orient='records'),'input_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [MASTER,TIER1,PLAN,PRE/'log2cpm_mapped_staged_87.tsv.gz',PRE/'zscore_mapped_staged_87.tsv.gz',PRE/'sample_metadata_staged.tsv']},'script_sha256':sha(Path(__file__)),'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({k:summary[k] for k in ['tier1_original_n','tier1_available','tier1_testable','tier1_primary_status_counts','tier1_unavailable_genes','common_family_n']},indent=2));print(tiers.to_string(index=False));print(clusters[['group','testable_n','centroid_shape_Pearson_5points','cluster_score_rho','cluster_score_q_BH5']].to_string(index=False))
if __name__=='__main__':main()
