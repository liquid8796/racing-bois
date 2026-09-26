"""Bounded function-level x86 oracle; no OS loader, imports, syscalls or network."""
from __future__ import annotations
import hashlib
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tools/python'))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ESI,UC_X86_REG_EBX,UC_X86_REG_EDI
import pefile
EXE_SHA='66ab853c5b7b73b82a7c22a0478f5ba5b1066ed27028ef96449f5fe36a6101c5'
DEST,SOURCE,STACK,STOP=0x1000000,0x2000000,0x3000000,0x4000000

def signed(n: int) -> int:
    return (n+2**31)%2**32-2**31

def div(a: int,b: int) -> int:
    if b==0:raise ValueError('native divide by zero')
    value=(abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)
    if not -2**31<=value<2**31:raise ValueError('native divide overflow')
    return value

def port_spec(payload: bytes,parameter: int) -> bytes:
    """Translate VA405EA0..406072. Raw fields remain unnamed without evidence."""
    if len(payload)!=356:raise ValueError('SPEC length must be 356')
    v=struct.unpack('<89i',payload);out=bytearray(1024)
    def put(off,value):struct.pack_into('<I',out,off,value&0xffffffff)
    def get(off):return struct.unpack_from('<i',out,off)[0]
    out[0x1bc]=v[0]&255
    for off,i in [(0x168,1),(0x16c,2),(0x170,3),(0x1b4,4),(0x1b8,5)]:put(off,v[i])
    out[0x1c4:0x2f4]=payload[28:332]
    base=v[6]+75
    left=signed(signed(get(0x250)*base)<<8);right=signed(signed(get(0x26c)*base)<<8)
    put(0x250,left);put(0x26c,right)
    denominator=v[6]+div(parameter,4)
    a=div(signed(get(0x2a0)*base),denominator);b=div(signed(get(0x2a4)*base),denominator)
    put(0x2a0,a);put(0x2a4,b);put(0x29c,0x2e00)
    put(0x2a8,div(0x2e00,a));put(0x2ac,div(0x2e00,b))
    denominator=v[6]+div(signed(parameter-75),8)+75
    left=div(left,denominator);right=div(right,denominator)
    put(0x260,left);put(0x27c,right)
    for dst,src,total in [(0x264,0x254,left),(0x268,0x258,left),(0x280,0x270,right),(0x284,0x274,right)]:put(dst,div(total,min(get(src),15)))
    put(0x2c4,20);put(0x248,0x2000);put(0x2dc,0x2000)
    return bytes(out)

class Oracle:
    def checksum(self,payload: bytes) -> int:
        if len(payload)>1024*1024:raise ValueError('checksum oracle input cap')
        uc=self.machine([(0x42efc0,0x42effc)],max(4096,len(payload)))
        if payload:uc.mem_write(SOURCE,payload)
        sp=STACK+0x8000;uc.mem_write(sp,struct.pack('<I',STOP))
        uc.reg_write(UC_X86_REG_ESP,sp);uc.reg_write(UC_X86_REG_ECX,SOURCE)
        uc.reg_write(UC_X86_REG_EDX,len(payload))
        uc.emu_start(0x42efc0,STOP,timeout=2000000,count=32*len(payload)+100)
        if uc.reg_read(UC_X86_REG_EIP)!=STOP:raise RuntimeError('checksum execution budget exceeded')
        return uc.reg_read(UC_X86_REG_EAX)

    def __init__(self,executable: bytes):
        if hashlib.sha256(executable).hexdigest()!=EXE_SHA:raise ValueError('unknown executable hash')
        pe=pefile.PE(data=executable);self.image=pe.get_memory_mapped_image();self.base=pe.OPTIONAL_HEADER.ImageBase

    def machine(self,allowed: list[tuple[int,int]],source_size=0x10000,destination_size=0x10000,write_ranges=()):
        # Additional writes are explicit, bounded addresses in the emulated PE,
        # never addresses in the host process. Default remains synthetic memory only.
        for start,end in write_ranges:
            if not self.base <= start < end <= self.base + len(self.image):
                raise ValueError("Additional write range escapes emulated image")
        uc=Uc(UC_ARCH_X86,UC_MODE_32);uc.mem_map(self.base,(len(self.image)+4095)&~4095);uc.mem_write(self.base,self.image)
        for address,size in [(DEST,destination_size),(SOURCE,source_size),(STACK,0x10000),(STOP,4096)]:uc.mem_map(address,(size+4095)&~4095)
        def code(machine,address,size,user):
            if not any(a<=address and address+size<=b for a,b in allowed):raise RuntimeError(f'execution outside whitelist: {address:#x}')
        def write(machine,access,address,size,value,user):
            if not (DEST<=address and address+size<=DEST+destination_size or STACK<=address and address+size<=STACK+0x10000 or any(a<=address and address+size<=b for a,b in write_ranges)):raise RuntimeError(f'write outside experiment memory: {address:#x}')
        uc.hook_add(UC_HOOK_CODE,code);uc.hook_add(UC_HOOK_MEM_WRITE,write)
        return uc

    def spec(self,payload: bytes,index: int,parameter: int) -> bytes:
        if len(payload)!=356 or not 0<=index<15:raise ValueError('SPEC bounds')
        uc=self.machine([(0x405ea0,0x406073)]);uc.mem_write(SOURCE,payload)
        uc.mem_write(0x47ea40+index*4,struct.pack('<I',SOURCE));sp=STACK+0x8000
        uc.mem_write(sp,struct.pack('<II',STOP,index));uc.reg_write(UC_X86_REG_ESP,sp)
        uc.reg_write(UC_X86_REG_ECX,DEST);uc.reg_write(UC_X86_REG_EDX,parameter&0xffffffff)
        uc.emu_start(0x405ea0,STOP,timeout=2000000,count=10000)
        if uc.reg_read(UC_X86_REG_EIP)!=STOP:raise RuntimeError('SPEC execution budget exceeded')
        return bytes(uc.mem_read(DEST,1024))

    def dat(self,payload: bytes,count: int) -> tuple[list[tuple[int,int,int]],int]:
        if not payload or not 0<count<=100000:raise ValueError('DAT oracle bounds')
        uc=self.machine([(0x443758,0x443787)],len(payload)+4096,count*8+4096)
        uc.mem_write(SOURCE,payload);uc.reg_write(UC_X86_REG_ESI,SOURCE)
        uc.reg_write(UC_X86_REG_EBX,DEST);uc.reg_write(UC_X86_REG_EDI,count)
        uc.emu_start(0x443758,0x443787,timeout=2000000,count=count*40)
        if uc.reg_read(UC_X86_REG_EIP)!=0x443787:raise RuntimeError('DAT execution budget exceeded')
        data=bytes(uc.mem_read(DEST,count*8));rows=[]
        for i in range(count):
            address,w,h=struct.unpack_from('<IBB',data,i*8);rows.append((address-SOURCE if address else -1,w,h))
        return rows,uc.reg_read(UC_X86_REG_ESI)-SOURCE
