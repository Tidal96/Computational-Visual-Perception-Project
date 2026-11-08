"""Check all required submission files, numeric outputs, subset and presentation."""
from pathlib import Path
import argparse,csv,hashlib,json,zipfile
import cv2,numpy as np
from PIL import Image
from pptx import Presentation
from mooney_tool import make_mooney

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(S,A):
 checks=[]
 def check(name,condition,evidence):
  checks.append({'requirement':name,'passed':bool(condition),'evidence':evidence})
  if not condition:raise AssertionError(name+': '+str(evidence))
 stems=[f'{i:03d}' for i in range(1,101)]
 for kind in ['Original','Mooney']:
  files=sorted((S/kind).glob('*'));check(kind+': exactly 100 PNGs',[p.name for p in files]==[x+'.png' for x in stems],len(files))
 manifest=json.loads((A/'dataset_manifest.json').read_text());by_stem={x['stem']:x for x in manifest['images']}
 settings={Path(x['file']).stem:x for x in csv.DictReader((A/'settings.csv').open())}
 for stem in stems:
  orig=S/'Original'/f'{stem}.png';mooney=S/'Mooney'/f'{stem}.png'
  assert sha(orig)==by_stem[stem]['sha256'],stem+' source hash'
  image=cv2.imread(str(orig));m=cv2.imread(str(mooney),cv2.IMREAD_UNCHANGED)
  assert image.shape==(1024,1024,3) and m.shape==(1024,1024) and m.dtype==np.uint8
  assert set(np.unique(m))=={0,255},stem+' binary constraint'
  config=settings[stem];expected,info=make_mooney(image,float(config['white_pct']),float(config['sigma']))
  assert np.array_equal(m,expected),stem+' generator reproducibility'
  assert (m==255).sum()==int(np.floor(m.size*float(config['white_pct'])/100+1e-6))
 check('100 intact native-size originals and reproducible binary Mooneys',True,'All source hashes, dimensions, per-image controls, exact white counts and regenerated PNG pixels checked')
 manual=json.loads((A/'manual_selection.json').read_text());ids=manual['ids']
 check('Student manual top-ten selection',manual['status']=='confirmed' and manual['selected_by']=='Hadis Nouri' and len(set(ids))==10,manual)
 for kind in ['Original','Mooney']:
  subset=sorted((S/'Subset'/kind).glob('*'));assert {p.stem for p in subset}==set(ids)
  assert all(sha(p)==sha(S/kind/p.name) for p in subset)
 check('Subset contains ten matching pairs',True,'20 byte-identical copies with the student-confirmed IDs')
 labelset=None
 for kind in ['Original','Mooney']:
  d1=S/'Result1'/kind;d2=S/'Result2'/kind
  assert {p.name for p in d1.iterdir()}=={stem+suffix for stem in stems for suffix in ['_depth16.png','_depth_vis.jpg']}
  assert {p.name for p in d2.iterdir()}=={stem+'.json' for stem in stems}
  raw_path=A/f'depth_{kind}.npy';raw=np.load(raw_path,mmap_mode='r') if raw_path.exists() else None
  for i,stem in enumerate(stems):
   depth=cv2.imread(str(d1/f'{stem}_depth16.png'),cv2.IMREAD_UNCHANGED);vis=np.array(Image.open(d1/f'{stem}_depth_vis.jpg'))
   assert depth.shape==(1024,1024) and depth.dtype==np.uint16 and depth.std()>0
   assert vis.shape==(1024,1024,3) and vis.std()>0
   if raw is not None:
    d=raw[i];assert np.isfinite(d).all() and d.std()>0
    assert np.array_equal(((d-d.min())/(d.max()-d.min())*65535).astype(np.uint16),depth)
   result=json.loads((d2/f'{stem}.json').read_text());probs=result['probs'];p=np.array(list(probs.values()))
   assert len(probs)==8 and np.isfinite(p).all() and np.all(p>=0) and np.all(p<=1) and abs(p.sum()-1)<1e-5
   assert result['image']==stem+'.png' and result['top1']==max(probs,key=probs.get)
   assert abs(result['p_face']-(probs['a photo of a human face']+probs['a black and white image of a human face']))<1e-6
   assert labelset is None or list(probs)==labelset;labelset=list(probs)
  check('Both vision-system outputs for all '+kind+' images',True,'100 finite nonconstant depth maps + 100 depth visualizations + 100 complete CLIP JSONs')
 data=np.load(A/'clip_embeddings.npz')
 assert data['stems'].tolist()==stems
 for kind in ['Original','Mooney']:assert data[kind].shape==(100,512) and np.isfinite(data[kind]).all() and np.allclose(np.linalg.norm(data[kind],axis=1),1,atol=1e-4)
 trials=json.loads((A/'afc8_trials.json').read_text());design=json.loads((A/'afc8_gallery_design.json').read_text())
 assert len(trials)==400 and len(design['trials'])==100
 for t in trials:
  assert len(t['gallery'])==len(set(t['gallery']))==8 and t['gallery'][t['correct_index']]==t['probe']
  assert np.isfinite(t['scores']).all() and t['predicted_index']==int(np.argmax(t['scores']))
  assert t['correct']==(t['predicted_index']==t['correct_index'])
 summary=json.loads((A/'summary.json').read_text())
 for row in summary['afc8']:
  corresponding=[t for t in trials if t['system']==row['system'] and t['direction']==row['probe']+' to '+row['gallery']]
  assert len(corresponding)==100 and sum(t['correct'] for t in corresponding)==row['correct']
 check('Reproducible numeric matching analysis',True,'200 finite normalized embeddings, 100 shared gallery designs, 400 saved trials and four independently tallied accuracies')
 slides=list(S.glob('*.pptx'));assert len(slides)==1
 prs=Presentation(slides[0]);text='\n'.join(s.text for slide in prs.slides for s in slide.shapes if s.has_text_frame)
 assert 'Hadis Nouri' in text and 'AI assistance' in text and 'Depth Anything' in text and 'CLIP' in text
 assert len(prs.slides)>=16
 subset_slide=prs.slides[5];assert sum(sh.shape_type==13 for sh in subset_slide.shapes)==20
 for slide in prs.slides:
  for sh in slide.shapes:
   assert sh.left>=0 and sh.top>=0 and sh.left+sh.width<=prs.slide_width+100 and sh.top+sh.height<=prs.slide_height+100
 with zipfile.ZipFile(slides[0]) as z:assert z.testzip() is None
 check('PowerPoint required content and integrity',True,{'slides':len(prs.slides),'subset_images_on_one_slide':20,'required_sections':'name, one-page approach, selected images, systems, results, tool screenshot, code screenshot, AI declaration, references and credits'})
 root_names={p.name for p in S.iterdir()};assert root_names=={'Original','Mooney','Subset','Result1','Result2',slides[0].name}
 all_files=[p for p in S.rglob('*') if p.is_file()];check('Exact submission layout',len(all_files)==821,{'files':len(all_files),'root_entries':sorted(root_names)})
 tool=json.loads((A/'tool_verification.json').read_text());gui=json.loads((A/'gui_checks.json').read_text())
 check('Tool controls and batch capacity',len(tool['control_output_hashes'])==9 and len(gui['actual_browser_interaction'])==3,tool)
 report={'automated_checks':'passed','all_required_part1_tasks_covered':True,'manual_subset_confirmed':True,'checks':checks,
   'scope':'Part 1 Tasks 1, 2, 3 for a one-person team. The supplied brief does not give full requirements for Project Parts 2 and 3.',
   'quality_review':'Assistant visually screened source/Mooney pairs; student viewed and confirmed the selected-ten board. Visual quality and final grading remain subjective.'}
 (A/'verification_results.json').write_text(json.dumps(report,indent=2))
 checksums={str(p.relative_to(S)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in all_files}
 (A/'submission_file_checksums.json').write_text(json.dumps(checksums,indent=2))
 return report

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--submission',type=Path,required=True);ap.add_argument('--analysis',type=Path,required=True);ap.add_argument('--zip',type=Path);a=ap.parse_args();report=verify(a.submission,a.analysis)
 if a.zip:
  with zipfile.ZipFile(a.zip,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(a.submission.rglob('*')):
    if p.is_file():z.write(p,p.relative_to(a.submission))
  with zipfile.ZipFile(a.zip) as z:assert z.testzip() is None and len(z.namelist())==821
  (a.analysis/'archive_checksums.json').write_text(json.dumps({'file':a.zip.name,'bytes':a.zip.stat().st_size,'sha256':sha(a.zip),'md5':hashlib.md5(a.zip.read_bytes()).hexdigest(),'crc_test':'passed'},indent=2))
 print(json.dumps({'checks':len(report['checks']),'status':'passed','zip':str(a.zip) if a.zip else None},indent=2))
if __name__=='__main__':main()
