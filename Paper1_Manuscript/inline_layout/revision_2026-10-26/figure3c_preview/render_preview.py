from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
ROOT=Path(__file__).resolve().parents[4]
d=pd.read_csv(ROOT/'Paper1_Results/Task2/task2_choosing_k.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'axes.linewidth':.8,'savefig.facecolor':'white'})
fig, axes=plt.subplots(2,1,figsize=(6.5,7.5))
fig.subplots_adjust(left=.16,right=.97,top=.91,bottom=.19,hspace=.45)
fig.suptitle('Cluster-number selection',fontsize=12,fontweight='semibold',y=.97)
axes[0].plot(d.k,d.silhouette,'o-',color='#30343b',lw=1.5,markersize=4.5)
axes[0].set_ylabel('Silhouette score',labelpad=10)
axes[0].set_ylim(.25,.62)
a=axes[1]
g=a.errorbar(d.k,d.stability_ARI_mean,yerr=d.stability_ARI_sd,fmt='o-',color='#30343b',lw=1.4,markersize=4.5,capsize=3,label='80% gene subsampling')
p=a.errorbar(d.k+.08,d.patient_bootstrap_ARI_mean,yerr=d.patient_bootstrap_ARI_sd,fmt='s--',color='#7d3c98',lw=1.4,markersize=4.5,capsize=3,label='Patient bootstrapping')
t=a.axhline(.95,color='#be3d35',ls='--',lw=1.1,label='Gene-subsampling threshold (ARI = 0.95)')
a.set_ylabel('Adjusted Rand index\n(mean ± SD)',labelpad=10)
a.set_ylim(.34,1.055)
for ax in axes:
 ax.axvspan(4.88,5.12,color='#2471a3',alpha=.13,lw=0,zorder=0)
 ax.set_xticks(d.k)
 ax.set_xlim(2.7,8.3)
 ax.set_xlabel('Number of clusters (k)',labelpad=7)
 ax.spines[['top','right']].set_visible(False)
 ax.tick_params(direction='out',length=3,pad=4)
axes[0].annotate('Selected k = 5',xy=(5,.615),xytext=(0,-1),textcoords='offset points',ha='center',va='top',fontsize=8.5,color='#215c7c')
fig.legend(handles=[g,p,t],loc='lower center',bbox_to_anchor=(.55,.025),fontsize=9,frameon=False,ncol=1,handlelength=2.8,labelspacing=.7)
out=Path(__file__).with_name('figure3c_preview.png')
fig.savefig(out,dpi=300,bbox_inches='tight',pad_inches=.12)
plt.close(fig)
print(out)
