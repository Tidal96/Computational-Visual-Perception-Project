"""Recompute descriptive statistics and reproducible same-photo 8AFC matching.

8AFC here tests original/Mooney views of the SAME photograph. It does not
reproduce Paper 1's cross-pose identity experiment or its human comparison.
"""
from pathlib import Path
import argparse,csv,json
import cv2
import numpy as np
from scipy.stats import binomtest


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('analysis',type=Path)
    args=ap.parse_args();A=args.analysis
    kinds=['Original','Mooney'];depth={k:np.load(A/f'depth_{k}.npy',mmap_mode='r') for k in kinds}
    data=np.load(A/'clip_embeddings.npz');stems=data['stems'].tolist();n=len(stems)
    def unit(x,center=False):
        if center:x=x-x.mean(axis=1,keepdims=True)
        return x/np.linalg.norm(x,axis=1,keepdims=True)
    vec={'CLIP':{k:unit(data[k]) for k in kinds},'Depth Anything':{k:unit(np.array([cv2.resize(d,(64,64),interpolation=cv2.INTER_LINEAR).ravel() for d in depth[k]]),True) for k in kinds}}
    depth_rows=[]
    def corr(a,b):
        a=a.ravel().astype(np.float64);b=b.ravel().astype(np.float64)
        a-=a.mean();b-=b.mean();return float(np.dot(a,b)/np.sqrt(np.dot(a,a)*np.dot(b,b)))
    for i,stem in enumerate(stems):
        depth_rows.append({'stem':stem,'paired_pearson':corr(depth['Original'][i],depth['Mooney'][i]),
            'next_image_control':corr(depth['Original'][i],depth['Mooney'][(i+1)%n])})
    with (A/'depth_metrics.csv').open('w',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=depth_rows[0]);writer.writeheader();writer.writerows(depth_rows)
    # One common shuffled gallery design for both systems and directions.
    rng=np.random.default_rng(0);design=[]
    for i,stem in enumerate(stems):
        choices=np.r_[i,rng.choice(np.delete(np.arange(n),i),7,replace=False)];rng.shuffle(choices)
        design.append({'probe':stem,'gallery':[stems[int(j)] for j in choices],'correct_index':int(np.where(choices==i)[0][0])})
    (A/'afc8_gallery_design.json').write_text(json.dumps({'seed':0,'task':'same-photograph original/Mooney matching','trials':design},indent=2))
    afc=[];trials=[]
    for system,v in vec.items():
        for probe,gallery in [('Original','Mooney'),('Mooney','Original')]:
            wins=0
            for i,trial in enumerate(design):
                indexes=[stems.index(s) for s in trial['gallery']]
                scores=v[gallery][indexes]@v[probe][i];pred=int(scores.argmax());correct=pred==trial['correct_index'];wins+=correct
                trials.append({'system':system,'direction':f'{probe} to {gallery}',**trial,'scores':scores.tolist(),'predicted_index':pred,'correct':bool(correct)})
            test=binomtest(wins,n,.125,alternative='greater');ci=binomtest(wins,n).proportion_ci(method='wilson')
            afc.append({'system':system,'probe':probe,'gallery':gallery,'correct':wins,'n':n,'accuracy':wins/n,
                'wilson95_low':float(ci.low),'wilson95_high':float(ci.high),'p_vs_chance_descriptive':float(test.pvalue)})
    (A/'afc8_trials.json').write_text(json.dumps(trials,indent=2))
    with (A/'afc8_results.csv').open('w',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=afc[0]);writer.writeheader();writer.writerows(afc)
    with (A/'clip_zero_shot.csv').open() as fh:clip_rows=list(csv.DictReader(fh))
    clip_summary={}
    for k in kinds:
        r=[x for x in clip_rows if x['kind']==k];values=np.array([float(x['p_face']) for x in r])
        counts={label:sum(x['top1']==label for x in r) for label in sorted({x['top1'] for x in r})}
        clip_summary[k]={'mean_face_prompt_share':float(values.mean()),'median_face_prompt_share':float(np.median(values)),
            'std_face_prompt_share':float(values.std()),'face_prompt_top1_count':sum(x['top1'] in ['a photo of a human face','a black and white image of a human face'] for x in r),'top1_counts':counts}
    matched=np.array([x['paired_pearson'] for x in depth_rows]);control=np.array([x['next_image_control'] for x in depth_rows])
    depth_summary={'mean_paired_pearson':float(matched.mean()),'median_paired_pearson':float(np.median(matched)),
        'std_paired_pearson':float(matched.std()),'mean_next_image_control':float(control.mean()),'paired_above_control_count':int((matched>control).sum())}
    all64=vec['Depth Anything']['Original']@vec['Depth Anything']['Mooney'].T
    depth_summary['mean_all_unrelated_64px_control']=float(all64[~np.eye(n,dtype=bool)].mean())
    summary={'n':n,'depth':depth_summary,'clip':clip_summary,'afc8':afc,
        'limitations':['No ground-truth depth: correlations measure consistency, not reconstruction accuracy.',
            'All original stimuli are faces; distractor prompts do not form a labeled multiclass test set.',
            'CLIP shares depend on these eight prompts and are not calibrated probabilities.',
            '8AFC uses the same photo in different representations, unlike Paper 1 cross-pose identity matching.',
            'Binomial p values are descriptive: probes and gallery images are reused.',
            'Source selection is a visual/illumination screening sample, not a random population sample.']}
    (A/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
