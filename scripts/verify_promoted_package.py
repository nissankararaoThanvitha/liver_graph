"""Check current package hashes, authoritative memberships and promotion aliases."""
from pathlib import Path
import csv,json,hashlib,ast
import pandas as pd
R=Path(__file__).resolve().parent.parent;P=R/'Paper1_Package';D=R/'final_combined_2026-10-10';checks=[]
def check(label,ok,detail=None):
 checks.append({'check':label,'passed':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+label)
manifest=list(csv.DictReader((P/'00_START_HERE/06_FILE_MANIFEST.csv').open()));bad=[]
for row in manifest:
 p=P/row['path']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:bad.append(row['path'])
check('Every rebuilt package manifest hash matches',not bad,{'files':len(manifest),'mismatches':bad})
f=pd.read_csv(R/'data/progression_full/progression_fibrosis.csv');d=pd.read_csv(R/'data/progression_full/progression_disease.csv');fs=f[(f.q_value<.05)&(f.n_agree==f.n_studies)];ds=d[(d.q_value<.05)&(d.n_agree==d.n_studies)]
check('Corrected active counts',len(fs)==3845 and len(ds)==4199 and len(set(fs.ensembl_id)|set(ds.ensembl_id))==6222)
edgefiles=[R/'data/graph_full/edges_my_progression.csv',R/'data/graph_okg/edges_my_progression.csv',P/'04_DATA/graph_nodes/edges_my_progression.csv',P/'04_DATA/knowledge_layer/edges_my_progression.csv'];edgelists=[pd.read_csv(p) for p in edgefiles];a=edgelists[0].sort_values(['rel','ensembl_id']).reset_index(drop=True);check('All four current progression-edge CSVs agree',all(a.equals(x.sort_values(['rel','ensembl_id']).reset_index(drop=True)) for x in edgelists[1:]))
live=json.loads((D/'live_graph_after_progression_update.json').read_text());check('CSV endpoints/types equal saved verified live graph',set(zip(a.ensembl_id,a.rel,a.disease_id))=={tuple(r[:3]) for r in live})
table=pd.read_csv(P/'02_TABLES/main/Table6_prioritised_genes.csv');current=pd.read_csv(R/'Paper1_HighConfidence/shortlist_with_membership_confidence.csv');check('Package shortlist includes current confidence',len(table)==23 and set(table.Ensembl_ID)==set(current.Ensembl_ID) and 'membership_confidence' in table)
for name,path in [('fibrosis','progression_fibrosis.csv'),('disease','progression_disease.csv')]:
 check('Package '+name+' progression matches active CSV',pd.read_csv(P/'04_DATA/progression_genes'/path).equals(pd.read_csv(R/'data/progression_full'/path)))
cluster=pd.read_csv(P/'02_TABLES/supplementary/TableS2_gene_cluster_assignments.csv');check('Current clustering covers exactly corrected fibrosis set',set(cluster.ensembl_id)==set(fs.ensembl_id) and len(cluster)==3845)
workbook=pd.read_excel(P/'02_TABLES/supplementary/TableS19_knowledge_graph_connections.xlsx',sheet_name=None);check('Current workbook/network counts', '2_tier1_447_KG' in workbook and len(workbook['4_figure_edges'])==154 and workbook['4_figure_edges'].Ensembl_ID.nunique()==42)
check('Old result naming removed from active data/package',not list(P.rglob('00_all_4692_progression_genes.csv')) and not list(P.rglob('progression_both.csv')))
check('Shared biopsy helper is shipped', (P/'05_CODE/biopsy_policy.py').is_file())
check('Older draft and HTML absent from active folders',not (R/'Paper1_Manuscript/Paper1_draft_v1.docx').exists() and not (R/'reports_progression_summary.html').exists())
check('Recovery archive verification retained',json.loads((R/'archives/pre_combined_final_2026-10-10_manifest.json').read_text())['verified'])
check('All result/data aliases point to canonical active paths',all((R/'biopsy_correction_2026-10-10'/rel).resolve()==(R/rel).resolve() for rel in ['Paper1_Results','Paper1_HighConfidence','data/progression_full','data/for_mentor','data/graph_full','data/graph_okg']))
check('Final graph properties verified',json.loads((D/'graph_verification.json').read_text())['verified'])
check('Alternative sensitivity-run folders removed',not (R/'sensitivity_2026-10-10').exists())
check('Current evidence planning contains all four deliverables',all((R/'manuscript_planning'/n).exists() for n in ['research_inventory.md','complete_workflow.md','results_evidence_map.md','missing_information.md']))
check('Top25/top12 selection logic verification retained',json.loads((R/'biopsy_correction_2026-10-10/selection_logic_verification.json').read_text())['verified'])
(D/'promotion_verification.json').write_text(json.dumps(checks,indent=2));status=json.loads((D/'promotion_status.json').read_text());status['package_rebuild_pending']=False;status['active_package_manifest_files']=len(manifest);status['promotion_verified']=all(r['passed'] for r in checks);(D/'promotion_status.json').write_text(json.dumps(status,indent=2));assert status['promotion_verified']
# Refresh current output hashes after adding Figure1 and explicit empty panels.
current_manifest={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for root in ['Paper1_Results','Paper1_HighConfidence','data/progression_full','data/for_mentor'] for p in (R/root).rglob('*') if p.is_file()};(D/'corrected_results_manifest.json').write_text(json.dumps(current_manifest,indent=2));print('All promotion checks passed.')
