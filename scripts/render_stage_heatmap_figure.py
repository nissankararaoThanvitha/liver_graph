from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
cl = pd.read_csv(ROOT/'Paper1_Results/Task2/task2_gene_clusters.csv')
sizes = pd.read_csv(ROOT/'Paper1_Results/Task2/task2_cluster_sizes.csv')
raw = cl[['F0','F1','F2','F3','F4']].to_numpy()
X = (raw-raw.mean(axis=1,keepdims=True))/raw.std(axis=1,keepdims=True)
assert len(cl)==3845
assert sizes.n_genes.tolist()==[857,1367,226,397,998]
plt.rcParams.update({'font.family':'Liberation Serif','font.size':12,'axes.labelsize':13,'xtick.labelsize':12,'ytick.labelsize':12,'axes.linewidth':.6,'pdf.fonttype':42,'savefig.facecolor':'white'})
fig=plt.figure(figsize=(6.5,8.6))
ax=fig.add_axes([.24,.12,.52,.76])
cax=fig.add_axes([.82,.32,.027,.36])
im=ax.pcolormesh(X,cmap='RdBu_r',vmin=-2,vmax=2,rasterized=False)
ax.invert_yaxis()
bounds=np.cumsum(sizes.n_genes)
for b in bounds[:-1]: ax.axhline(b,color='white',lw=1.2)
ax.set_yticks(bounds-sizes.n_genes/2,[f'C{c} (n = {n:,})' for c,n in zip(sizes.cluster,sizes.n_genes)])
ax.set_xticks(np.arange(5)+.5,['F0','F1','F2','F3','F4'])
ax.tick_params(axis='y',length=0,pad=12)
ax.tick_params(axis='x',length=0,pad=9)
ax.set_xlabel('Fibrosis stage',labelpad=12)
ax.set_title('Fibrosis-stage expression patterns',fontsize=15,pad=24)
cb=fig.colorbar(im,cax=cax,ticks=[-2,-1,0,1,2])
cb.solids.set_rasterized(False)
cb.solids.set_edgecolor("face")
cb.ax.tick_params(pad=7,length=3)
cb.set_label('Stage-profile z-score',labelpad=17)
cb.outline.set_linewidth(.6)
fig.text(.50,.035,'3,845 genes; n = genes per cluster',ha='center',fontsize=11,color='#444444')
out=ROOT/'Paper1_Results/Task2/pdfs/task2_heatmap.pdf'
fig.savefig(out,dpi=250,bbox_inches='tight',pad_inches=.15)
plt.close(fig)
print(out)
