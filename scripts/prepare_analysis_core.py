"""Recover analysis-format expression inputs from a verified graph-release ZIP.

Streams the ZIP's gzipped CSVs without loading the graph or changing results.
Keep the ZIP outside the repository; verify its published checksum first.
Requires every eligible gene/sample pair exactly once, including measured
zeros. Writes a NEW directory atomically; never overwrites an existing core.
This recovers deposited graph values, not a new raw-data reprocessing run.
"""
import argparse
import csv
import gzip
import io
import json
import math
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def records(z, name):
    with z.open(name) as raw, gzip.GzipFile(fileobj=raw) as gz, io.TextIOWrapper(gz, encoding='utf-8-sig', newline='') as text:
        yield from csv.DictReader(text)


def named(row):
    return {k.split(':', 1)[0]: v for k, v in row.items() if not k.startswith(':')}


def prepare_annotations(archive, out):
    """Recover only original Reactome/GO annotations; exclude graph additions."""
    if out.exists():
        raise ValueError(f'{out} already exists; choose a new output directory.')
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=out.name + '.partial-', dir=out.parent))
    specs = [
        ('nodes/Pathway__Reactome.csv.gz', 'nodes_pathway.csv', 'Pathway'),
        ('nodes/BioProcess.csv.gz', 'nodes_bioprocess.csv', 'BioProcess'),
        ('relationships/IN_PATHWAY__Gene__Pathway__Reactome.csv.gz', 'edges_pathway_gene.csv', 'Pathway'),
        ('relationships/INVOLVED_IN__Gene__BioProcess.csv.gz', 'edges_biological_process_gene.csv', 'BioProcess'),
    ]
    try:
        counts = {}
        with zipfile.ZipFile(archive) as z:
            for source, target, label in specs:
                is_node = source.startswith('nodes/')
                fields = ['node_id', 'name'] if is_node else ['from_id', 'to_id']
                with (temp / target).open('w', newline='', encoding='utf-8') as f:
                    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
                    n = 0
                    for row in records(z, source):
                        r = named(row)
                        w.writerow({k: r[k] for k in fields} if is_node else {
                            'from_id': row[':START_ID(Gene)'], 'to_id': row[f':END_ID({label})']})
                        n += 1
                    if not n:
                        raise ValueError(f'Empty original annotation file: {source}')
                    counts[target] = n
        if out.exists():
            raise ValueError('Output appeared during preparation.')
        os.rename(temp, out)
        return counts
    except BaseException:
        shutil.rmtree(temp)
        raise


def prepare(archive, out, background, clinical):
    if out.exists():
        raise ValueError(f'{out} already exists; choose a new output directory.')
    with background.open(encoding='utf-8-sig', newline='') as f:
        ids = [r['ensembl_id'] for r in csv.DictReader(f)]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Background must contain unique eligible Ensembl IDs.')
    genes = {g: i for i, g in enumerate(ids)}
    with clinical.open(encoding='utf-8-sig', newline='') as f:
        meta = list(csv.DictReader(f))
    samples = {r['sample_id']: r['dataset_id'] for r in meta}
    if len(samples) != len(meta) or not samples:
        raise ValueError('Clinical input must contain unique sample IDs.')
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=out.name + '.partial-', dir=out.parent))
    handles = {}
    try:
        with zipfile.ZipFile(archive) as z:
            files = z.namelist()
            gene_files = [n for n in files if n.startswith('nodes/Gene') and n.endswith('.csv.gz')]
            sample_files = [n for n in files if n.startswith('nodes/Sample') and n.endswith('.csv.gz')]
            expr_files = [n for n in files if n.startswith('relationships/EXPRESSES__Sample__Gene') and n.endswith('.csv.gz')]
            if not gene_files or not sample_files or not expr_files:
                raise ValueError('Not an export_graph.py release ZIP: required CSVs missing.')
            released_samples = set()
            for n in sample_files:
                for row in records(z, n):
                    r = named(row)
                    sid = r['sample_id']
                    if sid in released_samples or samples.get(sid) != r.get('dataset_id'):
                        raise ValueError('Release/clinical sample IDs or dataset assignments disagree.')
                    released_samples.add(sid)
            if released_samples != set(samples):
                raise ValueError('Release/clinical sample sets differ.')
            found = set()
            with (temp / 'nodes_gene.csv').open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['ensembl_id', 'symbol', 'n_datasets'])
                writer.writeheader()
                for n in gene_files:
                    for row in records(z, n):
                        r = named(row); gid = r['ensembl_id']
                        if gid not in genes:
                            continue
                        if gid in found or r.get('n_datasets') != '8':
                            raise ValueError('Eligible gene duplicated or not measured in all eight studies.')
                        found.add(gid)
                        writer.writerow({k: r.get(k, '') for k in writer.fieldnames})
            if found != set(genes):
                raise ValueError('Eligible genes missing from release.')
            writers, counts = {}, {}
            for ds in sorted(set(samples.values())):
                f = (temp / f'edges_{ds}.csv').open('w', newline='', encoding='utf-8')
                handles[ds] = f
                w = csv.writer(f); w.writerow(['sample_id', 'ensembl_id', 'value_raw', 'value_log', 'value_z'])
                writers[ds] = w; counts[ds] = 0
            seen = {sid: bytearray(len(genes)) for sid in samples}
            for n in expr_files:
                for row in records(z, n):
                    sid = row.get(':START_ID(Sample)'); gid = row.get(':END_ID(Gene)')
                    if sid not in samples:
                        raise ValueError('Unknown expression sample in release.')
                    if gid not in genes:
                        continue
                    i = genes[gid]
                    if seen[sid][i]:
                        raise ValueError(f'Duplicate eligible expression pair: {sid}, {gid}')
                    r = named(row)
                    if not math.isfinite(float(r['value_z'])):
                        raise ValueError('Eligible expression value_z must be finite.')
                    seen[sid][i] = 1
                    ds = samples[sid]
                    writers[ds].writerow([sid, gid, r.get('value_raw', ''), r.get('value_log', ''), r['value_z']])
                    counts[ds] += 1
            if any(sum(bits) != len(genes) for bits in seen.values()):
                raise ValueError('Incomplete eligible gene/sample matrix; output not promoted.')
        for f in handles.values():
            f.close()
        manifest = {'source_archive': archive.name, 'eligible_genes': len(genes), 'samples': len(samples),
                    'expression_rows': sum(counts.values()), 'rows_per_study': counts,
                    'every_eligible_pair_once': True, 'scope': 'analysis core only; not a full graph reload'}
        (temp / 'recovery_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # Refuse replacement even if another process created the destination.
        if out.exists():
            raise ValueError('Output appeared during preparation; refusing to replace it.')
        os.rename(temp, out)
        return manifest
    except BaseException:
        for f in handles.values():
            f.close()
        shutil.rmtree(temp)
        raise


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--out', type=Path, help='new output folder; default depends on mode')
    ap.add_argument('--annotations-only', action='store_true', help='recover original Reactome/GO layer instead of expression')
    ap.add_argument('--background', type=Path, default=ROOT / 'data/progression_full/progression_fibrosis.csv')
    ap.add_argument('--clinical', type=Path, default=ROOT / 'data/graph/nodes_sample_clinical.csv')
    args = ap.parse_args()
    if args.annotations_only:
        result = prepare_annotations(args.archive, args.out or ROOT / 'data/graph_okg')
    else:
        result = prepare(args.archive, args.out or ROOT / 'data/expression_analysis_core', args.background, args.clinical)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
