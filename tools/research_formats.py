"""Read-only bounded parsers. Valid structure does not prove gameplay semantics."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import struct

class FormatError(ValueError):
    pass

def legacy_checksum(data: bytes) -> int:
    """Exact unsigned-byte checksum from VA 0x42efc0..0x42effb."""
    alternating=total=weighted=0
    for remaining,value in zip(range(len(data),0,-1),data):
        total+=value
        weighted=(weighted+remaining*value)&0xffffffff
        alternating+=value if remaining&1 else -value
    return ((((alternating&0xffffffff)<<16)|(total&0xffff))^weighted)&0xffffffff

def save_envelope(data: bytes) -> dict:
    require(len(data)==160,'save length must be 160')
    expected,magic=struct.unpack_from('<II',data)
    require(magic==0xcafedead,'save magic')
    actual=legacy_checksum(data[4:])
    require(expected==actual,'save checksum mismatch')
    # Copies of the 32-byte profile and ten 12-byte records are proved by
    # VA42F03D..42F083 / VA42F1ED..42F244. Field names remain unverified.
    return dict(checksum=expected,magic=magic,profile_offset=8,profile_bytes=32,
                records_offset=40,record_count=10,record_bytes=12,
                profile_hex=data[8:40].hex(),
                records=[list(struct.unpack_from('<3I',data,40+12*i)) for i in range(10)])

def family_tree(data: bytes,depth: int=0,base: int=0) -> dict:
    """Recognize bounded counted offset arrays; opaque leaves stay opaque.

    Classification is structural, not a claim of material/mesh semantics.
    An empty node is [0,8], not eight zero bytes.
    """
    require(depth<16,'family tree depth cap')
    node=dict(offset=base,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if data==struct.pack('<II',0,8):
        return dict(node,kind='empty',children=[])
    if len(data)>=8:
        count=u32(data,0);end=4*(count+1)
        if 0<count<=4096 and end<=len(data):
            offsets=[u32(data,4+4*i) for i in range(count)]
            if offsets[0]==end and all(end<=a<b<=len(data) for a,b in zip(offsets,offsets[1:]+[len(data)])):
                children=[family_tree(data[a:b],depth+1,base+a) for a,b in zip(offsets,offsets[1:]+[len(data)])]
                return dict(node,kind='offset_array',count=count,children=children)
    return dict(node,kind='opaque',magic_hex=data[:16].hex())

def require(ok: bool, message: str) -> None:
    if not ok: raise FormatError(message)

def u32(data: bytes, offset: int) -> int:
    require(0 <= offset <= len(data)-4, f'u32 outside input: {offset}')
    return struct.unpack_from('<I',data,offset)[0]

def tag_name(tag: bytes) -> str:
    return tag[::-1].decode('ascii',errors='replace').strip()

@dataclass(frozen=True)
class Resource:
    tag: str
    id: int
    offset: int
    size: int
    data: bytes

def resources(data: bytes) -> list[Resource]:
    require(len(data)>=24 and data[:4]==b'CRSR','not RSRC')
    table=u32(data,16)
    require(table<=len(data)-16 and data[table:table+4]==b'LBTR','bad RTBL')
    count=u32(data,table+8); end=table+16+32*count
    require(count<=100000 and end<=len(data),'RTBL overflow')
    result=[]; identities=set()
    for i in range(count):
        tag,rid,off,size=struct.unpack_from('<4sIII',data,table+16+32*i)
        require(all(32<=v<127 for v in tag),'invalid FourCC')
        require(end<=off<=len(data) and size<=len(data)-off,'resource bounds')
        identity=(tag_name(tag),rid)
        require(identity not in identities,'duplicate resource ID');identities.add(identity)
        result.append(Resource(identity[0],rid,off,size,data[off:off+size]))
    ordered=sorted(result,key=lambda x:x.offset)
    require(all(a.offset+a.size<=b.offset for a,b in zip(ordered,ordered[1:])),'overlapping payloads')
    return result

@dataclass(frozen=True)
class Sprite:
    index: int
    offset: int
    width: int
    height: int
    pixels: bytes

def sprites(data: bytes) -> list[Sprite]:
    result=[];off=0
    while off<len(data):
        require(off+2<=len(data),'truncated DAT dimensions')
        w,h=data[off:off+2];end=off+2+w*h
        require(end<=len(data),'truncated DAT pixels')
        result.append(Sprite(len(result),off,w,h,data[off+2:end]));off=end
    return result

def encode_sprites(records: list[Sprite]) -> bytes:
    for r in records:
        require(0<=r.width<=255 and 0<=r.height<=255,'DAT dimension range')
        require(len(r.pixels)==r.width*r.height,'DAT pixel count')
    return b''.join(bytes([r.width,r.height])+r.pixels for r in records)

def decode_family(data: bytes) -> tuple[bytes,dict]:
    from decode_reference_assets import explode_binary
    require(len(data)>=16,'truncated FAM header')
    size,stored,unknown,method=struct.unpack_from('<4I',data)
    require(size<=64*1024*1024,'FAM output cap')
    require(stored==len(data)-16,'FAM stored size')
    if method==0: body,used=data[16:],stored
    elif method==1: body,used=explode_binary(data[16:],size)
    else: raise FormatError(f'unsupported FAM method {method}')
    require(len(body)==size,'FAM decoded size')
    require(used==stored,'unconsumed FAM compressed bytes')
    return body,dict(bytes=size,stored_bytes=stored,method=method,unknown_header=unknown,
                     consumed=used,sha256=hashlib.sha256(body).hexdigest(),placeholder=body==struct.pack('<II',0,8))

def course_sections(data: bytes) -> dict:
    require(len(data)>=16 and data[:4]==b'SGSR','not RSGS')
    require(u32(data,4)==len(data),'RSGS length')
    count=u32(data,8);end=16+52*count
    require(count<=100000 and end<=len(data),'RSGS descriptor overflow')
    rows=[list(struct.unpack_from('<13I',data,16+52*i)) for i in range(count)]
    offsets=sorted({v for row in rows for v in row if v})
    require(all(end<=v<=len(data)-8 for v in offsets),'RSGS pointer bounds')
    blocks=[]
    for i,off in enumerate(offsets):
        size=u32(data,off+4);stop=offsets[i+1] if i+1<len(offsets) else len(data)
        require(size>=8 and off+size==stop,'RSGS nested chunk boundary')
        require(all(32<=v<127 for v in data[off:off+4]),'invalid nested FourCC')
        blocks.append(dict(offset=off,bytes=size,tag=tag_name(data[off:off+4]),
            header_u32=[u32(data,j) for j in range(off+8,min(off+24,off+size),4)],
            sha256=hashlib.sha256(data[off:stop]).hexdigest()))
    require(not offsets or offsets[0]==end,'gap after RSGS table')
    return dict(count=count,header_12=u32(data,12),descriptor_bytes=52,descriptors=rows,
                blocks=blocks,scope='exact boundaries; route topology and field units unverified')

def riff_chunks(data: bytes) -> dict:
    require(len(data)>=12 and data[:4]==b'RIFF','not RIFF')
    end=8+u32(data,4);require(end<=len(data),'RIFF outer bounds');chunks=[]
    def walk(pos,stop,parent,depth=0):
        require(depth<12,'RIFF nesting cap')
        while pos<stop:
            require(pos+8<=stop,'truncated RIFF chunk')
            tag=data[pos:pos+4].decode('ascii',errors='replace');size=u32(data,pos+4)
            body=pos+8;chunk_end=body+size;require(chunk_end<=stop,'RIFF chunk bounds')
            item=dict(tag=tag,parent=parent,offset=pos,bytes=size);chunks.append(item)
            if tag=='LIST':
                require(size>=4,'short LIST');kind=data[body:body+4].decode('ascii',errors='replace');item['kind']=kind
                if kind!='movi':walk(body+4,chunk_end,parent+'/'+kind,depth+1)
            pos=chunk_end+(size&1);require(pos<=stop+1,'RIFF padding overflow')
    form=data[8:12].decode('ascii',errors='replace');walk(12,end,form)
    return dict(form=form,bytes=end,trailing_bytes=len(data)-end,chunks=chunks)

def midi_structure(data: bytes) -> dict:
    require(len(data)>=14 and data[:4]==b'MThd','not SMF MIDI')
    size=struct.unpack_from('>I',data,4)[0]
    require(size>=6 and size+8<=len(data),'MIDI header size')
    fmt,count,division=struct.unpack_from('>3H',data,8);pos=size+8;tracks=[]
    while pos<len(data):
        require(pos+8<=len(data) and data[pos:pos+4]==b'MTrk','MIDI track header')
        n=struct.unpack_from('>I',data,pos+4)[0];require(pos+8+n<=len(data),'MIDI track bounds')
        tracks.append(dict(offset=pos,bytes=n));pos+=8+n
    require(len(tracks)==count,'MIDI track count')
    return dict(format=fmt,tracks=count,division=division,track_table=tracks)

def sfnt_structure(data: bytes) -> dict:
    require(len(data)>=12 and data[:4]==b'\x00\x01\x00\x00','not sfnt font')
    count=struct.unpack_from('>H',data,4)[0]
    require(count<=4096 and 12+16*count<=len(data),'sfnt directory bounds');entries=[]
    for i in range(count):
        tag,checksum,off,size=struct.unpack_from('>4sIII',data,12+16*i)
        require(off<=len(data) and size<=len(data)-off,'sfnt table bounds')
        entries.append(dict(tag=tag.decode('ascii',errors='replace'),bytes=size))
    return dict(type='sfnt font; metadata only, never redistribute',tables=entries)
