"""Compare earlier frozen-map/targeted-BH process with the audited friend process."""
from pathlib import Path
import sys,importlib.util,json
A=Path(__file__).resolve().parent;R=A.parents[1];sys.path.insert(0,str(R));sys.path.insert(0,'/tmp/liver-validation-audit-deps')
import pandas as pd,numpy as np
from scipy.stats import spearmanr,false_discovery_control
spec=importlib.util.spec_from_file_location('friend_comparison',A/'friend_package/code/validate_external.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);f.ROOT=R;f.RAW=A/'sources'
O=A/'earlier_process_comparison';O.mkdir(exist_ok=True)
gm=pd.read_csv(R/'data/processed/gene_id_map.csv',dtype=str).fillna('');short=pd.read_csv(R/'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv');master=pd.read_csv(R/'Paper1_HighConfidence/11_final_all_3845_genes.csv');universe=pd.read_csv(R/'data/progression_full/progression_fibrosis.csv');U=set(universe.ensembl_id)
def mapping(col):
 s=gm.loc[gm[col].ne('') & gm.ensembl_id.ne(''),[col,'ensembl_id']].drop_duplicates().groupby(col).ensembl_id.agg(set)
 return {k:next(iter(v)) for k,v in s.items() if len(v)==1}
lookup={'entrez':mapping('entrez_id'),'symbol':mapping('symbol')};summary=[];comparison=[];mappingstats=[]
for g in ['GSE213621','GSE225740','GSE268273']:
 raw,typ,unit,meta=f.READERS[g]();raw.index=raw.index.astype(str).str.strip();raw=raw.loc[~raw.index.duplicated(keep='first')];lib=raw.sum(axis=0) if unit=='raw_count' else None;raw=raw[~raw.index.str.contains('_PAR_Y')]
 ens={e:f.strip_version(e) if typ=='ensembl' else lookup[typ].get(e) for e in raw.index};audit=pd.DataFrame({'raw_id':list(ens),'Ensembl_ID':list(ens.values())});audit.to_csv(O/f'{g}_mapping.csv',index=False);ens={k:v for k,v in ens.items() if v is not None}
 x=raw.loc[list(ens)].copy();x.index=x.index.map(ens)
 if unit=='log2_voom':v=np.log2(np.power(2.,x).groupby(level=0).sum())
 else:
  x=x.groupby(level=0).sum();v=np.log2(x.div(lib,axis=1)*1e6+1) if unit=='raw_count' else np.log2(x+1)
 meta=meta[meta.stage.notna()];cols=meta.col.tolist();v=v.loc[v.index.isin(U),cols];v=v[v.nunique(axis=1)>1]
 vals=np.array([spearmanr(a,meta.stage) for a in v.to_numpy()]);res=pd.DataFrame({'rho':vals[:,0],'p':vals[:,1]},index=v.index);res['q_universe']=false_discovery_control(res.p.to_numpy())
 current=pd.read_csv(A/f'verified/{g}_all_testable_universe.csv',index_col=0);ix=res.index.intersection(current.index)
 comparison.append({'cohort':g,'earlier_testable_universe':len(res),'friend_testable_universe':len(current),'common_genes':len(ix),'max_rho_difference_common':float(abs(res.loc[ix,'rho']-current.loc[ix,'rho']).max()),'max_p_difference_common':float(abs(res.loc[ix,'p']-current.loc[ix,'p']).max()),'earlier_only_genes':len(res.index.difference(current.index)),'friend_only_genes':len(current.index.difference(res.index))})
 for name,ids in [('shortlist23',set(short.Ensembl_ID)),('Tier1',set(master.loc[master.Tier.str.startswith('Tier 1'),'Ensembl_ID']))]:
  m=master[master.Ensembl_ID.isin(ids)].set_index('Ensembl_ID').join(res);valid=m.p.notna();m['q_targeted']=np.nan;m.loc[valid,'q_targeted']=false_discovery_control(m.loc[valid,'p'].to_numpy());m['same_direction']=np.sign(m.rho)==np.sign(m.Fibrosis_rho)
  for correction in ['targeted','universe']:
   sig=m['q_'+correction]<.05;summary.append({'cohort':g,'gene_set':name,'mapping':'earlier_frozen_discovery_map','correction':correction,'testable':int(valid.sum()),'same_direction':int((valid & m.same_direction).sum()),'concordant_significant':int((valid&m.same_direction&sig).sum()),'opposite_significant':int((valid&~m.same_direction&sig).sum())})
  m.to_csv(O/f'{g}_{name}_all_results.csv')
 print(g,'earlier-process comparison complete',flush=True)
pd.DataFrame(summary).to_csv(O/'summary.csv',index=False);pd.DataFrame(comparison).to_csv(O/'shared_gene_statistics_comparison.csv',index=False)
print(pd.DataFrame(summary).to_string(index=False));print(pd.DataFrame(comparison).to_string(index=False))
