"""Timestamped video samples; sampling is not a claim of watching every frame."""
from __future__ import annotations
import concurrent.futures, hashlib, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
VIDEO = Path(r'C:\Users\Liquid\Downloads\prompt\Road Rash PC (1995) - Big Game Mode (All Levels).mp4')
OUT = ROOT/'docs/research/evidence/video'
OUT.mkdir(parents=True,exist_ok=True)

def extract(t: int) -> dict:
    p = OUT/f'frame_{t:05d}.jpg'
    if not p.exists():
        r = subprocess.run(['ffmpeg','-v','error','-nostdin','-threads','1','-ss',str(t),'-i',str(VIDEO),'-frames:v','1','-q:v','2','-y',str(p)],capture_output=True,timeout=90)
        if r.returncode: return {'seconds':t,'error':r.stderr.decode(errors='replace')[:1000]}
    return {'seconds':t,'timestamp':f'{t//3600:02d}:{t//60%60:02d}:{t%60:02d}','file':p.name}

if __name__ == '__main__':
    times=[0,30,60,120,180,240,360,480,600,900,1200,1500,1800,2100,2400,2700,3000,3300,3600,3900,4200,4500,4800,5100,5400,5700,6000,6300,6600,6900,7200,7500,7800,8100,8400,8700,9000,9200,9250]
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(VIDEO)]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        samples=list(pool.map(extract,times))
    h=hashlib.sha256()
    with VIDEO.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    report={'source':str(VIDEO),'sha256':h.hexdigest(),'metadata':metadata,'samples':samples,'method':'Sparse timestamped sampling; not exhaustive scene/event coverage.'}
    (OUT/'video_samples.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for start in range(0,len(samples),12):
        group=samples[start:start+12]
        sheet=Image.new('RGB',(1280,((len(group)+3)//4)*266),(20,20,20)); draw=ImageDraw.Draw(sheet)
        for i,s in enumerate(group):
            if 'file' not in s:continue
            with Image.open(OUT/s['file']) as im:
                im.thumbnail((320,240)); x=i%4*320;y=i//4*266
                sheet.paste(im,(x,y));draw.text((x+8,y+244),s['timestamp'],fill='white')
        sheet.save(OUT/f'contact_sheet_{start//12+1}.jpg')
    print(json.dumps({'duration':metadata['format']['duration'],'sha256':h.hexdigest(),'sample_count':len(samples),'errors':[s for s in samples if 'error' in s]}))
