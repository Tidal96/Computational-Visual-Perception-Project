"""Build the course presentation from the actual current images/results."""
from pathlib import Path
import argparse,csv,json,math
from PIL import Image
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY='#14283f'; TEAL='#137e69'; BLUE='#557eb0'; MUTED='#536a82'; BG='#f0f3f7'; WHITE='#ffffff'; ORANGE='#b96643'
def color(hex):return RGBColor.from_string(hex.lstrip('#'))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--submission',type=Path,required=True);ap.add_argument('--analysis',type=Path,required=True);ap.add_argument('--figures',type=Path,required=True);ap.add_argument('--assets',type=Path,required=True);a=ap.parse_args()
 S,A,F,V=a.submission,a.analysis,a.figures,a.assets
 stats=json.loads((A/'summary.json').read_text());run=json.loads((A/'run_info.json').read_text());manual=json.loads((A/'manual_selection.json').read_text())
 assert manual['status']=='confirmed' and len(set(manual['ids']))==10
 ids=manual['ids'];manifest=json.loads((A/'dataset_manifest.json').read_text());by_id={x['stem']:x for x in manifest['images']}
 prs=Presentation();prs.slide_width=Inches(13.333333);prs.slide_height=Inches(7.5)
 prs.core_properties.title='Mooney Faces: Computational Visual Perception — Part 1';prs.core_properties.author='Hadis Nouri';prs.core_properties.subject='100 original/Mooney pairs; Depth Anything V2 Small and CLIP ViT-B/32'
 def box(sl,x,y,w,h,fill=WHITE,line=None,radius=False):
  shape=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h));shape.fill.solid();shape.fill.fore_color.rgb=color(fill)
  if line:shape.line.color.rgb=color(line)
  else:shape.line.fill.background()
  return shape
 def text(sl,txt,x,y,w,h,size=18,bold=False,fill=NAVY,font='Aptos',align=None,url=None):
  shape=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=shape.text_frame;tf.clear();tf.word_wrap=True;tf.margin_left=0;tf.margin_right=0;tf.margin_top=0;tf.margin_bottom=0
  for i,line in enumerate(str(txt).split('\n')):
   p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.space_after=Pt(6)
   if align is not None:p.alignment=align
   r=p.add_run();r.text=line;r.font.size=Pt(size);r.font.bold=bold;r.font.name=font;r.font.color.rgb=color(fill)
   if url:r.hyperlink.address=url
  return shape
 def picture(sl,path,x,y,w,h):
  with Image.open(path) as im:iw,ih=im.size
  factor=min(w/iw,h/ih);ww,hh=iw*factor,ih*factor
  return sl.shapes.add_picture(str(path),Inches(x+(w-ww)/2),Inches(y+(h-hh)/2),width=Inches(ww),height=Inches(hh))
 def slide(kicker,title,subtitle=None):
  sl=prs.slides.add_slide(prs.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=color(BG)
  text(sl,kicker.upper(),.55,.28,12,.25,11,True,TEAL)
  text(sl,title,.55,.70,12.2,.65,30,True)
  if subtitle:text(sl,subtitle,.58,1.35,12.0,.52,13,False,MUTED)
  box(sl,.55,7.02,12.2,.012,'#cad4df');text(sl,'HADIS NOURI  /  COMPVP  /  PART 1',.55,7.12,10,.18,9,False,MUTED);text(sl,f'{len(prs.slides):02d}',12.1,7.1,.6,.2,10,False,MUTED,align=PP_ALIGN.RIGHT)
  return sl
 def card(sl,x,title,body,y=2.0,w=3.9,h=4.45):
  box(sl,x,y,w,h,WHITE,radius=True);box(sl,x,y,.05,h,TEAL)
  text(sl,title,x+.22,y+.23,w-.43,.7,22,True)
  text(sl,body,x+.22,y+1.02,w-.43,h-1.2,17)
 # 01
 sl=slide('Computational visual perception','Mooney Faces','Project Part 1 · individual project · 100 photographs and their binary transformations')
 text(sl,'What survives\nwhen shading\nbecomes binary?',.60,2.0,5.3,2.5,39,True)
 text(sl,'Hadis Nouri',.65,5.16,5,.4,25,True,TEAL)
 text(sl,'Depth Anything V2 Small + CLIP ViT-B/32\n100 originals · 100 Mooneys · 2 vision systems',.65,5.76,5.4,.85,16,False,MUTED)
 for c,kind in enumerate(['Original','Mooney']):
  picture(sl,S/kind/'010.png',6.2+c*3.05,2.35,2.95,2.95);text(sl,kind,6.2+c*3.05,5.48,2.95,.3,16,True,align=PP_ALIGN.CENTER)
 text(sl,'Example 010 · source FFHQ 00041 · 1024 × 1024',6.3,6.1,6,.3,12,False,MUTED,align=PP_ALIGN.CENTER)
 # 02 — required one-page approach
 sl=slide('Approach / all three tasks','Faces under a controlled loss of shading','Question: do category preference, depth structure, and same-photo matching survive the Mooney transformation?')
 card(sl,.55,'01  Choose the images','100 aligned FFHQ photographs, each supplied at 1024 × 1024.\n\n512 candidates screened; 150 pairs visually reviewed by the assistant for facial structure and background clutter.\n\nNo model predictions used for selection.')
 card(sl,4.72,'02  Make the Mooneys','Grayscale → Gaussian blur → global brightness threshold.\n\nSigma 8 px; kernel 49 px. White-pixel target 22% or 28%, recorded per image.\n\nStudent viewed the review board and selected the final ten pairs.')
 card(sl,8.89,'03  Test two systems','Depth Anything V2 Small: relative inverse-depth consistency.\n\nCLIP ViT-B/32: prompt-relative face preference and embedding matching.\n\nBoth systems process all 100 originals and all 100 Mooneys.')
 # 03
 sl=slide('Task 2 / actual running tool','Interactive controls, shared with the batch generator','Screenshot captured from the local GUI. Moving the sliders changes the actual full-resolution PNG.')
 picture(sl,V/'tool_gui.png',.55,1.95,7.0,4.9)
 text(sl,'Two independent controls',7.95,2.0,4.7,.5,24,True)
 text(sl,'White-pixel percentage\nControls the proportion that remains white.\n\nBlur sigma (pixels)\nControls smoothing before thresholding.\n\nBatch CLI\nSingle images, folders, per-image CSV.',7.95,2.73,4.7,3.3,16)
 text(sl,'Verified: 101-image batch + nine parameter combinations + browser interaction.',7.95,6.28,4.7,.48,12,True,TEAL)
 # 04
 sl=slide('Task 2 / implementation','A reproducible Mooney transformation','Actual source screenshot; the complete editable source is provided in the repository and source archive.')
 picture(sl,V/'generator_code.png',.55,1.95,7.0,4.9)
 text(sl,'1  Grayscale in float32\n\n2  Gaussian smoothing\n    k = 2 × ceil(3 × sigma) + 1\n\n3  Global brightness threshold\n    requested white count = floor(N × p / 100)\n\n4  Deterministic boundary ties\n    tie handling is recorded in the CSV',7.95,2.05,4.7,4.2,17)
 text(sl,'Generation preserves input dimensions. No image generator, edge tracing, or segmentation is used.',7.95,6.15,4.7,.65,13,True,TEAL)
 # 05
 sl=slide('Task 2 / control demonstration','Blur and white percentage change different properties','One source photograph (010) is held fixed. Nine binary results are generated by the same function.')
 picture(sl,F/'parameter_sweep.png',.65,1.85,6.4,5.08)
 picture(sl,S/'Original/010.png',8.18,2.0,2.65,2.65)
 text(sl,'Fixed original: image 010',7.7,4.83,3.6,.32,17,True,align=PP_ALIGN.CENTER)
 text(sl,'Rows: 16%, 28%, 40% white\nColumns: sigma 0, 8, 16 px\n\nFinal settings are logged separately for every image.',7.65,5.32,4.8,1.25,17)
 # 06
 sl=slide('Task 2 / student-selected subset','The ten manually selected pairs','Hadis Nouri viewed the review board and explicitly confirmed these ten IDs. Each pair: original on the left, Mooney on the right.')
 for j,stem in enumerate(ids):
  x=.55+(j%5)*2.47;y=2.10+(j//5)*2.12
  text(sl,f'{stem}   /   white {by_id[stem]["white_pct"]:g}%',x,y,2.34,.28,13,True)
  for c,kind in enumerate(['Original','Mooney']):picture(sl,S/kind/f'{stem}.png',x+c*1.17,y+.36,1.13,1.13)
 text(sl,'The Subset files are byte-identical copies of the corresponding full-set files.',.6,6.55,12,.3,13,False,MUTED)
 # 07
 sl=slide('Task 3 / system declaration','Two pretrained vision systems, no project-specific training','One-person team: the brief requires two systems. All 200 input images are processed by each system.')
 card(sl,.6,'01  Depth Anything V2 Small','Task: monocular relative inverse depth.\n\nOfficial model: depth-anything/Depth-Anything-V2-Small-hf\n\nDefault processor; output bicubically interpolated to 1024 × 1024. Export: 16-bit normalized depth + INFERNO visualization.',y=2,w=5.9,h=4.58)
 card(sl,6.82,'02  CLIP ViT-B/32','Task: image/text similarity and visual embeddings.\n\nOfficial model: openai/clip-vit-base-patch32\n\nEight fixed prompts; face score sums the two face-prompt shares. Visual embeddings are unit-normalized for matching.',y=2,w=5.9,h=4.58)
 text(sl,'Official checkpoint hashes and model/config revisions are verified and stored in run_info.json.',.65,6.68,12,.25,12,False,MUTED)
 # 08
 sl=slide('System 1 / qualitative results','Depth structure is partly preserved, with visible failures','Examples at the 10th, 50th, and 90th positions of the sorted paired correlations; no best-only selection.')
 picture(sl,F/'depth_examples.png',.6,1.85,8.2,5.12)
 text(sl,f'Mean paired correlation\n{stats["depth"]["mean_paired_pearson"]:.3f}',9.0,2.12,3.7,1.25,25,True,TEAL)
 text(sl,'Each depth visualization is independently normalized. Brighter INFERNO colors indicate higher relative inverse depth within that image.\n\nColor similarity across images does not establish metric depth.',9.0,3.7,3.6,2.6,17)
 # 09
 sl=slide('System 1 / quantitative results','Corresponding pairs exceed an unrelated-image control','Full-resolution pixel-wise Pearson correlation: original depth vs. Mooney depth; control pairs original i with Mooney i+1 (cyclic).')
 picture(sl,F/'depth_statistics.png',.65,2.0,12,4.30)
 d=stats['depth'];text(sl,f'Paired mean {d["mean_paired_pearson"]:.3f}     |     control mean {d["mean_next_image_control"]:.3f}     |     {d["paired_above_control_count"]}/100 paired maps above control',.7,6.4,12,.32,16,True,TEAL)
 # 10
 sl=slide('System 2 / category preference','CLIP retains a strong face-prompt preference','The eight-prompt comparison is fixed for originals and Mooneys. These scores are relative softmax shares, not calibrated probabilities.')
 picture(sl,F/'clip_statistics.png',.65,1.98,12,4.5)
 o=stats['clip']['Original'];m=stats['clip']['Mooney']
 text(sl,f'Mean face-prompt share: originals {o["mean_face_prompt_share"]:.3f}; Mooneys {m["mean_face_prompt_share"]:.3f}.',.7,6.53,12,.3,17,True,TEAL)
 # 11
 sl=slide('System 2 / individual outputs','Examples include the Mooney face-prompt failure','Three subset examples plus the image whose top Mooney prompt is not a face. All eight prompt scores are saved per image.')
 picture(sl,F/'clip_examples.png',.65,1.95,12,4.9)
 # 12
 sl=slide('Two systems / optional matching analysis','Same-photo matching survives above the 12.5% baseline','One correct gallery image + seven distinct distractors; shuffled positions, seed 0; identical gallery design for both systems and directions.')
 picture(sl,F/'afc8_statistics.png',.65,1.95,8.7,4.9)
 text(sl,'What is being matched?',9.65,2.0,3.1,.7,23,True)
 text(sl,'Original and Mooney views of the same photograph.\n\nCLIP: cosine similarity of 512-D image embeddings.\n\nDepth: correlation of maps resized to 64 × 64, centered and unit-normalized.\n\nError bars: Wilson 95% intervals.',9.65,2.95,3.0,3.85,16)
 # 13
 sl=slide('Interpretation / relation to the papers','Recognizing a face and recovering identity are different','Category preference is high, while matching the corresponding photograph remains substantially harder.')
 card(sl,.6,'Paper 1: inspiration','Egger et al. compare inverse rendering with feedforward accounts on atypical faces.\n\nThis project uses their Mooney motivation and a related eight-alternative matching format.\n\nOur same-photo test does not reproduce their cross-pose identity experiment or human comparison.',y=2,w=5.9,h=4.6)
 card(sl,6.82,'Limits of the current evidence','No true depth is available: depth-map agreement measures consistency.\n\nThe face-prompt share depends on the prompt set; it is not recognition accuracy across object categories.\n\nPaper 2 studies fly visual motion circuits and informs later project parts; FlyVis is not one of these two systems.',y=2,w=5.9,h=4.6)
 # 14
 sl=slide('Delivery / reproducibility','The submission follows the required folder structure','Source code, provenance, parameters, embeddings and analysis tables are provided separately for reproducibility.')
 text(sl,'Original/                 100 PNG\nMooney/                   100 PNG\nSubset/Original/           10 PNG\nSubset/Mooney/             10 PNG\nResult1/Original/          100 depth PNG + 100 JPEG\nResult1/Mooney/            100 depth PNG + 100 JPEG\nResult2/Original/          100 CLIP JSON\nResult2/Mooney/            100 CLIP JSON\nCompVP_Part1_Hadis_Nouri.pptx',.7,2.0,8.5,4.4,18,False,NAVY,font='DejaVu Sans Mono')
 text(sl,'Checks before packaging',9.45,2.0,3.2,.7,22,True)
 text(sl,'100 matched image IDs\n\nBinary Mooneys + exact white counts\n\nComplete, finite model outputs\n\nTen confirmed subset pairs\n\nPPTX and archive integrity',9.45,2.95,3.2,3.5,16)
 # 15
 sl=slide('Declaration / AI usage','AI assistance is disclosed explicitly','The photographs are sourced from FFHQ. Their source credits and individual licenses are listed in the following appendix.')
 text(sl,'ChatGPT / Codex assisted with:',.65,2.05,11.8,.5,25,True)
 text(sl,'Reading the supplied brief and papers; writing and reviewing code; screening source images and choosing transformation settings; executing models; computing statistics; preparing figures, presentation and submission checks.',.7,2.85,11.7,1.35,21)
 box(sl,.65,4.45,12.0,1.9,WHITE,radius=True)
 text(sl,'Student decision and computed evidence',.9,4.66,11.4,.45,21,True,TEAL)
 text(sl,'Hadis Nouri reviewed the proposed subset board and selected the ten final pairs. Model outputs and numerical results were computed by the supplied programs. No generative-image model or invented human 1–5 ratings were used.',.9,5.24,11.35,.95,17)
 # 16
 sl=slide('Sources / methods and models','References and reproducibility records')
 refs=[('Project brief','CompVP Project Part 1, supplied lecture slides, 26 October 2026. Tasks 1–3 and submission requirements.',''),('Paper 1','Egger, Siegel, Arora, Soltani & Yildirim. Inverse Rendering Best Explains Face Perception Under Extreme Illuminations. Supplied PDF.',''),('Paper 2','Lappalainen et al. Connectome-constrained networks predict neural activity across the fly visual system. Nature (2024).','https://doi.org/10.1038/s41586-024-07939-3'),('Image collection','FFHQ (NVlabs). Aligned photographs from pinned mirror revision 505f94e2ecc6db64e967e8e6c8e2c2079ea0876b. Individual photo credits follow.','https://github.com/NVlabs/ffhq-dataset'),('Depth model','Depth Anything V2 Small. Official checkpoint revision 5426e4f0f36572d16453bbda7a8389317b1bef99.','https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf'),('CLIP model','CLIP ViT-B/32. Official config revision 3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268; verified weights and environment in run_info.json.','https://huggingface.co/openai/clip-vit-base-patch32')]
 for i,(label,body,url) in enumerate(refs):
  y=1.85+i*.79;text(sl,label,.65,y,1.5,.4,15,True,TEAL);text(sl,body,2.3,y,10.25,.66,14,url=url or None)
 # Individual photographers and source-license links, ten rows per slide.
 with (A/'ATTRIBUTION.csv').open() as fh:credits=list(csv.DictReader(fh))
 for start in range(0,100,10):
  sl=slide('Appendix / individual image credits',f'Photographs {start+1:03d}–{start+10:03d}','FFHQ alignment/cropping is retained. Mooney transformation: grayscale, Gaussian blur and global threshold. Source photo and license links are clickable.')
  headers=[('ID / FFHQ',.65,1.30),('Photographer / source',2.1,3.0),('Source photograph',5.25,4.55),('License',10.02,2.65)]
  for name,x,w in headers:text(sl,name,x,1.98,w,.3,13,True,TEAL)
  for j,c in enumerate(credits[start:start+10]):
   y=2.42+j*.405
   if j%2==0:box(sl,.58,y-.02,12.12,.38,WHITE)
   title=c['photo_title'] or 'Original source photograph';title=(title[:47]+'…') if len(title)>48 else title
   author=c['author'];author=(author[:29]+'…') if len(author)>30 else author
   text(sl,c['image'].replace('.png','')+' / '+c['ffhq_id'],.65,y,1.40,.32,11)
   text(sl,author,2.1,y,3.0,.32,11)
   text(sl,title,5.25,y,4.55,.32,11,False,BLUE,url=c['photo_url'])
   text(sl,c['license'],10.02,y,2.65,.32,11,False,TEAL,url=c['license_url'])
  text(sl,'Full, untruncated metadata, photo URLs and licenses: ATTRIBUTION.csv in the source/analysis archive.',.65,6.64,12,.25,11,False,MUTED)
 output=S/'CompVP_Part1_Hadis_Nouri.pptx';prs.save(output)
 text_extract=[]
 for i,sl in enumerate(prs.slides,1):
  text_extract.append({'slide':i,'text':'\n'.join(s.text for s in sl.shapes if s.has_text_frame),'pictures':sum(s.shape_type==13 for s in sl.shapes)})
 (A/'presentation_manifest.json').write_text(json.dumps({'file':output.name,'slides':len(prs.slides),'student_selection':ids,'items':text_extract},indent=2))
 print('Presentation saved:',output,'slides:',len(prs.slides))
if __name__=='__main__':main()
