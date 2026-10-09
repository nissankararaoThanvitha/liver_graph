import json,urllib.request,base64,getpass
from pathlib import Path
OUT=Path(__file__).parent/'audit'
password=getpass.getpass('Neo4j password: ')
headers={'Authorization':'Basic '+base64.b64encode(('neo4j:'+password).encode()).decode(),'Content-Type':'application/json','Accept':'application/json'}
def query(s,parameters=None):
 request=urllib.request.Request('http://127.0.0.1:7474/db/neo4j/query/v2',data=json.dumps({'statement':s,'parameters':parameters or {}}).encode(),headers=headers,method='POST')
 with urllib.request.urlopen(request,timeout=40) as r: return json.loads(r.read())
res={'endpoint':'http://127.0.0.1:7474','database':'neo4j','username':'neo4j','instance_from_user_screenshot':'liver_kg','queries':[]}
qs=['CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition','SHOW DATABASES YIELD name, currentStatus RETURN name, currentStatus']
qs += [f'MATCH (n:{l}) RETURN count(n) AS count' for l in ['Gene','Sample','Dataset','Disease','Drug','Pathway','BioProcess','Phenotype']]
qs += [f'MATCH ()-[r:{l}]->() RETURN count(r) AS count' for l in ['EXPRESSES','IN_DATASET','ASSOCIATED_WITH','INTERACTS_WITH','INVOLVED_IN','IN_PATHWAY','ACTS_ON','TREATS','CONTRAINDICATED_IN','OFF_LABEL_FOR','HAS_PHENOTYPE','PARENT_OF','TRACKS_FIBROSIS','TRACKS_INFLAMMATION']]
for s in qs:
 try:r=query(s);res['queries'].append({'statement':s,'result':r}); print(s, json.dumps(r.get('data',r)))
 except Exception as e:res['queries'].append({'statement':s,'error':str(e)});print('ERROR',type(e).__name__)
(OUT/'live_graph_readonly.json').write_text(json.dumps(res,indent=2))
from openpyxl import load_workbook
root=OUT.parent.parent
wb=load_workbook(root/'Paper1_Package/02_TABLES/supplementary/TableS19_knowledge_graph_connections.xlsx',read_only=True,data_only=True)
rows=list(wb['3_all_mechanisms_ranked'].values);h=rows[0];selected=[dict(zip(h,row)) for row in rows[1:] if row[h.index('selected_for_figure')]];wb.close()
s='MATCH (g:Gene)-[:IN_PATHWAY|INVOLVED_IN]->(m) WHERE m.node_id IN $ids RETURN m.node_id AS id, collect(DISTINCT g.ensembl_id) AS genes'
try:res['membership']=query(s,{'ids':[x['Mechanism_ID'] for x in selected]})
except Exception as e:res['membership_error']=str(e)
res['selected_mechanisms']=selected
(OUT/'live_graph_readonly.json').write_text(json.dumps(res,indent=2))
print('Saved read-only verification; credentials omitted.')
