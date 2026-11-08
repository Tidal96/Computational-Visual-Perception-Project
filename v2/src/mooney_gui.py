"""Local interactive GUI for the same generator used by the batch CLI.

python mooney_gui.py --original submission/Original --settings analysis/settings.csv
Open http://127.0.0.1:8765. This server binds to localhost only.
"""
import argparse, base64, csv, html, json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import cv2
from mooney_tool import make_mooney

PAGE = '''<!doctype html><html><head><meta charset="utf-8"><title>Mooney Studio · CompVP Part 1</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf1f6;color:#142339;font:16px Arial,sans-serif}header{background:#12253c;color:white;padding:24px 40px;display:flex;justify-content:space-between;align-items:center}h1{margin:4px 0;font-size:28px;letter-spacing:-.5px}.eyebrow{color:#80d5c1;font-size:12px;letter-spacing:2px}header a{color:#cce1f2;margin-left:20px}main{max-width:1380px;margin:25px auto;padding:0 22px}.controls,.pair{background:white;border:1px solid #d9e1eb;border-radius:12px;padding:20px}.controls{display:grid;grid-template-columns:150px 1fr 1fr 150px;gap:26px;align-items:center;margin-bottom:20px}label{font-size:13px;color:#506176;display:block}input[type=range]{width:100%;accent-color:#138e77}select,button{font:16px Arial;padding:10px;border:1px solid #ccd8e5;border-radius:6px;background:#f8fafc}button{background:#12866f;color:white;cursor:pointer}.value{font-size:19px;font-weight:bold;color:#12253c;float:right}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}.imagehead{display:flex;justify-content:space-between;color:#556c83;font-size:13px;margin:0 0 10px}.imagehead b{color:#152a42;font-size:17px}.pair img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:black;border-radius:6px}.meta{display:flex;justify-content:space-between;margin-top:16px;color:#405970;font-size:13px}.note{color:#536982;line-height:1.65;margin:15px 4px;font-size:13px}.tag{background:#e0f4ee;color:#07674f;border-radius:4px;padding:4px 8px}a{color:#13725f;text-decoration:none}pre{white-space:pre-wrap}#download{font-weight:bold}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:20px}.footer code{background:#dfe7f0;padding:10px;font-size:12px}</style></head><body>
<header><div><div class="eyebrow">COMPUTATIONAL VISUAL PERCEPTION / PART 1</div><h1>Mooney Studio</h1></div><nav><a href="/code">Generator source</a><a href="/log">Actual batch log</a></nav></header>
<main><section class="controls"><div><label>IMAGE ID</label><select id="stem">OPTIONS</select></div><div><label>WHITE PIXELS <span class="value" id="wv"></span></label><input id="white" type="range" min="5" max="65" step="1" value="28"></div><div><label>GAUSSIAN BLUR <span class="value" id="sv"></span></label><input id="sigma" type="range" min="0" max="24" step="1" value="8"></div><button id="apply">Apply controls</button></section>
<section class="pair"><div><div class="imagehead"><b>Original</b><span>FFHQ export · PNG</span></div><img id="original"><div class="meta"><span>Provided resolution: 1024 × 1024</span><span>Preserved input</span></div></div><div><div class="imagehead"><b>Mooney</b><span class="tag">Binary output · 0 / 255</span></div><img id="mooney"><div class="meta"><span id="stats">Processing…</span><a id="download" download="Mooney.png">Download PNG ↓</a></div></div></section>
<div class="note">The same function powers this preview and the batch CLI. Processing: grayscale → Gaussian blur → global brightness threshold. Controls change the actual full-resolution PNG. No resizing is used during generation.</div><div class="footer"><code>python mooney_tool.py Original/ Mooney/ --params settings.csv --log actual.csv</code><span class="note">Single image or 100+ image batches</span></div></main>
<script>const $=id=>document.getElementById(id);let timer;
function labels(){$('wv').textContent=$('white').value+'%';$('sv').textContent=$('sigma').value+' px';}
async function update(){labels();const stem=$('stem').value;$('original').src='/original?stem='+stem;const r=await fetch('/convert',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({stem,white:+$('white').value,sigma:+$('sigma').value})});const data=await r.json();if(!r.ok){$('stats').textContent=data.error;return;}const uri='data:image/png;base64,'+data.png;$('mooney').src=uri;$('download').href=uri;$('download').download=stem+'_mooney.png';$('stats').textContent=data.info.width+' × '+data.info.height+' · white '+data.info.white_pct_actual.toFixed(3)+'% · kernel '+data.info.ksize;$('mooney').dataset.info=JSON.stringify(data.info);}
async function changeImage(){const r=await fetch('/settings?stem='+$('stem').value);const data=await r.json();$('white').value=data.white_pct;$('sigma').value=data.sigma;await update();}
for(const id of ['white','sigma'])$(id).oninput=()=>{labels();clearTimeout(timer);timer=setTimeout(update,200);};$('stem').onchange=changeImage;$('apply').onclick=update;$('stem').value='010';changeImage();</script></body></html>'''


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--original',type=Path,required=True);ap.add_argument('--settings',type=Path,required=True)
    ap.add_argument('--log',type=Path);ap.add_argument('--port',type=int,default=8765)
    args=ap.parse_args();files={p.stem:p for p in sorted(args.original.glob('*.png'))}
    with args.settings.open() as fh:settings={Path(x['file']).stem:x for x in csv.DictReader(fh)}
    class Handler(BaseHTTPRequestHandler):
        def send(self,data,kind='text/html; charset=utf-8',status=200):
            if isinstance(data,str):data=data.encode()
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_GET(self):
            path=urlparse(self.path);stem=parse_qs(path.query).get('stem',[''])[0]
            if path.path=='/':self.send(PAGE.replace('OPTIONS',''.join(f'<option>{s}</option>' for s in files)))
            elif path.path=='/original' and stem in files:self.send(files[stem].read_bytes(),'image/png')
            elif path.path=='/settings' and stem in settings:self.send(json.dumps(settings[stem]),'application/json')
            elif path.path in ['/code','/log']:
                if path.path=='/code':
                    src=(Path(__file__).parent/'mooney_tool.py').read_text();src=src[src.index('def make_mooney'):src.index('\ndef main')];title='Actual generator source'
                else:src=args.log.read_text() if args.log else 'No batch log supplied';title='Actual batch execution log'
                self.send('<html><head><title>'+title+'</title><style>body{background:#122238;color:#e4edf7;margin:30px;font:17px monospace}h1{font:25px Arial;color:#8cdec6}pre{line-height:1.5;white-space:pre-wrap}</style></head><body><h1>'+title+'</h1><pre>'+html.escape(src)+'</pre></body></html>')
            else:self.send('Not found',status=404)
        def do_POST(self):
            try:
                if self.path!='/convert':return self.send('Not found',status=404)
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<4096:raise ValueError('invalid request size')
                data=json.loads(self.rfile.read(length));stem=str(data['stem'])
                if stem not in files:raise ValueError('unknown image ID')
                m,info=make_mooney(cv2.imread(str(files[stem])),float(data['white']),float(data['sigma']))
                ok,png=cv2.imencode('.png',m);assert ok
                self.send(json.dumps({'png':base64.b64encode(png).decode(),'info':info}),'application/json')
            except (KeyError,ValueError) as error:self.send(json.dumps({'error':str(error)}),'application/json',400)
    print(f'GUI at http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()


if __name__=='__main__':main()
