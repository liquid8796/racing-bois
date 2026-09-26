"""Repeatable corpus conformance. Native tests cover selected functions only."""
from __future__ import annotations
import argparse,collections,concurrent.futures,datetime,hashlib,json,random,struct,subprocess,sys,wave,xml.etree.ElementTree as ET
from pathlib import Path
from research_formats import resources,sprites,encode_sprites,decode_family,family_tree,course_sections,riff_chunks,sfnt_structure,legacy_checksum
from mids_reference import mids_events
from native_oracle import Oracle,port_spec,EXE_SHA
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=Path(r'C:\Users\Liquid\Downloads\Unity\racing_bois_mod')

def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)
def inventory(source):
    return [dict(path=p.relative_to(source).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(source.rglob('*')) if p.is_file()]
def flatten(node):
    return [node]+[x for child in node.get('children',[]) for x in flatten(child)]

def validate_paths(source: Path, out: Path) -> tuple[Path, Path]:
    source, out = source.resolve(), out.resolve()
    root = ROOT.resolve()
    if not source.is_dir():
        raise ValueError('Reference source directory does not exist')
    if not out.is_relative_to(root/'docs/research/evidence'):
        raise ValueError('Output must be under this workspace docs/research/evidence')
    if out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('Output and source must not overlap')
    private = (root/'ReferenceOnly').resolve()
    if private.is_relative_to(source) or source.is_relative_to(private):
        raise ValueError('Source cannot overlap ReferenceOnly output')
    return source, out


def run(source: Path,out: Path,media: bool):
    source, out = validate_paths(source, out)
    before=inventory(source);run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    version=ET.parse(ROOT/'Directory.Build.props').findtext('.//Version')
    errors=[];catalog=[];types=collections.Counter();families=[];courses=[];banks=[];saves=[];native=[]
    oracle=Oracle((source/'RacingBois.exe').read_bytes());rng=random.Random(260926)
    parameters=[-20,-1,0,1,3,4,74,75,76,100,255,300]+[rng.randrange(0,501) for _ in range(40)]
    for row in before:
        p=source/row['path'];data=p.read_bytes();ext=p.suffix.lower();item=dict(row)
        try:
            if data[:4]==b'CRSR':
                entries=resources(data);item.update(kind='RSRC',entries=len(entries))
                for e in entries:
                    types[e.tag]+=1
                    if e.tag=='FAM':
                        body,info=decode_family(e.data);info['id']=e.id;info['tree']=family_tree(body)
                        info['leaf_count']=sum(x['kind']=='opaque' for x in flatten(info['tree']));families.append(info)
                        dest=ROOT/'ReferenceOnly/phase0b/families'/f'{e.id:04d}.bin';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
                    elif e.tag=='SGS':
                        info=course_sections(e.data);info['source']=row['path'];courses.append(info)
                    elif e.tag=='SPEC':
                        for parameter in parameters:
                            actual=oracle.spec(e.data,e.id-1,parameter);expected=port_spec(e.data,parameter);match=actual==expected
                            native.append(dict(kind='SPEC',id=e.id,parameter=parameter,match=match,output_sha256=sha(actual)))
                            if not match:errors.append(dict(source=row['path'],test='SPEC native mismatch',id=e.id,parameter=parameter))
            elif ext=='.dat':
                records=sprites(data);actual,used=oracle.dat(data,len(records))
                expected=[(x.offset+2 if x.pixels else -1,x.width,x.height) for x in records]
                match=actual==expected and used==len(data) and encode_sprites(records)==data
                item.update(kind='DAT',records=len(records),nonempty=sum(bool(x.pixels) for x in records),native_match=match)
                banks.append(item);native.append(dict(kind='DAT',source=row['path'],match=match,records=len(records)))
                if not match:errors.append(dict(source=row['path'],test='DAT conformance'))
            elif data[:4]==b'RIFF':
                riff=riff_chunks(data);item.update(kind='RIFF/'+riff['form'],trailing_bytes=riff['trailing_bytes'])
                if riff['form']=='MIDS':
                    midi=mids_events(data)
                    item.update(events=len(midi['events']),buffers=len(midi['buffers']),division=midi['division'],last_tick=midi['last_tick'],event_types=dict(collections.Counter(x['kind'] for x in midi['events'])))
                    save(ROOT/'ReferenceOnly/phase0b/mids'/(p.stem+'.json'),midi)
                elif riff['form']=='WAVE':
                    with wave.open(str(p),'rb') as audio:
                        raw=audio.readframes(audio.getnframes())
                        if len(raw)!=audio.getnframes()*audio.getnchannels()*audio.getsampwidth():raise ValueError('truncated PCM')
                        item.update(channels=audio.getnchannels(),rate=audio.getframerate(),bits=8*audio.getsampwidth(),seconds=audio.getnframes()/audio.getframerate())
            elif ext in ('.rri','.bmp'):
                with Image.open(p) as image:image.load();item.update(kind=image.format,width=image.width,height=image.height)
            elif ext=='.dll' and data[:2]!=b'MZ':item.update(kind='sfnt-font-metadata',tables=len(sfnt_structure(data)['tables']))
            elif ext=='.rrs' or ext=='' and len(data)==160:
                if len(data)!=160:raise ValueError('save size')
                expected=legacy_checksum(data[4:]);actual=oracle.checksum(data[4:]);stored=struct.unpack_from('<I',data)[0]
                item.update(kind='save',magic_valid=data[4:8]==bytes.fromhex('addefeca'),checksum_valid=stored==expected,native_match=expected==actual)
                if ext=='' and data==bytes(160):
                    # Four root files are all-zero duplicates, not valid RRS saves.
                    item.update(kind='zero-filled-reference-file',not_a_valid_save=True)
                    native.append(dict(kind='zero-file-checksum',source=row['path'],match=expected==actual))
                else:
                    saves.append(item);native.append(dict(kind='save-checksum',source=row['path'],match=expected==actual))
                    if not item['magic_valid'] or not item['checksum_valid']:
                        errors.append(dict(source=row['path'],test='invalid saved envelope'))
                if expected!=actual:errors.append(dict(source=row['path'],test='checksum oracle'))
            elif data[:2]==b'MZ':item['kind']='native-PE'
            elif ext=='.bob':item['kind']='raw-indexed-BOB-dimensions-pending'
            elif ext=='.mip':item['kind']='MIP-layout-pending'
            else:item['kind']='support-file'
        except Exception as error:
            item['error']=str(error);errors.append(dict(source=row['path'],test='parse',error=str(error)))
        catalog.append(item)
    for i in range(80):
        payload=rng.randbytes(rng.randrange(0,1025));actual=oracle.checksum(payload);expected=legacy_checksum(payload)
        native.append(dict(kind='checksum-random',case=i,length=len(payload),match=actual==expected))
        if actual!=expected:errors.append(dict(test='random checksum oracle',case=i))
    media_results=[]
    if media:
        def probe(row):
            p=source/row['path'];result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,timeout=45)
            if result.returncode:return dict(source=row['path'],error=result.stderr.decode(errors='replace'))
            meta=json.loads(result.stdout)
            check=subprocess.run(['ffmpeg','-v','error','-nostdin','-threads','1','-i',str(p),'-map','0:v:0','-frames:v','1','-f','null','-'],capture_output=True,timeout=45)
            return dict(source=row['path'],duration=meta.get('format',{}).get('duration'),streams=[{k:x[k] for k in ['codec_type','codec_name','width','height','sample_rate'] if k in x} for x in meta['streams']],first_video_frame_decoded=check.returncode==0,stderr=check.stderr.decode(errors='replace'))
        def safe_probe(row):
            try:
                return probe(row)
            except (subprocess.TimeoutExpired, OSError, ValueError, KeyError) as error:
                return dict(source=row['path'], error=str(error), first_video_frame_decoded=False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            media_results=list(pool.map(safe_probe,[x for x in before if x['path'].lower().endswith('.avi')]))
        for result in media_results:
            if not result.get('first_video_frame_decoded',False):
                errors.append(dict(source=result['source'],test='AVI first frame',error=result.get('error',result.get('stderr','decode failed'))))
    after=inventory(source);unchanged=before==after
    old_path=ROOT/'docs/research/evidence/inventory.json';old=json.loads(old_path.read_text()) if old_path.exists() else []
    baseline=bool(old) and {x['path']:x['sha256'] for x in old}=={x['path']:x['sha256'] for x in before}
    result=dict(run_id=run_id,tool_version=version,files=len(before),bytes=sum(x['bytes'] for x in before),unique_hashes=len({x['sha256'] for x in before}),original_hashes_unchanged=unchanged,previous_inventory_matches=baseline,executable_sha256=EXE_SHA,
        kinds=dict(collections.Counter(x.get('kind','parse-failed') for x in catalog)),resource_types=dict(types),families=len(families),family_placeholders=sum(x['placeholder'] for x in families),family_leaves=sum(x['leaf_count'] for x in families),course_sections=sum(x['count'] for x in courses),course_chunks=sum(len(x['blocks']) for x in courses),
        dat_records=sum(x['records'] for x in banks),dat_nonempty=sum(x['nonempty'] for x in banks),native_cases=len(native),native_matches=sum(x['match'] for x in native),save_samples=len(saves),valid_save_checksums=sum(x['checksum_valid'] for x in saves),avi_probed=len(media_results),avi_first_frame_decoded=sum(x.get('first_video_frame_decoded',False) for x in media_results),errors=errors,
        classification_note='Four all-zero extensionless files are not saves; only 14 RRS envelopes are valid.',
        limitation='Native cases validate three selected functions only, not full gameplay or production assets.')
    for name,value in [('inventory',before),('catalog',catalog),('families',families),('courses',courses),('native_cases',native),('media',media_results),('summary',result)]:save(out/(name+'.json'),value)
    print(json.dumps(result,indent=2))
    return 0 if unchanged and baseline and not errors and all(x['match'] for x in native) else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=DEFAULT);parser.add_argument('--out',type=Path,default=ROOT/'docs/research/evidence/phase0b');parser.add_argument('--media',action='store_true')
    args=parser.parse_args();sys.exit(run(args.source,args.out,args.media))
