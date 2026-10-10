"""Prepare a frozen 2x2 sensitivity design; never edit active source inputs."""
from pathlib import Path
import shutil,json,hashlib,gzip,os,sys,ast
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[2];D=R/'sensitivity_2026-10-10'
if (D/'input_preparation.json').exists():raise SystemExit('Inputs already prepared; use existing manifest rather than overwrite')
shared=D/'shared';shared.mkdir(parents=True,exist_ok=True)
flag=pd.read_csv(R/'label_audit_GSE130970_2026-10-10/samples_requiring_review.csv');flagids=set(flag.sample_id);assert len(flagids)==5
clinical=pd.read_csv(R/'data/graph/nodes_sample_clinical.csv',dtype=str).fillna('');assert set(clinical.loc[clinical.sample_id.isin(flagids),'dataset_id'])=={'GSE130970'}
source_scripts=['biopsy_policy.py','find_progression_genes.py','export_for_mentor.py','paper1_task1_groups.py','paper1_task2_trajectories.py','paper1_task3_transitions.py','paper1_task4_enrichment.py','build_progression_edges.py','scripts/00_all_4692_progression_genes.py','scripts/powermatched_transitions.py','scripts/high_confidence_genes.py','scripts/loso_validation.py','scripts/kg_subgraph.py','scripts/make_fig1.py']
# Freeze active outputs/clinical metadata/code and verify preservation after the study.
protected=[p for name in ['Paper1_Package','Paper1_Results','Paper1_HighConfidence','data/progression_full','data/for_mentor','data/graph','data/processed'] for p in (R/name).rglob('*') if p.is_file()]
protected += [R/n for n in source_scripts]
(D/'active_baseline_hashes.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},indent=2))
# Recover the alternate transform directly from deposited linear RLE counts.
raw=R/'unit_audit_GSE193066_2026-10-10/GSE193066_NAFLD.HUn164.gct.gz'
with gzip.open(raw,'rt') as f:
 f.readline();f.readline();matrix=pd.read_csv(f,sep='\t',index_col=0)
matrix=matrix.select_dtypes(include='number');matrix.index=matrix.index.astype(str).str.strip();matrix=matrix[~matrix.index.duplicated(keep='first')];assert matrix.shape==(17231,164) and np.isfinite(matrix.to_numpy()).all() and (matrix.to_numpy()>=0).all()
gmap=pd.read_csv(R/'data/processed/gene_id_map.csv',dtype=str);lookup=gmap[gmap.dataset_id=='GSE193066'].set_index('gene_id_raw').ensembl_id
cw=pd.read_csv(R/'data/processed/sample_crosswalk.csv',dtype=str);samplemap=cw[cw.dataset_id=='GSE193066'].set_index('sample_key').sample_id
mapped=matrix.copy();mapped['ensembl_id']=matrix.index.map(lookup);mapped=mapped[mapped.ensembl_id.notna()].groupby('ensembl_id').sum();transformed=np.log2(mapped+1);z=transformed.sub(transformed.mean(axis=1),axis=0).div(transformed.std(axis=1,ddof=1).replace(0,np.nan),axis=0).fillna(0);z.columns=z.columns.map(samplemap)
core=pd.read_csv(R/'data/expression_analysis_core/nodes_gene.csv');eligible=list(core.loc[core.n_datasets==8,'ensembl_id']);assert len(eligible)==14794
z=z.loc[eligible];z.index.name='ensembl_id';z.columns.name='sample_id';long=z.stack().rename('value_z').reset_index()[['sample_id','ensembl_id','value_z']];assert len(long)==14794*164 and not long.duplicated(['sample_id','ensembl_id']).any()
alt=shared/'edges_GSE193066_preserved_RLE.csv';long.to_csv(alt,index=False)
# Independent single-gene arithmetic check of log+sample-SD standardisation.
for gid in eligible[:20]:
 v=np.array([np.log2(float(mapped.loc[gid,c])+1) for c in mapped.columns]);expected=(v-v.mean())/v.std(ddof=1);assert np.allclose(z.loc[gid].to_numpy(),expected,atol=1e-12)
# Design is fixed before examining any sensitivity shortlist.
design={'baseline':{'unclassify':False,'preserve_rle':False},'labels_only':{'unclassify':True,'preserve_rle':False},'normalisation_only':{'unclassify':False,'preserve_rle':True},'combined':{'unclassify':True,'preserve_rle':True}}
for name,config in design.items():
 run=D/name;run.mkdir(exist_ok=False)
 for n in source_scripts:
  dest=run/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,dest)
 for folder in ['data/processed','data/graph']:shutil.copytree(R/folder,run/folder)
 for folder in ['data/graph_okg','data/genesets']:
  p=run/folder;p.symlink_to(os.path.relpath(R/folder,p.parent),target_is_directory=True)
 # Inputs are read-only references. Generated progression edges go elsewhere.
 exp=run/'data/expression_analysis_core';exp.mkdir()
 for p in (R/'data/expression_analysis_core').glob('*.csv'):
  target=alt if config['preserve_rle'] and p.name=='edges_GSE193066.csv' else p
  (exp/p.name).symlink_to(os.path.relpath(target,exp))
 clin=clinical.copy();clin['disease_group_baseline']=clin.disease_group;clin['label_sensitivity_status']='unchanged'
 if config['unclassify']:
  ix=clin.sample_id.isin(flagids);clin.loc[ix,'disease_group']='';clin.loc[ix,'disease_provenance']='unclassified_sensitivity';clin.loc[ix,'label_sensitivity_status']='flagged_case_unclassified'
 unchanged=[c for c in clinical if c not in ['disease_group','disease_provenance']];assert clin[unchanged].equals(clinical[unchanged]);assert clin.loc[~clin.sample_id.isin(flagids),'disease_group'].equals(clinical.loc[~clinical.sample_id.isin(flagids),'disease_group'])
 clin.to_csv(run/'data/graph/nodes_sample_clinical.csv',index=False)
 (run/'run_config.json').write_text(json.dumps(config,indent=2))
manifest={'runs':design,'unclassified_sample_ids':sorted(flagids),'alternate_transform':'log2(deposited RLE count+1), then within-gene study mean/sample-SD standardisation over all164 biopsies; no CPM rescaling','eligible_genes':14794,'alternate_rows':len(long),'source_matrix_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'alternate_csv_sha256':hashlib.sha256(alt.read_bytes()).hexdigest(),'fixed_clustering_k':5,'fixed_seed':42,'top25_rule':'five Tier1 genes per cluster, score then absolute rho; never lower thresholds to fill slots','top12_rule':'existing enrichment/size/connectivity/Jaccard rules','F_ablation':'set F=0; retain absolute Tier1>=7 threshold, maximum8; shortages of five per cluster reported rather than filled','active_files_modified':False}
(D/'input_preparation.json').write_text(json.dumps(manifest,indent=2));print('Prepared four isolated runs; five label exclusions verified; alternate164x14794 transform verified; active baseline hashed.')
