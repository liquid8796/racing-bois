"""Reproducible read-only corpus audit; summaries never imply gameplay completion.

Run from anywhere: python tools/run_phase0.py --source <reference-folder>
Private decoded data is written only under ReferenceOnly/phase0. Summaries and
hashes are safe to review separately. No legacy executable is launched here.
"""
from __future__ import annotations
import argparse,collections,datetime,hashlib,io,json,random,struct,sys,traceback,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tools/python'))
from PIL import Image
from research_formats import (resources,sprites,encode_sprites,decode_family,family_tree,
    course_sections,save_envelope,legacy_checksum,riff_chunks,midi_structure,sfnt_structure)
from native_oracle import Oracle,port_spec

def write(path: Path,value) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(path)

def inventory(source: Path) -> list[dict]:
    rows=[]
    for p in sorted(source.rglob('*')):
        if not p.is_file():continue
        if p.is_symlink():raise ValueError('Reference symlinks must be audited separately')
        h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
        rows.append(dict(path=p.relative_to(source).as_posix(),bytes=p.stat().st_size,sha256=h.hexdigest()))
    return rows

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=Path(r'C:\Users\Liquid\Downloads\Unity\racing_bois_mod'))
    args=ap.parse_args();source=args.source.resolve()
    if not source.is_dir():raise ValueError('Reference directory missing')
    if ROOT==source or ROOT.is_relative_to(source):raise ValueError('Outputs would modify the reference tree')
    out=ROOT/'docs/research/evidence/phase0';private=ROOT/'ReferenceOnly/phase0'
    original=inventory(source);write(out/'inventory.json',original)
    oracle=Oracle((source/'RacingBois.exe').read_bytes())
    report=dict(version='0.1.2',generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                files=len(original),bytes=sum(x['bytes'] for x in original),
                unique_file_hashes=len({x['sha256'] for x in original}),
                extensions=dict(collections.Counter(Path(x['path']).suffix.lower() for x in original)),
                resource_containers=0,resource_entries=0,images=0,wave=0,saves_valid=0,
                save_like_not_valid=0,errors=[],oracle_spec_cases=0,oracle_dat_records=0,oracle_checksum_cases=0)
    catalogs=dict(resources=[],sprites=[],families=[],courses=[],saves=[],media=[])
    params=[-100,-1,0,1,3,4,7,8,50,74,75,76,79,80,100,150,200,300,500]
    for row in original:
        p=source/row['path'];b=p.read_bytes();ext=p.suffix.lower();rel=row['path']
        try:
            if b[:4]==b'CRSR':
                rs=resources(b);report['resource_containers']+=1;report['resource_entries']+=len(rs)
                for r in rs:
                    catalogs['resources'].append(dict(path=rel,type=r.tag,id=r.id,offset=r.offset,bytes=r.size,sha256=hashlib.sha256(r.data).hexdigest()))
                    if r.tag=='SPEC':
                        for parameter in params:
                            actual=oracle.spec(r.data,r.id-1,parameter);expected=port_spec(r.data,parameter)
                            if actual!=expected:raise AssertionError(f'SPEC oracle mismatch: ID{r.id}, parameter{parameter}')
                            report['oracle_spec_cases']+=1
                    if r.tag=='FAM':
                        body,meta=decode_family(r.data);tree=family_tree(body)
                        meta.update(id=r.id,tree=tree);catalogs['families'].append(meta)
                        dest=private/'families'/f'{r.id:04d}.bin';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
                    if r.tag=='SGS':catalogs['courses'].append(dict(path=rel,**course_sections(r.data)))
            elif ext=='.dat' and 'BIKERS' in p.parts:
                frames=sprites(b)
                if encode_sprites(frames)!=b:raise AssertionError('DAT roundtrip mismatch')
                native,consumed=oracle.dat(b,len(frames))
                expected=[(f.offset+2 if f.pixels else -1,f.width,f.height) for f in frames]
                if native!=expected or consumed!=len(b):raise AssertionError('DAT native walker mismatch')
                report['oracle_dat_records']+=len(frames)
                catalogs['sprites'].append(dict(path=rel,records=len(frames),nonempty=sum(bool(f.pixels) for f in frames),
                    exact_eof=True,oracle_match=True,dimensions=[(f.width,f.height) for f in frames]))
            elif ext=='.rrs' or (not ext and len(b)==160):
                try:
                    v=save_envelope(b)
                    if oracle.checksum(b[4:])!=v['checksum']:raise AssertionError('Save native checksum mismatch')
                    report['saves_valid']+=1;report['oracle_checksum_cases']+=1
                    catalogs['saves'].append(dict(path=rel,valid=True,checksum=v['checksum'],sha256=row['sha256']))
                except ValueError as ex:
                    if ext=='.rrs':raise
                    report['save_like_not_valid']+=1
                    catalogs['saves'].append(dict(path=rel,valid=False,reason=str(ex)))
            elif ext in ('.rri','.bmp'):
                with Image.open(io.BytesIO(b)) as im:
                    im.load();catalogs['media'].append(dict(path=rel,kind='image',format=im.format,width=im.width,height=im.height))
                report['images']+=1
            elif b[:4]==b'RIFF':
                info=riff_chunks(b)
                if info['form']=='WAVE':
                    with wave.open(io.BytesIO(b)) as w:info.update(channels=w.getnchannels(),sample_rate=w.getframerate(),frames=w.getnframes(),duration=w.getnframes()/w.getframerate())
                    report['wave']+=1
                catalogs['media'].append(dict(path=rel,kind='riff',**info))
            elif b[:4]==b'MThd':catalogs['media'].append(dict(path=rel,kind='midi',**midi_structure(b)))
            elif b[:4]==bytes.fromhex('00010000'):catalogs['media'].append(dict(path=rel,kind='font_metadata_only',**sfnt_structure(b)))
        except Exception as ex:
            report['errors'].append(dict(path=rel,error=str(ex),exception=type(ex).__name__))
    rng=random.Random(20260926)
    for n in [0,1,2,3,4,7,8,15,16,31,32,155,156,157,255,256,511,1024,2048]:
        for blob in (bytes(n),bytes([255])*n,rng.randbytes(n)):
            if oracle.checksum(blob)!=legacy_checksum(blob):raise AssertionError('Synthetic checksum oracle mismatch')
            report['oracle_checksum_cases']+=1
    import phase0_tests
    log=io.StringIO();tests=unittest.defaultTestLoader.loadTestsFromModule(phase0_tests)
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(tests)
    (out/'tests.txt').write_text(log.getvalue(),encoding='utf-8')
    report['unit_tests']=dict(run=result.testsRun,failures=len(result.failures),errors=len(result.errors),passed=result.wasSuccessful())
    final=inventory(source);report['source_unchanged']=original==final
    fam=catalogs['families'];banks=catalogs['sprites'];courses=catalogs['courses']
    report.update(families_decoded=len(fam),family_placeholders=sum(f['placeholder'] for f in fam),
                  unique_family_payloads=len({f['sha256'] for f in fam}),dat_banks=len(banks),
                  sprite_records=sum(f['records'] for f in banks),sprite_nonempty=sum(f['nonempty'] for f in banks),
                  course_descriptor_count=sum(c['count'] for c in courses),course_nested_chunks=sum(len(c['blocks']) for c in courses))
    report['scope']='Structural parsing and bounded function-level native equivalence; not whole-game runtime or production asset validation.'
    report['passed']=not report['errors'] and report['source_unchanged'] and result.wasSuccessful()
    for name,value in catalogs.items():write(out/(name+'.json'),value)
    write(out/'summary.json',report);print(json.dumps(report,ensure_ascii=True,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:traceback.print_exc();raise SystemExit(2)
