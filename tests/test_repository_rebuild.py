"""Small fixtures for the repaired rebuild tools; no production graph writes."""
import csv
import gzip
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.prepare_analysis_core import prepare, prepare_annotations
from scripts.verify_against_neo4j import DEFAULT_WORKBOOK, compare
from scripts.unify_drug_schema import validate, needs_migration, snapshot, migrate


def gz_csv(header, rows):
    s = io.StringIO(newline=''); w = csv.writer(s); w.writerow(header); w.writerows(rows)
    return gzip.compress(s.getvalue().encode())


class CoreRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.bg = self.root / 'bg.csv'; self.bg.write_text('ensembl_id\ng1\ng2\n')
        self.lab = self.root / 'lab.csv'; self.lab.write_text('sample_id,dataset_id\ns1,GSE1\ns2,GSE2\n')

    def archive(self, missing=False, duplicate=False, nonfinite=False):
        p = self.root / 'release.zip'
        rows = [['s1','g1',0,0,0], ['s1','g2',1,1,-1], ['s2','g1',2,2,1], ['s2','g2',3,3,2]]
        if missing: rows.pop()
        if duplicate: rows.append(rows[0])
        if nonfinite: rows[0][-1] = 'nan'
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('nodes/Gene.csv.gz', gz_csv(['ensembl_id:ID(Gene)','symbol:string','n_datasets:long'],[['g1','A',8],['g2','B',8]]))
            z.writestr('nodes/Sample.csv.gz', gz_csv(['sample_id:ID(Sample)','dataset_id:string'],[['s1','GSE1'],['s2','GSE2']]))
            z.writestr('relationships/EXPRESSES__Sample__Gene.csv.gz',gz_csv([':START_ID(Sample)',':END_ID(Gene)','value_raw:double','value_log:double','value_z:double'],rows))
            for label in ['Pathway','BioProcess']:
                suffix = '__Reactome' if label == 'Pathway' else ''
                rel = 'IN_PATHWAY' if label == 'Pathway' else 'INVOLVED_IN'
                z.writestr(f'nodes/{label}{suffix}.csv.gz', gz_csv(['node_id:ID('+label+')','name:string'],[[label,'Original']]))
                z.writestr(f'relationships/{rel}__Gene__{label}{suffix}.csv.gz',gz_csv([':START_ID(Gene)',':END_ID('+label+')'],[['g1',label]]))
        return p

    def test_recovery_preserves_zero_and_is_complete(self):
        out = self.root/'core'; result=prepare(self.archive(),out,self.bg,self.lab)
        self.assertEqual(result['expression_rows'],4)
        with (out/'edges_GSE1.csv').open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(float(rows[0]['value_z']),0)
        self.assertEqual(prepare_annotations(self.root/'release.zip',self.root/'knowledge')['nodes_pathway.csv'],1)
        with self.assertRaises(ValueError): prepare(self.root/'release.zip',out,self.bg,self.lab)

    def test_invalid_matrix_not_promoted(self):
        for mode in ['missing','duplicate','nonfinite']:
            out=self.root/mode
            with self.assertRaises(ValueError): prepare(self.archive(**{mode:True}),out,self.bg,self.lab)
            self.assertFalse(out.exists())
            self.assertFalse(list(self.root.glob(mode+'.partial-*')))

    def test_mismatched_metadata_rejected(self):
        archive=self.archive();self.lab.write_text('sample_id,dataset_id\ns1,GSE9\ns2,GSE2\n')
        with self.assertRaises(ValueError): prepare(archive,self.root/'core',self.bg,self.lab)


class VerificationTests(unittest.TestCase):
    def test_default_workbook_is_in_results(self):
        self.assertEqual(DEFAULT_WORKBOOK.parent.name,'Paper1_HighConfidence')
        self.assertTrue(DEFAULT_WORKBOOK.is_file())

    def test_added_annotations_ignored_missing_or_duplicate_members_detected(self):
        reference=[{'id':'p1','label':'Pathway','rel':'IN_PATHWAY','members':['g1']}]
        class Result:
            def __init__(self, rows): self.rows=rows
            def data(self): return self.rows
        class Session:
            links=1
            def run(self, query, rows):
                return Result([{'id':r['id'],'nodes':1,'members':['g1'],'links':self.links} for r in rows])
        s=Session();self.assertEqual(compare(s,reference),[])
        s.links=2;self.assertEqual(compare(s,reference),['p1'])

    def test_migration_rejects_ambiguous_identifiers(self):
        with self.assertRaises(ValueError):validate({'nodes':[{'props':{'node_id':'d'}},{'props':{'node_id':'d'}}],'links':[]})
        self.assertFalse(needs_migration({'nodes':[{'labels':['Drug']}],'links':[]}))


@unittest.skipUnless(os.environ.get('TEST_NEO4J_URI') == 'bolt://127.0.0.1:17689', 'isolated Neo4j integration test only')
class MigrationIntegrationTests(unittest.TestCase):
    def test_atomic_preservation_and_repeat_run(self):
        from neo4j import GraphDatabase
        with GraphDatabase.driver(os.environ['TEST_NEO4J_URI'],auth=None) as drv:
            with drv.session(database='neo4j') as s:
                self.assertEqual(s.run('MATCH (n) RETURN count(n) AS n').single()['n'], 0, 'Use an empty isolated test database')
                s.run('''CREATE (d:Drug:ExternalDrug:RebuildTest {node_id:'d', name:'test', flags:['one','two']}),
                    (g:Gene:RebuildTest {ensembl_id:'g'}), (p:Pathway:RebuildTest {node_id:'p'})
                    CREATE (d)-[:EXTERNAL_ACTS_ON {action:'inhibitor', evidence:['A','B'], weight:0.0}]->(g),
                    (d)-[:ACTS_ON {action:'agonist', source:'original'}]->(g),
                    (g)-[:IN_PATHWAY]->(p)''').consume()
                before=s.execute_read(snapshot);validate(before)
                result=s.execute_write(migrate,before,'test-migration')
                self.assertEqual(result['relationships_converted'],1)
                after=s.execute_read(snapshot);self.assertFalse(needs_migration(after))
                self.assertEqual(len(after['links']),2)
                self.assertEqual(s.run('MATCH ()-[r:IN_PATHWAY]->() RETURN count(r) AS n').single()['n'],1)
                again=s.execute_write(migrate,after,'second-run');self.assertEqual(again['relationships_converted'],0)
                self.assertEqual(s.execute_read(snapshot),after)
                # Changes made inside a failed transaction must not be committed.
                def fail(tx):
                    tx.run("MATCH (d:Drug) SET d.name='changed'").consume()
                    raise ValueError('test rollback')
                with self.assertRaises(ValueError):s.execute_write(fail)
                self.assertEqual(s.execute_read(snapshot),after)
                # Execute the verifier's Cypher against a real engine.
                self.assertEqual(compare(s,[{'id':'p','label':'Pathway','rel':'IN_PATHWAY','members':['g']}]),[])

                s.run('MATCH (n:RebuildTest) DETACH DELETE n').consume()
