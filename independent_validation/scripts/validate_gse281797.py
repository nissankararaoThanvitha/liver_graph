#!/usr/bin/env python3
"""Second-cohort validation with frozen genes and F0-F3-only patterns."""
from pathlib import Path
import os,csv,gzip,re,json,hashlib,platform
os.environ.setdefault('MPLCONFIGDIR','/tmp/liver-validation-matplotlib')
import numpy as np
import pandas as pd
import scipy
from scipy.stats import rankdata,t,false_discovery_control,spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'independent_validation';SOURCE=BASE/'candidate_screening_2026-11-07/GSE281797';OUT=BASE/'GSE281797_validation';PRE=OUT/'preprocessed';MASTER=ROOT/'Paper1_HighConfidence/11_final_all_3845_genes.csv';SHORT=ROOT/'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv';TIER1=ROOT/'Paper1_HighConfidence/11_final_tier1_genes.csv';GM=ROOT/'data/processed/gene_id_map.csv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(df,path,index=True):df.to_csv(path,sep='\t',index=index,float_format='%.12g',compression={'method':'gzip','mtime':0} if str(path).endswith('.gz') else None)
def bht(p):
 p=np.asarray(p,float);out=np.full(len(p),np.nan);ok=np.isfinite(p)
 if ok.any():out[ok]=false_discovery_control(p[ok],method='bh')
 return out

def overlap_ids(path):
 s=gzip.decompress(path.read_bytes()).decode()
 return {k:set(re.findall(p,s,re.M)) for k,p in {'GSM':r'^\^SAMPLE = (GSM\d+)','BioSample':r'SAM[NED][A-Z]?\d+','SRA_experiment':r'[SED]RX\d+'}.items()}
def associations(log,st,master,short_ids,sub_ids):
 tab=master[['Gene','Ensembl_ID','Tier','Cluster','Cluster_pattern','Fibrosis_rho','Direction']].rename(columns={'Fibrosis_rho':'discovery_median_study_rho','Direction':'discovery_direction'}).copy()
 tab['available']=tab.Ensembl_ID.isin(log.index);tab['testable']=tab.Ensembl_ID.map(log[sub_ids].nunique(axis=1)).fillna(0)>1
 valid=tab.index[tab.testable];x=log.loc[tab.loc[valid,'Ensembl_ID'],sub_ids].to_numpy(float);y=st.loc[sub_ids].to_numpy(float)
 rx=rankdata(x,axis=1);rx-=rx.mean(axis=1,keepdims=True);ry=rankdata(y);ry-=ry.mean()
 rr=rx@ry/np.sqrt((rx*rx).sum(axis=1)*(ry*ry).sum());p=2*t.sf(np.abs(rr*np.sqrt((len(y)-2)/(1-rr*rr))),len(y)-2)
 tab.loc[valid,'validation_rho']=rr;tab.loc[valid,'validation_p']=p;tab['validation_n']=len(y)
 for family,mask in [('common3845',tab.testable),('Tier1',tab.testable & tab.Tier.str.startswith('Tier 1')),('shortlist23',tab.testable & tab.Ensembl_ID.isin(short_ids))]:
  tab[f'q_BH_{family}']=np.nan;sel=tab.index[mask];tab.loc[sel,f'q_BH_{family}']=bht(tab.loc[sel,'validation_p'].to_numpy())
 tab['same_direction']=pd.Series(pd.NA,index=tab.index,dtype='boolean');tab.loc[valid,'same_direction']=np.sign(rr)==np.sign(tab.loc[valid,'discovery_median_study_rho'])
 return tab

def main():
 PRE.mkdir(parents=True,exist_ok=True);plan=OUT/'analysis_plan.md';assert plan.exists()
 countfile=SOURCE/'GSE281797_GeneCount.txt.gz';metafile=SOURCE/'sample_metadata.tsv'
 with gzip.open(countfile,'rt') as f:header=next(csv.reader(f,delimiter='\t'))
 assert len(header)==len(set(header))
 raw=pd.read_csv(countfile,sep='\t',index_col=0);assert raw.index.is_unique and raw.columns.is_unique
 a=raw.to_numpy(float);assert np.isfinite(a).all() and (a>=0).all()
 fractions=int(np.count_nonzero(a!=np.floor(a)));library=raw.sum(axis=0);assert (library>0).all()
 meta=pd.read_csv(metafile,sep='\t',dtype=str,keep_default_na=False);meta['sample_key']=meta.title.str.replace('HumanLiver_','',regex=False)
 assert meta.sample_key.is_unique and meta.gsm.is_unique and set(meta.sample_key)==set(raw.columns)
 meta=meta.set_index('sample_key').loc[raw.columns];meta.index.name='sample_key'
 meta['fibrosis_stage']=pd.to_numeric(meta['fibrosis grade']);assert meta.fibrosis_stage.isin([0,1,2,3]).all()
 meta['MASLD_subset']=meta.diagnosis.isin(['MASL','MASH']);assert len(meta)==94 and meta.MASLD_subset.sum()==64
 for c in ['age at_biopsy','body mass_index','diabetes']:meta[c]=pd.to_numeric(meta[c],errors='raise')
 excluded=raw.index.str.contains('_PAR_Y');clean_ids=raw.index.str.replace(r'\.[0-9]+(?:_PAR_Y)?$','',regex=True)
 canonical=clean_ids.str.match(r'^ENSG[0-9]{11}$');keep=(~excluded)&canonical
 mapping=pd.DataFrame({'raw_id':raw.index,'ensembl_id':clean_ids,'status':np.where(excluded,'excluded_PAR_Y',np.where(~canonical,'noncanonical_identifier','retained'))})
 counts=raw.loc[keep].copy();counts.index=clean_ids[keep];before=len(counts);counts=counts.groupby(level=0).sum();counts.index.name='ensembl_id'
 log=np.log2(counts.div(library,axis=1)*1e6+1);sd=log.std(axis=1,ddof=1);z=log.sub(log.mean(axis=1),axis=0).div(sd.replace(0,np.nan),axis=0).fillna(0)
 gm=pd.read_csv(GM,dtype=str).fillna('');symbols=gm[gm.symbol.ne('')].groupby('ensembl_id').symbol.agg(lambda v:';'.join(sorted(set(v))))
 qc=pd.DataFrame({'symbol':counts.index.map(symbols),'zero_fraction':counts.eq(0).mean(axis=1),'n_cpm_ge_1':counts.div(library,axis=1).mul(1e6).ge(1).sum(axis=1),'nonconstant':log.nunique(axis=1)>1})
 sq=pd.DataFrame({'deposited_count_total':library,'detected_deposited_rows':raw.gt(0).sum(axis=0),'retained_count_fraction':counts.sum(axis=0)/library,'identical_expression_column':raw.T.duplicated(keep=False)})
 save(meta,PRE/'sample_metadata.tsv');save(mapping,PRE/'gene_id_audit.tsv.gz',False);save(qc,PRE/'gene_qc.tsv.gz');save(sq,PRE/'sample_qc.tsv')
 save(log,PRE/'log2cpm_94.tsv.gz');save(z,PRE/'zscore_94.tsv.gz')
 # All originals plus the first validation cohort; unavailable IDs never imply a negative match.
 candidate=overlap_ids(SOURCE/'GSE281797_family.soft.gz');overlap=[]
 others=list((BASE/'candidate_screening_2026-11-07/original_cohort_metadata').glob('*soft.gz'))+[BASE/'candidate_screening_2026-11-07/GSE225740/GSE225740_family.soft.gz']
 for path in sorted(others):
  o=overlap_ids(path);row={'other_accession':path.name.split('_')[0]}
  for k in candidate:row[k+'_candidate_available']=len(candidate[k]);row[k+'_other_available']=len(o[k]);row[k+'_intersection']=len(candidate[k]&o[k]) if candidate[k] and o[k] else 'not_assessable_missing_identifiers'
  overlap.append(row)
 save(pd.DataFrame(overlap),OUT/'deposited_identifier_overlap.tsv',False)
 master=pd.read_csv(MASTER);short=pd.read_csv(SHORT);tier1=pd.read_csv(TIER1)
 assert len(master)==3845 and master.Ensembl_ID.is_unique and len(short)==23 and len(tier1)==447
 assert set(tier1.Ensembl_ID)==set(master.loc[master.Tier.str.startswith('Tier 1'),'Ensembl_ID'])
 assert set(short.Ensembl_ID).issubset(log.index)
 ids=meta.index.tolist();sub=meta.index[meta.MASLD_subset].tolist();st=meta.fibrosis_stage
 full=associations(log,st,master,set(short.Ensembl_ID),ids);sens=associations(log,st,master,set(short.Ensembl_ID),sub)
 full.to_csv(OUT/'all3845_primary_94.csv',index=False,float_format='%.12g');sens.to_csv(OUT/'all3845_MASLDonly_64_sensitivity.csv',index=False,float_format='%.12g')
 summaries=[]
 for population,tab in [('primary_all94',full),('sensitivity_MASLD64',sens)]:
  for fam,mask in [('shortlist23',tab.Ensembl_ID.isin(short.Ensembl_ID)),('Tier1',tab.Tier.str.startswith('Tier 1')),('common3845',np.ones(len(tab),bool))]:
   g=tab[mask];v=g[g.testable];d=v.same_direction.astype(bool);sig=v['q_BH_'+fam]<.05
   summaries.append({'population':population,'family':fam,'original_n':len(g),'testable_n':len(v),'same_direction':int(d.sum()),'concordant_significant':int((d&sig).sum()),'opposite_significant':int((~d&sig).sum()),'same_direction_nonsignificant':int((d&~sig).sum()),'opposite_nonsignificant':int((~d&~sig).sum()),'unavailable_or_constant':int((~g.testable).sum())})
   if fam=='shortlist23':g=g.set_index('Ensembl_ID').loc[short.Ensembl_ID].reset_index()
   if fam!='common3845':g.to_csv(OUT/f'{fam}_{population}.csv',index=False,float_format='%.12g')
 summary_table=pd.DataFrame(summaries);summary_table.to_csv(OUT/'gene_replication_summary.csv',index=False)
 cluster_rows=[];profiles=[];scores=pd.DataFrame(index=ids);rng=np.random.default_rng(20261110)
 for c in ['C1','C2','C3','C4','C5']:
  group=full[full.Cluster.eq(c)];es=group.loc[group.testable,'Ensembl_ID'];score=z.loc[es].mean(axis=0);scores[c]=score
  vm=np.array([score[st==k].mean() for k in range(4)]);dm=master.set_index('Ensembl_ID').loc[es,['F0','F1','F2','F3']].mean(axis=0).to_numpy()
  shape=lambda v:(v-v.mean())/v.std(ddof=0)
  rr,pp=spearmanr(score,st)
  cluster_rows.append({'Cluster':c,'original_genes':len(group),'testable_genes':len(es),'centroid_shape_r_F0_F3':float(np.corrcoef(dm,vm)[0,1]),'score_rho_F0_F3':float(rr),'score_p':float(pp),'F4_assessable':False})
  for k in range(4):
   values=score[st==k].to_numpy();bs=values[rng.integers(0,len(values),size=(2000,len(values)))].mean(axis=1);lo,hi=np.percentile(bs,[2.5,97.5])
   profiles.append({'Cluster':c,'stage':k,'n_patients':len(values),'n_genes':len(es),'original_F0_F3_shape_z':shape(dm)[k],'validation_F0_F3_shape_z':shape(vm)[k],'validation_mean_score':vm[k],'pointwise_CI95_low':lo,'pointwise_CI95_high':hi})
 clusters=pd.DataFrame(cluster_rows);clusters['score_q_BH5']=bht(clusters.score_p.to_numpy());clusters.to_csv(OUT/'fixed_clusters_F0_F3.csv',index=False,float_format='%.12g');profiles=pd.DataFrame(profiles);profiles.to_csv(OUT/'fixed_cluster_stage_profiles_F0_F3.csv',index=False,float_format='%.12g');save(scores,OUT/'fixed_cluster_patient_scores.tsv')
 # Shortlist stage means only over observed stages. Original F4 is deliberately omitted.
 sp=[]
 for _,r in short.iterrows():
  for k in range(4):sp.append({'Gene':r.Gene,'Ensembl_ID':r.Ensembl_ID,'Cluster':r.Cluster,'stage':k,'n':int((st==k).sum()),'validation_mean_log2CPM':float(log.loc[r.Ensembl_ID,st.index[st==k]].mean()),'original_recorded_profile':r[f'F{k}']})
 pd.DataFrame(sp).to_csv(OUT/'shortlist23_stage_profiles_F0_F3.csv',index=False,float_format='%.12g')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
 fig,axes=plt.subplots(2,3,figsize=(11,7),sharex=True,sharey=True)
 for i,c in enumerate(['C1','C2','C3','C4','C5']):
  ax=axes.flat[i];p=profiles[profiles.Cluster.eq(c)];cr=clusters.iloc[i]
  ax.plot(range(4),p.original_F0_F3_shape_z,'s--',color='#64748b',label='Frozen discovery (F0–F3)');ax.plot(range(4),p.validation_F0_F3_shape_z,'o-',color='#166d8d',label='GSE281797 (F0–F3)');ax.set_title(f'{c}: {cr.testable_genes}/{cr.original_genes} genes\nShape r = {cr.centroid_shape_r_F0_F3:.2f}',fontsize=11);ax.set_xticks(range(4),['F0','F1','F2','F3']);ax.tick_params(labelbottom=True);ax.axhline(0,color='#aaa',lw=.6);ax.grid(alpha=.15)
 axes.flat[5].axis('off');handles,labels=axes.flat[0].get_legend_handles_labels();axes.flat[5].legend(handles,labels,loc='upper left',fontsize=9);axes.flat[5].text(.02,.5,'Four stage means; descriptive only.\nNo F4 samples or F4 extrapolation.\nStage n: 42 / 26 / 20 / 6.\nC2’s defining F3–F4 rise is untested.',transform=axes.flat[5].transAxes,fontsize=10,va='top');fig.supxlabel('Fibrosis stage (cross-sectional)');fig.supylabel('Within-centroid standardized mean, F0–F3');fig.tight_layout(rect=(.025,.025,1,1));fig.savefig(OUT/'fixed_clusters_F0_F3.pdf',bbox_inches='tight');fig.savefig(OUT/'fixed_clusters_F0_F3.png',dpi=180,bbox_inches='tight');plt.close(fig)
 # All 23 genes displayed in frozen order, both population definitions retained.
 f=full.set_index('Ensembl_ID').loc[short.Ensembl_ID];s=sens.set_index('Ensembl_ID').loc[short.Ensembl_ID]
 fig,ax=plt.subplots(figsize=(8,10));yy=np.arange(22,-1,-1)
 ax.scatter(f.validation_rho,yy+.12,color=np.where(f.q_BH_shortlist23<.05,'#197c61','#999999'),s=35,label='Primary: all 94')
 ax.scatter(s.validation_rho,yy-.12,marker='s',facecolors='none',edgecolors='#c27a24',s=28,label='Sensitivity: MASLD-only 64')
 ax.axvline(0,color='black',ls='--',lw=.8);ax.set_yticks(yy,short.Gene);ax.set_xlim(-1,1);ax.set_xlabel('Spearman correlation with F0–F3');ax.set_title('Fixed 23-gene associations in GSE281797',pad=12);ax.grid(axis='x',alpha=.15);ax.legend(loc='lower right',fontsize=8);fig.text(.15,.012,'Primary circles: green q<0.05; grey nonsignificant (BH over 23).\nSquares show sensitivity rho, without encoding sensitivity significance.',fontsize=8);fig.tight_layout(rect=(0,.05,1,1));fig.savefig(OUT/'shortlist23_comparison.pdf',bbox_inches='tight');fig.savefig(OUT/'shortlist23_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
 summary={'dataset':'GSE281797','primary_n':94,'MASLD_sensitivity_n':64,'stage_n':{str(k):int((st==k).sum()) for k in range(4)},'MASLD_subset_stage_n':{str(k):int((st.loc[sub]==k).sum()) for k in range(4)},'raw_rows':len(raw),'fractional_values_preserved':fractions,'PAR_Y_rows_excluded':int(excluded.sum()),'other_noncanonical_rows_excluded':int(((~excluded)&(~canonical)).sum()),'retained_versionless_ensembl_genes':len(counts),'additional_mapping_collapses':before-len(counts),'all_zero_genes':int(counts.sum(axis=1).eq(0).sum()),'duplicate_expression_samples':int(sq.identical_expression_column.sum()),'gene_replication_summary':summaries,'cluster_summary':clusters.to_dict(orient='records'),'input_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [countfile,metafile,MASTER,TIER1,SHORT,GM,plan]},'script_sha256':sha(Path(__file__)),'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}}
 first=BASE/'GSE225740_validation/validation_all_23_genes.csv'
 if first.exists():
  old=pd.read_csv(first);new=full[full.Ensembl_ID.isin(short.Ensembl_ID)]
  joint=old[['Gene','Ensembl_ID','validation_rho','validation_q_BH23','same_direction']].merge(new[['Ensembl_ID','validation_rho','q_BH_shortlist23','same_direction']],on='Ensembl_ID',suffixes=('_GSE225740','_GSE281797'),validate='one_to_one')
  joint['concordant_significant_in_both']=(joint.validation_q_BH23<.05)&(joint.q_BH_shortlist23<.05)&joint.same_direction_GSE225740&joint.same_direction_GSE281797
  joint.to_csv(OUT/'shortlist23_two_cohort_comparison.csv',index=False,float_format='%.12g')
  summary['shortlist_concordant_significant_both_cohorts']=int(joint.concordant_significant_in_both.sum());summary['input_hashes'][str(first.relative_to(ROOT))]=sha(first)
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary_table.to_string(index=False));print(clusters.to_string(index=False));print('fractional count values:',fractions,'PAR_Y excluded:',int(excluded.sum()),'retained genes:',len(counts))
if __name__=='__main__':main()
