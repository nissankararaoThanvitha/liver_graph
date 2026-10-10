"""Package final writing evidence without bulk inputs, credentials or history."""
from pathlib import Path
import csv, hashlib, io, json, zipfile

R = Path(__file__).resolve().parents[1]
out = R / 'handover_exports'
out.mkdir(exist_ok=True)
archive = out / 'manuscript_handover_2026-10-10.zip'
roots = ['Paper1_Package','Paper1_Manuscript','manuscript_planning','docs',
         'final_combined_2026-10-10','drug_shortlist_audit_2026-10-10',
         'label_audit_GSE130970_2026-10-10','label_source_search_2026-10-10',
         'unit_audit_GSE193066_2026-10-10']
files = {}
for root in roots:
    for p in sorted((R/root).rglob('*')):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(R)
        if any(part in ['graph_rollback','__pycache__','matplotlib'] for part in rel.parts):
            continue
        if root != 'Paper1_Package' and p.suffix.lower() not in {'.md','.txt','.csv','.json','.pdf','.xlsx'}:
            continue
        files[str(rel)] = p
for skill in ['bio-paper-writing','bioinfo-evidence-orchestrator']:
    base = Path('/home/nikitha07/.agents/skills')/skill
    for p in base.rglob('*.md'):
        files['writing_skills/'+skill+'/'+str(p.relative_to(base))] = p
manifest = [{'path': name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for name,p in files.items()]
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for name,p in files.items():
        z.write(p,name)
    z.writestr('START_HERE.md',(R/'Paper1_Manuscript/START_HERE_HANDOVER.md').read_text())
    z.writestr('FILE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for row in manifest:
        assert hashlib.sha256(z.read(row['path'])).hexdigest() == row['sha256'],row['path']
report = {'archive':archive.name,'files_verified':len(manifest),'archive_bytes':archive.stat().st_size,
          'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'verified':True,
          'purpose':'Portable manuscript-writing evidence; not a full raw-data or graph backup'}
(out/'handover_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
