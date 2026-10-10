from pathlib import Path
import urllib.request,json,hashlib,concurrent.futures
D=Path(__file__).parent
sources=[('oa_manifest.xml','https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC6715650'),('original_supplement.pdf','https://pmc.ncbi.nlm.nih.gov/articles/PMC6715650/bin/41598_2019_48746_MOESM1_ESM.pdf'),('publisher_supplement.pdf','https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs41598-019-48746-5/MediaObjects/41598_2019_48746_MOESM1_ESM.pdf'),('secondary_repository_tree.json','https://api.github.com/repos/saezlab/NRF2-activity-in-CLD/git/trees/master?recursive=1')]
def fetch(item):
 name,url=item
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'ResearchMetadataAudit/1.0'})
  with urllib.request.urlopen(req,timeout=25) as r:data=r.read()
  if name.endswith('.pdf') and not data.startswith(b'%PDF'):raise ValueError('Response is not PDF')
  (D/name).write_bytes(data);return {'file':name,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 except Exception as e:return {'file':name,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
 records=[]
 for r in executor.map(fetch,sources):records.append(r);print(json.dumps(r),flush=True)
(D/'retrieval_manifest.json').write_text(json.dumps(records,indent=2))
