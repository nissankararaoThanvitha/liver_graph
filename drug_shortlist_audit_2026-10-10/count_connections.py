"""Count recorded drug connections; indication annotations are not approvals."""
from pathlib import Path
import hashlib, json
import pandas as pd

R = Path(__file__).resolve().parents[1]
O = Path(__file__).resolve().parent
paths = {
    'shortlist': 'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv',
    'drug_gene': 'data/graph_okg/edges_drug_gene.csv',
    'drug_disease': 'data/graph_okg/edges_drug_disease.csv',
    'drug_nodes': 'data/graph_okg/nodes_drug.csv',
    'disease_nodes': 'data/graph_okg/nodes_disease.csv',
}
s, e, a, n, d = (pd.read_csv(R / paths[k]) for k in paths)
x = e[e.to_id.isin(s.Ensembl_ID)].merge(s[['Gene', 'Ensembl_ID']], left_on='to_id', right_on='Ensembl_ID')
x = x.merge(n.rename(columns={'node_id': 'drug_id', 'name': 'drug_name'}), left_on='from_id', right_on='drug_id')
x.to_csv(O / 'shortlist_drug_connections.csv', index=False)
a = a[a.from_id.isin(x.from_id)].merge(d.rename(columns={'node_id': 'disease_id', 'name': 'disease_name'}), left_on='to_id', right_on='disease_id')
# Explicit label-based scope, including liver cancers and biliary diseases.
z = a[a.disease_name.str.contains(r'liver|hepat|steato|cirrhos|cholang|biliary', case=False, na=False)].copy()
z = z.merge(n.rename(columns={'node_id': 'drug_id', 'name': 'drug_name'}), left_on='from_id', right_on='drug_id')
z.to_csv(O / 'liver_biliary_annotations.csv', index=False)
t = z[(z.rel_type == 'INDICATION') & z.to_id.isin(['EFO_0003095', 'EFO_1001249'])]
t.to_csv(O / 'nafld_nash_indication_annotations.csv', index=False)
counts = x.groupby('Gene').from_id.nunique().rename('unique_drugs')
s[['Gene', 'Ensembl_ID']].merge(counts, on='Gene', how='left').fillna({'unique_drugs': 0}).to_csv(O / 'per_gene_drug_counts.csv', index=False)
summary = {
    'source': 'local graph CSV exports; not a fresh live Neo4j query',
    'shortlist_genes': len(s), 'genes_with_drug_links': x.Gene.nunique(),
    'unique_connected_drugs': x.from_id.nunique(), 'drug_gene_rows': len(x),
    'unique_drugs_with_target_action_links': x[x.rel_type.isin(['TARGET', 'BLOCKER', 'INHIBITOR', 'ANTAGONIST', 'AGONIST'])].from_id.nunique(),
    'liver_biliary_unique_drugs_by_relation': z.groupby('rel_type').from_id.nunique().to_dict(),
    'nafld_nash_unique_indication_drugs': t.from_id.nunique(),
    'genes_without_recorded_drug_links': s[~s.Gene.isin(x.Gene)].Gene.tolist(),
    'source_sha256': {v: hashlib.sha256((R / v).read_bytes()).hexdigest() for v in paths.values()},
    'limitations': 'INDICATION may include investigational evidence and is not verified approval. Contraindications are counted separately. Liver/biliary scope uses the explicit disease-label pattern in this script. ENZYME, CARRIER and TRANSPORTER links do not imply therapeutic targeting.',
}
(O / 'summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps({k: v for k, v in summary.items() if k != 'source_sha256'}, indent=2))
print(t[['drug_name', 'disease_name']].drop_duplicates().sort_values(['drug_name', 'disease_name']).to_string(index=False))
