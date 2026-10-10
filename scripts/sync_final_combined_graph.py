"""Synchronise final derived properties and progression links with rollback."""
from pathlib import Path
import base64, getpass, gzip, json, urllib.request
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
O = R / 'final_combined_2026-10-10'
password = getpass.getpass('Neo4j password: ')
headers = {'Authorization': 'Basic ' + base64.b64encode(('neo4j:' + password).encode()).decode(), 'Content-Type': 'application/json'}
def query(statement, parameters=None):
    req = urllib.request.Request('http://127.0.0.1:7474/db/neo4j/query/v2', data=json.dumps({'statement': statement, 'parameters': parameters or {}}).encode(), headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=180) as response:
        value = json.loads(response.read())
    if value.get('errors'):
        raise RuntimeError(value['errors'])
    return value['data']['values']

def counts():
    types = json.loads((R / 'biopsy_correction_2026-10-10/final_graph_readonly_verification.json').read_text())['counts']
    return {rel: query(f'MATCH ()-[r:{rel}]->() RETURN count(r)')[0][0] for rel in types}

if (O / 'graph_verification.json').exists():
    raise SystemExit('Already synchronised; refusing to repeat')
before_counts = counts()
# Reconstruct ALL mapped genes in this study, not just the analysis core.
with gzip.open(R / 'unit_audit_GSE193066_2026-10-10/GSE193066_NAFLD.HUn164.gct.gz', 'rt') as f:
    f.readline(); f.readline(); matrix = pd.read_csv(f, sep='\t', index_col=0)
matrix = matrix.select_dtypes(include='number')
matrix.index = matrix.index.astype(str).str.strip()
matrix = matrix[~matrix.index.duplicated(keep='first')]
matrix = matrix[~matrix.index.str.contains('_PAR_Y')]
gm = pd.read_csv(R / 'data/processed/gene_id_map.csv', dtype=str)
cw = pd.read_csv(R / 'data/processed/sample_crosswalk.csv', dtype=str)
lookup = gm[gm.dataset_id == 'GSE193066'].set_index('gene_id_raw').ensembl_id
samplemap = cw[cw.dataset_id == 'GSE193066'].set_index('sample_key').sample_id
matrix['ensembl_id'] = matrix.index.map(lookup)
raw = matrix[matrix.ensembl_id.notna()].groupby('ensembl_id').sum()
raw.columns = raw.columns.map(samplemap)
logged = np.log2(raw + 1)
z = logged.sub(logged.mean(axis=1), axis=0).div(logged.std(axis=1, ddof=1).replace(0, np.nan), axis=0).fillna(0)
core = pd.read_csv(R / 'data/expression_analysis_core/edges_GSE193066.csv')
for sample in raw.columns:
    c = core[core.sample_id == sample].set_index('ensembl_id').value_z
    assert np.allclose(c, z.loc[c.index, sample], atol=1e-12)

read_sample = 'MATCH (s:Sample {sample_id:$sample})-[r:EXPRESSES]->(g:Gene) RETURN g.ensembl_id, properties(r)'
update_sample = '''UNWIND $rows AS row MATCH (s:Sample {sample_id:$sample})-[r:EXPRESSES]->(g:Gene {ensembl_id:row.gene}) SET r.value_log=row.log, r.value_z=row.z, r.normalisation='deposited_RLE_log2_sample_SD', r.analysis_run='final_combined_2026-10-10' RETURN count(r)'''
restore_sample = 'UNWIND $rows AS row MATCH (s:Sample {sample_id:$sample})-[r:EXPRESSES]->(g:Gene {ensembl_id:row.gene}) SET r=row.props RETURN count(r)'
backup_dir = O / 'graph_rollback'
backup_dir.mkdir(exist_ok=True)
updated = []
pq = 'MATCH (g:Gene)-[r:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->(d:Disease) RETURN g.ensembl_id,type(r),d.node_id,properties(r)'
old_progression = query(pq)
expected_old = json.loads((R / 'biopsy_correction_2026-10-10/live_graph_after_progression_update.json').read_text())['data']['values']
assert {(r[0],r[1],r[2]) for r in old_progression} == {(r[0],r[1],r[2]) for r in expected_old}, 'Live progression links differ from previous verified version'
(O / 'live_graph_before_progression_update.json').write_text(json.dumps(old_progression))
clinical = pd.read_csv(R / 'data/graph/nodes_sample_clinical.csv', dtype=str).fillna('')
flagged = clinical[clinical.label_sensitivity_status == 'flagged_case_unclassified']
old_labels = query('MATCH (s:Sample) WHERE s.sample_id IN $ids RETURN s.sample_id, properties(s)', {'ids': flagged.sample_id.tolist()})
assert len(old_labels) == 5
(O / 'live_sample_labels_before.json').write_text(json.dumps(old_labels))
replacement = '''CALL { MATCH ()-[r:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->() DELETE r RETURN count(r) AS removed }
CALL { UNWIND $fib AS row MATCH (g:Gene {ensembl_id:row.gene}) MATCH (d:Disease {node_id:row.disease}) CREATE (g)-[r:TRACKS_FIBROSIS]->(d) SET r=row.props RETURN count(r) AS fib_written }
CALL { UNWIND $dis AS row MATCH (g:Gene {ensembl_id:row.gene}) MATCH (d:Disease {node_id:row.disease}) CREATE (g)-[r:TRACKS_INFLAMMATION]->(d) SET r=row.props RETURN count(r) AS dis_written }
RETURN removed,fib_written,dis_written'''
new = pd.read_csv(R / 'data/graph_full/edges_my_progression.csv')
ids = new.ensembl_id.unique().tolist()
assert query('MATCH (g:Gene) WHERE g.ensembl_id IN $ids RETURN count(g)', {'ids': ids})[0][0] == len(ids)
assert query('MATCH (d:Disease) WHERE d.node_id IN $ids RETURN count(d)', {'ids': new.disease_id.unique().tolist()})[0][0] == new.disease_id.nunique()
params = {'fib': [], 'dis': []}
for r in new.itertuples():
    params['fib' if r.rel == 'TRACKS_FIBROSIS' else 'dis'].append({'gene':r.ensembl_id, 'disease':r.disease_id, 'props':{'rho':r.rho, 'q':r.q, 'n_studies':int(r.n_studies), 'direction':r.direction, 'source':'our_patients', 'biopsy_policy':'same_stage_mean_otherwise_first', 'analysis_run':'final_combined_2026-10-10'}})
try:
    for i, sample in enumerate(raw.columns, 1):
        old = query(read_sample, {'sample':sample})
        assert len(old) == len(raw) and {r[0] for r in old} == set(raw.index), (sample, len(old), len(raw))
        for gene, props in old:
            assert np.isclose(props['value_raw'], raw.loc[gene, sample], atol=1e-8), (sample, gene, 'raw mismatch')
        with gzip.open(backup_dir / (sample + '.json.gz'), 'wt') as f:
            json.dump(old, f)
        rows = [{'gene':g, 'log':float(logged.loc[g, sample]), 'z':float(z.loc[g, sample])} for g in raw.index]
        updated.append(sample)
        assert query(update_sample, {'sample':sample, 'rows':rows})[0][0] == len(raw)
        actual = query(read_sample, {'sample':sample})
        for gene, props in actual:
            assert np.isclose(props['value_z'], z.loc[gene,sample], atol=1e-12)
            assert np.isclose(props['value_log'], logged.loc[gene,sample], atol=1e-12)
            assert np.isclose(props['value_raw'], raw.loc[gene,sample], atol=1e-8)
        if i % 10 == 0 or i == 164:
            print('Verified expression samples:', i, '/164', flush=True)
    rows = [{'id':r.sample_id, 'baseline':r.disease_group_baseline} for r in flagged.itertuples()]
    query("UNWIND $rows AS row MATCH (s:Sample {sample_id:row.id}) SET s.disease_group=null,s.disease_group_baseline=row.baseline,s.disease_provenance='unclassified_sensitivity',s.label_sensitivity_status='flagged_case_unclassified' RETURN count(s)", {'rows':rows})
    query(replacement, params)
    actual = query(pq)
    wanted = {(r['gene'], 'TRACKS_FIBROSIS' if rel == 'fib' else 'TRACKS_INFLAMMATION', r['disease']):r['props'] for rel,arr in params.items() for r in arr}
    assert {(r[0],r[1],r[2]):r[3] for r in actual} == wanted
    after_counts = counts()
    assert all(after_counts[k] == v for k,v in before_counts.items() if not k.startswith('TRACKS_'))
    assert after_counts['TRACKS_FIBROSIS'] == 3845 and after_counts['TRACKS_INFLAMMATION'] == 4199
    labels = query('MATCH (s:Sample) WHERE s.sample_id IN $ids RETURN s.sample_id,s.disease_group,s.disease_provenance', {'ids':flagged.sample_id.tolist()})
    assert len(labels) == 5 and all(r[1] is None and r[2] == 'unclassified_sensitivity' for r in labels)
    (O / 'live_graph_after_progression_update.json').write_text(json.dumps(actual))
    (O / 'graph_verification.json').write_text(json.dumps({'verified':True, 'counts':after_counts, 'total_relationships':sum(after_counts.values()), 'expression_samples_verified':164, 'expression_relationships_updated':len(raw)*164, 'raw_values_preserved':True, 'curated_relationship_counts_preserved':True, 'unclassified_sample_ids':flagged.sample_id.tolist(), 'progression_properties_exact_match':True}, indent=2))
    status = json.loads((O / 'promotion_status.json').read_text()); status['graph_update_pending']=False
    (O / 'promotion_status.json').write_text(json.dumps(status, indent=2))
    print('Graph synchronisation complete and verified.', flush=True)
except Exception:
    print('Restoring pre-update derived graph values.', flush=True)
    for sample in updated:
        with gzip.open(backup_dir / (sample + '.json.gz'), 'rt') as f:
            old = json.load(f)
        query(restore_sample, {'sample':sample, 'rows':[{'gene':g,'props':p} for g,p in old]})
    query('UNWIND $rows AS row MATCH (s:Sample {sample_id:row.id}) SET s=row.props RETURN count(s)', {'rows':[{'id':i,'props':p} for i,p in old_labels]})
    rollback = {'fib':[], 'dis':[]}
    for gene, rel, disease, props in old_progression:
        rollback['fib' if rel == 'TRACKS_FIBROSIS' else 'dis'].append({'gene':gene, 'disease':disease, 'props':props})
    query(replacement, rollback)
    raise
