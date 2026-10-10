"""Promote the researcher-selected combined run; retain a verified recovery copy."""
from pathlib import Path
import hashlib, json, shutil, tarfile
import pandas as pd

R = Path(__file__).resolve().parents[1]
S = R / 'sensitivity_2026-10-10'
C = S / 'combined'
O = R / 'final_combined_2026-10-10'
O.mkdir(exist_ok=True)
if (O / 'promotion_status.json').exists():
    raise SystemExit('Already promoted; refuse to repeat')
assert all(c['passed'] for c in json.loads((S / 'verification_results.json').read_text()))
assert len(pd.read_csv(C / 'Paper1_HighConfidence/11_final_tier1_genes.csv')) == 447
assert len(pd.read_csv(C / 'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv')) == 23
archive = R / 'archives/pre_combined_final_2026-10-10.tar.gz'
sources = ['Paper1_Results', 'Paper1_HighConfidence', 'Paper1_Package', 'data/progression_full',
           'data/for_mentor', 'data/graph/nodes_sample_clinical.csv',
           'data/expression_analysis_core/edges_GSE193066.csv', 'sensitivity_2026-10-10',
           'README.md', 'CLAUDE.md', 'BIOPSY_CORRECTION.md', 'docs', 'manuscript_planning']
if archive.exists():
    raise SystemExit('Recovery archive already exists')
manifest = {}
with tarfile.open(archive, 'w:gz', compresslevel=1) as t:
    def record(info):
        if info.isfile():
            manifest[info.name] = hashlib.sha256((R / info.name).read_bytes()).hexdigest()
        return info
    for rel in sources:
        t.add(R / rel, arcname=rel, filter=record)
with tarfile.open(archive, 'r:gz') as t:
    for name, digest in manifest.items():
        assert hashlib.sha256(t.extractfile(name).read()).hexdigest() == digest, name
(R / 'archives/pre_combined_final_2026-10-10_manifest.json').write_text(json.dumps({'verified': True, 'files': manifest}, indent=2))
for name in ['PROTOCOL.md', 'SENSITIVITY_REPORT.md', 'comparison_summary.csv',
             'shortlist_comparison.csv', 'network_comparison.csv', 'candidate_stability.csv',
             'membership_and_cluster_details.json', 'verification_results.json',
             'input_preparation.json', 'runtime_requirements.txt']:
    shutil.copy2(S / name, O / name)
shutil.copytree(C / 'logs', O / 'logs', ignore=shutil.ignore_patterns('matplotlib'), dirs_exist_ok=True)
shutil.copy2(C / 'run_status.json', O / 'analysis_run_status.json')
for rel in ['Paper1_Results', 'Paper1_HighConfidence', 'data/progression_full', 'data/for_mentor']:
    dest = R / rel
    shutil.rmtree(dest)
    shutil.copytree(C / rel, dest)
shutil.copy2(C / 'data/graph/nodes_sample_clinical.csv', R / 'data/graph/nodes_sample_clinical.csv')
shutil.copy2(S / 'shared/edges_GSE193066_preserved_RLE.csv', R / 'data/expression_analysis_core/edges_GSE193066.csv')
for folder in ['graph_full', 'graph_okg']:
    for name in ['edges_my_progression.csv', 'gene_progression_scores.csv']:
        src = C / 'data/graph_full' / name
        if src.exists():
            shutil.copy2(src, R / 'data' / folder / name)
shutil.copytree(R / 'data/progression_full', R / 'Paper1_Results/00_progression_genes', dirs_exist_ok=True)
for name in ['genes_by_fibrosis_stage.csv', 'genes_by_disease_group.csv', 'sample_demographics.csv']:
    shutil.copy2(R / 'data/for_mentor' / name, R / 'Paper1_Results/00_progression_genes' / name)
short = pd.read_csv(R / 'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv')
cl = pd.read_csv(R / 'Paper1_Results/Task2/task2_gene_clusters.csv')
extra = [c for c in ['ensembl_id', 'membership_confidence', 'confidence_n_bootstraps'] if c in cl]
short.merge(cl[extra], left_on='Ensembl_ID', right_on='ensembl_id', validate='1:1').drop(columns='ensembl_id').to_csv(R / 'Paper1_HighConfidence/shortlist_with_membership_confidence.csv', index=False)
(O / 'promotion_status.json').write_text(json.dumps({'selected_approach': 'combined', 'researcher_authorised': True,
    'fibrosis_genes': 3845, 'disease_genes': 4199, 'shared': 1822, 'union': 6222,
    'tier1': 447, 'shortlist': 23, 'archive_verified_files': len(manifest),
    'active_inputs_and_results_promoted': True, 'graph_update_pending': True,
    'package_rebuild_pending': True, 'alternative_cleanup_pending': True}, indent=2))
print('Promoted combined inputs/results; verified recovery files:', len(manifest))
