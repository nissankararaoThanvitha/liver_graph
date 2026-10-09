"""Atomically replace only the two patient-derived progression relationships.
Verify source snapshot and endpoints first; retain a complete rollback snapshot.
No raw expression, sample, gene, knowledge node or curated edge is altered.
"""
from pathlib import Path
import base64,csv,getpass,json,urllib.request
D=Path(__file__).resolve().parents[1];R=D.parent
checks=json.loads((D/'verification_results.json').read_text())
if not all(c['passed'] for c in checks):raise RuntimeError('Corrected evidence has not passed verification')
password=getpass.getpass('Neo4j password: ')
headers={'Authorization':'Basic '+base64.b64encode(('neo4j:'+password).encode()).decode(),'Content-Type':'application/json','Accept':'application/json'}
def query(statement,parameters=None):
 req=urllib.request.Request('http://127.0.0.1:7474/db/neo4j/query/v2',data=json.dumps({'statement':statement,'parameters':parameters or {}}).encode(),headers=headers,method='POST')
 with urllib.request.urlopen(req,timeout=120) as r:val=json.loads(r.read())
 if val.get('errors'):raise RuntimeError(val['errors'])
 return val
q='MATCH (g:Gene)-[r:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->(d:Disease) RETURN g.ensembl_id, type(r), d.node_id, properties(r)'
before=query(q);backup=D/'live_graph_before_progression_update.json';backup.write_text(json.dumps(before,indent=2));current=before['data']['values']
old=list(csv.DictReader((R/'Paper1_Package/04_DATA/graph_nodes/edges_my_progression.csv').open()));expected={(r['ensembl_id'],r['rel'],r['disease_id']) for r in old}
if {(v[0],v[1],v[2]) for v in current}!=expected:raise RuntimeError('Live graph changed since baseline; update aborted before mutation')
rows=list(csv.DictReader((D/'data/graph_full/edges_my_progression.csv').open()));ids=sorted({r['ensembl_id'] for r in rows});endpoint=query('MATCH (g:Gene) WHERE g.ensembl_id IN $ids RETURN collect(g.ensembl_id)',{'ids':ids})['data']['values'][0][0]
if set(endpoint)!=set(ids):raise RuntimeError('Missing gene endpoints; update aborted')
ends=query('MATCH (d:Disease) WHERE d.node_id IN $ids RETURN collect(d.node_id)',{'ids':['EFO_0003095','EFO_1001249']})['data']['values'][0][0]
if set(ends)!={'EFO_0003095','EFO_1001249'}:raise RuntimeError('Missing disease endpoints; update aborted')
params={rel:[] for rel in ['fib','dis']}
for r in rows:
 params['fib' if r['rel']=='TRACKS_FIBROSIS' else 'dis'].append({'gene':r['ensembl_id'],'disease':r['disease_id'],'props':{'rho':float(r['rho']),'q':float(r['q']),'n_studies':int(r['n_studies']),'direction':r['direction'],'source':'our_patients','biopsy_policy':'same_stage_mean_otherwise_first','analysis_run':'biopsy_correction_2026-10-10'}})
statement='''CALL { MATCH ()-[r:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->() DELETE r RETURN count(r) AS removed }
CALL { UNWIND $fib AS row MATCH (g:Gene {ensembl_id:row.gene}) MATCH (d:Disease {node_id:row.disease}) CREATE (g)-[r:TRACKS_FIBROSIS]->(d) SET r = row.props RETURN count(r) AS fibrosis_written }
CALL { UNWIND $dis AS row MATCH (g:Gene {ensembl_id:row.gene}) MATCH (d:Disease {node_id:row.disease}) CREATE (g)-[r:TRACKS_INFLAMMATION]->(d) SET r = row.props RETURN count(r) AS disease_written }
RETURN removed,fibrosis_written,disease_written'''
result=query(statement,params);after=query(q);actual={(v[0],v[1],v[2]):v[3] for v in after['data']['values']};wanted={(r['gene'], 'TRACKS_FIBROSIS' if rel=='fib' else 'TRACKS_INFLAMMATION',r['disease']):r['props'] for rel,arr in params.items() for r in arr}
if actual!=wanted:
 rollback={'fib':[],'dis':[]}
 for gene,rel,dis,p in current:rollback['fib' if rel=='TRACKS_FIBROSIS' else 'dis'].append({'gene':gene,'disease':dis,'props':p})
 query(statement,rollback);raise RuntimeError('Post-update check failed; original relationships restored')
(D/'live_graph_after_progression_update.json').write_text(json.dumps(after,indent=2));(D/'graph_update_verification.json').write_text(json.dumps({'result':result,'verified_relationships':len(actual),'identity_and_all_properties_match':True,'backup':str(backup),'only_mutated_types':['TRACKS_FIBROSIS','TRACKS_INFLAMMATION']},indent=2));print('Progression update verified:',len(params['fib']),'fibrosis links;',len(params['dis']),'disease links. Complete rollback snapshot saved.')
