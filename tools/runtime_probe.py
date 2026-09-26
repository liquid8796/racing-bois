"""Bounded, opt-in launch of a private copy of the supplied reference executable.

This is instrumentation, NOT an OS sandbox. No BAT/REG is executed. Registry
writes and network calls through the covered Win32 APIs are denied. The only
native replacement supplies the private media root; no gameplay code is tuned.
"""
from __future__ import annotations
import argparse,ctypes,datetime,hashlib,json,os,sys,time,threading
import xml.etree.ElementTree as ET
from ctypes import wintypes as W
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA='66ab853c5b7b73b82a7c22a0478f5ba5b1066ed27028ef96449f5fe36a6101c5'

def windows(pid, include_hidden=False):
    u=ctypes.windll.user32;result=[]
    callback=ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    @callback
    def visit(hwnd,_):
        owner=W.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        visible=bool(u.IsWindowVisible(hwnd))
        if owner.value==pid and (visible or include_hidden):
            text=ctypes.create_unicode_buffer(2048);u.GetWindowTextW(hwnd,text,2048)
            rect=W.RECT();u.GetWindowRect(hwnd,ctypes.byref(rect));children=[]
            @callback
            def child(ch,_):
                s=ctypes.create_unicode_buffer(2048);u.GetWindowTextW(ch,s,2048)
                if s.value:children.append(s.value)
                return True
            u.EnumChildWindows(hwnd,child,0)
            result.append(dict(hwnd=int(hwnd),title=text.value,visible=visible,rect=[rect.left,rect.top,rect.right,rect.bottom],children=children))
        return True
    u.EnumWindows(visit,0);return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--virtual-media-root',action='store_true');ap.add_argument('--seconds',type=int,default=25)
    ap.add_argument('--cnc-ddraw',action='store_true',help='Use pinned, temporary private-copy DirectDraw wrapper')
    a=ap.parse_args()
    if not a.virtual_media_root:ap.error('Explicit --virtual-media-root acknowledgement is required')
    if not 5<=a.seconds<=120:ap.error('Duration must be 5..120 seconds')
    copy=(ROOT/'ReferenceOnly/runtime-sandbox').resolve();exe=copy/'RacingBois.exe'
    if not copy.is_relative_to((ROOT/'ReferenceOnly').resolve()):raise ValueError('Private path escaped')
    if hashlib.sha256(exe.read_bytes()).hexdigest()!=SHA:raise ValueError('Reference executable hash mismatch')
    import frida, pefile
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=ROOT/'ReferenceOnly/runtime-probes'/stamp;out.mkdir(parents=True,exist_ok=False)
    events=[];device=frida.get_local_device();pid=None;session=None;process_handle=None
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];kernel.OpenProcess.restype=W.HANDLE
    kernel.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];kernel.WaitForSingleObject.restype=W.DWORD
    kernel.CloseHandle.argtypes=[W.HANDLE];kernel.CloseHandle.restype=W.BOOL
    start=time.monotonic();observations=[];lifecycle=[];cleanup_errors=[]
    state={'resumed':False,'cleanup_started':False,'error':None}
    compatibility=None;lease=None
    lock=threading.RLock()
    def persist():
        # Snapshot under lock; callbacks never do quadratic disk writes.
        with lock:
            snapshots={'events':list(events),'observations':list(observations),'lifecycle':list(lifecycle)}
        for name,values in snapshots.items():
            dest=out/(name+'.json');temp=dest.with_suffix('.json.tmp')
            temp.write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(dest)
    pe = pefile.PE(str(exe))
    iat = {item.name.decode("ascii"): item.address - pe.OPTIONAL_HEADER.ImageBase
           for module in pe.DIRECTORY_ENTRY_IMPORT for item in module.imports if item.name}
    js=(ROOT/'tools/runtime_probe.js').read_text(encoding='utf-8').replace('__MEDIA_ROOT_JSON__',json.dumps(str(copy))).replace('__IAT_JSON__', json.dumps(iat))
    try:
        if a.cnc_ddraw:
            from reference_compatibility import prepare_cnc_ddraw
            lease,compatibility=prepare_cnc_ddraw(ROOT,copy)
            lease.install()
        pid=device.spawn([str(exe)],cwd=str(copy))
        process_handle=kernel.OpenProcess(0x00100000,False,pid)
        if not process_handle:raise ctypes.WinError(ctypes.get_last_error())
        session=device.attach(pid)
        def detached(reason, crash=None):
            with lock:
                lifecycle.append(dict(seconds=round(time.monotonic()-start,3),event='detached',
                                      reason=str(reason),during_cleanup=state['cleanup_started'],
                                      crash=str(crash) if crash is not None else None))
        session.on('detached',detached)
        script=session.create_script(js);ready=threading.Event()
        def message(m,data):
            if m.get('type')=='send' and m.get('payload',{}).get('ready'):ready.set()
            with lock:
                if len(events)<10000:
                    events.append(dict(seconds=round(time.monotonic()-start,3),message=m))
        script.on('message',message);script.load()
        if not ready.wait(2):raise RuntimeError('Instrumentation initialization failed; process not resumed')
        device.resume(pid);state['resumed']=True
        for elapsed in range(a.seconds):
            time.sleep(1)
            if elapsed in (2,7,14,a.seconds-1):
                view=windows(pid,include_hidden=True)
                observations.append(dict(seconds=elapsed+1,session_detached=session.is_detached,windows=view))
                persist()
                # Window-only capture: no focus changes and no whole-desktop image.
                for w in view:
                    if w['visible'] and w['rect'][2]>w['rect'][0] and w['rect'][3]>w['rect'][1]:
                        from PIL import ImageGrab
                        ImageGrab.grab(window=w['hwnd']).save(out/f"window_{elapsed+1:03d}_{w['hwnd']}.png")
            if session.is_detached:
                break
    except Exception as error:
        state['error']=f'{type(error).__name__}: {error}'
        raise
    finally:
        state['cleanup_started']=True
        if pid is not None:
            for w in windows(pid,include_hidden=True):ctypes.windll.user32.PostMessageW(w['hwnd'],0x10,0,0)
            time.sleep(1)
            try:device.kill(pid)
            except frida.ProcessNotFoundError:pass
            except Exception as error:cleanup_errors.append(f'kill: {error}')
        if process_handle is not None:
            result=kernel.WaitForSingleObject(process_handle,5000)
            lifecycle.append(dict(event='owned_process_exit_wait',result=int(result),during_cleanup=True))
            if result!=0:cleanup_errors.append(f'Owned process exit was not confirmed: wait={result}')
            kernel.CloseHandle(process_handle)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass
            except Exception as error:cleanup_errors.append(f'detach: {error}')
        if lease is not None:
            if cleanup_errors:
                cleanup_errors.append('Compatibility files retained because process cleanup was not confirmed')
            else:
                cleanup_errors.extend(lease.cleanup())
        persist()
        script_errors=[event for event in events if event['message'].get('type')=='error']
        report=dict(pid=pid,seconds=a.seconds,executable_sha256=SHA,events=len(events),
                    tool_version=ET.parse(ROOT/'Directory.Build.props').findtext('.//Version'),
                    resumed=state['resumed'],harness_error=state['error'],cleanup_errors=cleanup_errors,
                    script_errors=script_errors,lifecycle=lifecycle,
                    visible_window_observed=any(w['visible'] for o in observations for w in o['windows']),
                    gameplay_observed=False,
                    compatibility=compatibility,
                    virtual_media_root=True,reference_modified=hashlib.sha256(exe.read_bytes()).hexdigest()!=SHA,
                    scope='Opt-in startup instrumentation; observer overhead exists. No gameplay input/physics changes; no gameplay-success claim; not an OS sandbox.')
        (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(dict(report,output=str(out))))
        if cleanup_errors and state['error'] is None:
            raise RuntimeError('Probe cleanup incomplete; see report')

if __name__=='__main__':main()
