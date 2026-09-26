"""Strict DAT sprite decode and bounded reference-resource characterization.

DAT layout independently matched against RacingBois.exe VA 0x443758..0x443785.
DCL decoder below is an altered Python implementation based on Mark Adler's
blast format description and canonical code tables, NOT the original blast.c.
See THIRD_PARTY_NOTICES.md. This is analysis tooling, not production game code.
"""
from __future__ import annotations
import collections, hashlib, json, struct, zlib
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'C:\Users\Liquid\Downloads\Unity\racing_bois_mod')
OUT = ROOT/'docs/research/evidence'
REF = ROOT/'ReferenceOnly/decoded'

def save_json(name: str, value: object) -> None:
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

class DclReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = self.buf = self.nbits = 0

    def bits(self, n: int) -> int:
        while self.nbits < n:
            if self.pos >= len(self.data):
                raise ValueError('Truncated DCL bitstream')
            self.buf |= self.data[self.pos] << self.nbits
            self.pos += 1
            self.nbits += 8
        value = self.buf & ((1 << n)-1)
        self.buf >>= n
        self.nbits -= n
        return value

    def symbol(self, table: tuple[list[int],list[int]]) -> int:
        counts, symbols = table
        code = first = index = 0
        for length in range(1,14):
            code |= self.bits(1) ^ 1
            count = counts[length]
            if code < first+count:
                return symbols[index+code-first]
            index += count
            first = (first+count) << 1
            code <<= 1
        raise ValueError('Invalid DCL Huffman code')

def huffman_table(compact: list[int]) -> tuple[list[int],list[int]]:
    lengths = [v & 15 for v in compact for _ in range((v >> 4)+1)]
    counts = [lengths.count(i) for i in range(14)]
    symbols = sorted(range(len(lengths)),key=lambda i:(lengths[i],i))
    assert 0 not in lengths
    return counts,symbols

LENGTH = huffman_table([2,35,36,53,38,23])
DISTANCE = huffman_table([2,20,53,230,247,151,248])
BASE = [3,2,4,5,6,7,8,9,10,12,16,24,40,72,136,264]
EXTRA = [0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8]

def explode_binary(data: bytes, limit: int) -> tuple[bytes,int]:
    r = DclReader(data)
    mode, dictionary = r.bits(8),r.bits(8)
    if mode != 0 or dictionary not in (4,5,6):
        raise ValueError(f'Unsupported DCL header mode={mode}, dictionary={dictionary}')
    output = bytearray()
    while True:
        if r.bits(1):
            symbol = r.symbol(LENGTH)
            length = BASE[symbol]+r.bits(EXTRA[symbol])
            if length == 519:
                break
            extra_bits = 2 if length == 2 else dictionary
            distance = (r.symbol(DISTANCE) << extra_bits)+r.bits(extra_bits)+1
            if distance > len(output):
                raise ValueError('DCL distance points before output')
            if len(output)+length > limit:
                raise ValueError('DCL output exceeds declared/capped size')
            for _ in range(length):
                output.append(output[-distance])
        else:
            if len(output) >= limit:
                raise ValueError('DCL literal exceeds declared/capped size')
            output.append(r.bits(8))
    return bytes(output),r.pos

def sheet(items: list[tuple[str,Image.Image]], destination: Path, columns: int = 8, cell: tuple[int,int] = (150,170)) -> None:
    width,height = cell
    canvas = Image.new('RGB',(columns*width,((len(items)+columns-1)//columns)*height),(55,55,55))
    draw = ImageDraw.Draw(canvas)
    for i,(label,image) in enumerate(items):
        im=image.convert('RGB');im.thumbnail((width-8,height-26),Image.Resampling.NEAREST)
        x=(i%columns)*width;y=(i//columns)*height
        canvas.paste(im,(x+(width-im.width)//2,y))
        draw.text((x+4,y+height-22),label[:24],fill='white')
    canvas.save(destination)

def main() -> None:
    known, consumed = explode_binary(bytes.fromhex('00 04 82 24 25 8f 80 7f'),1024)
    assert known == b'AIAIAIAIAIAIA' and consumed == 8
    palette_bytes = (SOURCE/'DATA/PALETTE.RAW').read_bytes()
    assert len(palette_bytes) == 1024
    # Windows PALETTEENTRY-style RGB preview. Color order is reviewed visually,
    # while the PNG preserves the exact original palette indices.
    palette = [v for i in range(256) for v in palette_bytes[i*4:i*4+3]]
    sprite_banks = []
    lookup = {}
    for path in sorted((SOURCE/'DATA/BIKERS').glob('*.DAT')):
        data = path.read_bytes(); offset=0; frames=[]; preview=[]
        folder = REF/'sprites'/path.stem
        folder.mkdir(parents=True,exist_ok=True)
        while offset < len(data):
            if offset+2 > len(data):
                raise ValueError(f'Truncated sprite header: {path} at {offset}')
            w,h=data[offset:offset+2];size=w*h;end=offset+2+size
            if end > len(data):
                raise ValueError(f'Sprite exceeds file: {path} at {offset}')
            entry={'index':len(frames),'offset':offset,'width':w,'height':h,'empty':size==0}
            if size:
                pixels=data[offset+2:end]
                image=Image.frombytes('P',(w,h),pixels);image.putpalette(palette)
                dest=folder/f'{len(frames):04d}.png';image.save(dest)
                with Image.open(dest) as check:
                    assert check.tobytes() == pixels
                entry['pixel_sha256']=hashlib.sha256(pixels).hexdigest()
                entry['roundtrip_match']=True
                if len(preview)<48:
                    preview.append((str(len(frames)),image.copy()))
            frames.append(entry);offset=end
        info={'path':path.relative_to(SOURCE).as_posix(),'bytes':len(data),'records':len(frames),'nonempty':sum(not x['empty'] for x in frames),'exact_eof':offset==len(data),'frames':frames}
        sprite_banks.append(info);lookup[path.stem]=info
        sheet(preview,OUT/f'sprites_{path.stem}.jpg')
    pair_checks=[]
    for hi,lo in [('HIBOB','LOBOB'),('HISHADOW','LOSHADOW'),('HISHADOC','LOSHADOC')]:
        a,b=lookup[hi]['frames'],lookup[lo]['frames']
        ok=len(a)==len(b) and all(x['width']==2*y['width'] and x['height']==2*y['height'] for x,y in zip(a,b))
        pair_checks.append({'hi':hi,'lo':lo,'matching_records_and_2x_dimensions':ok})
    save_json('sprite_catalog.json',{'format':'Repeated uint8 width, uint8 height, width*height uint8 palette indices; zero-sized records retained','code_evidence':'RacingBois.exe VA 0x443758..0x443785','palette_interpretation':'RGB preview; indices byte-exact; in-engine palette variants and transparency remain to verify','banks':sprite_banks,'hi_lo_checks':pair_checks})

    containers=json.loads((OUT/'resource_tables.json').read_text())
    families=[];sections=[]
    for container in containers:
        data=(SOURCE/container['path']).read_bytes()
        for e in container['entries']:
            payload=data[e['offset']:e['offset']+e['size']]
            if e['type']=='FAM':
                raw_size,stored_size,unknown,flags=struct.unpack_from('<4I',payload)
                item={'id':e['id'],'raw_size':raw_size,'stored_size':stored_size,'unknown_header_u32':unknown,'flags':flags,'container_bytes':len(payload)}
                try:
                    assert stored_size == len(payload)-16
                    assert raw_size <= 64*1024*1024
                    if flags == 1:
                        body,used=explode_binary(payload[16:],raw_size)
                    elif flags == 0:
                        body=payload[16:];used=len(body)
                    else:
                        raise ValueError(f'Unknown FAM flags {flags}')
                    assert len(body)==raw_size
                    dest=REF/'families'/f'{e["id"]:04d}.bin';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
                    item.update(decoded=True,consumed_compressed_bytes=used,trailing_compressed_bytes=stored_size-used,sha256=hashlib.sha256(body).hexdigest(),crc32=zlib.crc32(body),first_96_hex=body[:96].hex(' '))
                except Exception as exc:
                    item.update(decoded=False,error=str(exc))
                families.append(item)
            if e['type']=='SGS':
                magic,total,count,unknown=struct.unpack_from('<4I',payload)
                table_end=16+52*count
                descriptors=[]
                for idx in range(count):
                    fields=struct.unpack_from('<13I',payload,16+52*idx)
                    descriptors.append({'index':idx,'raw_fields':list(fields),'candidate_offsets_in_bounds':all(v==0 or table_end<=v<len(payload) for v in fields)})
                sections.append({'course':container['path'],'resource_id':e['id'],'bytes':len(payload),'declared_bytes_match':total==len(payload),'section_count_candidate':count,'header_u32_12':unknown,'descriptor_bytes_candidate':52,'table_end':table_end,'descriptors':descriptors,'status':'structural candidate; field meaning, topology and units unverified'})
    save_json('family_decode.json',{'decoder':'DCL binary mode, test vector passed; flags=0 stored','entries':families})
    save_json('course_section_tables.json',sections)
    # BOB has no dimensions in its file. These are explicitly labelled hypotheses.
    bob_items=[];bob_catalog=[]
    for path in sorted((SOURCE/'IMAGES').rglob('*.BOB')):
        data=path.read_bytes();rel=path.relative_to(SOURCE).as_posix();width=None
        if path.name=='MATTE.BOB':width=640
        elif path.parent.name=='HORIZONS':width=640 if path.name.startswith('L') else 1280
        elif path.name in ['BIGCLOUD.BOB','LILCLOUD.BOB']:width=512 if path.name.startswith('BIG') else 256
        elif path.name in ['BIGMETER.BOB','LILMETER.BOB']:width=160 if path.name.startswith('BIG') else 80
        elif 'DASH' in path.name:width=640 if 'HI' in path.name else 320
        if width and len(data)%width==0:
            image=Image.frombytes('P',(width,len(data)//width),data);image.putpalette(palette)
            dest=REF/'bob_candidates'/Path(rel).with_suffix('.png');dest.parent.mkdir(parents=True,exist_ok=True);image.save(dest)
            bob_catalog.append({'path':rel,'candidate_size':[image.width,image.height],'status':'candidate dimensions; exact raw palette indices preserved; code/runtime dimension validation pending'})
            if path.name=='MATTE.BOB' or path.parent.name=='HORIZONS' and not path.name.startswith('L'):
                bob_items.append((path.name,image))
    sheet(bob_items,OUT/'bob_candidates.jpg',columns=2,cell=(640,240))
    save_json('bob_candidates.json',bob_catalog)
    result={'dat_banks':len(sprite_banks),'sprite_records':sum(x['records'] for x in sprite_banks),'sprite_nonempty':sum(x['nonempty'] for x in sprite_banks),'all_dat_exact_eof':all(x['exact_eof'] for x in sprite_banks),'hi_lo_checks':pair_checks,'families_decoded':sum(x['decoded'] for x in families),'family_entries':len(families),'family_errors':[x for x in families if not x['decoded']],'bob_candidates':len(bob_catalog)}
    save_json('asset_decode_summary.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
