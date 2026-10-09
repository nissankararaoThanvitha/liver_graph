from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[2];OUT=R/'biopsy_correction_2026-10-10';BACK=OUT/'original_code';BACK.mkdir(exist_ok=True)
names=['find_progression_genes.py','export_for_mentor.py','paper1_task1_groups.py','paper1_task2_trajectories.py','paper1_task3_transitions.py','paper1_task4_enrichment.py','scripts/loso_validation.py','scripts/powermatched_transitions.py','scripts/high_confidence_genes.py','scripts/kg_subgraph.py','scripts/00_all_4692_progression_genes.py','build_progression_edges.py']
for n in names:
 src=R/n;dst=BACK/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def edit(name,old,new):
 p=R/name;s=p.read_text();assert old in s,(name,old[:80]);p.write_text(s.replace(old,new,1))
for n in ['find_progression_genes.py','export_for_mentor.py','paper1_task2_trajectories.py','paper1_task3_transitions.py']:
 edit(n,'import pandas as pd','import pandas as pd\nfrom biopsy_policy import select_biopsies, patient_expression')
for n in ['scripts/loso_validation.py','scripts/powermatched_transitions.py']:
 edit(n,'ROOT = HERE.parent','ROOT = HERE.parent\nimport sys\nsys.path.insert(0, str(ROOT))\nfrom biopsy_policy import select_biopsies')
edit('find_progression_genes.py','REPEAT_POLICY = "first"','REPEAT_POLICY = "same_stage_mean"')
edit('find_progression_genes.py','if REPEAT_POLICY == "first":','if REPEAT_POLICY == "same_stage_mean":\n            lab = select_biopsies(lab, axis)\n\n        if REPEAT_POLICY == "first":')
edit('find_progression_genes.py','choices=["first", "average"]','choices=["same_stage_mean", "first", "average"]')
edit('find_progression_genes.py','"biopsy only (default); \'average\' is the "','"biopsy only; \'same_stage_mean\' (default) averages same-stage repeats "\n                         "and otherwise keeps biopsy 1; \'average\' is the "')
edit('export_for_mentor.py','"disease_group"]],','"disease_group", "biopsy_number"]],')
edit('export_for_mentor.py','e = load_expression(genes).merge(samples, on="sample_id")','e = patient_expression(load_expression(genes), samples)')
edit('export_for_mentor.py','"age_band", "fibrosis_stage", "disease_group"]]','"age_band", "fibrosis_stage", "disease_group", "biopsy_number"]]')
for n in ['paper1_task2_trajectories.py','paper1_task3_transitions.py','scripts/powermatched_transitions.py']:
 edit(n,'samples = pd.read_csv(SAMPLES)','samples = select_biopsies(pd.read_csv(SAMPLES))')
edit('scripts/loso_validation.py','keep = set(t1.ensembl_id)','report_genes = set(t1.ensembl_id)\ncore_nodes = pd.read_csv(GRAPH / "nodes_gene.csv")\nkeep = set(core_nodes.loc[core_nodes.n_datasets == 8, "ensembl_id"])')
edit('scripts/loso_validation.py','lab = lab[lab.fibrosis_stage.notna()]','lab = select_biopsies(lab)\nlab = lab[lab.fibrosis_stage.notna()]')
edit('scripts/loso_validation.py','runs.to_csv(HERE / "10_loso_runs.csv", index=False)','runs.to_csv(HERE / "10_loso_all_eligible_runs.csv", index=False)\nruns = runs[runs.ensembl_id.isin(report_genes)].copy()\nruns.to_csv(HERE / "10_loso_runs.csv", index=False)\nRHO.join(PV, lsuffix="_rho", rsuffix="_p").to_csv(HERE / "10_loso_per_study_all_eligible.csv")')
edit('paper1_task3_transitions.py','    # a patient on both sides keeps one stage, chosen at random\n    dup = m.patient_id.duplicated(keep=False)\n    drop = []\n    for pid, g in m[dup].groupby("patient_id"):\n        drop.append(rng.choice(g.index.to_numpy()))\n    return m.drop(index=drop).index.to_numpy()','    assert not m.patient_id.duplicated().any(), "Biopsy policy left duplicate patients"\n    return m.index.to_numpy()')
edit('scripts/powermatched_transitions.py','    dup = m.patient_id.duplicated(keep=False)\n    drop = [rng.choice(g.index.to_numpy())\n            for _, g in m[dup].groupby("patient_id")]\n    return m.drop(index=drop).index.to_numpy()','    assert not m.patient_id.duplicated().any(), "Biopsy policy left duplicate patients"\n    return m.index.to_numpy()')
# Stage an independent runnable project tree. Baseline outputs and package are untouched.
for n in names+['biopsy_policy.py']:
 dst=OUT/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,dst)
for n in ['data/processed','data/graph']:
 shutil.copytree(R/n,OUT/n,dirs_exist_ok=True)
shutil.copy2(R/'Paper1_Package/04_DATA/graph_nodes/nodes_gene.csv',OUT/'data/graph_full/nodes_gene.csv')
shutil.copytree(R/'Paper1_Package/04_DATA/knowledge_layer',OUT/'data/graph_okg',dirs_exist_ok=True)
# Record baseline result hashes for later preservation check.
files=[p for d in ['Paper1_Package','Paper1_Results','Paper1_HighConfidence','data/for_mentor','data/progression_full'] for p in (R/d).rglob('*') if p.is_file()]
(OUT/'baseline_hashes.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
print('Patched shared policy, staged isolated run, baseline protected.')
