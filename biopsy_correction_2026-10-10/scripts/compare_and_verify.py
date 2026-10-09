from pathlib import Path
import hashlib,json,sys
import numpy as np,pandas as pd
from scipy.stats import spearmanr
R=Path(__file__).resolve().parents[2];D=R/'biopsy_correction_2026-10-10';sys.path.insert(0,str(D))
from biopsy_policy import select_biopsies,patient_expression
checks=[]
def check(label,ok,detail=''):
 checks.append({'check':label,'passed':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+label,detail)
def rd(base,path):
    if base == R:
        import tarfile,io
        with tarfile.open(R/'archives/previous_results_2026-10-10.tar.gz','r:gz') as archive:
            return pd.read_csv(io.BytesIO(archive.extractfile(path).read()))
    return pd.read_csv(base/path)
def sig(t):return t[(t.q_value<.05)&(t.n_agree==t.n_studies)]
changed=[]
with __import__('tarfile').open(R/'archives/previous_results_2026-10-10.tar.gz','r:gz') as archive:
    for p,h in json.loads((D/'baseline_hashes.json').read_text()).items():
        if hashlib.sha256(archive.extractfile(p).read()).hexdigest()!=h:changed.append(p)
check('All original result/package files preserved in recovery archive',not changed,changed)
oldf=sig(rd(R,'data/progression_full/progression_fibrosis.csv'));newf=sig(rd(D,'data/progression_full/progression_fibrosis.csv'));oldd=sig(rd(R,'data/progression_full/progression_disease.csv'));newd=sig(rd(D,'data/progression_full/progression_disease.csv'))
comparison={}
for axis,a,b in [('fibrosis',oldf,newf),('disease',oldd,newd)]:
 sa,sb=set(a.ensembl_id),set(b.ensembl_id);comparison[axis]={'original_count':len(a),'corrected_count':len(b),'added':sorted(sb-sa),'removed':sorted(sa-sb)}
 a=a.set_index('ensembl_id');b=b.set_index('ensembl_id');both=a[['symbol','median_rho','q_value']].join(b[['median_rho','q_value']],lsuffix='_original',rsuffix='_corrected',how='outer');both.to_csv(D/f'{axis}_statistics_comparison.csv')
 union=sa|sb;changes=both.loc[list((sa-sb)|(sb-sa))].copy();changes['membership_change']=['added' if g in sb else 'removed' for g in changes.index];changes.to_csv(D/f'{axis}_membership_changes.csv')
check('Disease-axis gene membership unchanged',comparison['disease']['added']==[] and comparison['disease']['removed']==[])
clusters=rd(D,'Paper1_Results/Task2/task2_gene_clusters.csv');check('Corrected cluster IDs exactly match fibrosis selection',set(clusters.ensembl_id)==set(newf.ensembl_id) and not clusters.ensembl_id.duplicated().any())
clinical=rd(D,'data/graph/nodes_sample_clinical.csv');selected=select_biopsies(clinical);patients=selected[selected.fibrosis_stage.notna()].drop_duplicates(['dataset_id','patient_id']);check('Exactly 610 independent staged patients',len(patients)==610)
perstudy=rd(D,'Paper1_HighConfidence/10_loso_per_study_all_eligible.csv');check('LOSO uses full 14794-gene eligible universe',len(perstudy)==14794)
runs=rd(D,'Paper1_HighConfidence/10_loso_all_eligible_runs.csv');check('LOSO records all eligible genes in five omitted-study fits',len(runs)==14794*5 and runs.left_out.nunique()==5)
# Independently verify the repeat-policy Spearman results for 20 genes, rather than mirroring vector code.
ids=clusters.ensembl_id.head(20).tolist();raw=rd(D,'data/expression_analysis_core/edges_GSE193066.csv');raw=raw[raw.ensembl_id.isin(ids)];lab=clinical[clinical.dataset_id=='GSE193066'];obs=patient_expression(raw,lab);key=perstudy.columns[0];rho_table=perstudy.set_index(key)
errors=[]
for gid,g in obs.groupby('ensembl_id'):
 rho,p=spearmanr(g.value_z,g.fibrosis_stage);expected=float(rho_table.loc[gid,'GSE193066_rho'])
 if not np.isclose(rho,expected,rtol=1e-10,atol=1e-12):errors.append(gid)
check('Independent scipy Spearman agrees for repeated-biopsy cohort',not errors,errors)
short=rd(D,'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv');tier=rd(D,'Paper1_HighConfidence/11_final_tier1_genes.csv');oldshort=rd(R,'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv');oldtier=rd(R,'Paper1_HighConfidence/11_final_tier1_genes.csv')
check('Shortlist contains 25 unique corrected Tier1 genes',len(short)==25 and short.Ensembl_ID.nunique()==25 and set(short.Ensembl_ID)<=set(tier.Ensembl_ID))
confidence=short.merge(clusters[['ensembl_id','membership_confidence','confidence_n_bootstraps']],left_on='Ensembl_ID',right_on='ensembl_id',validate='1:1').drop(columns='ensembl_id');confidence.to_csv(D/'Paper1_HighConfidence/shortlist_with_membership_confidence.csv',index=False)
comparison['shortlist']={'original_count':len(oldshort),'corrected_count':len(short),'retained':len(set(short.Ensembl_ID)&set(oldshort.Ensembl_ID)),'added_genes':sorted(set(short.Gene)-set(oldshort.Gene)),'removed_genes':sorted(set(oldshort.Gene)-set(short.Gene))}
comparison['tier1']={'original_count':len(oldtier),'corrected_count':len(tier),'retained':len(set(tier.Ensembl_ID)&set(oldtier.Ensembl_ID))}
comparison['loso']={c:{'original':oldtier[c].value_counts().sort_index().to_dict(),'corrected':tier[c].value_counts().sort_index().to_dict()} for c in ['LOSO_still_significant_of_5','LOSO_still_strong_rho0.30_of_5']}
comparison['clusters']=clusters.groupby(['cluster','cluster_name']).size().reset_index(name='genes').to_dict('records')
comparison['transitions']=rd(D,'Paper1_Results/Task3/task3_transition_summary.csv').fillna('').to_dict('records')
comparison['eligible_gene_universe']=14794;comparison['patient_policy']={'same_stage_repeats_averaged':28,'different_stage_second_biopsy_discarded':30,'staged_patients':610}
edge=rd(D,'data/graph_full/edges_my_progression.csv');check('Regenerated progression edges exactly reflect corrected selections',set(edge[edge.rel=='TRACKS_FIBROSIS'].ensembl_id)==set(newf.ensembl_id) and set(edge[edge.rel=='TRACKS_INFLAMMATION'].ensembl_id)==set(newd.ensembl_id))
# Export aggregation independently checked against one-patient stage averages for the audit genes.
stage=rd(D,'data/for_mentor/genes_by_fibrosis_stage.csv').set_index('ensembl_id');parts=[]
for file in sorted((D/'data/expression_analysis_core').glob('edges_GSE*.csv')):
 x=pd.read_csv(file);parts.append(x[x.ensembl_id.isin(ids)])
observations=patient_expression(pd.concat(parts,ignore_index=True),clinical);mean=observations[observations.fibrosis_stage.notna()].pivot_table(index='ensembl_id',columns='fibrosis_stage',values='value_z',aggfunc='mean').round(3)
check('Exported stage means equal one-patient averages',all(np.allclose(mean[c].loc[ids],stage.loc[ids,f'stage_{int(c)}'],atol=1e-12) for c in mean.columns))
check('Recovery script obtains credentials interactively', 'getpass.getpass' in (D/'scripts/export_core_from_live.py').read_text())
(D/'comparison_summary.json').write_text(json.dumps(comparison,indent=2,default=str));(D/'verification_results.json').write_text(json.dumps(checks,indent=2,default=str))
if not all(c['passed'] for c in checks):sys.exit(1)
print(json.dumps(comparison,indent=2,default=str))
