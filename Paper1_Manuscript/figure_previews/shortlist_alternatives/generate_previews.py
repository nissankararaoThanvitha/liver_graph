from pathlib import Path
import re,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.lines import Line2D
root=Path(__file__).resolve().parent
source=Path(__file__).resolve().parents[2]/'live_manuscript/main.tex'
s=source.read_text();t=s[s.index('\\caption{Final 23-gene shortlist}'):];t=t[:t.index('\\end{longtable}')]
rows=[]
for line in t.splitlines():
 if re.match(r'^\w+ & C[1-5] &',line):
  fields=[x.strip() for x in line.split('&')];pair=re.findall(r'F[0-4]',fields[6]);rows.append(dict(gene=fields[0],cluster=fields[1],score=int(fields[2]),rho=float(fields[3]),confidence=float(fields[4]),denominator=int(fields[5]),contrast='–'.join(pair)))
assert len(rows)==23
(root/'plotted_data.json').write_text(json.dumps(rows,indent=2))
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':11,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
clusters=['C1','C2','C3','C4','C5'];cc=['#326A9E','#B56A27','#55834A','#885BA1','#AC4D67'];pairs=['F0–F1','F1–F2','F2–F3','F3–F4'];pc=['#007F86','#A87513','#7161A8','#CB4F43']
colors=dict(zip(pairs,pc))
def save(fig,name):
 for ext in ['png','pdf','svg']:fig.savefig(root/f'{name}.{ext}',dpi=210,bbox_inches='tight',facecolor='white')
 plt.close(fig)
# Diagram of disjoint candidate groups. Colour represents selected contrast, not causality.
fig,ax=plt.subplots(figsize=(10.5,6.7));ax.set(xlim=(0,10.5),ylim=(0,7));ax.axis('off')
positions=[(1.85,4.85),(5.25,4.85),(8.65,4.85),(3.55,1.95),(6.95,1.95)]
for c,(x,y),edge in zip(clusters,positions,cc):
 group=[r for r in rows if r['cluster']==c]
 ax.add_patch(Ellipse((x,y),3.1,2.65,facecolor=edge+'0F',edgecolor=edge,lw=1.8))
 ax.text(x,y+0.92,f'{c} · {len(group)} candidates',ha='center',va='center',fontsize=13,fontweight='bold',color=edge)
 for i,r in enumerate(group): ax.text(x,y+0.48-i*0.34,r['gene'],ha='center',va='center',fontsize=12.5,color=colors[r['contrast']],fontweight='bold')
fig.suptitle('Candidate genes grouped by expression pattern',fontsize=17,y=.99)
handles=[Line2D([0],[0],marker='s',lw=0,color=col,markersize=9,label=p) for p,col in zip(pairs,pc)]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,-.015),ncol=4,frameon=False,title='Strongest adjacent-stage contrast')
fig.subplots_adjust(bottom=.09,top=.92)
save(fig,'01_cluster_groups')
# Contrast matrix plus score and confidence, each in its own scale.
fig=plt.figure(figsize=(10.7,9));gs=fig.add_gridspec(1,4,width_ratios=[3.6,1.2,1.5,1.5],wspace=.17,left=.16,right=.96,top=.87,bottom=.12)
axes=[fig.add_subplot(gs[0,j]) for j in range(4)];n=len(rows)
for ax in axes:ax.set_ylim(n-.5,-.5);ax.set_yticks(range(n));ax.tick_params(axis='both',length=0)
mat=np.ones((n,4,4));mat[:]=matplotlib.colors.to_rgba('#F0F1F2')
for i,r in enumerate(rows):mat[i,pairs.index(r['contrast'])]=matplotlib.colors.to_rgba(colors[r['contrast']])
axes[0].imshow(mat,aspect='auto');axes[0].set_xticks(range(4),pairs);axes[0].set_yticklabels([r['gene'] for r in rows]);axes[0].set_title('Strongest contrast',pad=15,fontweight='bold')
for j,(field,title,lo,hi,cmap) in enumerate([('score','Score / 9',7,9,'Blues'),('rho','Median ρ',-.55,.55,'RdBu_r'),('confidence','Membership\nconfidence',0,1,'Greens')],1):
 vals=np.array([r[field] for r in rows]);axes[j].imshow(vals[:,None],aspect='auto',vmin=lo,vmax=hi,cmap=cmap);axes[j].set_xticks([]);axes[j].set_yticklabels([]);axes[j].set_title(title,pad=15,fontweight='bold')
 for i,v in enumerate(vals):
  txt=str(int(v)) if field=='score' else f'{v:.2f}'
  rgba=plt.get_cmap(cmap)((v-lo)/(hi-lo));bright=.299*rgba[0]+.587*rgba[1]+.114*rgba[2]
  axes[j].text(0,i,txt,ha='center',va='center',fontsize=10,color='white' if bright<.55 else '#172127')
for ax in axes:
 ax.set_yticks(np.arange(-.5,n,1),minor=True);ax.grid(which='minor',axis='y',color='white',lw=1.4);ax.tick_params(which='minor',length=0)
 for z in [4.5,9.5,14.5,17.5]:ax.axhline(z,color='#555',lw=1.2)
 for spine in ax.spines.values():spine.set_visible(False)
for c,idx in zip(clusters,[2,7,12,16,20]):axes[0].text(-1.9,idx,c,ha='center',va='center',color=cc[clusters.index(c)],fontweight='bold',clip_on=False)
fig.suptitle('Candidate evidence profiles',fontsize=17,y=.97)
fig.text(.53,.035,'Coloured cells mark the largest absolute full-data adjacent-stage coefficient.\nρ: median fibrosis correlation; confidence: conditional bootstrap membership.',ha='center',fontsize=10)
save(fig,'02_evidence_matrix')
# Dot plot showing two measured features without conflating their scales.
sortedrows=sorted(rows,key=lambda r:(-r['score'],-abs(r['rho'])))
fig,(ax,ac)=plt.subplots(1,2,figsize=(10.5,9),gridspec_kw={'width_ratios':[3,1.6]},sharey=True)
y=np.arange(n)
for i,r in enumerate(sortedrows):
 col=cc[clusters.index(r['cluster'])]
 ax.plot([0,r['rho']],[i,i],color=col,alpha=.35,lw=1.5);ax.scatter(r['rho'],i,s={7:65,8:105,9:155}[r['score']],color=col,edgecolor='white',lw=.7,zorder=3)
 ac.scatter(r['confidence'],i,s=60,color=col,zorder=3)
ax.axvline(0,color='#aaa',lw=.8);ax.set_yticks(y,[r['gene'] for r in sortedrows]);ax.set_ylim(n-.5,-.8);ax.set_xlim(-.59,.63);ax.set_xlabel('Median fibrosis correlation (ρ)');ax.set_title('Association and prioritisation',pad=16,fontweight='bold')
ac.set_xlim(0,1.05);ac.set_xticks([0,.5,1]);ac.set_xlabel('Membership confidence');ac.set_title('Cluster assignment',pad=16,fontweight='bold');ac.axvline(.8,color='#aaa',ls='--',lw=1)
for z in (ax,ac):z.grid(axis='x',color='#e6e6e6');z.set_axisbelow(True);z.tick_params(axis='y',length=0)
clusterhandles=[Line2D([0],[0],marker='o',lw=0,color=c,label=k,markersize=7) for k,c in zip(clusters,cc)]
scorehandles=[Line2D([0],[0],marker='o',lw=0,color='#666',markersize=np.sqrt(sz),label=str(sc)) for sc,sz in [(7,65),(8,105),(9,155)]]
fig.legend(handles=clusterhandles,loc='lower center',bbox_to_anchor=(.4,.045),ncol=5,frameon=False,title='Expression cluster')
fig.legend(handles=scorehandles,loc='lower center',bbox_to_anchor=(.84,.045),ncol=3,frameon=False,title='Score / 9')
fig.suptitle('Ranked candidate evidence',fontsize=17,y=.98)
fig.subplots_adjust(left=.16,right=.97,top=.9,bottom=.19,wspace=.2)
fig.text(.56,.015,'Ranked by score, then |ρ|. Dashed line: confidence-core threshold (0.8).',ha='center',fontsize=10)
save(fig,'03_ranked_dotplot')
(root/'README.md').write_text('Three figure previews derived from the current 23-gene manuscript table. No analyses rerun and no manuscript assets replaced. PNG previews and editable vector SVG/PDF exports are provided. Exact source values: plotted_data.json. The matrix rounds displayed correlations to two decimal places; JSON preserves input precision. Contrast colours represent the largest absolute full-data coefficient, not gene movement or causal effects. Membership confidence is conditional on assessable bootstrap refits; varying denominators are retained in the data file and complete table.\n')
print('Generated three PNG, PDF and SVG previews from 23 table rows.')
