from pathlib import Path
import argparse,csv,json,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import cv2
from mooney_tool import make_mooney

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--submission',type=Path,required=True);ap.add_argument('--analysis',type=Path,required=True);ap.add_argument('--figures',type=Path,required=True);a=ap.parse_args();S=a.submission;A=a.analysis;O=a.figures;O.mkdir(parents=True,exist_ok=True)
 summary=json.loads((A/'summary.json').read_text())
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#20354d','text.color':'#20354d','axes.titleweight':'bold','savefig.facecolor':'white'})
 colors=['#187e6b','#557eb0']
 with (A/'depth_metrics.csv').open() as f:depth=list(csv.DictReader(f))
 metrics=sorted(depth,key=lambda x:float(x['paired_pearson']));examples=[metrics[i]['stem'] for i in [9,49,89]]
 fig,axes=plt.subplots(3,4,figsize=(10,7.8),layout='constrained')
 for r,stem in enumerate(examples):
  paths=[S/'Original'/f'{stem}.png',S/'Mooney'/f'{stem}.png',S/'Result1/Original'/f'{stem}_depth_vis.jpg',S/'Result1/Mooney'/f'{stem}_depth_vis.jpg']
  for c,path in enumerate(paths):
   axes[r,c].imshow(Image.open(path).convert('RGB'));axes[r,c].set_xticks([]);axes[r,c].set_yticks([])
   for sp in axes[r,c].spines.values():sp.set_visible(False)
   if r==0:axes[r,c].set_title(['Original','Mooney','Original → depth','Mooney → depth'][c],fontsize=12)
  corr=next(float(x['paired_pearson']) for x in depth if x['stem']==stem)
  axes[r,0].set_ylabel(f'Image {stem}\nr = {corr:.3f}',fontsize=10)
 fig.savefig(O/'depth_examples.png',dpi=200);plt.close(fig)
 paired=np.array([float(x['paired_pearson']) for x in depth]);control=np.array([float(x['next_image_control']) for x in depth])
 fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained');bins=np.linspace(-.5,1,19)
 axes[0].hist(control,bins=bins,alpha=.60,color=colors[1],label=f'Next-image control: {control.mean():.3f}')
 axes[0].hist(paired,bins=bins,alpha=.67,color=colors[0],label=f'Paired: {paired.mean():.3f}')
 axes[0].set(xlabel='Pixel-wise Pearson correlation',ylabel='Number of images',title='Depth-map consistency');axes[0].legend(fontsize=9,frameon=False)
 axes[1].scatter(control,paired,s=24,color=colors[0],alpha=.7);axes[1].plot([-.5,1],[-.5,1],color='#9aaabe',ls='--',lw=1)
 axes[1].set(xlim=(-.5,1),ylim=(-.5,1),xlabel='Next-image control correlation',ylabel='Paired correlation',title=f'{(paired>control).sum()}/100 pairs above control')
 fig.savefig(O/'depth_statistics.png',dpi=200);fig.savefig(O/'depth_statistics.pdf');plt.close(fig)
 with (A/'clip_zero_shot.csv').open() as f:clip=list(csv.DictReader(f))
 fig,axes=plt.subplots(1,2,figsize=(9.8,4.1),layout='constrained')
 for k,(kind,color) in enumerate(zip(['Original','Mooney'],colors)):
  values=np.array([float(x['p_face']) for x in clip if x['kind']==kind]);axes[0].scatter(np.full(100,k)+np.random.default_rng(0).normal(0,.035,100),values,color=color,s=13,alpha=.4)
  axes[0].plot([k-.21,k+.21],[values.mean()]*2,color=color,lw=4)
  count=summary['clip'][kind]['face_prompt_top1_count'];axes[1].bar(k,count,color=color,width=.52);axes[1].text(k,count+1,f'{count}/100',ha='center',fontsize=13,fontweight='bold')
 axes[0].set(xticks=[0,1],xticklabels=['Original','Mooney'],ylabel='Combined face-prompt softmax share',ylim=(0,1.03),title='Prompt-relative face preference')
 axes[1].set(xticks=[0,1],xticklabels=['Original','Mooney'],ylim=(0,110),ylabel='Number of images',title='Top prompt describes a face')
 fig.savefig(O/'clip_statistics.png',dpi=200);fig.savefig(O/'clip_statistics.pdf');plt.close(fig)
 failures=[x['stem'] for x in clip if x['kind']=='Mooney' and x['top1'] not in ['a photo of a human face','a black and white image of a human face']]
 chosen=['010','022','052']+failures[:1]
 chosen=list(dict.fromkeys(chosen))
 fig,axes=plt.subplots(2,len(chosen),figsize=(10,5.4),layout='constrained')
 for c,stem in enumerate(chosen):
  for r,kind in enumerate(['Original','Mooney']):
   entry=next(x for x in clip if x['stem']==stem and x['kind']==kind)
   axes[r,c].imshow(Image.open(S/kind/f'{stem}.png').convert('RGB'));axes[r,c].axis('off')
   short=entry['top1'].replace('a photo of a human face','face').replace('a black and white image of a human face','B&W face').replace('an ink blot','ink blot')
   axes[r,c].set_title(f'{kind} {stem}\n{short} | face share {float(entry["p_face"]):.3f}',fontsize=9)
 fig.savefig(O/'clip_examples.png',dpi=200);plt.close(fig)
 fig,ax=plt.subplots(figsize=(9.5,4.8),layout='constrained');rows=summary['afc8'];xx=np.arange(4)
 vals=np.array([r['accuracy'] for r in rows])*100;lo=vals-np.array([r['wilson95_low'] for r in rows])*100;hi=np.array([r['wilson95_high'] for r in rows])*100-vals
 ax.bar(xx,vals,color=[colors[0]]*2+[colors[1]]*2,width=.6,yerr=np.stack([lo,hi]),capsize=4,error_kw={'ecolor':'#354c66'})
 for x,v in zip(xx,vals):ax.text(x,v+12,f'{v:.0f}%',ha='center',fontsize=14,fontweight='bold')
 ax.axhline(12.5,ls='--',color='#be6948',lw=1.8,label='Chance: 12.5%');ax.legend(frameon=False,loc='upper right')
 ax.set(xticks=xx,xticklabels=['CLIP\nOriginal → Mooney','CLIP\nMooney → Original','Depth\nOriginal → Mooney','Depth\nMooney → Original'],ylabel='Correct same-photo matches (%)',ylim=(0,100))
 fig.savefig(O/'afc8_statistics.png',dpi=200);fig.savefig(O/'afc8_statistics.pdf');plt.close(fig)
 # A single source across nine settings demonstrates both controls.
 original=cv2.imread(str(S/'Original/010.png'))
 fig,axes=plt.subplots(3,3,figsize=(6.4,6.5),layout='constrained')
 for r,white in enumerate([16,28,40]):
  for c,sigma in enumerate([0,8,16]):
   m,_=make_mooney(original,white,sigma);axes[r,c].imshow(m,cmap='gray',vmin=0,vmax=255);axes[r,c].axis('off');axes[r,c].set_title(f'White {white}% · sigma {sigma}px',fontsize=10)
 fig.savefig(O/'parameter_sweep.png',dpi=200);plt.close(fig)
 (A/'figure_examples.json').write_text(json.dumps({'depth_examples':examples,'depth_quantile_positions':[10,50,90],'clip_examples':chosen,'clip_mooney_failures':failures},indent=2))
 print('Generated six result/control figures; example selection and failure IDs saved.')
if __name__=='__main__':main()
