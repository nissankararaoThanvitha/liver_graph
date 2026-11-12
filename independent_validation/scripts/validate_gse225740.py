#!/usr/bin/env python3
"""Execute the recorded fixed-23-gene replication plan, without modifying discovery."""
from pathlib import Path
import hashlib,json,platform,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/liver-validation-matplotlib')
import numpy as np
import pandas as pd
import scipy
from scipy.stats import spearmanr,rankdata,false_discovery_control
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/'independent_validation/GSE225740_preprocessed'
OUT=ROOT/'independent_validation/GSE225740_validation'
SHORT=ROOT/'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm_rows(a):
 a=a-a.mean(axis=1,keepdims=True)
 return a/np.sqrt((a*a).sum(axis=1,keepdims=True))
def main():
 OUT.mkdir(exist_ok=True)
 plan=OUT/'analysis_plan.md';assert plan.exists()
 frozen=pd.read_csv(SHORT)
 meta=pd.read_csv(PRE/'sample_metadata_staged.tsv',sep='\t',dtype={'patient_id':str})
 data=pd.read_csv(PRE/'shortlist23_log2cpm_staged_87.tsv',sep='\t',index_col=0)
 qc=pd.read_csv(PRE/'shortlist23_availability_qc.tsv',sep='\t',index_col=0)
 assert len(frozen)==23 and frozen.Ensembl_ID.is_unique
 assert data.index.tolist()==frozen.Ensembl_ID.tolist()
 assert data.Gene.tolist()==frozen.Gene.tolist()
 ids=meta.patient_id.tolist();assert data.columns[1:].tolist()==ids
 x=data[ids].to_numpy(float);stage=meta.fibrosis_stage.to_numpy(float)
 assert x.shape==(23,87) and np.isfinite(x).all()
 results=[spearmanr(row,stage,alternative='two-sided') for row in x]
 rho=np.array([r.statistic for r in results]);p=np.array([r.pvalue for r in results])
 assert np.isfinite(rho).all() and np.isfinite(p).all()
 q=false_discovery_control(p,method='bh')
 ranked=norm_rows(rankdata(x,axis=1));ystd=norm_rows(rankdata(stage)[None,:])[0]
 assert np.allclose(ranked@ystd,rho)
 rng=np.random.default_rng(20261107)
 perm=np.array([rng.permutation(ystd) for _ in range(9999)])
 pr=ranked@perm.T
 pp=(1+np.sum(np.abs(pr)>=np.abs(rho[:,None])-1e-12,axis=1))/10000
 pq=false_discovery_control(pp,method='bh')
 rng=np.random.default_rng(20261108)
 strata=[np.flatnonzero(stage==k) for k in range(5)]
 ix=np.concatenate([rng.choice(s,size=(2000,len(s)),replace=True) for s in strata],axis=1)
 boot_y=stage[ix[0]];assert np.all(stage[ix]==boot_y)
 yr=norm_rows(rankdata(boot_y)[None,:])[0]
 boot=np.array([norm_rows(rankdata(row[ix],axis=1))@yr for row in x])
 ci=np.percentile(boot,[2.5,97.5],axis=1)
 direction=np.sign(rho)==np.sign(frozen.Fibrosis_rho.to_numpy())
 sig=q<.05
 status=np.where(sig&direction,'concordant_significant',np.where(sig,'opposite_significant',np.where(direction,'concordant_not_significant','opposite_not_significant')))
 table=frozen[['Gene','Ensembl_ID','Cluster','Cluster_pattern','Fibrosis_rho','Direction']].copy()
 table=table.rename(columns={'Fibrosis_rho':'discovery_median_study_rho','Direction':'discovery_direction'})
 table['validation_n']=87;table['validation_rho']=rho;table['validation_p_two_sided']=p;table['validation_q_BH23']=q
 table['rho_CI95_low_stage_bootstrap']=ci[0];table['rho_CI95_high_stage_bootstrap']=ci[1]
 table['same_direction']=direction;table['primary_replication_status']=status
 table['permutation_p_9999']=pp;table['permutation_q_BH23']=pq
 table['permutation_concordant_significant']=(pq<.05)&direction
 table['n_staged_cpm_ge_1']=qc.loc[frozen.Ensembl_ID,'n_staged_cpm_ge_1'].to_numpy()
 table['preflagged_low_expression']=table.Gene.isin(['HTR7','CACNA1C'])
 table.to_csv(OUT/'validation_all_23_genes.csv',index=False,float_format='%.12g')
 means=np.array([x[:,stage==k].mean(axis=1) for k in range(5)]).T
 orig=frozen[['F0','F1','F2','F3','F4']].to_numpy(float)
 def shape(a):return (a-a.mean(axis=1,keepdims=True))/a.std(axis=1,keepdims=True,ddof=0)
 vo=shape(means);do=shape(orig)
 profiles=[]
 for i,r in frozen.iterrows():
  for k in range(5):profiles.append({'Gene':r.Gene,'Ensembl_ID':r.Ensembl_ID,'Cluster':r.Cluster,'stage':k,'validation_n_stage':int((stage==k).sum()),'validation_mean_log2CPM':means[i,k],'discovery_recorded_profile':orig[i,k],'validation_shape_z':vo[i,k],'discovery_shape_z':do[i,k]})
 pd.DataFrame(profiles).to_csv(OUT/'stage_profiles_23_genes.csv',index=False,float_format='%.12g')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
 fig,ax=plt.subplots(figsize=(8,10))
 colors=np.where(status=='concordant_significant','#197c61',np.where(status=='opposite_significant','#bd3540','#777777'))
 for i in range(23):
  yy=22-i
  ax.plot([ci[0,i],ci[1,i]],[yy,yy],color=colors[i],lw=1.5)
  ax.scatter(rho[i],yy,color=colors[i],s=30,zorder=3)
 ax.scatter(frozen.Fibrosis_rho,np.arange(22,-1,-1),marker='D',facecolors='none',edgecolors='#1c2f46',s=24,label='Discovery median study correlation',zorder=2)
 ax.axvline(0,color='black',lw=.8,ls='--')
 ax.set_yticks(range(23),frozen.Gene.iloc[::-1]);ax.set_xlabel('Spearman correlation with fibrosis stage')
 ax.set_title('GSE225740: fixed 23-gene replication',pad=14)
 ax.set_xlim(-1,1);ax.grid(axis='x',alpha=.18);ax.legend(loc='lower left',fontsize=8)
 fig.text(.12,.017,'Filled circles: validation rho; lines: pointwise 95% within-stage bootstrap intervals.\nGreen: concordant BH q < 0.05; red: opposite BH q < 0.05; grey: not significant.',fontsize=8)
 fig.tight_layout(rect=(0,.055,1,1));fig.savefig(OUT/'association_comparison.pdf',bbox_inches='tight');fig.savefig(OUT/'association_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
 fig,axes=plt.subplots(5,5,figsize=(14,15),sharex=True,sharey=True)
 for i,ax in enumerate(axes.flat):
  if i>=23:ax.axis('off');continue
  ax.plot(range(5),do[i],color='#64748b',ls='--',marker='s',markersize=3,label='Discovery')
  ax.plot(range(5),vo[i],color='#166d8d',marker='o',markersize=3,label='Validation')
  ax.axhline(0,color='#aaaaaa',lw=.6)
  ax.set_title(f'{frozen.Gene.iloc[i]} · {frozen.Cluster.iloc[i]}',fontsize=11)
  ax.set_xticks(range(5),['F0','F1','F2','F3','F4']);ax.tick_params(labelbottom=True,labelleft=True,labelsize=8)
  ax.grid(alpha=.15);ax.set_ylim(-2.2,2.2)
 handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper right',ncol=2,bbox_to_anchor=(.98,.985))
 fig.suptitle('Frozen discovery patterns and validation stage means',x=.36,y=.988,fontsize=14)
 fig.supxlabel('Fibrosis stage (cross-sectional)');fig.supylabel('Within-profile standardized stage mean (shape comparison only)')
 fig.tight_layout(rect=(.025,.025,1,.96));fig.savefig(OUT/'stage_profiles_all23.pdf',bbox_inches='tight');fig.savefig(OUT/'stage_profiles_all23.png',dpi=160,bbox_inches='tight');plt.close(fig)
 summary={'dataset':'GSE225740','n_staged':87,'fixed_gene_family':23,'same_direction':int(direction.sum()),'primary_status_counts':table.primary_replication_status.value_counts().to_dict(),'permutation_concordant_significant':int(((pq<.05)&direction).sum()),'primary_permutation_significance_disagreements':int(((q<.05)!=(pq<.05)).sum()),'concordant_significant_genes':table.loc[status=='concordant_significant','Gene'].tolist(),'opposite_significant_genes':table.loc[status=='opposite_significant','Gene'].tolist(),'stage_n':{str(k):int((stage==k).sum()) for k in range(5)},'versions':{'python':platform.python_version(),'scipy':scipy.__version__,'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__},'input_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [SHORT,PRE/'shortlist23_log2cpm_staged_87.tsv',PRE/'sample_metadata_staged.tsv',PRE/'shortlist23_availability_qc.tsv',plan]},'script_sha256':sha(Path(__file__))}
 (OUT/'validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
