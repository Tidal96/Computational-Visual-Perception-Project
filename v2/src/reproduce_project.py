"""Rebuild all three Part 1 tasks, metrics, slides and submission ZIP.

Run from the project source directory:
  python src/reproduce_project.py --project-root . --output run
This downloads the 100 pinned source images unless --original supplies a folder.
Official model revisions and weight hashes are checked by run_models.py.
"""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,sys,time,zipfile
import requests

STATIC=['dataset_manifest.json','settings.csv','ATTRIBUTION.csv','ATTRIBUTION.md','manual_selection.json','tool_verification.json','gui_checks.json','batch101_log.txt','mooney_cli_log.txt']

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--original',type=Path);ap.add_argument('--depth-model',type=Path);ap.add_argument('--clip-model',type=Path);a=ap.parse_args()
 project=a.project_root.resolve();root=a.output.resolve();S=root/'submission';A=root/'analysis';F=root/'figures'
 if any(root.rglob('*.png')):raise SystemExit('Use a new output directory to avoid mixing runs.')
 for p in [S/'Original',S/'Mooney',S/'Subset/Original',S/'Subset/Mooney',A,F]:p.mkdir(parents=True,exist_ok=True)
 for name in STATIC:shutil.copyfile(project/'analysis'/name,A/name)
 manifest=json.loads((A/'dataset_manifest.json').read_text())
 def get(item):
  name=item['stem']+'.png';target=S/'Original'/name
  if a.original:data=(a.original/name).read_bytes()
  else:
   for attempt in range(4):
    try:
     r=requests.get(item['source_url'],timeout=90);r.raise_for_status();data=r.content;break
    except requests.RequestException:
     if attempt==3:raise
     time.sleep(1+attempt)
  if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Source checksum mismatch: '+name)
  target.write_bytes(data)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(get,manifest['images']))
 src=project/'src'
 def call(script,params,log):
  command=[sys.executable,str(src/script),*map(str,params)];print('RUN',script,flush=True)
  result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (A/log).write_text(result.stdout);print(result.stdout[-1800:],flush=True)
  if result.returncode:raise RuntimeError(f'{script} failed: see {A/log}')
 call('mooney_tool.py',[S/'Original',S/'Mooney','--params',A/'settings.csv','--log',A/'mooney_parameters.csv'],'generation.log')
 manual=json.loads((A/'manual_selection.json').read_text());assert manual['status']=='confirmed'
 for kind in ['Original','Mooney']:
  for stem in manual['ids']:shutil.copyfile(S/kind/(stem+'.png'),S/'Subset'/kind/(stem+'.png'))
 model_args=['--submission',S,'--analysis',A]
 if a.depth_model:model_args+=['--depth-model',a.depth_model]
 if a.clip_model:model_args+=['--clip-model',a.clip_model]
 call('run_models.py',model_args,'model_run.log')
 call('analyze_results.py',[A],'statistics.log')
 call('make_figures.py',['--submission',S,'--analysis',A,'--figures',F],'figures.log')
 assets=project/'assets' if (project/'assets').is_dir() else project/'review'
 call('build_presentation.py',['--submission',S,'--analysis',A,'--figures',F,'--assets',assets],'presentation.log')
 output=root/'CompVP_Part1_Hadis_Nouri.zip'
 call('verify_project.py',['--submission',S,'--analysis',A,'--zip',output],'verification.log')
 # Keep weights and large raw depth arrays out of the portable source/analysis ZIP.
 bundle=root/'CompVP_Part1_Source_Analysis.zip'
 with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for p in src.glob('*.py'):z.write(p,'src/'+p.name)
  for p in A.iterdir():
   if p.is_file() and p.suffix in {'.json','.csv','.txt','.md','.npz'}:z.write(p,'analysis/'+p.name)
  for p in F.iterdir():
   if p.is_file():z.write(p,'figures/'+p.name)
  for name in ['tool_gui.png','generator_code.png']:
   z.write(assets/name,'assets/'+name)
  for name in ['README.md','requirements.txt']:
   if (project/name).exists():z.write(project/name,name)
 print('COMPLETE:',output,'and',bundle,flush=True)
if __name__=='__main__':main()
