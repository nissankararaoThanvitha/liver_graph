"""Run the existing analysis pipeline in an isolated workspace; stop on any error."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
PYTHON='/tmp/liver-biopsy-venv/bin/python';env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(ROOT/'logs/matplotlib'),PYTHONUNBUFFERED='1')
steps=[
 ('00_reproduce_discovery', ['find_progression_genes.py','--repeat-policy','first','--out','data/baseline_reproduced']),
 ('01_corrected_discovery',['find_progression_genes.py','--repeat-policy','same_stage_mean','--out','data/progression_full']),
 ('02_patient_exports',['export_for_mentor.py']),
 ('03_groups',['paper1_task1_groups.py','--out','Paper1_Results/Task1']),
 ('04_trajectories',['paper1_task2_trajectories.py','--out','Paper1_Results/Task2','5']),
 ('05_transitions',['paper1_task3_transitions.py','--out','Paper1_Results/Task3','--clusters','Paper1_Results/Task2/task2_gene_clusters.csv']),
 ('06_enrichment',['paper1_task4_enrichment.py','--out','Paper1_Results/Task4','--clusters','Paper1_Results/Task2/task2_gene_clusters.csv']),
 ('07_union',['scripts/00_all_4692_progression_genes.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),
 ('08_matched',['scripts/powermatched_transitions.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),
 ('09_score',['scripts/high_confidence_genes.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),
 ('10_loso',['scripts/loso_validation.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),
 ('11_final_score',['scripts/high_confidence_genes.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),
 ('12_mechanisms',['scripts/kg_subgraph.py','--out','Paper1_HighConfidence','--results','Paper1_Results']),
 ('13_progression_edges',['build_progression_edges.py','--knowledge','data/graph_okg','--out','data/graph_full']),
]
status={'runtime':sys.version,'stages':[],'scope':'patient-policy correction and LOSO eligible-universe BH; no live graph mutation'}
for name,args in steps:
 print('START',name,flush=True);start=time.time()
 with (ROOT/'logs'/f'{name}.log').open('w') as f:p=subprocess.run([PYTHON]+args,stdout=f,stderr=subprocess.STDOUT,env=env)
 status['stages'].append({'stage':name,'command':[PYTHON]+args,'seconds':round(time.time()-start,2),'exit_code':p.returncode});(ROOT/'run_status.json').write_text(json.dumps(status,indent=2));print('FINISH',name,'exit',p.returncode,'seconds',round(time.time()-start,1),flush=True)
 if p.returncode:
  print((ROOT/'logs'/f'{name}.log').read_text()[-3000:],flush=True);sys.exit(p.returncode)
 if name=='00_reproduce_discovery':
  import pandas as pd,numpy as np
  for axis in ['fibrosis','disease']:
   old=pd.read_csv(ROOT.parent/'data/progression_full'/f'progression_{axis}.csv').set_index('ensembl_id').sort_index();new=pd.read_csv(ROOT/'data/baseline_reproduced'/f'progression_{axis}.csv').set_index('ensembl_id').sort_index()
   if not old.index.equals(new.index):raise RuntimeError('Recovered baseline tested IDs differ')
   for c in ['median_rho','combined_p','q_value','n_studies','n_agree']:
    if not np.allclose(old[c],new[c],atol=1e-12,rtol=1e-8,equal_nan=True):raise RuntimeError(f'Baseline recovery mismatch: {axis}/{c}')
  print('BASELINE DISCOVERY REPRODUCED: all tested IDs/statistics agree',flush=True)
print('ALL STAGES COMPLETE',flush=True)
