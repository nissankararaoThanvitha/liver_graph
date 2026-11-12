#!/usr/bin/env python3
"""Retrospective audit; supplied inputs/results remain untouched."""
from pathlib import Path
import sys,importlib.util,hashlib,json,gzip,re,platform
sys.path.insert(0,'/tmp/liver-validation-audit-deps')
A=Path(__file__).resolve().parent;R=A.parents[1];sys.path.insert(0,str(R))
import numpy as np,pandas as pd,scipy
from scipy.stats import spearmanr,false_discovery_control,rankdata
spec=importlib.util.spec_from_file_location('friend_audit',A/'friend_package/code/validate_external.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);f.ROOT=R;f.RAW=A/'sources'
O=A/'verified';O.mkdir(exist_ok=True)
GSES=['GSE213621','GSE225740','GSE268273'];gene=pd.read_csv(R/'Paper1_HighConfidence/11_final_all_3845_genes.csv');short=pd.read_csv(R/'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv');universe=pd.read_csv(R/'data/progression_full/progression_fibrosis.csv');U=set(universe.ensembl_id)
T1=set(gene.loc[gene.Tier.str.startswith('Tier 1'),'Ensembl_ID']);SS=set(short.Ensembl_ID);SETS={'shortlist23':SS,'Tier1':T1,'all3845':set(gene.Ensembl_ID)};signs=gene.set_index('Ensembl_ID').Fibrosis_rho.apply(np.sign)
lk=f.build_lookups(str(A/'sources/reference/hgnc_complete_set.txt'))
friend=pd.read_csv(A/'friend_package/results/validation_per_gene.csv').set_index('Ensembl_ID');repro=pd.read_csv(A/'reproduction_current_hgnc/validation_per_gene.csv').set_index('Ensembl_ID');fs=pd.read_csv(A/'friend_package/results/validation_summary.csv')

def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def soft_samples(path):
 text=gzip.decompress(path.read_bytes()).decode();samples=[]
 for b in text.split('^SAMPLE = ')[1:]:
  d={'GSM':b.splitlines()[0].strip()};rel=[]
  for line in b.splitlines()[1:]:
   if line.startswith('^'):break
   if not line.startswith('!Sample_') or ' = ' not in line:continue
   k,v=line.split(' = ',1);k=k.removeprefix('!Sample_')
   if k=='relation':rel.append(v)
   if k=='characteristics_ch1' and ': ' in v:ck,cv=v.split(': ',1);d[ck.lower()]=cv
   elif k in ['title','description']:d[k]=v
  rel='\n'.join(rel);d['BioSample']=';'.join(sorted(set(re.findall(r'\bSAM[NED][A-Z]?\d+\b',rel))));d['SRA_experiment']=';'.join(sorted(set(re.findall(r'\b[SED]RX\d+\b',rel))));samples.append(d)
 return pd.DataFrame(samples)
def idsets(df):return {k:set(s for cell in df[k].fillna('') for s in cell.split(';') if s) for k in ['GSM','BioSample','SRA_experiment']}
def auc_pair(score,pos,neg):
 # Independent pairwise probability, including half credit for ties.
 a=np.asarray(score)[np.asarray(pos,bool)];b=np.asarray(score)[np.asarray(neg,bool)]
 return float(((a[:,None]>b[None,:])+.5*(a[:,None]==b[None,:])).mean()) if len(a) and len(b) else np.nan

def calc(v,m):
 cols=m.col.tolist();x=v.loc[v.index.isin(U),cols];x=x[x.nunique(axis=1)>1];y=m.stage.to_numpy(float)
 vals=np.array([spearmanr(row,y) for row in x.to_numpy()]);res=pd.DataFrame({'rho':vals[:,0],'p':vals[:,1]},index=x.index);res['q_universe']=false_discovery_control(res.p.to_numpy());return res

def summarise(res,population,gse):
 rows=[]
 for name,ids in SETS.items():
  selected=gene[gene.Ensembl_ID.isin(ids)].copy().set_index('Ensembl_ID');selected=selected.join(res);valid=selected.p.notna();q=np.full(len(selected),np.nan)
  if valid.any():q[valid]=false_discovery_control(selected.loc[valid,'p'].to_numpy())
  selected['q_targeted_family']=q;selected['same_direction']=np.sign(selected.rho)==np.sign(selected.Fibrosis_rho);selected.loc[~valid,'same_direction']=False
  selected['concordant_significant_universe']=valid & selected.same_direction & (selected.q_universe<.05);selected['concordant_significant_targeted']=valid & selected.same_direction & (selected.q_targeted_family<.05)
  selected.to_csv(O/f'{gse}_{population}_{name}.csv')
  for correction in ['universe','targeted_family']:
   sig=selected['q_'+correction]<.05
   rows.append({'cohort':gse,'population':population,'gene_set':name,'correction':correction,'original_genes':len(selected),'testable':int(valid.sum()),'same_direction':int((valid&selected.same_direction).sum()),'concordant_significant':int((valid&selected.same_direction&sig).sum()),'opposite_significant':int((valid&~selected.same_direction&selected.rho.ne(0)&sig).sum())})
 return rows

qc=[];overlaps=[];matches=[];summary=[];aucs=[];groups=[];log=[];manifest=[];allsoft={};stage_tables=[];metadata={}
# Recover sample records from SOFT, separately from expression reader.
paths={p.name.split('_')[0]:p for p in (R/'independent_validation/candidate_screening_2026-11-07/original_cohort_metadata').glob('*soft.gz')}
for g in ['GSE225740','GSE281797','GSE49541']:
 paths[g]=R/f'independent_validation/candidate_screening_2026-11-07/{g}/{g}_family.soft.gz'
for g in ['GSE213621','GSE268273']:paths[g]=A/f'sources/{g}/{g}_family.soft.gz'
for g,p in paths.items():allsoft[g]=soft_samples(p)
for g in GSES:
 raw,typ,unit,m=f.READERS[g]();fullm=f.series_matrix(g);assert raw.columns.is_unique and m.col.is_unique and m.geo_accession.is_unique
 assert set(m.col)==set(raw.columns),'Non-bijective sample alignment'
 assert np.isfinite(raw.to_numpy(dtype=float)).all()
 if unit!='log2_voom':assert raw.to_numpy().min()>=0
 assert not raw.T.duplicated(keep=False).any(),'Identical full expression profiles'
 staged=m[m.stage.notna()].copy();assert len(staged) in [299,87,109]
 soft=allsoft[g].set_index('GSM');primary=soft.loc[staged.geo_accession].copy();primary.to_csv(O/f'{g}_primary_source_metadata.tsv',sep='\t')
 metadata[g]=primary
 for other,s in allsoft.items():
  if other==g:continue
  a=idsets(primary.reset_index());b=idsets(s);d={'cohort':g,'other_cohort':other}
  for k in a:d[k+'_available']=len(a[k]);d[k+'_other_available']=len(b[k]);d[k+'_overlap']=len(a[k]&b[k]) if a[k] and b[k] else 'not_assessable_missing_identifiers'
  overlaps.append(d)
 v,z=f.preprocess(raw,typ,unit,lk,log);assert v.index.is_unique and np.isfinite(v.to_numpy()).all()
 # Verify a separate reconstruction of mapping, aggregation, denominator and transform.
 rx=raw.loc[~raw.index.astype(str).str.strip().duplicated(keep='first')].copy();rx.index=rx.index.astype(str).str.strip();lib=rx.sum(axis=0) if unit=='raw_count' else None;rx=rx[~rx.index.str.contains('_PAR_Y')];maps={s:f.resolve(s,typ,lk) for s in rx.index};maps={k:val[0] for k,val in maps.items() if val is not None};mx=rx.loc[list(maps)].copy();mx.index=mx.index.map(maps)
 if unit=='log2_voom':manual=np.log2(np.power(2.,mx).groupby(level=0).sum())
 else:
  mx=mx.groupby(level=0).sum();manual=np.log2(mx.div(lib,axis=1)*1e6+1) if unit=='raw_count' else np.log2(mx+1)
 np.testing.assert_allclose(v.sort_index(),manual.sort_index(),atol=1e-12,rtol=1e-12)
 res=calc(v,staged);res.to_csv(O/f'{g}_all_testable_universe.csv')
 ix=friend.index[friend[g+'_p'].notna()];assert set(ix)==(set(res.index)&set(gene.Ensembl_ID))
 for suffix,ourcol in [('rho','rho'),('p','p'),('q','q_universe')]:
  diff=float(np.max(np.abs(friend.loc[ix,g+'_'+suffix].to_numpy()-res.loc[ix,ourcol].to_numpy())));matches.append({'cohort':g,'quantity':suffix,'n_genes':len(ix),'max_abs_difference':diff,'match_tolerance_1e_10':diff<1e-10});assert diff<1e-10
 summary+=summarise(res,'all_staged',g)
 qc.append({'cohort':g,'raw_rows':len(raw),'raw_duplicate_rows':int(raw.index.duplicated().sum()),'all_columns':raw.shape[1],'staged_columns':len(staged),'excluded_unstaged_or_control':len(m)-len(staged),'raw_min':float(raw.min().min()),'raw_max':float(raw.max().max()),'nonfinite_values':0,'identical_profiles':0,'mapped_genes':len(v),'testable_universe':len(res),'unit':unit})
 stagefield={'GSE213621':'fibrotic stage','GSE225740':'fibrosis','GSE268273':'fibrosis degree'}[g]
 for k,n in staged.stage.value_counts().sort_index().items():stage_tables.append({'cohort':g,'analysis_stage_code':k,'n':n})
 for name,ids in SETS.items():
  present=sorted(ids & set(res.index));up=[e for e in present if signs[e]>0];down=[e for e in present if signs[e]<0];score=z.loc[up,staged.col].mean(axis=0)-z.loc[down,staged.col].mean(axis=0)
  # Mann–Whitney score and independent pairwise AUC must agree.
  pos=staged.advanced.to_numpy(bool);neg=staged.mild.to_numpy(bool);a=auc_pair(score,pos,neg);np.testing.assert_allclose(a,f.auc(score.to_numpy(),pos,neg),atol=1e-12)
  fname={'shortlist23':'Top 23 shortlist','Tier1':'Tier 1 (447)','all3845':'All 3,845'}[name];expected=fs[(fs.cohort==g)&(fs.subgroup=='all')&(fs.gene_set==fname)].iloc[0];assert abs(a-expected.auc_advanced_vs_mild)<=.000501
  # Standardizing only eligible staged patients is a labelled score sensitivity.
  local=v[staged.col];local=local.sub(local.mean(axis=1),axis=0).div(local.std(axis=1,ddof=1).replace(0,np.nan),axis=0);score_local=local.loc[up].mean(axis=0)-local.loc[down].mean(axis=0)
  std_sensitivity=auc_pair(score_local,pos,neg);n=len(staged);ddof1score=score*np.sqrt((raw.shape[1]-1)/raw.shape[1]);np.testing.assert_allclose(auc_pair(ddof1score,pos,neg),a,atol=1e-12)
  rng=np.random.default_rng(20261107);pi=np.where(pos)[0];ni=np.where(neg)[0];boot=[];sa=score.to_numpy()
  for _ in range(2000):
   bpa=rng.choice(pi,len(pi));bna=rng.choice(ni,len(ni));aa=sa[bpa];bb=sa[bna];boot.append(float(((aa[:,None]>bb[None,:])+.5*(aa[:,None]==bb[None,:])).mean()))
  lo,hi=np.quantile(boot,[.025,.975]);aucs.append({'cohort':g,'gene_set':name,'n_genes':len(present),'n_mild':int(neg.sum()),'n_advanced':int(pos.sum()),'AUC_verified_pairwise':a,'friend_AUC_rounded':expected.auc_advanced_vs_mild,'independent_bootstrap2000_CI_low':lo,'independent_bootstrap2000_CI_high':hi,'AUC_z_within_staged_only_sensitivity':std_sensitivity,'score_stage_rho':float(spearmanr(score,staged.stage).statistic),'score_stage_rho_friend_rounded':expected.score_rho_with_stage})
  pd.DataFrame({'sample_column':staged.col,'GSM':staged.geo_accession,'stage_code':staged.stage,'mild':pos*0+neg,'advanced':pos,'score_friend_ddof0_all_columns':sa,'score_staged_ddof1_sensitivity':score_local.to_numpy()}).to_csv(O/f'{g}_{name}_patient_scores.csv',index=False)
 if g=='GSE268273':
  full=fullm.set_index('geo_accession');labels=full.loc[staged.geo_accession,'case/control'].to_numpy();stage=staged.stage.to_numpy()
  for group in sorted(set(labels)):
   sub=staged.iloc[np.where(labels==group)[0]];groups.append({'cohort':g,'group':group,'n':len(sub),'stage_counts':json.dumps(sub.stage.value_counts().sort_index().to_dict())});sres=calc(v,sub);summary+=summarise(sres,group,g)
  # Partial rank correlation controlling IMID/classic and sex; descriptive confounding sensitivity.
  idx=staged.col.tolist();primarylabel=labels=='IMID-NAFLD';sex=full.loc[staged.geo_accession,'sex'].str.lower().eq('male').to_numpy();design=np.column_stack([np.ones(len(staged)),primarylabel,sex]);assert np.linalg.matrix_rank(design)==3
  y=rankdata(staged.stage);y=y-design@np.linalg.lstsq(design,y,rcond=None)[0];xx=np.apply_along_axis(rankdata,1,v.loc[res.index,idx].to_numpy());xx-= (design@np.linalg.lstsq(design,xx.T,rcond=None)[0]).T;xx-=xx.mean(axis=1,keepdims=True);y-=y.mean();rr=xx@y/np.sqrt((xx*xx).sum(axis=1)*(y*y).sum());df=len(staged)-4
  pp=2*scipy.stats.t.sf(np.abs(rr*np.sqrt(df/np.maximum(1-rr*rr,1e-30))),df);partial=pd.DataFrame({'rho':rr,'p':pp,'q_universe':false_discovery_control(pp)},index=res.index);summary+=summarise(partial,'partial_rank_adjusted_IMID_sex',g);partial.to_csv(O/f'{g}_partial_rank_IMID_sex_all_universe.csv')
 print(g,'QC, scalar Spearman, BH, frozen-gene counts, scores/AUC checked',flush=True)

pd.DataFrame(qc).to_csv(O/'sample_expression_QC.csv',index=False);pd.DataFrame(overlaps).to_csv(O/'deposited_identifier_overlap.tsv',sep='\t',index=False);pd.DataFrame(matches).to_csv(O/'friend_gene_results_comparison.csv',index=False);pd.DataFrame(summary).to_csv(O/'gene_set_summary_both_corrections.csv',index=False);pd.DataFrame(aucs).to_csv(O/'score_AUC_verification.csv',index=False);pd.DataFrame(groups).to_csv(O/'GSE268273_subgroup_stage_counts.csv',index=False);pd.DataFrame(stage_tables).to_csv(O/'stage_counts.csv',index=False)
for p in list((A/'sources').rglob('*'))+[R/'map_gene_ids.py',R/'build_graph_all.py',R/'data/processed/gene_id_map.csv',R/'data/progression_full/progression_fibrosis.csv',R/'Paper1_HighConfidence/11_final_all_3845_genes.csv',R/'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv',Path(__file__),A/'reproduce_friend.py',A/'audit_plan.md',Path('/home/nikitha07/Downloads/Paper1_Validation.zip')]:
 if p.is_file():manifest.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sh(p)})
(A/'audit_manifest.json').write_text(json.dumps({'software':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__},'files':manifest},indent=2));print('Completed audit files:',O,flush=True)
