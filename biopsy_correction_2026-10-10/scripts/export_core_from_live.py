"""Recover the all-eight-study analysis universe from Neo4j with read-only queries.
No credentials are saved. Each completed study is written atomically and hashed.
The recovery is an analysis subset, not a full graph export.
"""
import base64,csv,getpass,hashlib,json,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT.parent
password=getpass.getpass('Neo4j password: ')
headers={'Authorization':'Basic '+base64.b64encode(('neo4j:'+password).encode()).decode(),'Content-Type':'application/json','Accept':'application/json'}
def query(statement,parameters=None):
 request=urllib.request.Request('http://127.0.0.1:7474/db/neo4j/query/v2',data=json.dumps({'statement':statement,'parameters':parameters or {}}).encode(),headers=headers,method='POST')
 with urllib.request.urlopen(request,timeout=120) as response:r=json.loads(response.read())
 if r.get('errors'):raise RuntimeError(r['errors'])
 return r['data']['values']
clinical=list(csv.DictReader((SOURCE/'data/graph/nodes_sample_clinical.csv').open()))
nodefile=SOURCE/'Paper1_Package/04_DATA/graph_nodes/nodes_gene.csv'
core={r['ensembl_id'] for r in csv.DictReader(nodefile.open()) if r['n_datasets']=='8'}
livecore={r[0] for r in query('MATCH (g:Gene) WHERE g.n_datasets = 8 RETURN g.ensembl_id')}
if livecore!=core:raise RuntimeError('Live all-eight-study gene universe differs from CSV')
samples=query('MATCH (s:Sample) RETURN s.sample_id, properties(s)');(ROOT/'data/live_samples.json').write_text(json.dumps(samples,indent=2))
if {r[0] for r in samples}!={r['sample_id'] for r in clinical}:raise RuntimeError('Live sample IDs differ from clinical table')
record={'source':'http://127.0.0.1:7474/db/neo4j/query/v2','database':'neo4j','subset':'genes with n_datasets=8, all samples','genes':len(core),'studies':[],'read_only':True}
for ds in sorted({r['dataset_id'] for r in clinical}):
 ids=sorted(r['sample_id'] for r in clinical if r['dataset_id']==ds);out=ROOT/'data/graph_full'/f'edges_{ds}.csv';partial=out.with_suffix('.partial');n=0
 with partial.open('w',newline='') as f:
  writer=csv.writer(f);writer.writerow(['sample_id','ensembl_id','value_z'])
  for i,sid in enumerate(ids,1):
   values=query('MATCH (s:Sample {sample_id:$sample})-[r:EXPRESSES]->(g:Gene) WHERE g.n_datasets = 8 RETURN s.sample_id,g.ensembl_id,r.value_z',{'sample':sid})
   if len(values)!=len(core) or {r[1] for r in values}!=core or any(r[2] is None for r in values):raise RuntimeError(f'Incomplete or duplicated measurements: {sid}')
   writer.writerows(values);n+=len(values)
   if i%25==0:print(ds,i,'/',len(ids),'samples',flush=True)
 partial.rename(out);entry={'dataset_id':ds,'samples':len(ids),'rows':n,'path':str(out.relative_to(ROOT)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()};record['studies'].append(entry);(ROOT/'data/expression_recovery_manifest.json').write_text(json.dumps(record,indent=2));print('Completed',ds,n,'measurements',flush=True)
print('Recovery complete',sum(r['rows'] for r in record['studies']),flush=True)
