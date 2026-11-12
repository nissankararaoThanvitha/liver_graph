#!/usr/bin/env python3
"""Frozen transitions and fresh-cohort ORA; no source GMT memberships are exported."""
from pathlib import Path
import os,json,hashlib
os.environ.setdefault('MPLCONFIGDIR','/tmp/liver-validation-matplotlib')
import numpy as np
import pandas as pd
from scipy.stats import rankdata,t,hypergeom,false_discovery_control
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'independent_validation';PRE=BASE/'GSE225740_preprocessed';OUT=BASE/'GSE225740_transition_pathway_validation'
MASTER=ROOT/'Paper1_HighConfidence/11_final_all_3845_genes.csv';SHORT=ROOT/'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv';OLDT=ROOT/'Paper1_Results/Task3/task3_all_genes_all_transitions.csv';OLDP=ROOT/'Paper1_Results/Task4/task4_top_pathways_per_group.csv';BG=ROOT/'data/progression_full/progression_fibrosis.csv';PLAN=BASE/'GSE225740_validation/transition_pathway_plan.md'
DB={'GO_BP':'c5.go.bp','KEGG':'c2.cp.kegg_legacy','Reactome':'c2.cp.reactome','Hallmark':'h.all'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bh(p):
 out=np.full(len(p),np.nan);ok=np.isfinite(p)
 if ok.any():out[ok]=false_discovery_control(np.asarray(p)[ok],method='bh')
 return out
def main():
 OUT.mkdir(exist_ok=True)
 master=pd.read_csv(MASTER);short=pd.read_csv(SHORT);old=pd.read_csv(OLDT);top=pd.read_csv(OLDP)
 meta=pd.read_csv(PRE/'sample_metadata_staged.tsv',sep='\t',dtype={'patient_id':str});ids=meta.patient_id.tolist();stage=meta.fibrosis_stage.to_numpy(int)
 z=pd.read_csv(PRE/'zscore_mapped_staged_87.tsv.gz',sep='\t',index_col=0);log=pd.read_csv(PRE/'log2cpm_mapped_staged_87.tsv.gz',sep='\t',index_col=0)
 assert z.columns.tolist()==ids==log.columns.tolist()
 available=master.Ensembl_ID.isin(z.index);vary=master.Ensembl_ID.map(log.nunique(axis=1)).fillna(0)>1;es=master.loc[available&vary,'Ensembl_ID'];x=z.loc[es].to_numpy(float)
 contrasts=[]
 for a in range(4):
  label=f'F{a}→F{a+1}';low=x[:,stage==a];high=x[:,stage==a+1];n0=low.shape[1];n1=high.shape[1];df=n0+n1-2
  beta=high.mean(axis=1)-low.mean(axis=1)
  s2=(((low-low.mean(axis=1,keepdims=True))**2).sum(axis=1)+((high-high.mean(axis=1,keepdims=True))**2).sum(axis=1))/df
  se=np.sqrt(s2*(1/n0+1/n1));p=np.full(len(es),np.nan);ok=se>0;p[ok]=2*t.sf(np.abs(beta[ok]/se[ok]),df)
  qq=bh(p)
  r=pd.DataFrame({'ensembl_id':es.to_numpy(),'transition':label,'validation_beta':beta,'validation_se':se,'validation_p':p,'validation_q_per_contrast':qq,'n_lower':n0,'n_higher':n1,'df':df})
  contrasts.append(r)
 new=pd.concat(contrasts,ignore_index=True)
 assert not old.duplicated(['ensembl_id','transition']).any()
 # Preserve original rows, including unavailable genes, so denominator losses are visible.
 comparison=old.rename(columns={'beta_adjusted':'discovery_beta','q_value':'discovery_q','substantial':'discovery_substantial'}).merge(new,on=['ensembl_id','transition'],how='left',validate='one_to_one')
 assert len(comparison)==3845*4
 comparison['validation_testable']=comparison.validation_p.notna()
 comparison['validation_substantial']=(comparison.validation_q_per_contrast<.05)&(comparison.validation_beta.abs()>=.2)
 comparison['same_direction']=pd.Series(pd.NA,index=comparison.index,dtype='boolean')
 k=comparison.validation_testable
 comparison.loc[k,'same_direction']=np.sign(comparison.loc[k,'validation_beta'])==np.sign(comparison.loc[k,'discovery_beta'])
 comparison['replicated_original_substantial']=comparison.discovery_substantial&comparison.validation_substantial&comparison.same_direction.fillna(False)
 comparison['Tier']=comparison.ensembl_id.map(master.set_index('Ensembl_ID').Tier)
 comparison.to_csv(OUT/'all_original_adjacent_contrasts.csv',index=False,float_format='%.12g')
 sums=[]
 for label,g in comparison.groupby('transition',sort=False):
  for name,part in [('all3845',g),('Tier1',g[g.Tier.str.startswith('Tier 1')]),('shortlist23',g[g.ensembl_id.isin(short.Ensembl_ID)])]:
   orig=part[part.discovery_substantial];test=orig[orig.validation_testable]
   sums.append({'transition':label,'scope':name,'n_lower':int(g.n_lower.dropna().iloc[0]),'n_higher':int(g.n_higher.dropna().iloc[0]),'original_substantial':len(orig),'original_substantial_testable':len(test),'original_substantial_untestable':len(orig)-len(test),'same_direction_original_substantial':int(test.same_direction.fillna(False).sum()),'replicated_original_substantial':int(test.replicated_original_substantial.sum()),'replication_fraction_testable':float(test.replicated_original_substantial.mean()) if len(test) else np.nan})
 ts=pd.DataFrame(sums);ts.to_csv(OUT/'transition_replication_summary.csv',index=False,float_format='%.12g')
 selected=short[['Gene','Ensembl_ID','Largest_transition','Transition_beta']].merge(new,left_on=['Ensembl_ID','Largest_transition'],right_on=['ensembl_id','transition'],how='left',validate='one_to_one')
 selected['validation_q_frozen23']=bh(selected.validation_p.to_numpy());selected['same_direction']=np.sign(selected.Transition_beta)==np.sign(selected.validation_beta)
 selected['concordant_significant_frozen23']=(selected.validation_q_frozen23<.05)&selected.same_direction
 selected['concordant_substantial_frozen23']=selected.concordant_significant_frozen23&(selected.validation_beta.abs()>=.2)
 selected.to_csv(OUT/'shortlist23_frozen_largest_transition.csv',index=False,float_format='%.12g')
 # Independent gene selection in the eligible measurable background, not in frozen clusters.
 bg=pd.read_csv(BG);assert bg.ensembl_id.is_unique and bg.symbol.is_unique
 b=bg[bg.ensembl_id.isin(log.index)].copy();b=b[b.ensembl_id.map(log.nunique(axis=1))>1]
 vals=log.loc[b.ensembl_id].to_numpy(float);rx=rankdata(vals,axis=1);rx-=rx.mean(axis=1,keepdims=True);ry=rankdata(stage);ry-=ry.mean()
 rho=(rx@ry)/np.sqrt((rx*rx).sum(axis=1)*(ry*ry).sum());pp=2*t.sf(np.abs(rho*np.sqrt(85/(1-rho*rho))),85);qq=bh(pp)
 b['validation_rho']=rho;b['validation_p']=pp;b['validation_q_BG']=qq
 b[['ensembl_id','symbol','validation_rho','validation_p','validation_q_BG']].to_csv(OUT/'validation_background_gene_associations.csv',index=False,float_format='%.12g')
 background=set(b.symbol);queries={'up':set(b.loc[(qq<.05)&(rho>0),'symbol']),'down':set(b.loc[(qq<.05)&(rho<0),'symbol'])};N=len(background)
 rows=[];gmts=[]
 for db,stem in DB.items():
  path=ROOT/f'data/genesets/{stem}.v2024.1.Hs.symbols.gmt';gmts.append(path);sets={}
  for line in path.open():
   parts=line.rstrip('\n').split('\t');g=set(parts[2:])&background
   if 10<=len(g)<=500:sets[parts[0]]=g
  for direction,query in queries.items():
   if len(query)<5:continue
   rr=[]
   for term,genes in sets.items():
    K=len(genes);overlap=len(genes&query);n=len(query)
    rr.append({'database':db,'direction':direction,'term':term,'background_n':N,'query_n':n,'term_size_in_background':K,'overlap':overlap,'fold_enrichment':overlap/n/(K/N),'p':float(hypergeom.sf(overlap-1,N,K,n))})
   d=pd.DataFrame(rr);d['q_BH_direction_database']=bh(d.p.to_numpy());rows.append(d)
 enrich=pd.concat(rows,ignore_index=True);enrich.to_csv(OUT/'validation_enrichment_all_terms.csv',index=False,float_format='%.12g')
 enrich[enrich.q_BH_direction_database<.05].to_csv(OUT/'validation_enrichment_significant.csv',index=False,float_format='%.12g')
 frozen=top[top.group.str.match(r'^C[1-5]_all$')].copy();assert not frozen.duplicated(['group','database','term']).any()
 expected={c:('up' if g.Fibrosis_rho.median()>0 else 'down') for c,g in master.groupby('Cluster')}
 frozen['expected_validation_direction']=frozen.group.str[:2].map(expected)
 tested=frozen[['group','database','term','term_label','q_value','expected_validation_direction']].rename(columns={'q_value':'discovery_q'}).merge(enrich,left_on=['database','term','expected_validation_direction'],right_on=['database','term','direction'],how='left',validate='many_to_one')
 tested['testable']=tested.p.notna();tested['validation_enriched']=tested.q_BH_direction_database<.05
 tested.to_csv(OUT/'frozen_cluster_top_pathways_comparison.csv',index=False,float_format='%.12g')
 ps=tested.groupby(['group','database'],sort=True).agg(original_top_terms=('term','size'),testable=('testable','sum'),enriched_validation=('validation_enriched','sum')).reset_index();ps.to_csv(OUT/'frozen_pathway_replication_summary.csv',index=False)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
 fig,axes=plt.subplots(1,2,figsize=(11,4.5));main=ts[ts.scope=='all3845'];xx=np.arange(4)
 axes[0].bar(xx,main.replication_fraction_testable*100,color='#197c61');axes[0].set_xticks(xx,['F0–F1','F1–F2','F2–F3','F3–F4']);axes[0].set_ylim(0,5);axes[0].set_ylabel('Original substantial contrasts replicated (%)');axes[0].set_title('Fixed adjacent-stage comparisons')
 for i,row in main.reset_index(drop=True).iterrows():axes[0].text(i,row.replication_fraction_testable*100+.15,f'{int(row.replicated_original_substantial)}/{int(row.original_substantial_testable)}',ha='center',fontsize=8)
 mat=ps.pivot(index='group',columns='database',values='enriched_validation').reindex([f'C{k}_all' for k in range(1,6)])[list(DB)]
 den=ps.pivot(index='group',columns='database',values='testable').reindex(mat.index)[list(DB)]
 im=axes[1].imshow(mat.to_numpy()/den.to_numpy(),vmin=0,vmax=1,cmap='Blues',aspect='auto');axes[1].set_xticks(range(4),list(DB),rotation=25);axes[1].set_yticks(range(5),[f'C{k}' for k in range(1,6)]);axes[1].set_title('Frozen top pathway terms\nEnriched / testable in validation direction')
 for i in range(5):
  for j in range(4):
   if den.iloc[i,j]>0:axes[1].text(j,i,f'{int(mat.iloc[i,j])}/{int(den.iloc[i,j])}',ha='center',va='center',color='white' if mat.iloc[i,j]/den.iloc[i,j]>.6 else 'black')
   else:axes[1].text(j,i,'—',ha='center',va='center')
 fig.colorbar(im,ax=axes[1],label='Fraction',shrink=.8);fig.tight_layout();fig.savefig(OUT/'transition_pathway_summary.pdf',bbox_inches='tight');fig.savefig(OUT/'transition_pathway_summary.png',dpi=180,bbox_inches='tight');plt.close(fig)
 summary={'transition_summary_all':main.to_dict(orient='records'),'shortlist_frozen23_testable':int(selected.validation_p.notna().sum()),'shortlist_frozen23_direction_concordant':int(selected.same_direction.sum()),'shortlist_frozen23_concordant_significant':int(selected.concordant_significant_frozen23.sum()),'shortlist_frozen23_concordant_substantial':int(selected.concordant_substantial_frozen23.sum()),'validation_background_n':N,'validation_up_n':len(queries['up']),'validation_down_n':len(queries['down']),'frozen_pathway_pairs':len(tested),'frozen_pathway_pairs_testable':int(tested.testable.sum()),'frozen_pathway_pairs_enriched':int(tested.validation_enriched.sum()),'pathway_summary':ps.to_dict(orient='records'),'input_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [MASTER,SHORT,OLDT,OLDP,BG,PLAN,*gmts,PRE/'zscore_mapped_staged_87.tsv.gz',PRE/'log2cpm_mapped_staged_87.tsv.gz']},'script_sha256':sha(Path(__file__))}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['input_hashes','pathway_summary']},indent=2));print(ps.to_string(index=False))
if __name__=='__main__':main()
