from pathlib import Path
import urllib.request,json,hashlib
D=Path(__file__).parent
sources=[('GSE193066_NAFLD.HUn164.gct.gz','https://ftp.ncbi.nlm.nih.gov/geo/series/GSE193nnn/GSE193066/suppl/GSE193066_NAFLD.HUn164.gct.gz'),('GSE193066_series_matrix.txt.gz','https://ftp.ncbi.nlm.nih.gov/geo/series/GSE193nnn/GSE193066/matrix/GSE193066_series_matrix.txt.gz')]
records=[]
for name,url in sources:
 try:
  with urllib.request.urlopen(url,timeout=45) as r:data=r.read()
  (D/name).write_bytes(data);records.append({'file':name,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});print(name,len(data),flush=True)
 except Exception as e:records.append({'file':name,'url':url,'error':str(e)});print(type(e).__name__,str(e),flush=True)
(D/'source_manifest.json').write_text(json.dumps(records,indent=2))
