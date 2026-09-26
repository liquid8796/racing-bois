"""Read-only legacy reference audit; outputs never go into Unity Assets/."""
from __future__ import annotations
import collections, csv, hashlib, json, re, struct, sys, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools/python'))
SOURCE = Path(r'C:\Users\Liquid\Downloads\Unity\racing_bois_mod')
OUT = ROOT / 'docs/research/evidence'
REF = ROOT / 'ReferenceOnly/decoded'
OUT.mkdir(parents=True, exist_ok=True)
REF.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from('<I', data, offset)[0]

def fourcc(data: bytes) -> str:
    return data[::-1].decode('ascii', errors='replace').strip()

def main() -> None:
    from PIL import Image, ImageDraw
    import pefile
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM
    inventory, images, audio, containers, saves, pes = [], [], [], [], [], []
    grouped: dict[str, list[str]] = collections.defaultdict(list)
    for path in sorted(SOURCE.rglob('*')):
        if not path.is_file():
            continue
        data = path.read_bytes()
        rel = path.relative_to(SOURCE).as_posix()
        sha = hashlib.sha256(data).hexdigest()
        row = {'path': rel, 'bytes': len(data), 'sha256': sha, 'extension': path.suffix.lower(), 'magic_hex': data[:16].hex()}
        inventory.append(row)
        grouped[sha].append(rel)
        ext = path.suffix.lower()
        if ext in ('.rri', '.bmp'):
            try:
                with Image.open(path) as im:
                    im.load()
                    dest = REF / 'images' / Path(rel).with_suffix('.png')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    im.convert('RGB').save(dest)
                    images.append({'path': rel, 'format': im.format, 'size': list(im.size), 'mode': im.mode, 'decoded': True})
            except Exception as exc:
                images.append({'path': rel, 'error': str(exc)})
        if data[:4] == b'RIFF' and data[8:12] == b'WAVE':
            try:
                with wave.open(str(path), 'rb') as wav:
                    audio.append({'path': rel, 'channels': wav.getnchannels(), 'sample_rate': wav.getframerate(), 'bits': wav.getsampwidth()*8, 'frames': wav.getnframes(), 'duration': wav.getnframes()/wav.getframerate(), 'sha256': sha})
                if ext == '.rra':
                    dest = REF / 'audio' / (path.stem + '.wav')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
            except Exception as exc:
                audio.append({'path': rel, 'error': str(exc)})
        if data[:4] == b'CRSR':
            table = u32(data, 16)
            if data[table:table+4] != b'LBTR':
                raise ValueError(f'Invalid resource table: {rel}')
            count = u32(data, table+8)
            if count > 100000 or table + 16 + 32*count > len(data):
                raise ValueError(f'Invalid descriptor bounds: {rel}')
            entries = []
            for idx in range(count):
                pos = table + 16 + 32*idx
                tag, rid, offset, size = struct.unpack_from('<4sIII', data, pos)
                # RTBL points directly at the payload. There is no generic
                # type/size prefix at this location; ANIM/CEL have inner headers.
                in_bounds = offset >= table+16+32*count and offset+size <= len(data)
                entry = {'index': idx, 'type': fourcc(tag), 'id': rid, 'offset': offset, 'size': size, 'in_bounds': in_bounds, 'descriptor_hex': data[pos:pos+32].hex(), 'status': 'structural-only'}
                if in_bounds:
                    payload = data[offset:offset+size]
                    entry['payload_sha256'] = hashlib.sha256(payload).hexdigest()
                    dest = REF / 'resources' / rel / f'{idx:04d}_{fourcc(tag)}_{rid}.bin'
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(payload)
                    assert dest.read_bytes() == payload, f'Extraction roundtrip failed: {dest}'
                    entry['roundtrip_match'] = True
                    entry['first_64_hex'] = payload[:64].hex(' ')
                    if fourcc(tag) == 'SPEC':
                        entry['u32'] = list(struct.unpack('<'+'I'*(len(payload)//4), payload[:len(payload)//4*4]))
                        entry['i32'] = list(struct.unpack('<'+'i'*(len(payload)//4), payload[:len(payload)//4*4]))
                        entry['semantic_warning'] = 'Raw fields only; units and behavior require code/runtime confirmation.'
                entries.append(entry)
            containers.append({'path': rel, 'version': u32(data,8), 'table_offset': table, 'count': count, 'entries': entries})
        if ext == '.rrs' or (ext == '' and len(data) == 160):
            saves.append({'path': rel, 'bytes': len(data), 'header_hex': data[:20].hex(' '), 'name_at_20': data[20:48].split(b'\0')[0].decode('cp1252', errors='replace'), 'dwords': list(struct.unpack('<40I', data)), 'hex': data.hex(' ')})
        if data[:2] == b'MZ':
            try:
                pe = pefile.PE(data=data)
                info = {'path': rel, 'machine': hex(pe.FILE_HEADER.Machine), 'image_base': hex(pe.OPTIONAL_HEADER.ImageBase), 'entry_rva': hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint), 'timestamp_raw': pe.FILE_HEADER.TimeDateStamp,
                    'sections': [{'name': s.Name.rstrip(b'\0').decode(errors='replace'), 'rva': s.VirtualAddress, 'virtual_bytes': s.Misc_VirtualSize, 'raw_offset': s.PointerToRawData, 'raw_bytes': s.SizeOfRawData, 'entropy': s.get_entropy()} for s in pe.sections],
                    'imports': [{'dll': d.dll.decode(errors='replace'), 'functions': [i.name.decode(errors='replace') if i.name else f'ordinal:{i.ordinal}' for i in d.imports]} for d in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[])],
                    'resource_types': []}
                strings = [{'offset': m.start(), 'text': m.group().decode('ascii')} for m in re.finditer(rb'[\x20-\x7e]{5,}', data)]
                write_json(OUT / 'strings' / f'{rel.replace("/","_")}.json', strings)
                loc = []
                for typ in getattr(getattr(pe,'DIRECTORY_ENTRY_RESOURCE',None),'entries',[]):
                    info['resource_types'].append({'id': typ.id, 'name': str(typ.name) if typ.name else None, 'count': len(typ.directory.entries)})
                    if typ.id != 6:
                        continue
                    for block in typ.directory.entries:
                        for lang in block.directory.entries:
                            d = lang.data.struct
                            blob = pe.get_data(d.OffsetToData,d.Size)
                            off = 0
                            for k in range(16):
                                if off+2 > len(blob): break
                                n = struct.unpack_from('<H',blob,off)[0]; off += 2
                                value = blob[off:off+2*n].decode('utf-16-le',errors='replace'); off += 2*n
                                if value: loc.append({'id': (block.id-1)*16+k, 'language': lang.id, 'text': value})
                if loc: write_json(OUT / 'localization' / f'{path.stem}.json', loc)
                info['localized_strings'] = len(loc)
                if path.name.lower() == 'racingbois.exe':
                    anchors = {}
                    keywords = re.compile(r'(?i)bike|course|\.crs|\.rsc|\.rrs|damage|punch|kick|nitro|race|rider|speed|weapon|police|network|dplay|directplay|level|save|money|cash|rsrc|win|wreck|bust')
                    for item in strings:
                        if not keywords.search(item['text']): continue
                        try:
                            va = pe.OPTIONAL_HEADER.ImageBase+pe.get_rva_from_offset(item['offset'])
                            anchors[va] = item
                        except Exception: pass
                    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
                    refs, calls = [], []
                    iat = {i.address: f'{d.dll.decode()}!{i.name.decode() if i.name else i.ordinal}' for d in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]) for i in d.imports}
                    count_ins = 0
                    asm_path = OUT / 'RacingBois.text.asm'
                    with asm_path.open('w',encoding='utf-8') as stream:
                        for sec in pe.sections:
                            if not sec.Characteristics & 0x20000000: continue
                            for ins in md.disasm(sec.get_data(), pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress):
                                count_ins += 1
                                stream.write(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}\n')
                                if ins.id == 0: continue
                                for op in ins.operands:
                                    val = op.imm if op.type == CS_OP_IMM else op.mem.disp if op.type == CS_OP_MEM else None
                                    if val in anchors:
                                        refs.append({'instruction_va': hex(ins.address), 'instruction': ins.mnemonic+' '+ins.op_str, 'string_va': hex(val), 'text': anchors[val]['text']})
                                    if val in iat:
                                        calls.append({'instruction_va': hex(ins.address), 'instruction': ins.mnemonic+' '+ins.op_str, 'import': iat[val]})
                    write_json(OUT / 'code_string_xrefs.json',refs)
                    write_json(OUT / 'code_import_xrefs.json',calls)
                    info['linear_disassembly_instructions'] = count_ins
                    info['keyword_xrefs'] = len(refs)
                    info['analysis_warning'] = 'Linear disassembly and literal references are navigation aids, NOT validated function boundaries or recovered semantics.'
                pes.append(info)
            except Exception as exc:
                pes.append({'path': rel, 'error': str(exc)})
    for name, obj in [('inventory',inventory),('image_catalog',images),('audio_catalog',audio),('resource_tables',containers),('save_samples',saves),('pe_analysis',pes)]:
        write_json(OUT / f'{name}.json',obj)
    with (OUT/'inventory.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w = csv.DictWriter(f,fieldnames=inventory[0].keys()); w.writeheader(); w.writerows(inventory)
    byext = collections.defaultdict(lambda: {'files':0,'bytes':0})
    for item in inventory:
        byext[item['extension']]['files'] += 1
        byext[item['extension']]['bytes'] += item['bytes']
    summary = {'source':str(SOURCE),'files':len(inventory),'bytes':sum(i['bytes'] for i in inventory),'unique_file_hashes':len(grouped),'duplicate_groups':[v for v in grouped.values() if len(v)>1], 'extensions':dict(byext),'decoded_images':sum(bool(i.get('decoded')) for i in images),'wave_files':len(audio),'resource_containers':len(containers),'resource_entries':sum(c['count'] for c in containers),'resource_entries_validated':sum(e['in_bounds'] and e.get('roundtrip_match',False) for c in containers for e in c['entries']), 'resource_validation_scope':'descriptor bounds and byte-exact extraction, not semantic asset decoding', 'save_samples':len(saves), 'pe_files':len(pes)}
    write_json(OUT/'summary.json',summary)
    # Contact sheets are inspection aids, not production concepts.
    chosen = sorted((REF/'images/IMAGES/BIKES').rglob('*.png'))
    chosen += [REF/'images/IMAGES/MAIN.png', REF/'images/IMAGES/STREET.png']
    sheet = Image.new('RGB',(1000,((len(chosen)+3)//4)*212),(30,30,30)); draw = ImageDraw.Draw(sheet)
    for idx,p in enumerate(chosen):
        if not p.exists(): continue
        with Image.open(p) as im:
            im.thumbnail((244,184)); x=(idx%4)*250; y=(idx//4)*212
            sheet.paste(im,(x,y)); draw.text((x,y+186),str(p.relative_to(REF/'images/IMAGES'))[:36],fill='white')
    sheet.save(OUT/'reference_bikes_contact_sheet.jpg')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
