"""Promote verified corrections, retaining one checksum-verified recovery archive."""
from pathlib import Path
import hashlib,json,shutil,tarfile,os
R=Path(__file__).resolve().parents[2];D=R/'biopsy_correction_2026-10-10';A=R/'archives/previous_results_2026-10-10.tar.gz'
if A.exists():raise SystemExit('Recovery archive already exists; do not repeat promotion')
if not all(c['passed'] for c in json.loads((D/'verification_results.json').read_text())):raise SystemExit('Verification required')
sources=['Paper1_Results','Paper1_HighConfidence','Paper1_Package','Paper1_Manuscript','data/for_mentor','data/progression_full','docs/package','docs/provenance','README.md','CLAUDE.md','BIOPSY_CORRECTION.md','reports_progression_summary.html','build_paper1_package.py','scripts/make_fig1.py','manuscript_planning_2026-10-09_audit','biopsy_correction_2026-10-10/original_code','biopsy_correction_2026-10-10/data/baseline_reproduced']
files=[p for n in sources for p in ([R/n] if (R/n).is_file() else (R/n).rglob('*')) if p.is_file()]
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(A,'w:gz',compresslevel=3) as archive:
 for n in sources:
  if (R/n).exists():archive.add(R/n,arcname=n)
with tarfile.open(A,'r:gz') as archive:
 for n,h in manifest.items():
  if hashlib.sha256(archive.extractfile(n).read()).hexdigest()!=h:raise RuntimeError('Archive hash mismatch '+n)
(R/'archives/previous_results_2026-10-10_manifest.json').write_text(json.dumps({'archive':A.name,'files':manifest,'verified':True},indent=2))
# Preserve reference-only inputs before the package is rebuilt.
(R/'data/interim_full').mkdir(exist_ok=True);shutil.copy2(R/'Paper1_Package/04_DATA/harmonisation/_parse_summary.csv',R/'data/interim_full/_parse_summary.csv')
(D/'data/graph_full/nodes_dataset.csv').parent.mkdir(exist_ok=True);shutil.copy2(R/'Paper1_Package/04_DATA/graph_nodes/nodes_dataset.csv',D/'data/graph_full/nodes_dataset.csv')
shutil.copy2(R/'manuscript_planning_2026-10-09_audit/audit/live_graph_readonly.json',D/'source_graph_at_intake.json')
for rel in ['Paper1_Results','Paper1_HighConfidence','data/for_mentor','data/progression_full']:
 destination=R/rel
 if destination.exists():shutil.rmtree(destination)
 shutil.copytree(D/rel,destination)
# Result-tree progression inputs include raw sample metadata and corrected patient summaries.
shutil.copytree(R/'data/progression_full',R/'Paper1_Results/00_progression_genes',dirs_exist_ok=True)
for name in ['genes_by_fibrosis_stage.csv','genes_by_disease_group.csv','sample_demographics.csv']:
 shutil.copy2(R/'data/for_mentor'/name,R/'Paper1_Results/00_progression_genes'/name)
for folder in ['graph_okg','graph_full','genesets']:
 shutil.copytree(D/'data'/folder,R/'data'/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('edges_GSE*.csv'))
# Measurement recovery is explicitly the analysis core, not a full expression-load export.
core=R/'data/expression_analysis_core';core.mkdir(exist_ok=True)
for p in (D/'data/graph_full').glob('edges_GSE*.csv'):shutil.move(str(p),core/p.name)
shutil.copy2(R/'data/graph_full/nodes_gene.csv',core/'nodes_gene.csv');shutil.copy2(D/'data/expression_recovery_manifest.json',core/'expression_recovery_manifest.json')
(core/'README.md').write_text('''# Recovered expression analysis core\n\n16,051,490 value_z measurements: 14,794 all-eight-study genes ×1,085 samples. Recovered and verified against baseline discovery. This is a core-only analysis input, not the full32,471,042-measurement graph export. Do not use it to replace all EXPRESSES relationships. Raw expression in Neo4j is unchanged.\n''')
# Archive old manuscript and overview; no new prose draft is fabricated.
for rel in ['Paper1_Manuscript','manuscript_planning_2026-10-09_audit','biopsy_correction_2026-10-10/original_code','biopsy_correction_2026-10-10/data/baseline_reproduced']:
 if (R/rel).exists():shutil.rmtree(R/rel)
if (R/'reports_progression_summary.html').exists():(R/'reports_progression_summary.html').unlink()
(R/'Paper1_Manuscript').mkdir();(R/'Paper1_Manuscript/README.md').write_text('''# Manuscript status\n\nThe earlier Word draft and its generator were archived because they contain superseded analyses. No replacement manuscript prose has been drafted. Use Paper1_Package for current results and manuscript_planning for the evidence plan.\n''')
# Rename misleading result filename while retaining the existing source-script name for callers.
for folder in [R/'Paper1_HighConfidence',D/'Paper1_HighConfidence']:
 old=folder/'00_all_4692_progression_genes.csv'
 if old.exists():old.rename(folder/'00_all_progression_genes.csv')
for rel in ['scripts/00_all_4692_progression_genes.py', 'biopsy_correction_2026-10-10/scripts/00_all_4692_progression_genes.py']:
 p=R/rel;p.write_text(p.read_text().replace('"00_all_4692_progression_genes.csv"','"00_all_progression_genes.csv"'))
for rel in ['data/progression_full','Paper1_Results/00_progression_genes']:
 old=R/rel/'progression_both.csv'
 if old.exists():old.rename(R/rel/'diagnostic_both_q_significant.csv')
for rel in ['find_progression_genes.py','biopsy_correction_2026-10-10/find_progression_genes.py']:
 p=R/rel;p.write_text(p.read_text().replace('f"{OUT}/progression_both.csv"','f"{OUT}/diagnostic_both_q_significant.csv"'))
# Report consumers now point to a frozen archive when comparing original results.
(R/'archives/README.md').write_text('''# Recovery archive\n\nprevious_results_2026-10-10.tar.gz contains the superseded results/package, draft, documentation and source snapshots. Its member hashes were verified before replacement. The archive is for recovery/history; active analysis files are corrected.\n''')
(D/'promotion_status.json').write_text(json.dumps({'archive':str(A.relative_to(R)),'archive_verified_files':len(manifest),'active_results_promoted':True,'expression_core_path':'data/expression_analysis_core','package_rebuild_pending':True},indent=2))
print('Archive verified:',len(manifest),'files; corrected active results promoted.')
