from pathlib import Path
import json,hashlib,csv,re
import pandas as pd
R=Path(__file__).parent.parent;D=Path(__file__).parent;A=D/'audit';files=json.loads((A/'file_inventory.json').read_text());properties=json.loads((A/'live_graph_properties.json').read_text());values=properties[-1]['result']['data']['values'];print('live relationship property example',values[0])
cur=pd.read_csv(R/'Paper1_Package/04_DATA/graph_nodes/edges_my_progression.csv');old=pd.read_csv(R/'Paper1_Package/04_DATA/knowledge_layer/edges_my_progression.csv');live={(v[0],v[1],v[2]):v[3] for v in values};want={(r.ensembl_id,r.rel,r.disease_id):r for r in cur.itertuples()};mismatches=[]
for k,r in want.items():
 p=live.get(k,{})
 for field in ['rho','q','n_studies','direction']:
  expected=getattr(r,field); actual=p.get(field)
  if isinstance(expected,(float,int)):
   ok=actual is not None and abs(float(expected)-float(actual))<=max(1e-12,abs(float(expected))*1e-8)
  else:ok=str(expected)==str(actual)
  if not ok:mismatches.append({'key':k,'field':field,'csv':expected,'live':actual})
comparison={'csv_keys':len(want),'live_keys':len(live),'csv_only':sorted(set(want)-set(live)),'live_only':sorted(set(live)-set(want)),'property_mismatches':mismatches,'tolerance':'max(1e-12, 1e-8 relative) for numeric properties','old_duplicate_relationship_counts':old.rel.value_counts().to_dict()};(A/'live_progression_comparison.json').write_text(json.dumps(comparison,indent=2,default=str));print('progression comparison',len(comparison['csv_only']),len(comparison['live_only']),len(mismatches))
changed=[x['path'] for x in files if not (R/x['path']).is_file() or hashlib.sha256((R/x['path']).read_bytes()).hexdigest()!=x['sha256']];(A/'source_preservation_check.json').write_text(json.dumps({'checked_files':len(files),'changed_or_missing':changed},indent=2));print('Source preservation',len(files),changed)
p=D/'research_inventory.md';s=p.read_text();s+='\n| File in Paper1_Package | Inspection | Rows / image / sheets |\n|---|---|---|\n'
for r in files:
 if not r['path'].startswith('Paper1_Package/'):continue
 desc=str(r.get('rows',''))
 if r['type']=='.png':desc=f"{r['width']}×{r['height']}; {r.get('dpi')} dpi"
 if 'sheets'in r:desc='; '.join(r['sheets'])
 if 'lines'in r:desc=str(r['lines'])+' text lines'
 s+=f"| {r['path'].removeprefix('Paper1_Package/')} | {r['status']} | {desc} |\n"
s+='\n### Additional sources outside the package\n\n'
for r in files:
 if r['path'].startswith('Paper1_Package/'):continue
 s+=f"- {r['path']} — {r['status']}"+(f"; {r['rows']} rows" if 'rows'in r else '')+'\n'
s+='\n### Database progression identity audit\n\nAll 7,699 current progression endpoint/type identities match the live graph; numeric rho, q and n_studies and direction comparisons are recorded in audit/live_progression_comparison.json. Numeric agreement uses a tolerance of max(10^-12,10^-8 relative). Full expression and all curated relationship properties were not exhaustively compared.\n'
p.write_text(s)
# Lightweight evidence-pack handoff uses the four requested products; no prose drafting.
(D/'EVIDENCE_PACK.md').write_text('''# Evidence pack index\n\nPrepared 9 October 2026 using bioinfo-evidence-orchestrator and bio-paper-writing.\n\n1. Study questions, dataset inventory, statistical design and evidence strength: research_inventory.md.\n2. Workflow provenance and implemented versus historical choices: complete_workflow.md.\n3. Findings, figure/table inventory, manuscript placement and claim boundaries: results_evidence_map.md.\n4. Risks, missing inputs and author questions: missing_information.md.\n5. Read-only graph/schema/membership checks, file profiles and preservation checks: audit/.\n\nThe pack supports planning only. Stored LOSO findings need policy/testing-family review and rerun. No classifier, independent clinical validation or successful drug model is established. The password supplied for local authentication was not saved.\n''')
print('Output word counts',{p.name:len(p.read_text().split()) for p in D.glob('*.md')})
