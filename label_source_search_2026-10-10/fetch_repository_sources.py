from pathlib import Path
import urllib.request,json,hashlib,concurrent.futures,zipfile,io
D=Path(__file__).parent
sources=[('oa_manifest_alt.xml','https://www.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC6715650'),('NRF2_repository.zip','https://codeload.github.com/saezlab/NRF2-activity-in-CLD/zip/refs/heads/master'),('BioStudies_S-BSST1361.json','https://www.ebi.ac.uk/biostudies/api/v1/studies/S-BSST1361'),('BioStudies_original_paper.json','https://www.ebi.ac.uk/biostudies/api/v1/studies/S-EPMC6715650')]
def fetch(item):
 name,url=item
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ResearchMetadataAudit/1.0'}),timeout=25) as r:b=r.read()
  (D/name).write_bytes(b);return {'file':name,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 except Exception as e:return {'file':name,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
 records=list(executor.map(fetch,sources))
for r in records:print(json.dumps(r),flush=True)
(D/'repository_retrieval_manifest.json').write_text(json.dumps(records,indent=2))
p=D/'NRF2_repository.zip'
if p.exists():
 with zipfile.ZipFile(p) as z:
  names=z.namelist();(D/'NRF2_repository_inventory.json').write_text(json.dumps(names,indent=2));print('Candidate repository files',[n for n in names if n.lower().endswith(('.r','.rmd','.md','.csv','.tsv','.xlsx'))])
  for name in names:
   if name.lower().endswith(('.r','.rmd','.md','.csv','.tsv','.xlsx')) and z.getinfo(name).file_size<5_000_000:
    dest=D/'NRF2_repository'/Path(*Path(name).parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
