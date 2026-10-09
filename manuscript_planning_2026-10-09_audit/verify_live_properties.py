import urllib.request,json,base64,getpass
from pathlib import Path
password=getpass.getpass('Neo4j password: ');hdr={'Authorization':'Basic '+base64.b64encode(('neo4j:'+password).encode()).decode(),'Content-Type':'application/json','Accept':'application/json'};res=[]
qs=['CALL db.labels() YIELD label RETURN label','CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType','SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties RETURN name, type, labelsOrTypes, properties','MATCH (s:Sample) RETURN keys(s) AS keys LIMIT 1','MATCH (g:Gene)-[r:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->(d:Disease) RETURN g.ensembl_id AS ensembl_id, type(r) AS rel, d.node_id AS disease_id, properties(r) AS properties']
for q in qs:
 req=urllib.request.Request('http://127.0.0.1:7474/db/neo4j/query/v2',data=json.dumps({'statement':q}).encode(),headers=hdr,method='POST')
 with urllib.request.urlopen(req,timeout=40) as r:val=json.loads(r.read())
 res.append({'statement':q,'result':val});print(q,'returned',len(val.get('data',{}).get('values',[])),'rows')
(Path(__file__).parent/'audit/live_graph_properties.json').write_text(json.dumps(res,indent=2));print('Saved without credentials.')
