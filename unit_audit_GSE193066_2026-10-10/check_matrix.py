from pathlib import Path
import gzip,csv,json,math
import numpy as np,pandas as pd
D=Path(__file__).parent;R=D.parent
with gzip.open(D/'GSE193066_NAFLD.HUn164.gct.gz','rt') as f:
 version=f.readline().strip();declared=f.readline().strip();matrix=pd.read_csv(f,sep='\t',index_col=0)
annotation_columns=[c for c in matrix.columns if not pd.api.types.is_numeric_dtype(matrix[c])]
matrix=matrix.select_dtypes(include='number')
matrix=matrix.apply(pd.to_numeric,errors='raise');matrix.index=matrix.index.astype(str).str.strip();matrix=matrix[~matrix.index.duplicated(keep='first')];X=matrix.to_numpy(float)
stats={'gct_version':version,'annotation_columns_excluded':annotation_columns,'declared_dimensions':declared,'genes':len(matrix),'samples':len(matrix.columns),'min_value':float(X.min()),'max_value':float(X.max()),'fraction_noninteger':float((X!=np.round(X)).mean()),'fraction_zero':float((X==0).mean()),'negative_values':int((X<0).sum()),'column_sum_min':float(X.sum(0).min()),'column_sum_max':float(X.sum(0).max()),'column_sum_median':float(np.median(X.sum(0)))}
# Reproduce the current transformation without changing any active CSV.
gmap=pd.read_csv(R/'data/processed/gene_id_map.csv',dtype=str);gmap=gmap[gmap.dataset_id=='GSE193066'].set_index('gene_id_raw').ensembl_id
cw=pd.read_csv(R/'data/processed/sample_crosswalk.csv',dtype=str);cw=cw[cw.dataset_id=='GSE193066'].set_index('sample_key').sample_id
mapped=matrix.copy();mapped['ensembl_id']=matrix.index.map(gmap);mapped=mapped[mapped.ensembl_id.notna()];mapped=mapped.groupby('ensembl_id').sum();log_cpm=np.log2(mapped.div(matrix.sum(0),axis=1)*1e6+1);z=log_cpm.sub(log_cpm.mean(1),axis=0).div(log_cpm.std(1,ddof=1).replace(0,np.nan),axis=0).fillna(0);z.columns=z.columns.map(cw)
core=pd.read_csv(R/'data/expression_analysis_core/edges_GSE193066.csv');expected=core.pivot(index='ensembl_id',columns='sample_id',values='value_z');reproduced=z.reindex(index=expected.index,columns=expected.columns);difference=(expected-reproduced).abs();stats['current_value_z_rows_checked']=int(expected.size);stats['current_value_z_max_absolute_difference']=float(difference.max().max());stats['current_value_z_reproduced']=bool(np.allclose(expected,reproduced,atol=1e-10,rtol=1e-8))
# Descriptive comparison only: how far could preserving deposited normalisation move ranks?
# This does not replace an analysis method or rerun statistical discovery.
log_rle=np.log2(mapped+1);rank_correlations=log_cpm.rank(axis=1).corrwith(log_rle.rank(axis=1),axis=1);stats['descriptive_gene_rank_corr_median']=float(rank_correlations.median());stats['descriptive_gene_rank_corr_10pct']=float(rank_correlations.quantile(.1));stats['descriptive_gene_rank_corr_min']=float(rank_correlations.min());stats['genes_rank_correlation_below_0_9']=int((rank_correlations<.9).sum())
rank_correlations.rename('spearman_across_samples_cpm_vs_deposited').to_csv(D/'normalisation_rank_comparison.csv')
column_sums=pd.DataFrame({'sample_key':matrix.columns,'sample_id':matrix.columns.map(cw),'deposited_RLE_column_sum':matrix.sum(0).to_numpy()});column_sums.to_csv(D/'sample_column_sums.csv',index=False)
(D/'matrix_checks.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
with gzip.open(D/'GSE193066_series_matrix.txt.gz','rt') as f:text=f.read()
(D/'GSE193066_series_matrix.txt').write_text(text)
rows=list(csv.reader(text.splitlines(),delimiter='\t'));processing=[r for r in rows if r and 'data_processing' in r[0]];lines=[]
for r in processing:
 for value in r[1:]:
  if value not in lines:lines.append(value)
(D/'source_processing_fields.json').write_text(json.dumps(lines,indent=2));print('PROCESSING',json.dumps(lines,indent=2))
assert stats['current_value_z_reproduced']
