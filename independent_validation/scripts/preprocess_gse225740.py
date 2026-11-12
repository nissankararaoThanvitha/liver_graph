#!/usr/bin/env python3
"""Prepare held-out GSE225740 without testing gene associations or reranking genes.

Run from any directory. Uses project-retained gene mapping, not a new annotation release.
Library totals use every deposited gene; mapping collisions sum counts before log.
Within-cohort z scores use all 93 deposited samples (ddof=1), then select 87 staged.
No expression-prevalence filter or automatic sample-outlier exclusion is applied.
"""
from pathlib import Path
import csv, hashlib, json, platform
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'independent_validation/candidate_screening_2026-11-07/GSE225740'
OUT = ROOT / 'independent_validation/GSE225740_preprocessed'
MAP = ROOT / 'data/processed/gene_id_map.csv'
SHORTLIST = ROOT / 'Paper1_HighConfidence/11_FINAL_shortlist_23_genes.csv'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(df, name, index=True):
    df.to_csv(OUT / name, sep='\t', index=index, float_format='%.12g',
              compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    counts_path = SOURCE / 'GSE225740_NAFLD_RNA_counts.csv.gz'
    pheno_path = SOURCE / 'GSE225740_NAFLD_phenotypes.csv.gz'
    geo_path = SOURCE / 'sample_metadata.tsv'
    # Read the unmodified header to catch duplicate columns before pandas renames them.
    import gzip
    with gzip.open(counts_path, 'rt') as f:
        header = next(csv.reader(f))
    assert len(header) == len(set(header)), 'Duplicate expression columns'
    counts = pd.read_csv(counts_path, dtype={'EntrezGene':str}).set_index('EntrezGene')
    assert counts.index.is_unique and counts.columns.is_unique
    values = counts.to_numpy(dtype=float)
    assert np.isfinite(values).all() and (values >= 0).all()
    assert np.equal(values, np.floor(values)).all(), 'Deposited counts not integer-valued'
    ph = pd.read_csv(pheno_path, dtype=str, keep_default_na=False).rename(columns={'pt. ID':'patient_id'})
    geo = pd.read_csv(geo_path, sep='\t', dtype=str, keep_default_na=False)
    assert ph.patient_id.is_unique and geo.description.is_unique and geo.gsm.is_unique
    assert set(counts.columns) == set(ph.patient_id) == set(geo.description)
    ph = ph.set_index('patient_id').loc[counts.columns]
    geo = geo.set_index('description').loc[counts.columns]
    for k in ['fibrosis','nas','steatohep']:
        a = ph[k].replace({'NA':'','NaN':''})
        b = geo[k].replace({'NA':'','NaN':''})
        assert a.equals(b.rename(a.name)), f'Phenotype/GEO mismatch: {k}'
    meta = ph.copy()
    meta['gsm'] = geo.gsm
    meta['dataset_id'] = 'GSE225740'
    meta['fibrosis_stage_raw'] = ph.fibrosis
    meta['fibrosis_stage'] = pd.to_numeric(ph.fibrosis.replace({'NA':''}), errors='coerce').astype('Int64')
    assert meta.fibrosis_stage.dropna().isin(range(5)).all()
    meta['eligible_for_stage_analysis'] = meta.fibrosis_stage.notna()
    meta['exclusion_reason'] = np.where(meta.eligible_for_stage_analysis,'','missing_fibrosis_stage')
    meta.index.name = 'patient_id'
    staged = meta.index[meta.eligible_for_stage_analysis].tolist()
    assert len(staged) == 87 and len(meta) == 93
    library = counts.sum(axis=0)
    assert (library > 0).all()
    log_all = np.log2(counts.div(library,axis=1) * 1e6 + 1)
    # Only unique Entrez -> Ensembl mappings are used. Keep unmapped raw rows in the
    # complete Entrez matrix and in the denominator, never silently in mapped results.
    gm = pd.read_csv(MAP, dtype=str).fillna('')
    gm = gm[gm.entrez_id.ne('') & gm.ensembl_id.ne('')]
    pairs = gm[['entrez_id','ensembl_id']].drop_duplicates()
    n_targets = pairs.groupby('entrez_id').ensembl_id.nunique()
    ambiguous = set(n_targets.index[n_targets > 1])
    unique = pairs[~pairs.entrez_id.isin(ambiguous)].set_index('entrez_id').ensembl_id
    mapping = pd.DataFrame(index=counts.index)
    mapping['ensembl_id'] = mapping.index.map(unique)
    mapping['mapping_status'] = ['ambiguous' if k in ambiguous else 'mapped' if pd.notna(v) else 'unmapped'
                                 for k,v in mapping.ensembl_id.items()]
    mapping['symbol'] = ''
    symbols = gm[gm.symbol.ne('')].groupby('ensembl_id').symbol.agg(lambda s:';'.join(sorted(set(s))))
    mapping['symbol'] = mapping.ensembl_id.map(symbols).fillna('')
    mapped_counts = counts.assign(ensembl_id=mapping.ensembl_id).dropna(subset=['ensembl_id']).groupby('ensembl_id').sum()
    mapped_log = np.log2(mapped_counts.div(library,axis=1) * 1e6 + 1)
    sd = mapped_log.std(axis=1,ddof=1)
    z = mapped_log.sub(mapped_log.mean(axis=1),axis=0).div(sd.replace(0,np.nan),axis=0).fillna(0)
    assert np.isfinite(z.to_numpy()).all()
    varying = sd > 0
    assert np.allclose(z.loc[varying].mean(axis=1),0,atol=1e-10)
    assert np.allclose(z.loc[varying].std(axis=1,ddof=1),1,atol=1e-10)
    shortlist = pd.read_csv(SHORTLIST)
    assert len(shortlist)==23 and shortlist.Ensembl_ID.is_unique
    assert set(shortlist.Ensembl_ID).issubset(mapped_counts.index)
    # QC flags describe availability; they are not validation outcomes or filters.
    gene_qc = pd.DataFrame(index=mapped_counts.index)
    gene_qc['symbol'] = gene_qc.index.map(symbols)
    gene_qc['zero_fraction_staged'] = mapped_counts[staged].eq(0).mean(axis=1)
    gene_qc['n_staged_cpm_ge_1'] = mapped_counts[staged].div(library[staged],axis=1).mul(1e6).ge(1).sum(axis=1)
    gene_qc['nonconstant_staged'] = mapped_log[staged].nunique(axis=1)>1
    gene_qc['in_fixed_shortlist'] = gene_qc.index.isin(shortlist.Ensembl_ID)
    sample_qc = meta[['gsm','fibrosis_stage','eligible_for_stage_analysis']].copy()
    sample_qc['deposited_gene_count_total'] = library
    sample_qc['detected_deposited_genes'] = counts.gt(0).sum(axis=0)
    sample_qc['zero_gene_fraction'] = counts.eq(0).mean(axis=0)
    sample_qc['mapped_count_fraction'] = mapped_counts.sum(axis=0)/library
    sample_qc['identical_expression_column'] = counts.T.duplicated(keep=False)
    save(meta,'sample_metadata_all.tsv')
    save(meta.loc[staged],'sample_metadata_staged.tsv')
    save(meta.loc[~meta.eligible_for_stage_analysis],'samples_excluded_from_stage_analysis.tsv')
    save(sample_qc,'sample_qc.tsv')
    save(mapping,'gene_mapping_audit.tsv.gz')
    save(gene_qc,'gene_qc.tsv.gz')
    save(log_all,'log2cpm_all_entrez_93.tsv.gz')
    save(mapped_counts[staged],'counts_mapped_staged_87.tsv.gz')
    save(mapped_log[staged],'log2cpm_mapped_staged_87.tsv.gz')
    save(z[staged],'zscore_mapped_staged_87.tsv.gz')
    for matrix,name in [(mapped_log,'shortlist23_log2cpm_staged_87.tsv'),(z,'shortlist23_zscore_staged_87.tsv')]:
        df=matrix.loc[shortlist.Ensembl_ID,staged].copy()
        df.insert(0,'Gene',shortlist.set_index('Ensembl_ID').Gene.loc[df.index])
        save(df,name)
    selected_qc = gene_qc.loc[shortlist.Ensembl_ID].copy()
    selected_qc.insert(0,'Gene',shortlist.set_index('Ensembl_ID').Gene.loc[selected_qc.index])
    save(selected_qc,'shortlist23_availability_qc.tsv')
    stages = meta.loc[staged].fibrosis_stage.value_counts().sort_index()
    summary = {
      'status':'preprocessing complete; no association tests performed',
      'input_genes':len(counts),'input_samples':len(meta),'staged_samples':len(staged),
      'missing_stage_samples':len(meta)-len(staged),'stage_counts':{str(k):int(v) for k,v in stages.items()},
      'mapping_status_counts':mapping.mapping_status.value_counts().to_dict(),
      'mapped_ensembl_genes':len(mapped_counts),'mapping_collapses':int(mapping.ensembl_id.notna().sum()-len(mapped_counts)),
      'shortlist_genes_mapped':len(shortlist),'shortlist_nonconstant_staged':int(selected_qc.nonconstant_staged.sum()),
      'duplicate_expression_columns':int(sample_qc.identical_expression_column.sum()),
      'library_total_min':int(library.min()),'library_total_median':float(library.median()),'library_total_max':int(library.max()),
      'all_values_nonnegative_integer_finite':True,'automatic_sample_exclusions_for_expression_qc':0,
      'normalization':'log2(count / sum of all 19101 deposited genes in the sample * 1e6 + 1)',
      'mapping':'retained discovery gene_id_map.csv; unambiguous Entrez to Ensembl; sum before logarithm',
      'zscore_reference':'all 93 deposited samples independently of discovery data; ddof=1; constant genes -> 0',
      'gene_filter':'none; zero/low expression and nonconstant flags retained for later testability decisions',
      'patient_independence':'deposited-ID overlap screened; independent patient provenance still unresolved',
      'versions':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},
      'inputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [counts_path,pheno_path,geo_path,MAP,SHORTLIST]],
      'script_sha256':sha(Path(__file__)),
    }
    (OUT/'preprocessing_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
