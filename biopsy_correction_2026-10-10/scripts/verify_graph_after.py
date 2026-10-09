import base64,getpass,json,urllib.request
from pathlib import Path
import pandas as pd
D=Path(__file__).resolve().parents[1];password=getpass.getpass('Neo4j password: ')
headers={'Authorization':'Basic '+base64.b64encode(('neo4j:'+password).encode()).decode(),'Content-Type':'application/json','Accept':'application/json'}
def query(s,p=None):
 req=urllib.request.Request('http://127.0.0.1:7474/db/neo4j/query/v2',data=json.dumps({'statement':s,'parameters':p or {}}).encode(),headers=headers,method='POST')
 with urllib.request.urlopen(req,timeout=120) as r:v=json.loads(r.read())
 if v.get('errors'):raise RuntimeError(v['errors'])
 return v['data']['values']
counts={}
for rel in ['EXPRESSES','IN_DATASET','ASSOCIATED_WITH','INTERACTS_WITH','INVOLVED_IN','IN_PATHWAY','ACTS_ON','TREATS','CONTRAINDICATED_IN','OFF_LABEL_FOR','HAS_PHENOTYPE','PARENT_OF','TRACKS_FIBROSIS','TRACKS_INFLAMMATION']:
 counts[rel]=query(f'MATCH ()-[r:{rel}]->() RETURN count(r)')[0][0]
old=json.loads((D/'source_graph_at_intake.json').read_text());expected={}
for q in old['queries']:
 s=q['statement']
 if s.startswith('MATCH ()-'):expected[s.split('r:')[1].split(']')[0]]=q['result']['data']['values'][0][0]
assert all(counts[k]==v for k,v in expected.items() if not k.startswith('TRACKS_'))
rank=pd.read_excel(D/'Paper1_HighConfidence/12_KG_supplementary.xlsx',sheet_name='3_all_mechanisms_ranked');ids=list(rank[rank.selected_for_figure].Mechanism_ID)
member=dict(query('MATCH (g:Gene)-[:IN_PATHWAY|INVOLVED_IN]->(m) WHERE m.node_id IN $ids RETURN m.node_id, collect(DISTINCT g.ensembl_id)',{'ids':ids}));edges=pd.concat([pd.read_csv(D/'data/graph_okg/edges_pathway_gene.csv'),pd.read_csv(D/'data/graph_okg/edges_biological_process_gene.csv')]);checks=[]
for mid in ids:
 a=set(edges[edges.to_id==mid].from_id);b=set(member[mid]);assert a==b;checks.append({'mechanism_id':mid,'members':len(a),'exact_match':True})
(D/'final_graph_readonly_verification.json').write_text(json.dumps({'counts':counts,'total_relationships':sum(counts.values()),'other_relationship_counts_preserved':True,'corrected_mechanism_memberships':checks},indent=2));print('Final graph verified:',sum(counts.values()),'relationships; all 12 corrected mechanism memberships match; other relationship counts unchanged.')
