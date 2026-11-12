#!/usr/bin/env python3
"""Frozen genes, independent grouped-severity microarray validation."""
from pathlib import Path
import csv,gzip,io,re,json,hashlib,platform,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/liver-validation-matplotlib')
import numpy as np
import pandas as pd
import scipy
from scipy.stats import t,false_discovery_control
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];B=R/'independent_validation';S=B/'candidate_screening_2026-11-07/GSE49541';O=B/'GSE49541_validation'
SHORT=R/'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv';TIER=R/'Paper1_HighConfidence/11_final_tier1_genes.csv';GM=R/'data/processed/gene_id_map.csv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ids(p):
 s=gzip.decompress(p.read_bytes()).decode();s='\n'.join(l for l in s.splitlines() if l.startswith(('^SAMPLE =','!Sample_relation')));return {k:set(re.findall(v,s,re.M)) for k,v in {'GSM':r'^\^SAMPLE = (GSM\d+)','BioSample':r'SAM[NED][A-Z]?\d+','SRA_experiment':r'[SED]RX\d+'}.items()}
def bh(p):
 p=np.asarray(p,float);out=np.full(p.shape,np.nan);ok=np.isfinite(p)
 if ok.any():out[ok]=false_discovery_control(p[ok])
 return out

def analyse(expr,frozen,meta):
 tab=frozen[['Gene','Ensembl_ID','Cluster','Fibrosis_rho','Direction']].rename(columns={'Fibrosis_rho':'discovery_median_rho','Direction':'discovery_direction'}).copy()
 tab['available']=tab.Ensembl_ID.isin(expr.index);tab['testable']=tab.Ensembl_ID.map(expr.max(axis=1)-expr.min(axis=1)).fillna(0).gt(1e-10)
 valid=tab.index[tab.testable];a=expr.loc[tab.loc[valid,'Ensembl_ID'],meta.index[meta.group.eq('advanced')]].to_numpy();m=expr.loc[tab.loc[valid,'Ensembl_ID'],meta.index[meta.group.eq('mild')]].to_numpy()
 diff=a.mean(axis=1)-m.mean(axis=1);v1=a.var(axis=1,ddof=1)/a.shape[1];v0=m.var(axis=1,ddof=1)/m.shape[1];se=np.sqrt(v1+v0);df=(v1+v0)**2/(v1*v1/(a.shape[1]-1)+v0*v0/(m.shape[1]-1));crit=t.ppf(.975,df)
 statistic=diff/se;pvalue=2*t.sf(np.abs(statistic),df)
 for k,v in {'mean_advanced':a.mean(axis=1),'mean_mild':m.mean(axis=1),'advanced_minus_mild':diff,'welch_statistic':statistic,'welch_df':df,'variance_advanced':a.var(axis=1,ddof=1),'variance_mild':m.var(axis=1,ddof=1),'p_two_sided':pvalue,'CI95_low':diff-crit*se,'CI95_high':diff+crit*se}.items():tab.loc[valid,k]=v
 tab['q_BH']=bh(tab.get('p_two_sided',np.full(len(tab),np.nan)));tab['same_direction']=pd.Series(pd.NA,index=tab.index,dtype='boolean');tab.loc[valid,'same_direction']=np.sign(diff)==np.sign(tab.loc[valid,'discovery_median_rho']);tab['replicated']=tab.testable & tab.same_direction.fillna(False) & tab.q_BH.lt(.05)
 return tab

def main():
 assert (O/'analysis_plan.md').exists();(O/'preprocessed').mkdir(exist_ok=True)
 soft=S/'GSE49541_family.soft.gz';matrix=S/'GSE49541_series_matrix.txt.gz';text=gzip.decompress(soft.read_bytes()).decode()
 annotation=text.split('!platform_table_begin\n',1)[1].split('!platform_table_end',1)[0];annot=pd.read_csv(io.StringIO(annotation),sep='\t',dtype=str,keep_default_na=False)
 gm=pd.read_csv(GM,dtype=str,keep_default_na=False);pairs=gm.loc[gm.entrez_id.str.fullmatch(r'\d+') & gm.ensembl_id.str.fullmatch(r'ENSG\d{11}'),['entrez_id','ensembl_id']].drop_duplicates();sets=pairs.groupby('entrez_id').ensembl_id.agg(set);unique={k:next(iter(v)) for k,v in sets.items() if len(v)==1}
 audit=annot[['ID','Gene Symbol','ENTREZ_GENE_ID']].copy();audit['single_entrez']=audit.ENTREZ_GENE_ID.str.fullmatch(r'\d+');audit['Ensembl_ID']=audit.ENTREZ_GENE_ID.map(unique).where(audit.single_entrez,'');audit['status']=np.where(~audit.single_entrez,'no_single_Entrez',np.where(audit.Ensembl_ID.fillna('').eq(''),'unmapped_or_ambiguous_Entrez','retained'));audit.to_csv(O/'preprocessed/probe_mapping_audit.tsv.gz',sep='\t',index=False)
 s=gzip.decompress(matrix.read_bytes()).decode();body=s.split('!series_matrix_table_begin\n',1)[1].split('!series_matrix_table_end',1)[0];expr=pd.read_csv(io.StringIO(body),sep='\t',index_col=0);assert expr.index.is_unique and expr.columns.is_unique and expr.shape==(54675,72)
 assert np.isfinite(expr.to_numpy()).all();quant=np.quantile(expr.to_numpy(),[0,.01,.5,.99,1]);assert quant[-1]<30,'Unexpected scale; inspect before testing'
 meta=pd.read_csv(S/'sample_metadata.tsv',sep='\t',dtype=str,keep_default_na=False).set_index('gsm').loc[expr.columns];assert meta.index.is_unique and meta.title.is_unique
 meta['group']=meta.stage.str.extract(r'^(mild|advanced)',expand=False);assert meta.group.value_counts().to_dict()=={'mild':40,'advanced':32};assert set(meta.data_processing)=={'GC-RMA'}
 assert not expr.T.duplicated(keep=False).any(),'Identical expression profiles require review'
 meta.to_csv(O/'preprocessed/sample_metadata.tsv',sep='\t');qc=pd.DataFrame({'group':meta.group,'min':expr.min(),'q25':expr.quantile(.25),'median':expr.median(),'q75':expr.quantile(.75),'max':expr.max(),'mean':expr.mean(),'sd':expr.std()});qc.to_csv(O/'preprocessed/sample_qc.tsv',sep='\t')
 retained=audit[audit.status.eq('retained')].set_index('ID');mapped=expr.loc[retained.index].copy();mapped.index=retained.Ensembl_ID;means=mapped.groupby(level=0).mean();medians=mapped.groupby(level=0).median();means.to_csv(O/'preprocessed/gene_mean_log_expression.tsv.gz',sep='\t',float_format='%.10g');medians.to_csv(O/'preprocessed/gene_median_log_expression.tsv.gz',sep='\t',float_format='%.10g')
 tier=pd.read_csv(TIER);short=pd.read_csv(SHORT);assert len(tier)==447 and len(short)==23
 cov=[];results={};summaries=[]
 for name,frozen in [('shortlist23',short),('Tier1',tier)]:
  coverage=frozen[['Gene','Ensembl_ID']].copy();coverage['eligible_probes']=coverage.Ensembl_ID.map(retained.Ensembl_ID.value_counts()).fillna(0).astype(int);coverage.to_csv(O/f'{name}_probe_coverage.csv',index=False)
  for method,x in [('primary_mean',means),('sensitivity_median',medians)]:
   tab=analyse(x,frozen,meta);tab['eligible_probes']=tab.Ensembl_ID.map(retained.Ensembl_ID.value_counts()).fillna(0).astype(int);tab.to_csv(O/f'{name}_{method}.csv',index=False,float_format='%.12g');results[name,method]=tab
   v=tab[tab.testable];d=v.same_direction.astype(bool);sig=v.q_BH.lt(.05);summaries.append({'family':name,'method':method,'original_genes':len(tab),'testable_genes':len(v),'same_direction':int(d.sum()),'concordant_significant':int((d&sig).sum()),'opposite_significant':int((~d&sig).sum()),'same_direction_nonsignificant':int((d&~sig).sum()),'opposite_nonsignificant':int((~d&~sig).sum()),'untestable':int((~tab.testable).sum())})
 summary=pd.DataFrame(summaries);summary.to_csv(O/'replication_summary.csv',index=False)
 # Probe effects are descriptive; they never determine inclusion or the primary summary.
 targets=set(tier.Ensembl_ID);pr=retained[retained.Ensembl_ID.isin(targets)].copy();pr['advanced_minus_mild']=expr.loc[pr.index,meta.index[meta.group.eq('advanced')]].mean(axis=1)-expr.loc[pr.index,meta.index[meta.group.eq('mild')]].mean(axis=1);dr=tier.set_index('Ensembl_ID').Fibrosis_rho;pr['range_all72']=expr.loc[pr.index].max(axis=1)-expr.loc[pr.index].min(axis=1);pr['fraction_at_deposited_floor']=expr.loc[pr.index].eq(quant[0]).mean(axis=1);pr['same_direction']=np.sign(pr.advanced_minus_mild)==np.sign(pr.Ensembl_ID.map(dr));pr.to_csv(O/'Tier1_probe_direction_audit.csv',index_label='probe_id')
 opposite=pr.groupby('Ensembl_ID').advanced_minus_mild.agg(lambda x:bool((x>0).any() and (x<0).any()));pd.DataFrame({'mixed_probe_effect_directions':opposite}).to_csv(O/'Tier1_probe_disagreement.csv')
 candidate=ids(soft);others=list((B/'candidate_screening_2026-11-07/original_cohort_metadata').glob('*soft.gz'))+[B/f'candidate_screening_2026-11-07/{g}/{g}_family.soft.gz' for g in ['GSE225740','GSE281797']];overlaps=[]
 for p in sorted(others):
  other=ids(p);row={'other_accession':p.name.split('_')[0]}
  for k in candidate:row[k+'_candidate_available']=len(candidate[k]);row[k+'_other_available']=len(other[k]);row[k+'_overlap']=len(candidate[k]&other[k]) if candidate[k] and other[k] else 'not_assessable_missing_identifiers'
  overlaps.append(row)
 pd.DataFrame(overlaps).to_csv(O/'deposited_identifier_overlap.tsv',sep='\t',index=False)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
 tab=results['shortlist23','primary_mean'];sens=results['shortlist23','sensitivity_median'];fig,ax=plt.subplots(figsize=(8,9));yy=np.arange(len(tab))[::-1];valid=tab.testable.to_numpy();v=tab.loc[valid];color=np.where(v.replicated,'#147d64',np.where(v.q_BH.lt(.05),'#a62639','#929292'))
 for idx,(_,r),c in zip(yy[valid],v.iterrows(),color):ax.plot([r.CI95_low,r.CI95_high],[idx,idx],color=c,lw=1.2);ax.scatter(r.advanced_minus_mild,idx,color=c,s=28,zorder=3)
 for idx,(_,r) in zip(yy[~valid],tab.loc[~valid].iterrows()):ax.text(.02,idx,'Not measurable',transform=ax.get_yaxis_transform(),va='center',color='#666')
 ax.axvline(0,color='black',ls='--',lw=.8);ax.set_yticks(yy,tab.Gene);ax.set_xlabel('Advanced − mild: mean GC-RMA log expression (95% CI)');ax.set_title('GSE49541: fixed 23-gene shortlist',pad=14);ax.grid(axis='x',alpha=.15);fig.text(.16,.015,'40 mild (F0–F1), 32 advanced (F3–F4).\nGreen: concordant and BH q<0.05; grey: nonsignificant; red: opposite and significant.\nBH family contains only testable shortlisted genes. CIs are pointwise, not multiplicity-adjusted.',fontsize=8);fig.tight_layout(rect=(0,.08,1,1));fig.savefig(O/'shortlist23_group_contrast.pdf',bbox_inches='tight');fig.savefig(O/'shortlist23_group_contrast.png',dpi=180,bbox_inches='tight');plt.close(fig)
 fig,ax=plt.subplots(figsize=(10,4));ax.boxplot([expr[c].to_numpy() for c in expr.columns],showfliers=False,widths=.65,patch_artist=False);ax.set_xticks([1,18,36,54,72]);ax.set_xlabel('Sample order in deposited matrix');ax.set_ylabel('GC-RMA processed log expression');ax.set_title('GSE49541 deposited expression distributions');fig.tight_layout();fig.savefig(O/'sample_distributions.pdf',bbox_inches='tight');plt.close(fig)
 payload={'accession':'GSE49541','n_patients':72,'groups':{'mild_F0_F1':40,'advanced_F3_F4':32},'deposited_processing':'GC-RMA; already logarithmic; no second transform or CPM','probe_rows':len(expr),'expression_quantiles_0_1_50_99_100_percent':quant.tolist(),'mapping_status_counts':audit.status.value_counts().to_dict(),'gene_summaries':len(means),'mixed_probe_directions_Tier1_genes':int(opposite.sum()),'results':summaries,'software':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'inputs_sha256':{str(p.relative_to(R)):sha(p) for p in [soft,matrix,S/'sample_metadata.tsv',SHORT,TIER,GM,O/'analysis_plan.md',Path(__file__)]},'limitations':['Grouped-stage severity comparison only; no individual F0–F4 stage inference.','Unique legacy probe annotation is not a demonstration of probe specificity; no detection p-values or raw CEL reprocessing.','Unadjusted group contrasts: age, sex and metabolic confounding cannot be excluded.','GSE31803 and GSE49541 reuse specimens; do not count them as independent cohorts.','Provenance supports distinct recruitment but public identifiers cannot prove donor-level nonoverlap.']}
 (O/'summary.json').write_text(json.dumps(payload,indent=2));print(summary.to_string(index=False));print('Missing shortlist:',tab.loc[~tab.testable,'Gene'].tolist());print('Quantiles:',quant);print('Mapping:',payload['mapping_status_counts']);print('Mixed probe directions Tier1:',int(opposite.sum()))
if __name__=='__main__':main()
