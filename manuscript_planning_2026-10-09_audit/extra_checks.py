from pathlib import Path
import pandas as pd,json
R=Path(__file__).parent.parent;O=Path(__file__).parent/'audit';P=R/'Paper1_Package'
def rd(s):return pd.read_csv(P/s)
for s in ['04_DATA/graph_nodes/edges_my_progression.csv','04_DATA/knowledge_layer/edges_my_progression.csv']:
 a=rd(s);print(s,len(a),list(a));print(a.head(2).to_string(index=False))
print('background',rd('04_DATA/progression_genes/progression_fibrosis.csv').symbol.nunique())
a=rd('03_RESULTS/Task5_gene_prioritisation/01_master_table.csv');print('tiers',a.tier.value_counts().to_dict());print('delta_disagree',a[~a.delta_agrees][['symbol','fibrosis_rho','delta_F0_F4']].to_dict('records'));print('Tier1 clusters',a[a.HighConfidenceScore>=7].cluster.value_counts().to_dict())
short=rd('02_TABLES/main/Table6_prioritised_genes.csv');cl=rd('03_RESULTS/Task2_trajectories/task2_gene_clusters.csv');m=short.merge(cl[['ensembl_id','membership_confidence','confidence_n_bootstraps']],left_on='Ensembl_ID',right_on='ensembl_id');print('short confidence',m[['Gene','Cluster','membership_confidence','confidence_n_bootstraps']].to_string(index=False))
lo=rd('03_RESULTS/Task5_gene_prioritisation/10_loso_summary.csv');print('LOSO counts', {c:lo[c].value_counts().sort_index().to_dict() for c in ['loso_direction_kept','loso_still_significant','loso_still_strong']})
a=rd('03_RESULTS/Task5_gene_prioritisation/05_powermatched_per_gene.csv');print('Matched per gene counts',a[a.matched_frac_significant>=.5].transition.value_counts().to_dict())
wb=pd.read_excel(P/'02_TABLES/supplementary/TableS19_knowledge_graph_connections.xlsx',sheet_name=None)
rank=wb['3_all_mechanisms_ranked'];print('rank counts',len(rank),rank.eligible_for_figure.sum(),rank.selected_for_figure.sum());print(rank[rank.selected_for_figure].to_string(index=False));print('tier1_507_actual',wb['2_tier1_507_KG'].Ensembl_ID.nunique());print('figure',len(wb['4_figure_edges']),wb['4_figure_edges'].Ensembl_ID.nunique(),wb['4_figure_edges'][wb['4_figure_edges'].In_final_25].Gene.unique())
all_edges=pd.concat([rd('04_DATA/knowledge_layer/edges_pathway_gene.csv'),rd('04_DATA/knowledge_layer/edges_biological_process_gene.csv')]);live=json.loads((O/'live_graph_readonly.json').read_text());values=dict(live['membership']['data']['values']);result=[]
for _,r in rank[rank.selected_for_figure].iterrows():
 c=set(all_edges[all_edges.to_id==r.Mechanism_ID].from_id);d=set(values.get(r.Mechanism_ID,[]));result.append({'mechanism_id':r.Mechanism_ID,'name':r.mechanism,'csv_members':len(c),'live_members':len(d),'csv_only':sorted(c-d),'live_only':sorted(d-c),'equal':c==d})
(O/'live_membership_comparison.json').write_text(json.dumps(result,indent=2));print('12 mechanism membership equality',all(x['equal'] for x in result))
for s in ['03_RESULTS/Task4_enrichment/enrichment_tables/C1_core__GO_BP.csv','03_RESULTS/Task4_enrichment/enrichment_tables/C3_core__GO_BP.csv','03_RESULTS/Task4_enrichment/enrichment_tables/C4_core__Reactome.csv']:
 a=rd(s); print('residual',s,len(a),a.n_group_genes.unique(),a.significant.sum())
print('all_significant_rows',len(rd('03_RESULTS/Task4_enrichment/task4_all_significant.csv')))
