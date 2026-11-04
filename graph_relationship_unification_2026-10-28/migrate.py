import base64, collections, getpass, hashlib, json, pathlib, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
PASSWORD = getpass.getpass('Neo4j password: ')
AUTH = base64.b64encode(('neo4j:' + PASSWORD).encode()).decode()

def query(statement, parameters=None):
    body = json.dumps({'statements': [{'statement': statement, 'parameters': parameters or {}}]}).encode()
    req = urllib.request.Request('http://127.0.0.1:7474/db/neo4j/tx/commit', data=body,
        headers={'Authorization': 'Basic ' + AUTH, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as response:
        data = json.load(response)
    if data.get('errors'):
        raise RuntimeError(data['errors'])
    result = data['results'][0]
    return [dict(zip(result['columns'], item['row'])) for item in result['data']]

def save(name, data):
    target = ROOT / name
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False))

EXPORT = '''MATCH (a)-[r:ACTS_ON|EXTERNAL_ACTS_ON]->(b)
RETURN elementId(r) AS id, type(r) AS type, elementId(a) AS start,
elementId(b) AS end, labels(a) AS start_labels, labels(b) AS end_labels,
a.node_id AS drug_id, b.ensembl_id AS gene_id, properties(r) AS props'''

def stats():
    return {'nodes': query('MATCH (n) RETURN count(n) AS n')[0]['n'],
            'relationships': query('MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS n')}

mode = sys.argv[1]
if mode == 'audit':
    if (ROOT / 'before.json').exists():
        raise RuntimeError('Backup already exists; refusing overwrite')
    rows = query(EXPORT)
    save('before.json', rows)
    save('before_stats.json', stats())
    summary = {}
    for kind in ['ACTS_ON', 'EXTERNAL_ACTS_ON']:
        subset = [r for r in rows if r['type'] == kind]
        summary[kind] = {'count': len(subset), 'keys': dict(collections.Counter(k for r in subset for k in r['props'])),
                         'examples': [r['props'] for r in subset[:3]]}
    save('property_audit.json', summary)
    print(json.dumps(summary, indent=2))

elif mode == 'migrate':
    before = json.loads((ROOT / 'before.json').read_text())
    live = query(EXPORT)
    assert sorted(before, key=lambda r:r['id']) == sorted(live, key=lambda r:r['id']), 'Graph changed since backup'
    assert len(before) == 25890
    reserved = {'unified_actions', 'unified_sources', 'original_relationship_type', 'migration_record_id'}
    assert not any(reserved.intersection(r['props']) for r in before), 'Property-name collision'
    assert all('Drug' in r['start_labels'] and 'Gene' in r['end_labels'] for r in before)

    def values(v):
        if v is None: return []
        if isinstance(v, list): return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list): return [str(x).strip() for x in parsed if str(x).strip()]
            except (ValueError, TypeError): pass
            return [x.strip() for x in v.split(';') if x.strip()]
        return [str(v)]

    records = []
    for r in before:
        p = r['props']
        actions = sorted(set(x.upper() for key in ['action', 'action_labels', 'external_action_label'] for x in values(p.get(key))))
        sources = sorted(set(x for key in ['sources_direct', 'sources', 'external_action_sources'] for x in values(p.get(key))))
        record = {'id': r['id'], 'type': r['type'], 'extra': {
            'original_relationship_type': r['type'], 'migration_record_id': r['id']}}
        if actions: record['extra']['unified_actions'] = actions
        if sources: record['extra']['unified_sources'] = sources
        records.append(record)
    save('normalization_records.json', records)
    # One atomic transaction: either all records migrate or none do.
    result = query('''UNWIND $records AS row
      MATCH (a)-[r:ACTS_ON|EXTERNAL_ACTS_ON]->(b) WHERE elementId(r) = row.id
      CALL (a, r, b, row) {
        WITH a, r, b, row WHERE row.type = 'EXTERNAL_ACTS_ON'
        CREATE (a)-[n:ACTS_ON]->(b) SET n = properties(r) SET n += row.extra
        DELETE r RETURN elementId(n) AS new_id
        UNION ALL
        WITH a, r, b, row WHERE row.type = 'ACTS_ON'
        SET r += row.extra RETURN elementId(r) AS new_id
      }
      RETURN row.id AS old_id, new_id''', {'records': records})
    save('id_mapping.json', result)
    print(json.dumps({'migrated_records': len(result)}))
    assert len(result) == len(before)

elif mode == 'verify':
    before = json.loads((ROOT / 'before.json').read_text())
    after = query(EXPORT)
    save('after.json', after)
    now = stats()
    save('after_stats.json', now)
    prior = json.loads((ROOT / 'before_stats.json').read_text())
    indexed = {r['props'].get('migration_record_id'): r for r in after}
    checks = {'records_before': len(before), 'records_after': len(after),
       'all_ACTS_ON': all(r['type'] == 'ACTS_ON' for r in after),
       'one_record_per_original': len(indexed) == len(before) == len(after),
       'endpoints_preserved': all((r['start'], r['end']) == (indexed[r['id']]['start'], indexed[r['id']]['end']) for r in before),
       'original_properties_preserved': all(all(indexed[r['id']]['props'].get(k) == v for k,v in r['props'].items()) for r in before),
       'original_types_preserved': all(indexed[r['id']]['props']['original_relationship_type'] == r['type'] for r in before),
       'nodes_unchanged': now['nodes'] == prior['nodes'],
       'total_relationships_unchanged': sum(r['n'] for r in now['relationships']) == sum(r['n'] for r in prior['relationships']),
       'other_relationship_types_unchanged': {r['type']:r['n'] for r in now['relationships'] if r['type'] != 'ACTS_ON'} == {r['type']:r['n'] for r in prior['relationships'] if r['type'] not in ['ACTS_ON','EXTERNAL_ACTS_ON']}}
    expected = json.loads((ROOT / 'normalization_records.json').read_text())
    checks['normalized_fields_exact'] = all(all(indexed[r['id']]['props'].get(k)==v for k,v in r['extra'].items()) for r in expected)
    save('verification.json', checks)
    print(json.dumps(checks, indent=2))
    assert all(v for k,v in checks.items() if isinstance(v,bool))

elif mode == 'restore':
    # Explicitly invoked restoration only; preserves separately recorded evidence.
    before = json.loads((ROOT / 'before.json').read_text())
    live = query(EXPORT)
    assert len(live) == len(before)
    assert len({r['props'].get('migration_record_id') for r in live}) == len(before)
    result = query('''UNWIND $records AS row
      MATCH (a)-[r:ACTS_ON]->(b) WHERE r.migration_record_id = row.id
      CALL (a,r,b,row) {
        WITH a,r,b,row WHERE row.type = 'EXTERNAL_ACTS_ON'
        CREATE (a)-[n:EXTERNAL_ACTS_ON]->(b) SET n = row.props DELETE r RETURN 1 AS restored
        UNION ALL
        WITH a,r,b,row WHERE row.type = 'ACTS_ON'
        SET r = row.props RETURN 1 AS restored
      } RETURN count(*) AS restored''', {'records': before})
    print(result)
else:
    raise ValueError(mode)
