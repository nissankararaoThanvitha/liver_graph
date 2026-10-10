"""Run frozen sensitivity projects sequentially without writing active output folders."""
from pathlib import Path
import json,os,sys,subprocess,time
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[2];D=R/'sensitivity_2026-10-10';python=sys.executable
steps=[('discovery',['find_progression_genes.py','--repeat-policy','same_stage_mean','--out','data/progression_full']),('exports',['export_for_mentor.py']),('groups',['paper1_task1_groups.py','--out','Paper1_Results/Task1']),('clustering',['paper1_task2_trajectories.py','--out','Paper1_Results/Task2','5']),('transitions',['paper1_task3_transitions.py','--out','Paper1_Results/Task3','--clusters','Paper1_Results/Task2/task2_gene_clusters.csv']),('enrichment',['paper1_task4_enrichment.py','--out','Paper1_Results/Task4','--clusters','Paper1_Results/Task2/task2_gene_clusters.csv']),('union',['scripts/00_all_4692_progression_genes.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),('matched',['scripts/powermatched_transitions.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),('score',['scripts/high_confidence_genes.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),('loso',['scripts/loso_validation.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),('final_score',['scripts/high_confidence_genes.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),('network',['scripts/kg_subgraph.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),('edges',['build_progression_edges.py','--knowledge','data/graph_okg','--out','data/graph_full'])]
status={'python':sys.version,'started':time.strftime('%Y-%m-%dT%H:%M:%S'),'runs':{}}
for name in ['baseline','labels_only','normalisation_only','combined']:
 run=D/name;logs=run/'logs';logs.mkdir(exist_ok=True);env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONUNBUFFERED='1',MPLCONFIGDIR=str(logs/'matplotlib'))
 if (run/'run_status.json').exists():raise RuntimeError('Refuse to overwrite a completed/partial run without explicit resume')
 status['runs'][name]=[];print('START RUN',name,flush=True)
 for step,args in steps:
  start=time.time();print(name,step,flush=True)
  with (logs/(step+'.log')).open('w') as f:p=subprocess.run([python]+args,cwd=run,env=env,stdout=f,stderr=subprocess.STDOUT)
  record={'step':step,'command':[python]+args,'exit_code':p.returncode,'seconds':round(time.time()-start,2)};status['runs'][name].append(record);(run/'run_status.json').write_text(json.dumps(status['runs'][name],indent=2));(D/'run_status.json').write_text(json.dumps(status,indent=2))
  if p.returncode:print((logs/(step+'.log')).read_text()[-3000:],flush=True);raise SystemExit(p.returncode)
  if name=='baseline' and step=='discovery':
   for axis in ['fibrosis','disease']:
    a=pd.read_csv(R/'data/progression_full'/f'progression_{axis}.csv').set_index('ensembl_id').sort_index();b=pd.read_csv(run/'data/progression_full'/f'progression_{axis}.csv').set_index('ensembl_id').sort_index();assert a.index.equals(b.index)
    for c in ['median_rho','q_value','combined_p','n_studies','n_agree']:assert np.allclose(a[c],b[c],atol=1e-12,rtol=1e-8,equal_nan=True),(axis,c)
   print('BASELINE DISCOVERY REPRODUCED',flush=True)
  if name=='baseline' and step=='final_score':
   a=pd.read_csv(R/'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv');b=pd.read_csv(run/'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv');assert set(a.Ensembl_ID)==set(b.Ensembl_ID);assert set(pd.read_csv(R/'Paper1_HighConfidence/11_final_tier1_genes.csv').Ensembl_ID)==set(pd.read_csv(run/'Paper1_HighConfidence/11_final_tier1_genes.csv').Ensembl_ID);print('BASELINE TIER1/SHORTLIST REPRODUCED',flush=True)
 print('FINISH RUN',name,flush=True)
status['complete']=True;(D/'run_status.json').write_text(json.dumps(status,indent=2));print('ALL FOUR MAIN RUNS COMPLETE',flush=True)
