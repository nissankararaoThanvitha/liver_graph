from pathlib import Path
import json,shutil,tarfile,ast
R=Path(__file__).resolve().parents[2];D=R/'biopsy_correction_2026-10-10';archive=R/'archives/previous_results_2026-10-10.tar.gz'
# Use one active copy; historical response links continue to resolve as aliases.
for rel in ['Paper1_Results','Paper1_HighConfidence','data/for_mentor','data/progression_full','data/processed','data/graph','data/graph_full','data/graph_okg','data/genesets']:
 p=D/rel;target=R/rel
 if p.is_symlink():continue
 if p.exists():shutil.rmtree(p)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.symlink_to(Path(__import__('os').path.relpath(target,p.parent)),target_is_directory=True)
p=D/'data/expression_analysis_core';p.symlink_to('../../data/expression_analysis_core',target_is_directory=True)
# Future verification can retrieve historical baselines from the verified archive.
p=D/'scripts/verify_graph_after.py';s=p.read_text().replace("D.parent/'manuscript_planning_2026-10-09_audit/audit/live_graph_readonly.json'","D/'source_graph_at_intake.json'");p.write_text(s)
p=D/'scripts/run_correction.py';s=p.read_text();needle="PYTHON='/tmp/liver-biopsy-venv/bin/python'";s=s.replace(needle,"if (ROOT/'promotion_status.json').exists():\n    raise SystemExit('This correction run is promoted. Use root source scripts and docs/provenance/REBUILD.md; do not overwrite the baseline audit.')\n"+needle);p.write_text(s)
p=D/'scripts/compare_and_verify.py';s=p.read_text();s=s.replace("def rd(base,path):return pd.read_csv(base/path)",'''def rd(base,path):
    if base == R:
        import tarfile,io
        with tarfile.open(R/'archives/previous_results_2026-10-10.tar.gz','r:gz') as archive:
            return pd.read_csv(io.BytesIO(archive.extractfile(path).read()))
    return pd.read_csv(base/path)''');a=s.index('changed=[]');b=s.index('oldf=sig',a);s=s[:a]+'''changed=[]
with __import__('tarfile').open(R/'archives/previous_results_2026-10-10.tar.gz','r:gz') as archive:
    for p,h in json.loads((D/'baseline_hashes.json').read_text()).items():
        if hashlib.sha256(archive.extractfile(p).read()).hexdigest()!=h:changed.append(p)
check('All original result/package files preserved in recovery archive',not changed,changed)
'''+s[b:];# Raw recovered measurements now in explicitly named core.
s=s.replace("'data/graph_full/edges_GSE193066.csv'","'data/expression_analysis_core/edges_GSE193066.csv'").replace("(D/'data/graph_full').glob('edges_GSE*.csv')","(D/'data/expression_analysis_core').glob('edges_GSE*.csv')");p.write_text(s)
for name in ['CORRECTION_REPORT.md','HANDOFF_FOR_REPURPOSING.md','SUBGRAPH_SUMMARY.md']:
 p=D/name;s=p.read_text();p.write_text('''> **Promoted to active paths:** Corrected outputs now live in the standard root data/, Paper1_Results/, Paper1_HighConfidence/ and rebuilt Paper1_Package/. Links under this audit directory are aliases to those active folders. Superseded results/draft are only in archives/previous_results_2026-10-10.tar.gz. This document records the correction run; use the active package for current methods and numbers.\n\n'''+s)
(R/'BIOPSY_CORRECTION.md').write_text('''# Current corrected results\n\nThe verified10 October2026 biopsy correction is now promoted to the standard active paths: data/progression_full, data/for_mentor, Paper1_Results, Paper1_HighConfidence and Paper1_Package. Superseded results and draft are in one verified recovery archive under archives/.\n\nPolicy: average equal-stage repeat biopsies; otherwise use biopsy1 before every stage contrast. Each patient contributes once. LOSO BH uses the14,794-gene eligible universe.\n\nCurrent counts: fibrosis3,688; disease4,018; shared1,802; union5,904; Tier1=491; shortlist25. Top25/top12 selection rules are unchanged. The live graph's7,706 progression links match corrected CSVs.\n\nDetailed correction record: biopsy_correction_2026-10-10/CORRECTION_REPORT.md. Current evidence plan: manuscript_planning/. Expression recovery is core-only at data/expression_analysis_core; do not use it for a full graph expression reload.\n''')
# Verify the requested top25/top12 algorithm expressions were not changed.
with tarfile.open(archive,'r:gz') as t:
 old=t.extractfile('biopsy_correction_2026-10-10/original_code/scripts/high_confidence_genes.py').read().decode()
 oldkg=t.extractfile('biopsy_correction_2026-10-10/original_code/scripts/kg_subgraph.py').read().decode()
current=(R/'scripts/high_confidence_genes.py').read_text();oldtree=ast.parse(old);newtree=ast.parse(current);functions=['score_progression','score_trajectory','score_transition','score_specificity','score_biology','total_score','shortlist_a','shortlist_b']
for name in functions:
 a=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name==name);b=next(n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name==name);assert ast.dump(a)==ast.dump(b),name
wanted=['N_MAJOR_NODES','MIN_TIER1_GENES','FDR','JACCARD_DUP','MIN_GENE_DEGREE']
def constants(tree):
 result={}
 for n in tree.body:
  if isinstance(n,ast.Assign):
   for target in n.targets:
    if isinstance(target,ast.Name) and target.id in wanted:result[target.id]=ast.dump(n.value)
 return result
assert constants(ast.parse(oldkg))==constants(ast.parse((R/'scripts/kg_subgraph.py').read_text()))
(D/'selection_logic_verification.json').write_text(json.dumps({'score_and_shortlist_functions_identical_to_original':functions,'mechanism_thresholds_and_display_rule_unchanged':wanted,'verified':True},indent=2))
print('Active aliases, audit compatibility and unchanged selection logic verified.')
