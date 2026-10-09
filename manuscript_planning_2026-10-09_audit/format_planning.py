from pathlib import Path
import re,json,zipfile,io
from PIL import Image,ImageDraw
D=Path(__file__).parent;R=D.parent
terms=['genes','gene','samples','sample','patients','patient','studies','study','rows','terms','records','labels','first','fibrosis','disease','rule','versus','core','with','old','increasing','decreasing','Tier','top','of','selected','relationships','edges','nodes','scores','directions','untested','discovery','shortlist','significant','summaries','run','refit','total','confidence','subset','stage','columns','variants']
for p in D.glob('*.md'):
 s=p.read_text()
 for t in sorted(terms,key=len,reverse=True):s=re.sub(r'(\d)('+re.escape(t)+r')',r'\1 \2',s)
 s=s.replace('DOI10.','DOI 10.').replace('PMID357','PMID 357').replace('PMID399','PMID 399').replace('Python3.','Python 3.').replace('Enterprise2026','Enterprise 2026').replace('MSigDB2024','MSigDB 2024')
 p.write_text(s)
# Save and inspect Word embedded media; does not modify the Word source.
media=[]
with zipfile.ZipFile(R/'Paper1_Manuscript/Paper1_draft_v1.docx') as z:
 for n in z.namelist():
  if n.startswith('word/media/'):
   b=z.read(n);p=D/'audit'/('draft_'+Path(n).name);p.write_bytes(b)
   try:
    im=Image.open(io.BytesIO(b));im.load();media.append((p,im.copy().convert('RGB')))
   except Exception:pass
for a in range(0,len(media),6):
 canvas=Image.new('RGB',(1600,1200),'white');dr=ImageDraw.Draw(canvas)
 for i,(p,im) in enumerate(media[a:a+6]):
  im.thumbnail((780,360));x=i%2*800;y=i//2*400;canvas.paste(im,(x+(800-im.width)//2,y+30));dr.text((x+8,y+8),p.name,fill='black')
 canvas.save(D/'audit'/f'word_media_contact_sheet_{a//6+1}.png')
print('Embedded Word figures',len(media))
# Identify exact-image duplicate groups, useful for coverage accounting.
f=json.loads((D/'audit/file_inventory.json').read_text());groups={}
for r in f:
 if r['type']=='.png':groups.setdefault(r['sha256'],[]).append(r['path'])
(D/'audit/image_duplicate_groups.json').write_text(json.dumps(list(groups.values()),indent=2));print('Unique existing PNG assets',len(groups),'from',sum(len(v) for v in groups.values()))
