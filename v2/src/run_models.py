"""Run both vision systems on every original and Mooney; no synthetic results.

python run_models.py --submission submission --analysis analysis
Optional: --depth-model /local/verified/model --clip-model /local/verified/model
"""
import argparse, csv, hashlib, json, os, platform, time
from pathlib import Path
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
import transformers
from transformers import AutoImageProcessor, AutoModelForDepthEstimation, CLIPModel, CLIPProcessor

DEPTH_ID = 'depth-anything/Depth-Anything-V2-Small-hf'
DEPTH_REV = '5426e4f0f36572d16453bbda7a8389317b1bef99'
CLIP_ID = 'openai/clip-vit-base-patch32'
CLIP_REV = '3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268'
CLIP_SAFE_REV = 'c237dc49a33fc61debc9276459120b7eac67e7ef'
HASHES = {'depth': '3152477ce0d8d6978d76b995120de97cb5b928701fd0f817769f59e249a16b70',
          'clip': '99d28a652e6ec46629ab7047a0ac82c69b1fe11e0ce672c43af65d3a9a3fc05d'}
CLIP_BIN_SHA256 = 'a63082132ba4f97a80bea76823f544493bffa8082296d62d71581a4feff1576f'
ASSET_GIT_SHA1 = {
    'depth': {'config.json':'9207d3a304e86517dab21638c559d8b3195d41b6',
              'preprocessor_config.json':'a7822a90a0e91a14d50d1996953bac8f389a4377'},
    'clip': {'config.json':'a2a88b96561196777ca173b15309ea859f4d2ce0',
        'preprocessor_config.json':'5a12a1eb250987a4eee0e3e7d7338c4b22724be1',
        'tokenizer_config.json':'4fdaf6842dd5a725b940c92b6b692490ce59d548',
        'vocab.json':'182766ce89b439768edadda342519f33802f5364',
        'merges.txt':'bbfec752c9a675946c6dce106def6f35c882dcc2'}}
LABELS = ['a photo of a human face', 'a black and white image of a human face',
          'a photo of an animal', 'a photo of an object', 'a photo of a landscape',
          'an abstract black and white pattern', 'a map', 'an ink blot']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b''): h.update(chunk)
    return h.hexdigest()


def resolve_models(args):
    if args.depth_model and args.clip_model:
        paths = {'depth': args.depth_model, 'clip': args.clip_model}
    else:
        from huggingface_hub import snapshot_download, hf_hub_download
        import shutil
        d = Path(snapshot_download(DEPTH_ID, revision=DEPTH_REV,
            allow_patterns=['config.json','preprocessor_config.json','model.safetensors']))
        c = Path(snapshot_download(CLIP_ID, revision=CLIP_REV,
            allow_patterns=['config.json','preprocessor_config.json','tokenizer_config.json','vocab.json','merges.txt','special_tokens_map.json']))
        safe = Path(hf_hub_download(CLIP_ID, 'model.safetensors', revision=CLIP_SAFE_REV))
        target = args.analysis/'clip_model_local'; target.mkdir(parents=True, exist_ok=True)
        for p in c.iterdir():
            if p.is_file() and p.suffix in {'.json','.txt'}: shutil.copyfile(p, target/p.name)
        if not (target/'model.safetensors').exists(): os.link(safe.resolve(), target/'model.safetensors')
        paths = {'depth': d, 'clip': target}
    for key,path in paths.items():
        weight = path/'model.safetensors'
        expected_hash = HASHES[key]
        if key=='clip' and not weight.exists():
            weight=path/'pytorch_model.bin';expected_hash=CLIP_BIN_SHA256
        actual = sha256(weight)
        if actual != expected_hash: raise ValueError(f'{key}: model checksum mismatch')
        for filename,expected_git_sha in ASSET_GIT_SHA1[key].items():
            b=(path/filename).read_bytes()
            actual_git_sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            if actual_git_sha!=expected_git_sha:raise ValueError(f'{key}: {filename} checksum mismatch')
        expected = 'depth_anything' if key=='depth' else 'clip'
        if json.loads((path/'config.json').read_text())['model_type'] != expected:
            raise ValueError(f'{key}: incorrect model configuration')
    return paths


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--submission', type=Path, required=True)
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--depth-model', type=Path)
    ap.add_argument('--clip-model', type=Path)
    ap.add_argument('--threads', type=int, default=2)
    args=ap.parse_args(); args.analysis.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(args.threads)
    device='cuda' if torch.cuda.is_available() else 'cpu'
    start=time.monotonic(); paths=resolve_models(args)
    files={k:sorted((args.submission/k).glob('*.png')) for k in ['Original','Mooney']}
    stems=[p.stem for p in files['Original']]
    assert len(stems)==100 and stems==[p.stem for p in files['Mooney']]
    depth_proc=AutoImageProcessor.from_pretrained(paths['depth'],local_files_only=True)
    depth_model=AutoModelForDepthEstimation.from_pretrained(paths['depth'],local_files_only=True).to(device).eval()
    map_rows=[]
    for kind,inputs in files.items():
        dest=args.submission/'Result1'/kind;dest.mkdir(parents=True,exist_ok=True)
        h,w=np.array(Image.open(inputs[0])).shape[:2]
        maps=np.lib.format.open_memmap(args.analysis/f'depth_{kind}.npy',mode='w+',dtype=np.float32,shape=(len(inputs),h,w))
        for i,path in enumerate(inputs):
            im=Image.open(path).convert('RGB');assert im.size==(w,h)
            x=depth_proc(images=im,return_tensors='pt')['pixel_values'].to(device)
            with torch.inference_mode():
                pred=depth_model(pixel_values=x).predicted_depth
                d=F.interpolate(pred.unsqueeze(1),size=(h,w),mode='bicubic',align_corners=False)[0,0].float().cpu().numpy()
            assert np.isfinite(d).all() and d.std()>0
            maps[i]=d
            norm=(d-d.min())/(d.max()-d.min())
            assert cv2.imwrite(str(dest/f'{path.stem}_depth16.png'),(norm*65535).astype(np.uint16))
            assert cv2.imwrite(str(dest/f'{path.stem}_depth_vis.jpg'),cv2.applyColorMap((norm*255).astype(np.uint8),cv2.COLORMAP_INFERNO),[cv2.IMWRITE_JPEG_QUALITY,94])
            map_rows.append({'kind':kind,'stem':path.stem,'raw_min':float(d.min()),'raw_max':float(d.max()),'raw_std':float(d.std())})
            if (i+1)%10==0:print(f'Depth {kind}: {i+1}/100; {time.monotonic()-start:.1f}s',flush=True)
        maps.flush();del maps
    del depth_model
    clip_proc=CLIPProcessor.from_pretrained(paths['clip'],local_files_only=True)
    clip=CLIPModel.from_pretrained(paths['clip'],local_files_only=True).to(device).eval()
    text=clip_proc(text=LABELS,padding=True,return_tensors='pt').to(device)
    assert clip_proc.tokenizer(LABELS[0])['input_ids'][0]==49406
    embeddings={};rows=[]
    for kind,inputs in files.items():
        dest=args.submission/'Result2'/kind;dest.mkdir(parents=True,exist_ok=True);emb=[]
        for start_i in range(0,len(inputs),16):
            batch=inputs[start_i:start_i+16]
            x=clip_proc(images=[Image.open(p).convert('RGB') for p in batch],return_tensors='pt')['pixel_values'].to(device)
            with torch.inference_mode():out=clip(pixel_values=x,**text)
            e=out.image_embeds.float().cpu().numpy();p=out.logits_per_image.softmax(-1).float().cpu().numpy()
            assert e.shape==(len(batch),512) and np.isfinite(e).all()
            assert np.isfinite(p).all() and np.allclose(p.sum(1),1,atol=1e-5)
            emb.append(e)
            for path,prob in zip(batch,p):
                result={'image':path.name,'model':CLIP_ID,'prompt_set':LABELS,
                    'top1':LABELS[int(prob.argmax())],'p_face':float(prob[:2].sum()),
                    'interpretation':'Relative softmax share of the two face prompts among these eight prompts; not calibrated probability.',
                    'probs':{label:float(value) for label,value in zip(LABELS,prob)}}
                (dest/f'{path.stem}.json').write_text(json.dumps(result,indent=2))
                rows.append({'kind':kind,'stem':path.stem,'top1':result['top1'],'p_face':result['p_face']})
        embeddings[kind]=np.concatenate(emb)
        print(f'CLIP {kind}: 100/100; {time.monotonic()-start:.1f}s',flush=True)
    np.savez_compressed(args.analysis/'clip_embeddings.npz',stems=np.array(stems),**embeddings)
    for name,data in [('clip_zero_shot.csv',rows),('depth_output_ranges.csv',map_rows)]:
        with (args.analysis/name).open('w',newline='') as fh:
            writer=csv.DictWriter(fh,fieldnames=data[0]);writer.writeheader();writer.writerows(data)
    clip_weight=paths['clip']/('model.safetensors' if (paths['clip']/'model.safetensors').exists() else 'pytorch_model.bin')
    info={'seconds':time.monotonic()-start,'device':device,'threads':args.threads,'images_per_kind':100,
        'input_size':[w,h],'models':{'depth':{'id':DEPTH_ID,'revision':DEPTH_REV,'safetensors_sha256':HASHES['depth']},
        'clip':{'id':CLIP_ID,'config_revision':CLIP_REV,'weights_revision':CLIP_SAFE_REV if clip_weight.suffix=='.safetensors' else CLIP_REV,
                'weight_file':clip_weight.name,'weight_sha256':sha256(clip_weight)}},
        'versions':{'python':platform.python_version(),'torch':torch.__version__,'transformers':transformers.__version__,'numpy':np.__version__,'opencv':cv2.__version__},
        'depth_preprocessing':depth_proc.to_dict(),'clip_image_preprocessing':clip_proc.image_processor.to_dict(),
        'depth_export':'Relative inverse depth. Full-resolution bicubic interpolation; each saved 16-bit PNG and INFERNO JPEG independently min-max normalized. Not metric depth.',
        'prompt_set':LABELS}
    (args.analysis/'run_info.json').write_text(json.dumps(info,indent=2))
    print('Both models complete:',round(info['seconds'],1),'seconds',flush=True)


if __name__=='__main__':main()
