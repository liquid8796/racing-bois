"""Read RIFF/MIDS buffers without executing or redistributing reference media."""
import struct
from research_formats import riff_chunks,require,u32

def mids_events(data: bytes) -> dict:
    riff=riff_chunks(data);require(riff['form']=='MIDS','not MIDS')
    fmt=next((x for x in riff['chunks'] if x['tag']=='fmt '),None)
    body=next((x for x in riff['chunks'] if x['tag']=='data'),None)
    require(fmt is not None and body is not None and fmt['bytes']>=12,'MIDS chunks')
    division,buffer_size,flags=struct.unpack_from('<3I',data,fmt['offset']+8)
    require(flags in (0,1),'unsupported MIDS flags')
    start=body['offset']+8;end=start+body['bytes'];count=u32(data,start);pos=start+4
    require(count<100000,'MIDS buffer count cap');buffers=[];events=[];tick=0
    for i in range(count):
        require(pos+8<=end,'MIDS buffer header')
        first_tick,size=struct.unpack_from('<II',data,pos);pos+=8;stop=pos+size
        require(stop<=end,'MIDS buffer bounds');initial=tick;first=len(events)
        while pos<stop:
            stride=8 if flags&1 else 12;require(pos+stride<=stop,'MIDS event bounds')
            delta=u32(data,pos);stream=0 if flags&1 else u32(data,pos+4)
            event=u32(data,pos+stride-4);pos+=stride;tick+=delta
            kind=event>>24;parameter=event&0xffffff
            item=dict(tick=tick,delta=delta,stream=stream,kind=kind,parameter=parameter)
            if kind&0x80:
                n=(parameter+3)&~3;require(pos+n<=stop,'MIDS long event bounds')
                item['payload_hex']=data[pos:pos+parameter].hex();pos+=n
            events.append(item)
        buffers.append(dict(index=i,first_tick=first_tick,previous_tick=initial,events=len(events)-first,bytes=size))
    require(pos==end,'MIDS unconsumed bytes')
    return dict(division=division,buffer_size=buffer_size,flags=flags,buffers=buffers,events=events,last_tick=tick)
