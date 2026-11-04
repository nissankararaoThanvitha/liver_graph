"""Redraw final Paper 1 results as vector PDFs; never refit analyses.

Run from any directory: python scripts/export_corrected_figure_pdfs.py
Inputs are the promoted final CSVs and saved subgraph workbook. Historical
column names remain unchanged; display labels use disease-group association.
"""
from pathlib import Path
import hashlib
import json
import re
import textwrap
import zipfile
import argparse
from matplotlib.text import Text

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--main-only', action='store_true', help='Export only the nine manuscript panels')
args = parser.parse_args()
MAIN_NAMES = {'task1_venn', 'task1_shared_rho_scatter', 'task2_cluster_trajectories',
              'task2_heatmap', 'task2_choosing_k', 'task3_transition_comparison',
              'task4_heatmap_hallmark', '12_mechanistic_subgraph'}
ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'Paper1_Results'
HC = ROOT / 'Paper1_HighConfidence'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'pdf.fonttype': 42, 'ps.fonttype': 42})
INPUTS = list((RES / '00_progression_genes').glob('*.csv'))
INPUTS += list((RES / 'Task2').glob('*.csv'))
INPUTS += list((RES / 'Task3').glob('*.csv'))
INPUTS += [RES / 'Task4/task4_all_significant.csv',
           HC / '12_KG_supplementary.xlsx', HC / '11_final_tier1_genes.csv',
           HC / '11_FINAL_shortlist_25_genes.csv', ROOT / 'scripts/kg_subgraph.py']

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

before = {str(p.relative_to(ROOT)): digest(p) for p in INPUTS}
OUTPUTS = []

def save(fig, folder, name):
    if args.main_only and name not in MAIN_NAMES:
        plt.close(fig)
        return None
    # Increase source typography, then recompute spacing before vector export.
    # This changes presentation only: all plotted values and memberships are retained.
    fig.canvas.draw()
    for txt in fig.findobj(match=Text):
        scale = 1.8 if name == 'task4_heatmap_hallmark' else (1.6 if name in {'12_mechanistic_subgraph', 'task2_cluster_trajectories', 'task2_heatmap'} else 1.45)
        txt.set_fontsize(txt.get_fontsize() * scale)
    fig.tight_layout(pad=1.5)
    # Matplotlib otherwise rasterises dense colourbars automatically.
    for ax in fig.axes:
        for collection in ax.collections:
            collection.set_rasterized(False)
    out = folder / 'pdfs' / (name + '.pdf')
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches='tight', facecolor='white',
                metadata={'Title': name, 'Subject': 'Final combined results; display-only export'})
    OUTPUTS.append(out)
    plt.close(fig)
    return out

genes = pd.read_csv(RES / '00_progression_genes/genes_by_fibrosis_stage.csv')
cl = pd.read_csv(RES / 'Task2/task2_gene_clusters.csv')
sizes = pd.read_csv(RES / 'Task2/task2_cluster_sizes.csv')
ks = pd.read_csv(RES / 'Task2/task2_choosing_k.csv')
cnt = pd.read_csv(RES / 'Task3/task3_transition_summary.csv')
sig = pd.read_csv(RES / 'Task4/task4_all_significant.csv')
assert len(genes) == 6222 and len(cl) == 3845
assert sizes.n_genes.tolist() == [857, 1367, 226, 397, 998]
short = pd.read_csv(HC / '11_FINAL_shortlist_25_genes.csv')
tier = pd.read_csv(HC / '11_final_tier1_genes.csv')
assert len(short) == 23 and len(tier) == 447
names = sizes.set_index('cluster').cluster_name.to_dict()
# Keep the established descriptive cluster names and all saved assignments.
def wrap(s, width=32):
    return '\n'.join(textwrap.wrap(str(s), width=width, break_long_words=False))

# Task 1: same membership/counts and same across-gene correlation statistic.
fo = genes[genes.ladder.eq('fibrosis_only')]
do = genes[genes.ladder.eq('inflammation_only')]
shared = genes[genes.ladder.eq('both')]
fig, ax = plt.subplots(figsize=(8, 5.5))
for x, color in [(-.6, '#c0392b'), (.6, '#2471a3')]:
    ax.add_patch(Circle((x, 0), 1.3, alpha=.35, color=color))
for x, n in [(-1.15, len(fo)), (0, len(shared)), (1.15, len(do))]:
    ax.text(x, 0, f'{n:,}\n({100*n/len(genes):.1f}%)', ha='center', va='center', fontsize=12)
ax.text(-1.05, 1.5, f'Fibrosis-stage\nassociated\n(n={len(fo)+len(shared):,})', ha='center', fontsize=11)
ax.text(1.05, 1.5, f'Disease-group\nassociated\n(n={len(do)+len(shared):,})', ha='center', fontsize=11)
ax.set(xlim=(-2.3, 2.3), ylim=(-1.65, 2.1), aspect='equal')
ax.axis('off')
ax.set_title('6,222 genes associated with fibrosis stage\nor ordered disease group', fontsize=13)
save(fig, RES/'Task1', 'task1_venn')
rho, p = spearmanr(shared.fibrosis_rho, shared.inflammation_rho)
fig, ax = plt.subplots(figsize=(6.5, 6.5))
ax.scatter(shared.fibrosis_rho, shared.inflammation_rho, s=6, alpha=.5, color='#555')
ax.axhline(0, color='grey', lw=.8); ax.axvline(0, color='grey', lw=.8)
ax.set_xlabel('Median within-study Spearman ρ\nFibrosis stage (F0–F4)')
ax.set_ylabel('Median within-study Spearman ρ\nOrdered disease group (control → NAFL → NASH)')
ax.set_title(f'Shared genes (n={len(shared):,})\nAcross-gene Spearman ρ = {rho:.3f}, p = {p:.1e}')
fig.tight_layout()
save(fig, RES/'Task1', 'task1_shared_rho_scatter')

# Task 2: plot saved assignments and stored stage means, no re-clustering.
labels = ['F0', 'F1', 'F2', 'F3', 'F4']
raw = cl[labels].to_numpy()
X = (raw - raw.mean(axis=1, keepdims=True)) / raw.std(axis=1, keepdims=True)
fig, axes = plt.subplots(3, 2, figsize=(10, 11), sharey=True)
for k, ax in zip(range(1, 6), axes.ravel()):
    members = X[cl.cluster.eq(k)]
    ax.plot(range(5), members.T, color='grey', alpha=.05, lw=.6)
    ax.plot(range(5), members.mean(axis=0), color='#c0392b', lw=3)
    ax.set_title(f'C{k}: {wrap(names[k], 24)}\n(n={len(members):,})', fontsize=10)
    ax.set_xticks(range(5), labels)
    ax.axhline(0, color='black', lw=.5)
    ax.set_xlabel('Fibrosis stage')
axes.ravel()[-1].axis('off')
for ax in axes[:, 0]:
    ax.set_ylabel('Stage-profile z-score')
fig.tight_layout()
save(fig, RES/'Task2', 'task2_cluster_trajectories')
fig, ax = plt.subplots(figsize=(6.5, 10))
# pcolormesh exports individual heatmap cells as vector elements.
im = ax.pcolormesh(X, cmap='RdBu_r', vmin=-2, vmax=2, rasterized=False)
ax.invert_yaxis()
bounds = np.cumsum(sizes.n_genes)
for b in bounds[:-1]:
    ax.axhline(b, color='black', lw=1.2)
ax.set_yticks(bounds - sizes.n_genes/2,
              [f'C{c} (n={n:,})' for c, n in zip(sizes.cluster, sizes.n_genes)])
ax.set_xticks(np.arange(5)+.5, labels)
ax.set_xlabel('Fibrosis stage')
ax.set_title('3,845 fibrosis-associated genes across F0–F4')
fig.colorbar(im, ax=ax, fraction=.05, pad=.03, label='Stage-profile z-score (colour limits: −2 to 2)')
save(fig, RES/'Task2', 'task2_heatmap')
fig, axes = plt.subplots(2, 1, figsize=(8, 11))
axes[0].plot(ks.k, ks.silhouette, 'o-', color='#333')
axes[0].set_ylabel('Silhouette score')
axes[1].errorbar(ks.k, ks.stability_ARI_mean, yerr=ks.stability_ARI_sd,
                 fmt='o-', color='#333', capsize=3, label='80% gene subsamples')
axes[1].errorbar(ks.k+.08, ks.patient_bootstrap_ARI_mean,
                 yerr=ks.patient_bootstrap_ARI_sd, fmt='s--', color='#7d3c98',
                 capsize=3, label='Patient bootstrap')
axes[1].axhline(.95, color='#c0392b', ls='--', lw=1, label='Gene-subsample ARI = 0.95')
axes[1].set_ylabel('Adjusted Rand index\n(mean ± SD; 50 refits)')
axes[1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.32), fontsize=8)
for ax in axes:
    ax.axvline(5, color='#2471a3', lw=6, alpha=.2)
    ax.set_xlabel('Number of clusters, k')
fig.suptitle('Cluster-number assessment\nSelected k = 5 by gene-subsample stability rule')
fig.tight_layout()
save(fig, RES/'Task2', 'task2_choosing_k')
fig, ax = plt.subplots(figsize=(9, 5.5))
for _, r in sizes.iterrows():
    ax.plot(labels, [r['mean_'+l] for l in labels], 'o-', lw=2,
            label=f'C{r.cluster}: {r.cluster_name} (n={r.n_genes:,})')
ax.axhline(0, color='black', lw=.5)
ax.set(ylabel='Mean within-study-standardised expression (value_z)',
       xlabel='Fibrosis stage', title='Cluster-average stage profiles (before across-stage scaling)')
ax.legend(fontsize=8, loc='best')
fig.tight_layout()
save(fig, RES/'Task2', 'task2_cluster_means')

# Task 3: use the saved refit medians; quartiles were not retained on disk.
fig, axes = plt.subplots(3, 1, figsize=(9, 14))
x = np.arange(4)
axes[0].bar(x, cnt.n_substantial_up, color='#c0392b', label='Higher at later stage')
axes[0].bar(x, -cnt.n_substantial_down, color='#2471a3', label='Lower at later stage')
for j, r in cnt.iterrows():
    axes[0].text(j, r.n_substantial_up, str(int(r.n_substantial_up)), ha='center', va='bottom', fontsize=9)
    axes[0].text(j, -r.n_substantial_down, str(int(r.n_substantial_down)), ha='center', va='top', fontsize=9)
axes[0].axhline(0, color='black', lw=.6)
axes[0].set_title('Substantial adjacent-stage\ndifferences (full data)\nq < 0.05 and |β| ≥ 0.20', fontsize=11)
axes[0].set_ylabel('Gene count\n(lower counts drawn below zero)')
axes[0].legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.32))
axes[0].margins(y=.18)
axes[0].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{abs(v):.0f}'))
med = cnt.matched_n_substantial_median.to_numpy()
axes[1].bar(x, med, color='#7d3c98')
for j, v in enumerate(med):
    axes[1].text(j, v, f'{v:g}', ha='center', va='bottom', fontsize=9)
axes[1].set_title('Sample-size-matched refits\n30 patients/stage; fixed study mix\nMedian of 50 refits', fontsize=11)
axes[1].set_ylabel('Median substantial-gene count')
axes[1].set_ylim(0, max(med)*1.2)
axes[2].bar(x, cnt.median_abs_beta, color='#555')
axes[2].set_title('Median |study-adjusted β|\nAcross 3,845 fibrosis-associated genes', fontsize=11)
axes[2].set_ylabel('Absolute coefficient\n(within-study SD units)')
for j, v in enumerate(cnt.median_abs_beta):
    axes[2].text(j, v, f'{v:.3f}', ha='center', va='bottom', fontsize=9)
axes[2].margins(y=.18)
for ax in axes:
    ax.set_xticks(x, cnt.transition)
    ax.set_xlabel('Adjacent-stage comparison')
fig.tight_layout(w_pad=2)
save(fig, RES/'Task3', 'task3_transition_comparison')
res = pd.read_csv(RES/'Task3/task3_all_genes_all_transitions.csv')
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, col, title in [(axes[0], 'delta_mean', 'Difference between stage means'),
                       (axes[1], 'beta_adjusted', 'Study-adjusted stage coefficient (β)')]:
    ax.violinplot([res.loc[res.transition.eq(t), col].dropna() for t in cnt.transition], showmedians=True)
    ax.axhline(0, color='black', lw=.6)
    for v in [-.2, .2]:
        ax.axhline(v, color='#c0392b', lw=.8, ls='--')
    ax.set_xticks(range(1, 5), cnt.transition)
    ax.set_title(title)
    ax.set_xlabel('Adjacent-stage comparison')
axes[0].set_ylabel('Expression difference (within-study SD units)')
fig.suptitle('Adjacent-stage contrasts among 3,845 fibrosis-associated genes; dashed lines: ±0.20')
fig.tight_layout()
save(fig, RES/'Task3', 'task3_delta_distributions')

# Task 4: display-only transformation of stored enrichment q values.
main = ['fibrosis_only_up', 'fibrosis_only_down', 'inflammation_only_up',
        'inflammation_only_down', 'shared_up', 'shared_down'] + [f'C{k}_all' for k in range(1, 6)]
group_labels = {
    'fibrosis_only_up': 'Fibrosis-only: positive association',
    'fibrosis_only_down': 'Fibrosis-only: negative association',
    'inflammation_only_up': 'Disease-group-only: positive association',
    'inflammation_only_down': 'Disease-group-only: negative association',
    'shared_up': 'Shared: positive on both axes',
    'shared_down': 'Shared: negative on both axes',
}
for k in range(1, 6):
    group_labels[f'C{k}_all'] = f'C{k}: full cluster'
    group_labels[f'C{k}_core'] = f'C{k}: membership-confidence core (≥0.8)'

def pretty(term):
    # Preserve the complete biological term rather than truncating its meaning.
    return sig.set_index('term').term_label.to_dict().get(term, term)

for db in ['Hallmark', 'GO_BP', 'Reactome', 'KEGG']:
    d = sig[sig.database.eq(db) & sig.group.isin(main)]
    terms = d.term.unique() if db == 'Hallmark' else d.sort_values('p_value').groupby('group').head(5).term.unique()
    m = d[d.term.isin(terms)].pivot_table(index='term', columns='group', values='q_value').reindex(columns=main)
    m = -np.log10(m).fillna(0)
    m = m.loc[m.idxmax(axis=1).map(main.index).sort_values(kind='stable').index]
    term_labels = [wrap(pretty(t), 55) for t in m.index]
    nlines = sum(s.count('\n')+1 for s in term_labels)
    fig, ax = plt.subplots(figsize=(11, max(6, .32*nlines+3.5)))
    im = ax.pcolormesh(m.clip(upper=10).to_numpy(), cmap='Reds', vmin=0, vmax=10, rasterized=False)
    ax.invert_yaxis()
    ax.set_xticks(np.arange(len(main))+.5, [group_labels[g] for g in main], rotation=55, ha='right', fontsize=10)
    ax.set_yticks(np.arange(len(m))+.5, term_labels, fontsize=10)
    ax.axvline(6, color='black', lw=1.5)
    ax.set_title(f'{db.replace("GO_BP", "GO Biological Process")} over-representation across gene groups\n'
                 + ('All significant terms' if db == 'Hallmark' else 'Union of top five terms per group')
                 + '; BH q < 0.05', fontsize=12)
    fig.colorbar(im, ax=ax, label='−log₁₀(q), capped at 10; 0 = no significant result', fraction=.025, pad=.02)
    fig.tight_layout()
    save(fig, RES/'Task4', 'task4_heatmap_'+{'GO_BP':'go_bp','KEGG':'kegg','Hallmark':'hallmark','Reactome':'reactome'}[db])

f, i = genes.fibrosis_rho, genes.inflammation_rho
groups = {
    'fibrosis_only_up': set(genes.loc[genes.ladder.eq('fibrosis_only') & f.gt(0), 'symbol']),
    'fibrosis_only_down': set(genes.loc[genes.ladder.eq('fibrosis_only') & f.lt(0), 'symbol']),
    'inflammation_only_up': set(genes.loc[genes.ladder.eq('inflammation_only') & i.gt(0), 'symbol']),
    'inflammation_only_down': set(genes.loc[genes.ladder.eq('inflammation_only') & i.lt(0), 'symbol']),
    'shared_up': set(genes.loc[genes.ladder.eq('both') & f.gt(0) & i.gt(0), 'symbol']),
    'shared_down': set(genes.loc[genes.ladder.eq('both') & f.lt(0) & i.lt(0), 'symbol'])}
for k in range(1, 6):
    groups[f'C{k}_all'] = set(cl.loc[cl.cluster.eq(k), 'Gene'])
    groups[f'C{k}_core'] = set(cl.loc[cl.cluster.eq(k) & cl.membership_confidence.ge(.8), 'Gene'])
background = set(pd.read_csv(RES/'00_progression_genes/progression_fibrosis.csv').symbol.dropna())
for grp, members in groups.items():
    d = sig[sig.group.eq(grp)].sort_values('p_value').groupby('database').head(5)
    n = len(members & background)
    if d.empty:
        fig, ax = plt.subplots(figsize=(8, 2.5)); ax.axis('off')
        ax.text(.5, .7, group_labels[grp], ha='center', weight='bold')
        ax.text(.5, .35, f'Not tested: {n} genes; minimum 5 required.' if n < 5
                else 'No saved enriched terms at BH q < 0.05.', ha='center')
    else:
        d = d.assign(db=pd.Categorical(d.database, ['GO_BP','KEGG','Reactome','Hallmark'], ordered=True))
        d = d.sort_values(['db','gene_ratio'], ascending=[False,True])
        lab = [wrap(f'{t} [{db}]', 65) for t,db in zip(d.term_label,d.database)]
        fig, ax = plt.subplots(figsize=(12, max(5,.36*sum(s.count('\n')+1 for s in lab)+2)))
        sc = ax.scatter(d.gene_ratio, np.arange(len(d)), s=d.overlap*6+10,
                        c=-np.log10(d.q_value), cmap='viridis', edgecolor='black', linewidth=.4)
        ax.set_yticks(np.arange(len(d)), lab, fontsize=8)
        ax.set_xlabel('Overlap genes / genes in the tested group')
        fig.colorbar(sc, ax=ax, label='−log₁₀(BH q)', fraction=.03, pad=.02)
        for nv in [5,20,50]:
            ax.scatter([],[],s=nv*6+10,color='grey',label=f'{nv} genes')
        ax.legend(loc='lower right',fontsize=7,title='Overlap',title_fontsize=8)
        ax.margins(x=.15, y=.06)
    ax.set_title(f'{group_labels[grp]} (n={n:,})\nTop five terms per collection; BH q < 0.05', fontsize=11)
    fig.tight_layout()
    save(fig, RES/'Task4', f'dot_{grp}')

# Network: consume the saved 154 edges; reuse the original rendering routine
# only, avoiding its upstream enrichment/selection calculations and workbook writes.
wb = HC/'12_KG_supplementary.xlsx'
fe = pd.read_excel(wb, sheet_name='4_figure_edges')
fn = pd.read_excel(wb, sheet_name='5_figure_nodes')
rank = pd.read_excel(wb, sheet_name='3_all_mechanisms_ranked')
major = rank[rank.selected_for_figure].copy()
chosen = major.Mechanism_ID.tolist()
fig_edges = fe.rename(columns={'Ensembl_ID':'from_id','Mechanism_ID':'to_id','In_final_25':'in_shortlist_25'})
assert len(fe) == 154 and fe.Ensembl_ID.nunique() == 42 and len(chosen) == 12
short_ids = set(short.Ensembl_ID)
n_short_in_fig = len(set(fe.Ensembl_ID) & short_ids)
assert n_short_in_fig == 4
meta = tier.set_index('Ensembl_ID')
name_of = fn.set_index('ID').Node.to_dict()
type_of = fn.set_index('ID').Kind.to_dict()
# Portrait graph layout: same 42 genes, 12 annotations and 154 edges.
# Two gene columns flank an annotation column; geometry is display-only.
G = nx.Graph()
for n in chosen:
    G.add_node(n)
for row in fig_edges.itertuples():
    G.add_edge(row.from_id, row.to_id)
gene_ids = sorted(set(fe.Ensembl_ID), key=lambda n: str(meta.Gene.get(n, n)))
left, right = gene_ids[:21], gene_ids[21:]
pos = {}
for column, xx in [(left, .16), (right, .84)]:
    for n, yy in zip(column, np.linspace(.96, .04, len(column))):
        pos[n] = (xx, yy)
for n, yy in zip(chosen, np.linspace(.94, .06, len(chosen))):
    pos[n] = (.5, yy)
fig, ax = plt.subplots(figsize=(10, 14))
for u, v in G.edges:
    ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
            color='#c2c8ce', lw=.65, alpha=.65, zorder=1)
for column, direction in [(left, -1), (right, 1)]:
    for n in column:
        shortlisted = n in short_ids
        color = '#e8743b' if shortlisted else '#8c99a6'
        size = 200 if shortlisted else 35 * G.degree(n)
        xx, yy = pos[n]
        ax.scatter([xx], [yy], s=size, c=color, edgecolors='#4a535d', linewidths=.7, zorder=3)
        ax.text(xx + direction*.035, yy, meta.Gene.get(n, ''),
                ha='right' if direction < 0 else 'left', va='center',
                fontsize=9, weight='bold', color='#7d3517' if shortlisted else '#202832', zorder=5)
for n in chosen:
    xx, yy = pos[n]
    color = '#2e6e9e' if type_of[n] == 'Pathway' else '#4a9a6f'
    ax.text(xx, yy, wrap(name_of[n], 22), ha='center', va='center', fontsize=9,
            weight='bold', color=color, zorder=6,
            bbox=dict(boxstyle='round,pad=.35', facecolor='white', edgecolor=color, linewidth=1.1))
ax.set(xlim=(-.02, 1.02), ylim=(-.10, 1.05))
ax.set_title('Tier-1 genes and selected biological annotations\n42 genes | 12 annotations | 154 connections', fontsize=13, pad=16)
ax.legend(handles=[
    mpatches.Patch(color='#2e6e9e', label='Pathway (Reactome)'),
    mpatches.Patch(color='#4a9a6f', label='Biological process (GO)'),
    mpatches.Patch(color='#e8743b', label='Shortlisted genes shown (4/23)'),
    mpatches.Patch(color='#8c99a6', label='Other Tier-1 genes\n(size = annotations reached: 3-6)'),
], loc='lower center', bbox_to_anchor=(.5, -.04), ncol=2, frameon=False, fontsize=8)
ax.axis('off')
fig.tight_layout()
save(fig, HC, '12_mechanistic_subgraph')

# Workflow is maintained as an independently reproducible vector drawing.
import runpy
runpy.run_path(str(ROOT / 'scripts/render_manuscript_workflow.py'), run_name='__main__')
OUTPUTS.append(RES / 'Figure1/pdfs/manuscript_v3_pipeline.pdf')

assert before == {str(p.relative_to(ROOT)): digest(p) for p in INPUTS}, 'Source files changed'
manifest = {
    'description': 'Display-only vector redraw from promoted final combined results',
    'input_sha256': before,
    'outputs': [str(p.relative_to(ROOT)) for p in OUTPUTS],
    'analysis_rerun': False,
    'display_font_scale': {'default': 1.45, 'clusters_heatmap_network': 1.6, 'hallmark': 1.8},
    'main_panels_only': args.main_only,
    'notes': [
        'No statistical models, clustering, gene selection, enrichment or graph selection were rerun.',
        'Spearman agreement annotation is recomputed from saved rho columns only, as in the original plotting script.',
        'Cluster curves are arithmetic means of saved row-standardised profiles; assignments are unchanged.',
        'Matched-refit quartiles were not saved; median bars intentionally have no IQR error bars.',
        'Existing cluster names, including C3 Early rise then plateau, are preserved as descriptive labels.',
        'The network edge set is identical; a portrait three-column layout is used.',
        'Historical inflammation column names and filenames remain for data compatibility; figure wording is corrected.',
        'Workflow is recreated as vector shapes, keeping the simplified abstract labels and ending at biological network interpretation.'
    ]}
bundle = ROOT/'handover_exports/large_label_vector_figures_2026-10-26'
bundle.mkdir(parents=True,exist_ok=True)
(bundle/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
readme = """# Larger-label vector manuscript figures

These nine panels were regenerated from the final combined analysis tables,
with labels increased by 45-80% in the Matplotlib sources. Plot spacing was
recomputed; the workflow uses fitted larger text. All data, memberships and
statistical results are unchanged. No analysis or graph-selection procedure
was rerun. The manifest records input hashes.

Figure 1: manuscript_v3_pipeline.pdf
Figure 2: task1_venn.pdf; task1_shared_rho_scatter.pdf
Figure 3: task2_cluster_trajectories.pdf; task2_heatmap.pdf; task2_choosing_k.pdf
Figure 4: task3_transition_comparison.pdf; task4_heatmap_hallmark.pdf
Figure 5: 12_mechanistic_subgraph.pdf

Dense composites are displayed on separate portrait continued-figure pages in the
updated manuscript. Upload the nine PDFs using their existing basenames.
The ZIP retains the project-relative paths for local use.
"""
(bundle/'README.md').write_text(readme)
zip_path = ROOT/'handover_exports/large_label_vector_figures_2026-10-26.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for out in OUTPUTS:
        z.write(out,out.relative_to(ROOT))
    for p in [bundle/'figure_manifest.json',bundle/'README.md',Path(__file__).resolve()]:
        z.write(p,p.relative_to(ROOT))
print(f'Exported {len(OUTPUTS)} PDFs. Source hashes unchanged. ZIP: {zip_path}')
