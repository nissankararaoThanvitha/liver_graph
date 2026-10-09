"""One patient observation: average equal-stage biopsies, otherwise retain biopsy 1.

Selection happens before filtering to a particular stage contrast, so a second
biopsy cannot re-enter when the first lies outside that contrast. Expression
is averaged only after this metadata selection. Unknown stages are never
assumed equal. Raw samples and the graph remain intact.
"""
import pandas as pd


def select_biopsies(labels, stage='fibrosis_stage'):
    required = {'sample_id', 'dataset_id', 'patient_id', 'biopsy_number', stage}
    missing = required - set(labels.columns)
    if missing:
        raise ValueError(f'Biopsy policy requires columns: {sorted(missing)}')
    if labels.sample_id.duplicated().any():
        raise ValueError('Duplicate clinical sample_id')
    keep = []
    for _, group in labels.groupby(['dataset_id', 'patient_id'], sort=False, dropna=False):
        if len(group) == 1:
            keep.extend(group.index)
            continue
        stages = pd.to_numeric(group[stage], errors='coerce')
        if stages.notna().all() and stages.nunique() == 1:
            keep.extend(group.index)
        else:
            order = pd.to_numeric(group.biopsy_number, errors='coerce')
            first = group[order == 1]
            if len(first) != 1:
                raise ValueError(f'Cannot identify a unique first biopsy for {group.patient_id.iloc[0]}')
            keep.extend(first.index)
    selected = labels.loc[keep].copy()
    selected["__biopsy_order"] = pd.to_numeric(selected.biopsy_number, errors="coerce")
    return selected.sort_values(["dataset_id", "patient_id", "__biopsy_order", "sample_id"]).drop(columns="__biopsy_order")


def patient_expression(expression, labels, stage='fibrosis_stage'):
    """Return one patient/gene row, averaging only selected equal-stage repeats."""
    selected = select_biopsies(labels, stage)
    merged = expression.merge(selected, on='sample_id', validate='many_to_one')
    keys = ['dataset_id', 'patient_id', 'ensembl_id']
    aggregate = {c: 'first' for c in selected.columns if c not in keys}
    aggregate['value_z'] = 'mean'
    return merged.groupby(keys, as_index=False, dropna=False).agg(aggregate)


def expression_directory(root=None):
    """Locate the explicitly named recovered core; otherwise use legacy full CSVs."""
    from pathlib import Path
    base = Path(root) if root is not None else Path.cwd()
    core = base / 'data/expression_analysis_core'
    return core if core.is_dir() else base / 'data/graph_full'
