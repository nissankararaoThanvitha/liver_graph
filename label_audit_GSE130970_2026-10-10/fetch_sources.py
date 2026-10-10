from pathlib import Path
import urllib.request,json,hashlib
D=Path(__file__).parent
sources=[('GSE130970_series_matrix.txt.gz','https://ftp.ncbi.nlm.nih.gov/geo/series/GSE130nnn/GSE130970/matrix/GSE130970_series_matrix.txt.gz'),('PMC6715650.xml','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6715650/fullTextXML')]
records=[]
for name,url in sources:
 try:
  with urllib.request.urlopen(url,timeout=45) as r:data=r.read()
  (D/name).write_bytes(data);records.append({'file':name,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});print(name,len(data),flush=True)
 except Exception as e:records.append({'file':name,'url':url,'error':str(e)});print(name,type(e).__name__,str(e),flush=True)
(D/'source_manifest.json').write_text(json.dumps(records,indent=2))
