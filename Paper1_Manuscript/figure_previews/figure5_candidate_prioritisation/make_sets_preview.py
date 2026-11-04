import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch
root=Path('/home/nikitha07/Projects/liver_graph/Paper1_Manuscript/figure_previews/figure5_candidate_prioritisation')
rows=list(csv.DictReader(open('/home/nikitha07/Projects/liver_graph/Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv')))
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(12,8.6));fig.patch.set_facecolor('white');ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');fig.subplots_adjust(0,0,1,1)
ink='#253C49';gray='#61717C'
colors={'F0→F1':'#257AA6','F1→F2':'#AE7410','F2→F3':'#287B50','F3→F4':'#92559F'}
ax.text(.5,.956,'23 prioritised genes across five distinct clusters',ha='center',fontsize=21,weight='bold',color=ink)
ax.text(.5,.920,'Selected from 447 Tier 1 genes • up to five per cluster',ha='center',fontsize=12,color=gray)
centers=[(.18,.684),(.5,.684),(.82,.684),(.34,.305),(.66,.305)]
patterns=['Early increase','Late increase','Early rise / plateau','Mid-stage decrease','Late decrease'];tiers=[93,262,7,3,82]
for j,(cx,cy) in enumerate(centers):
 group=[r for r in rows if r['Cluster']==f'C{j+1}']
 ax.add_patch(Ellipse((cx,cy),.300,.350,facecolor='#F4F7F9',edgecolor='#7E929F',linewidth=1.7))
 ax.text(cx,cy+.126,f'C{j+1}',ha='center',fontsize=17,weight='bold',color=ink)
 ax.text(cx,cy+.096,patterns[j],ha='center',fontsize=10.5,color=gray)
 ax.text(cx,cy+.070,f'{len(group)} selected / {tiers[j]} Tier 1',ha='center',fontsize=10,color=gray)
 for k,r in enumerate(group):
  y=cy+.030-k*.033
  if len(group)==3:y=cy+.010-k*.041
  col=colors[r['Largest_transition']]
  ax.text(cx-.014,y,r['Gene'],ha='right',va='center',fontsize=12.5,style='italic',weight='bold',color=col)
  ax.text(cx+.008,y,r['Largest_transition'].replace('→','–'),ha='left',va='center',fontsize=10.5,color=col)
# Legend is a stage-comparison key, not a cluster colour key.
ax.text(.10,.885,'Strongest stage contrast:',ha='left',va='center',fontsize=10.5,color=gray)
for i,(label,col) in enumerate(colors.items()):
 x=.43+i*.14
 ax.scatter([x],[.885],s=60,color=col)
 ax.text(x+.014,.885,label.replace('→','–'),va='center',fontsize=10.5,color=col)
ax.text(.5,.096,'Internal robustness across all five leave-one-study-out refits',ha='center',fontsize=11.5,weight='bold',color=ink)
ax.text(.5,.064,'23/23 retained significance     •     18/23 retained |median ρ| ≥ 0.30',ha='center',fontsize=11,color=gray)
ax.text(.5,.025,'Disjoint clusters; only shortlisted genes are shown. Stage contrasts represent cross-sectional differences.',ha='center',fontsize=9,color=gray)
fig.savefig(root/'figure5_candidate_sets_preview.png',dpi=220,bbox_inches='tight',pad_inches=.1)
fig.savefig(root/'figure5_candidate_sets_preview.svg',bbox_inches='tight',pad_inches=.1)
