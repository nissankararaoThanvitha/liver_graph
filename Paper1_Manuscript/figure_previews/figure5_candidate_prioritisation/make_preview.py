import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[2] / 'Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv'
# Resolve from the repository rather than from the historical filename's claimed size.
SOURCE = Path('/home/nikitha07/Projects/liver_graph/Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv')
rows = list(csv.DictReader(SOURCE.open()))
assert len(rows) == 23
assert sum(int(r['LOSO_still_significant_of_5']) == 5 for r in rows) == 23
assert sum(int(r['LOSO_still_strong_rho0.30_of_5']) == 5 for r in rows) == 18
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','font.size':11})
fig = plt.figure(figsize=(13.2, 8.1), facecolor='white')
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
ink='#243643'; gray='#596873'
colors={'F0→F1':'#277DA8','F1→F2':'#C68A12','F2→F3':'#337D57','F3→F4':'#925A9C'}
patterns=['Early increase','Late increase','Early rise / plateau','Mid-stage decrease','Late decrease']
tier=[93,262,7,3,82]
ax.text(.035,.958,'Candidate prioritisation across fibrosis-stage patterns',fontsize=21,weight='bold',color=ink)
ax.text(.035,.920,'447 Tier 1 genes  •  up to five candidates per cluster  •  23 shortlisted genes',fontsize=12,color=gray)
ax.text(.035,.870,'A',fontsize=17,weight='bold',color=ink)
ax.text(.062,.870,'Cluster membership and strongest adjacent-stage contrast',fontsize=13,weight='bold',color=ink)
for i,(key,col) in enumerate(colors.items()):
    x=.20+i*.18
    ax.add_patch(Rectangle((x,.825),.012,.014,facecolor=col,edgecolor='none'))
    ax.text(x+.019,.832,key.replace('→','–'),va='center',color=gray,fontsize=11)

left=.035; width=.178; gap=.010
for j in range(5):
    cluster=f'C{j+1}'; x=left+j*(width+gap)
    group=[r for r in rows if r['Cluster']==cluster]
    ax.add_patch(FancyBboxPatch((x,.275),width,.515,boxstyle='round,pad=0.006,rounding_size=0.009',facecolor='#F5F7F9',edgecolor='#DCE2E6',linewidth=1))
    ax.text(x+width/2,.758,cluster,ha='center',fontsize=16,weight='bold',color=ink)
    ax.text(x+width/2,.728,patterns[j],ha='center',fontsize=10,color=gray)
    ax.text(x+width/2,.702,f'{tier[j]} Tier 1  |  {len(group)} selected',ha='center',fontsize=10,color=gray)
    for k,r in enumerate(group):
        y=.624-k*.073
        color=colors[r['Largest_transition']]
        ax.add_patch(FancyBboxPatch((x+.009,y-.017),width-.018,.059,boxstyle='round,pad=0.002,rounding_size=0.004',facecolor='white',edgecolor='#E3E7EA',linewidth=.6))
        ax.add_patch(Rectangle((x+.009,y-.017),.004,.059,color=color,linewidth=0))
        ax.text(x+.021,y+.020,r['Gene'],fontsize=13,weight='bold',color=ink,va='center')
        contrast=r['Largest_transition'].replace('→','–')
        beta=float(r['Transition_beta'])
        ax.text(x+.021,y-.003,f'{contrast}   β = {beta:+.2f}',fontsize=10,color=color,va='center')
    if j==3:
        ax.text(x+width/2,.337,'Three genes meet\nthe Tier 1 threshold',ha='center',va='center',fontsize=10,color=gray,linespacing=1.5)
ax.text(.035,.234,'β: study-adjusted expression difference (higher stage − lower stage); within-study SD units.',fontsize=10,color=gray)
ax.text(.035,.183,'B',fontsize=17,weight='bold',color=ink)
ax.text(.062,.183,'Internal robustness across all five leave-one-study-out refits',fontsize=13,weight='bold',color=ink)
for y, label,n,color in [(.128,'Retained statistical significance',23,'#337D57'),(.079,'Retained |median ρ| ≥ 0.30',18,'#277DA8')]:
    ax.text(.062,y,label,fontsize=11,color=ink,va='center')
    ax.add_patch(FancyBboxPatch((.42,y-.010),.39,.020,boxstyle='round,pad=0,rounding_size=.004',facecolor='#E9EDF0',edgecolor='none'))
    ax.add_patch(FancyBboxPatch((.42,y-.010),.39*n/23,.020,boxstyle='round,pad=0,rounding_size=.004',facecolor=color,edgecolor='none'))
    ax.text(.833,y,f'{n}/23 genes',fontsize=12,weight='bold',color=ink,va='center')
ax.text(.035,.028,'Cross-sectional stage associations; the selected contrast need not match the cluster-average pattern. No independent validation.',fontsize=9,color=gray)
fig.savefig(ROOT/'figure5_candidate_prioritisation_preview.png',dpi=220,facecolor='white',bbox_inches='tight',pad_inches=.08)
fig.savefig(ROOT/'figure5_candidate_prioritisation_preview.svg',facecolor='white',bbox_inches='tight',pad_inches=.08)
(ROOT/'caption.txt').write_text('Candidate prioritisation across fibrosis-stage patterns. (A) The 23 shortlisted genes grouped by their five expression-pattern clusters. Colours identify the adjacent-stage comparison with the largest absolute full-data study-adjusted coefficient; labels show signed coefficients in within-study standard-deviation units. These contrasts describe cross-sectional stage differences, not within-person progression. (B) Numbers of shortlisted genes retaining statistical significance or an absolute median correlation of at least 0.30 across all five leave-one-study-out refits. These are internal robustness assessments, not independent validation. Source: Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv; all 23 rows were used.')
print(ROOT/'figure5_candidate_prioritisation_preview.png')
