from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parents[4]
d=pd.read_csv(root/'Paper1_Results/Task3/task3_transition_summary.csv')
plt.rcParams.update({'font.family':'Liberation Serif','font.size':10,'axes.labelsize':10,'axes.titlesize':12,'xtick.labelsize':10,'ytick.labelsize':9,'axes.linewidth':.7})
fig=plt.figure(figsize=(8,6.6))
gs=fig.add_gridspec(2,4,left=.115,right=.975,bottom=.10,top=.84,wspace=1.15,hspace=.82)
a=fig.add_subplot(gs[0,:2]);b=fig.add_subplot(gs[0,2:]);c=fig.add_subplot(gs[1,1:3]);x=np.arange(4)
a.bar(x,d.n_substantial_up,color='#c0392b',label='Higher at later stage')
a.bar(x,-d.n_substantial_down,color='#2471a3',label='Lower at later stage')
for j,r in d.iterrows():
 a.text(j,r.n_substantial_up+22,f'{int(r.n_substantial_up)}',ha='center',va='bottom',fontsize=9)
 a.text(j,-r.n_substantial_down-22,f'{int(r.n_substantial_down)}',ha='center',va='top',fontsize=9)
a.axhline(0,color='black',lw=.6)
a.set_ylim(-780,1100)
a.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{abs(v):.0f}'))
a.set_title('Substantial genes\n(full data)',pad=10)
a.set_ylabel('Gene count\n(lower-expression counts drawn below zero)',labelpad=8)
v=d.matched_n_substantial_median
b.bar(x,v,color='#7d3c98');b.set_ylim(0,280)
for j,y in enumerate(v): b.text(j,y+5,f'{y:g}',ha='center',va='bottom',fontsize=9)
b.set_title('Median substantial genes\n(matched, 30 per stage)',pad=10)
b.set_ylabel('Median substantial-gene count',labelpad=8)
c.bar(x,d.median_abs_beta,color='#555555');c.set_ylim(0,.43)
for j,y in enumerate(d.median_abs_beta):c.text(j,y+.009,f'{y:.3f}',ha='center',va='bottom',fontsize=9)
c.set_title('Effect size\n(median |β|)',pad=10)
c.set_ylabel('Absolute coefficient (within-study SD units)',labelpad=8)
for ax in [a,b,c]:
 ax.set_xticks(x,d.transition)
 ax.set_xlabel('Adjacent-stage comparison',labelpad=7)
 ax.spines[['top','right']].set_visible(False)
 ax.tick_params(axis='both',pad=4)
fig.legend(*a.get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.51,1.005),ncol=2,frameon=False,fontsize=10)
out=Path(__file__).with_name('figure4a_two_top_one_below_preview.png')
fig.savefig(out,dpi=230,bbox_inches='tight',pad_inches=.15)
plt.close(fig)
print(out)
