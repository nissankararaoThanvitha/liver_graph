from pathlib import Path
import urllib.request,json,hashlib,concurrent.futures
D=Path(__file__).parent;study=json.loads((D/'BioStudies_original_paper.json').read_text());files=study['section']['files']
def fetch(r):
 name=r['path'];url='https://www.ebi.ac.uk/biostudies/files/S-EPMC6715650/'+name
 try:
  with urllib.request.urlopen(url,timeout=35) as response:b=response.read()
  if name.endswith('.pdf') and not b.startswith(b'%PDF'):raise ValueError('Not PDF')
  if name.endswith('.xlsx') and not b.startswith(b'PK'):raise ValueError('Not XLSX')
  if len(b)!=r['size']:raise ValueError('Size differs from BioStudies record')
  (D/name).write_bytes(b);return {'file':name,'url':url,'bytes':len(b),'size_matches_record':True,'sha256':hashlib.sha256(b).hexdigest()}
 except Exception as e:return {'file':name,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 records=[]
 for r in pool.map(fetch,files):records.append(r);print(json.dumps(r),flush=True)
(D/'original_supplements_manifest.json').write_text(json.dumps(records,indent=2))
