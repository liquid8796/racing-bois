'use strict';
const root=__MEDIA_ROOT_JSON__;
const iatSlots=__IAT_JSON__;
const base=Process.mainModule.base;
if(Process.arch!=='ia32')throw new Error('Reference must be x86');
const refs=[];let logged=0;
function emit(x){if(logged++<9000)send(x);}
function cstr(p){try{return p.isNull()?'':p.readAnsiString();}catch(e){return '<unreadable>';}}
const imported=Process.mainModule.enumerateImports();
function exp(name){
 const hit=imported.find(x=>x.name===name&&x.address!==undefined);
 const address=iatSlots[name]!==undefined ? base.add(iatSlots[name]).readPointer() : (hit?hit.address:Module.getGlobalExportByName(name));
 const range=Process.findRangeByAddress(address);
 if(range===null || range.protection.indexOf("x")<0)throw new Error("Unresolved/non-executable import: "+name);
 emit({hook_binding:name,address:address.toString(),source:iatSlots[name]!==undefined?'pinned_pe_iat':(hit?'executable_import':'global_export')});
 return address;
}
function deny(name,args,result){
  const cb=new NativeCallback(function(){emit({blocked:name});return result;},'int',args,'stdcall');
  refs.push(cb);Interceptor.replace(exp(name),cb);
}
// Cover the native imports used by this binary. This is not a general sandbox.
deny('RegSetValueExA',['pointer','pointer','uint','uint','pointer','uint'],5);
deny('RegCreateKeyExA',['pointer','pointer','uint','pointer','uint','uint','pointer','pointer','pointer'],5);
deny('RegDeleteKeyA',['pointer','pointer'],5);
deny('RegDeleteValueA',['pointer','pointer'],5);
deny('SetPriorityClass',['pointer','uint'],0);
deny('CreateProcessA',['pointer','pointer','pointer','pointer','int','uint','pointer','pointer','pointer','pointer'],0);
for(const [name,args] of [['connect',['int','pointer','int']],['send',['int','pointer','int','int']],['sendto',['int','pointer','int','int','pointer','int']]]){
  deny(name,args,-1);
}
const virtualKey=ptr('0x0badc0de');
Interceptor.attach(exp('RegOpenKeyExA'),{
 onEnter(a){const key=cstr(a[1]);this.match=key.toLowerCase().includes('vexalith');this.out=a[4];emit({registry_open:key,virtual:this.match});},
 onLeave(r){if(this.match){this.out.writePointer(virtualKey);r.replace(0);emit({virtual_registry:'open'});}}
});
Interceptor.attach(exp('RegQueryValueExA'),{
 onEnter(a){this.match=a[0].equals(virtualKey);this.name=cstr(a[1]);this.data=a[4];this.length=a[5];this.type=a[3];},
 onLeave(r){if(!this.match)return;
  const n=this.name.toLowerCase();
  if(n==='path'){
   const required=root.length+1;
   if(this.length.isNull()){r.replace(87);return;}
   const capacity=this.length.readU32();this.length.writeU32(required);
   if(!this.type.isNull())this.type.writeU32(1);
   if(this.data.isNull()){r.replace(0);return;}
   if(capacity<required){r.replace(234);return;}
   this.data.writeAnsiString(root);r.replace(0);
  }else if(['hires','hiresbikers','hirescars','checkdialup'].includes(n)){
   if(this.length.isNull()){r.replace(87);return;}
   const capacity=this.length.readU32();this.length.writeU32(1);
   if(!this.type.isNull())this.type.writeU32(3);
   if(this.data.isNull()){r.replace(0);return;}
   if(capacity<1){r.replace(234);return;}
   this.data.writeU8(n==='checkdialup'?0:1);r.replace(0);
  }else r.replace(2);
  emit({virtual_registry:'query',name:this.name});
 }
});
Interceptor.attach(exp('RegCloseKey'),{onEnter(a){this.match=a[0].equals(virtualKey);},onLeave(r){if(this.match)r.replace(0);}});
const media=Memory.allocUtf8String(root);refs.push(media);
const mediaCallback=new NativeCallback(function(){emit({virtual_media_root:root});return media;},'pointer',[]);
refs.push(mediaCallback);Interceptor.replace(base.add(0x497c0),mediaCallback);
Interceptor.attach(exp('CreateFileA'),{onEnter(a){this.path=cstr(a[0]);this.access=a[1].toUInt32();},onLeave(r){emit({file:this.path,access:this.access,handle:r.toString()});}});
Interceptor.attach(exp('MessageBoxA'),{onEnter(a){emit({dialog:cstr(a[1]),title:cstr(a[2])});}});
Interceptor.attach(base.add(0x48b90),{onEnter(){emit({native_entry:"installation_options",registry_iat:base.add(iatSlots.RegOpenKeyExA).readPointer().toString()});}});
// Observers only: keep native exceptions and return values unchanged.
Process.setExceptionHandler(function(details){
 emit({native_exception:details.type,address:details.address.toString(),
       pc:details.context.pc.toString(),sp:details.context.sp.toString(),
       memory:details.memory?{operation:details.memory.operation,address:details.memory.address.toString()}:null});
 return false;
});
const watchedGraphics=new Set();
function observeGraphics(){
 const object=base.add(0x9e53c).readPointer();
 if(object.isNull()){emit({graphics_object_null:true});return;}
 const table=object.readPointer();
 for(const [offset,name] of [[0x54,'SetDisplayMode'],[0x18,'CreateSurface'],[0x4c,'RestoreDisplayMode']]){
  const address=table.add(offset).readPointer();const key=address.toString();
  if(watchedGraphics.has(key))continue;
  watchedGraphics.add(key);let count=0;
  Interceptor.attach(address,{
   onEnter(a){this.record=count++<30;this.args=name==='SetDisplayMode'?{width:a[1].toUInt32(),height:a[2].toUInt32(),bpp:a[3].toUInt32()}:{};
              if(this.record)emit({graphics_call:name,event:'enter',args:this.args,address:key});},
   onLeave(r){if(this.record)emit({graphics_call:name,event:'leave',hresult:r.toString(),args:this.args});}
  });
 }
}
for(const [rva,label] of [[0x3b270,'timer_scale'],[0x3b210,'timer_start'],
                         [0x485d0,'menu_display_setup'],[0x495f0,'window_setup'],
                         [0x49730,'window_cooperative_setup'],[0x480f0,'surface_cleanup']]){
 let count=0;
 Interceptor.attach(base.add(rva),{
  onEnter(){this.record=count++<20;if(this.record)emit({stage:label,event:'enter',rva:rva});if(label==='menu_display_setup')observeGraphics();},
  onLeave(result){if(this.record)emit({stage:label,event:'leave',return_raw:result.toString()});}
 });
}
Interceptor.attach(exp('CreateWindowExA'),{
 onEnter(a){this.title=cstr(a[2]);this.style=a[3].toUInt32();},
 onLeave(r){emit({window_created:r.toString(),title:this.title,style:this.style});}
});
Interceptor.attach(exp('ShowWindow'),{onEnter(a){emit({show_window:a[0].toString(),command:a[1].toInt32()});}});
Interceptor.attach(exp('ExitProcess'),{onEnter(a){emit({exit_process:a[0].toUInt32()});}});
Interceptor.attach(exp('timeSetEvent'),{
 onEnter(a){this.delay=a[0].toUInt32();this.callback=a[2].toString();},
 onLeave(r){emit({timer_created:r.toString(),delay_ms:this.delay,callback:this.callback});}
});
Interceptor.flush();
emit({ready:true,base:base.toString(),instrumentation:'pinned IAT hooks; virtual media/registry reads; covered writes/network denied'});
