"""Read-only verification of original annotation membership, not whole-graph totals.

New KEGG/Hallmark nodes are outside the original annotation universe. Whole
resource counts are checked separately by verify_extended_graph_counts.py.
"""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKBOOK = ROOT / 'Paper1_HighConfidence/12_KG_supplementary.xlsx'


def load_reference(kg, workbook):
    import pandas as pd
    rows = []
    for label, filename, edgefile, rel in (
        ('Pathway', 'nodes_pathway.csv', 'edges_pathway_gene.csv', 'IN_PATHWAY'),
        ('BioProcess', 'nodes_bioprocess.csv', 'edges_biological_process_gene.csv', 'INVOLVED_IN')):
        nodes = pd.read_csv(kg / filename, dtype=str)
        if nodes.node_id.duplicated().any():
            raise ValueError('Duplicate annotation node IDs')
        edges = pd.read_csv(kg / edgefile, dtype=str)
        if edges.duplicated(['from_id', 'to_id']).any():
            raise ValueError('Duplicate annotation membership in reference CSV')
        members = edges.groupby('to_id').from_id.agg(lambda s: sorted(set(s))).to_dict()
        for node in nodes.node_id:
            rows.append({'id': node, 'label': label, 'rel': rel, 'members': members.get(node, [])})
    selected = pd.read_excel(workbook, sheet_name='3_all_mechanisms_ranked')
    selected = selected[selected.selected_for_figure.map(lambda x: str(x).lower() in ('true', '1'))]
    ids = set(selected.Mechanism_ID.astype(str))
    if not ids or not ids <= {r['id'] for r in rows}:
        raise ValueError('Selected annotations missing from reference layer')
    return rows, ids


def compare(session, reference):
    failures = []
    for offset in range(0, len(reference), 500):
        batch = reference[offset:offset + 500]
        actual = session.run('''UNWIND $rows AS row
            OPTIONAL MATCH (m {node_id: row.id}) WHERE row.label IN labels(m)
            OPTIONAL MATCH (g:Gene)-[r:IN_PATHWAY|INVOLVED_IN]->(m) WHERE type(r) = row.rel
            RETURN row.id AS id, count(DISTINCT m) AS nodes,
                   collect(DISTINCT g.ensembl_id) AS members, count(r) AS links''', rows=batch).data()
        found = {r['id']: r for r in actual}
        for row in batch:
            a = found.get(row['id'], {})
            if a.get('nodes') != 1 or set(a.get('members', [])) != set(row['members']) or a.get('links') != len(row['members']):
                failures.append(row['id'])
    return failures


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--knowledge', type=Path, default=ROOT / 'data/graph_okg')
    ap.add_argument('--workbook', type=Path, default=DEFAULT_WORKBOOK)
    ap.add_argument('--uri', default=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'))
    ap.add_argument('--database', default=os.environ.get('NEO4J_DATABASE', 'neo4j'))
    ap.add_argument('--user', default=os.environ.get('NEO4J_USERNAME', os.environ.get('NEO4J_USER', 'neo4j')))
    args = ap.parse_args()
    needed = [args.workbook] + [args.knowledge / n for n in (
        'nodes_pathway.csv', 'nodes_bioprocess.csv', 'edges_pathway_gene.csv',
        'edges_biological_process_gene.csv')]
    missing = [str(p) for p in needed if not p.is_file()]
    if missing:
        ap.error('Missing inputs: ' + ', '.join(missing) +
                 '. See prepare_analysis_core.py --annotations-only and docs/provenance/REBUILD.md.')
    reference, selected = load_reference(args.knowledge, args.workbook)
    if not os.environ.get('NEO4J_PASSWORD'):
        ap.error('set NEO4J_PASSWORD in the environment')
    from neo4j import GraphDatabase, READ_ACCESS
    with GraphDatabase.driver(args.uri, auth=(args.user, os.environ['NEO4J_PASSWORD'])) as drv:
        with drv.session(database=args.database, default_access_mode=READ_ACCESS) as s:
            failures = compare(s, reference)
    print(f'Original annotations: {len(reference)}; mismatches: {len(failures)}; '
          f'selected annotation mismatches: {len(selected & set(failures))}')
    if failures:
        raise SystemExit('Annotation membership/duplicate checks failed: ' + ', '.join(failures[:20]))
    print('PASS: original annotation memberships match; added annotations excluded by scope.')


if __name__ == '__main__':
    main()
