from pathlib import Path
import json,re,csv
from pypdf import PdfReader
from openpyxl import load_workbook
D=Path(__file__).parent
reader=PdfReader(D/'41598_2019_48746_MOESM1_ESM.pdf');pages=[]
for i,p in enumerate(reader.pages,1):
 t=p.extract_text() or '';pages.append({'page':i,'text':t});print('PDF page',i, 'chars',len(t));
 if re.search(r'Table\s+S?1|Table\s+1|diagnos|clinical|demograph',t,re.I):print(t[:6000])
(D/'supplement_pdf_text.json').write_text(json.dumps(pages,indent=2))
profiles=[]
for file in sorted(D.glob('*.xlsx')):
 wb=load_workbook(file,read_only=True,data_only=True);record={'file':file.name,'sheets':[]}
 for ws in wb:
  ws.reset_dimensions()
  head=[];hits=[];n=0;max_columns=0
  for row in ws.values:
   n+=1;max_columns=max(max_columns,len(row))
   if n<=7:head.append(row)
   for cell in row:
    if isinstance(cell,str) and re.search(r'GSM3758|440393|440420|440421|440528|440529|diagnos|steatohepatitis|borderline|patient|control',cell,re.I):
     if len(hits)<20:hits.append({'row':n,'text':cell[:200]})
  record['sheets'].append({'name':ws.title,'rows_including_header':n,'columns':max_columns,'first_rows':head,'potential_label_hits':hits})
 profiles.append(record);print('WORKBOOK',file.name,json.dumps(record['sheets'],default=str)[:4000]);wb.close()
(D/'supplement_workbook_profiles.json').write_text(json.dumps(profiles,indent=2,default=str))
