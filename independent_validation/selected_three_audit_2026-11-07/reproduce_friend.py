"""Rerun supplied script unmodified, with isolated paths and explicit HGNC snapshot."""
from pathlib import Path
import sys,importlib.util,shutil
A=Path(__file__).resolve().parent;R=A.parents[1]
sys.path.insert(0,str(R));sys.path.insert(0,'/tmp/liver-validation-audit-deps')
spec=importlib.util.spec_from_file_location('friend_validation',A/'friend_package/code/validate_external.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
f.ROOT=R;f.RAW=A/'sources';f.HGNC=A/'sources/reference/hgnc_complete_set.txt';f.OUT=A/'reproduction_current_hgnc';f.READERS={g:f.READERS[g] for g in ['GSE213621','GSE225740','GSE268273']}
for name in ['GSE225740_NAFLD_RNA_counts.csv.gz','GSE225740_NAFLD_phenotypes.csv.gz']:
 shutil.copyfile(R/'independent_validation/candidate_screening_2026-11-07/GSE225740'/name,f.RAW/'GSE225740'/name)
if __name__=='__main__':f.main()
