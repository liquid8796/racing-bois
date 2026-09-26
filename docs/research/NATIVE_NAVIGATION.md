# Native navigation and experiment boundaries

Reference executable SHA-256:
66ab853c5b7b73b82a7c22a0478f5ba5b1066ed27028ef96449f5fe36a6101c5.

Ghidra 11.4.2 identified and emitted C-like output for 1,585 non-external
functions on 2026-09-26. This includes runtime/library functions. It is not a
count of original developer functions or a claim that gameplay is recovered.
Inferred types, split functions and calling conventions require assembly review.

Private output: ReferenceOnly/decompiled/function_catalog.json and
ReferenceOnly/decompiled/functions/*.c. Do not commit or ship these files.

Reproduction (Java 21 must already exist; use its verified installed path):

~~~powershell
$env:JAVA_HOME='C:\Program Files\Java\jdk-21.0.8'
& '.tools\ghidra_11.4.2_PUBLIC\support\analyzeHeadless.bat' 'ReferenceOnly\ghidra_projects' 'RBReference0B' -import 'C:\Users\Liquid\Downloads\Unity\racing_bois_mod\RacingBois.exe' -scriptPath 'tools\ghidra' -postScript ExportReference.java 'ReferenceOnly\decompiled' -analysisTimeoutPerFile 300 -max-cpu 2
~~~

Use a new project name for a new import. An existing project can be processed
with -process RacingBois.exe -noanalysis instead of re-importing over it.

## Anchors reviewed in decompiled output and assembly

| Address | Evidence-backed purpose | Boundary |
|---|---|---|
| 0x405E30 | Load 15 SPEC resource IDs into a pointer table | File loader, not tuning semantics |
| 0x405EA0 | Initialize entity fields from a cached SPEC | Bounded native/port equivalence tested |
| 0x443758 | DAT frame pointer/width/height walker | Bounded native/port equivalence tested |
| 0x42EFC0 | Save checksum | Bounded native/port equivalence tested |
| 0x42F000 / 0x42F110 | Save serialization / loading | Envelope/copy layout reviewed; not all profile fields named |
| 0x416310 | Choose high/low horizons, meter, bike dashboard | Rendering/input-state dependent |
| 0x44C5D0 | Meter loader supplies nominal 190 by 64 | Low-resolution scaling is in helper 0x44C5F0 |
| 0x420AA0 | Bike index to localized name ID | Native mapping needs corpus oracle |

Version 0.1.11 adds an independent pure mapping and bounded oracle for every
byte-valued bike index. It also adds a model/oracle for the full result-screen
prefix at 0x421290..0x421384, stopping before Win32 UI calls. Result entry
conditions, DNF handling and persistence are NOT implied by this experiment.
Run tools/validate_gameplay.py with a new --out directory under evidence;
only a successful recorded run establishes equivalence for tested inputs.
| 0x42129C | Result screen tail; contains reward calculation | Inferred function is split and enters with flags; not a standalone C function |
| 0x4497C0 | Scan A..Z for CD-ROM drive and select media path | Unmodified launch stops here without CD drive |
| 0x448B90 | Registry-based installation/options reads | Account-wide registry writes must not be performed by the research workflow |

## Launch probe

Compatibility run `20260926T062630Z` returned zero from both display-mode calls
and four CreateSurface calls, and observed a visible game window with Intro.AVI
children. No foreground-window image was captured. Cleanup attempted to remove
the owned DLL before Windows released it, reported WinError 5 and exited nonzero;
do not erase that failed experiment. Version 0.1.16 waits on an owned native
process handle and captures only that process's window handle, not the desktop.

Run `20260926T061618Z` observed actual SetDisplayMode(640,480,8) and
SetDisplayMode(640,480,16) both returning `0x80004001`, before usable menu capture.
Microsoft documents this value as E_NOTIMPL:
https://learn.microsoft.com/en-us/windows/win32/seccrypto/common-hresult-values

The optional `--cnc-ddraw` experiment leases only ddraw.dll, a minimal local
configuration and its MIT license into ReferenceOnly/runtime-sandbox. The
download is pinned to upstream v7.1.0.0 and a locally measured archive hash;
the release did not supply an independent publisher digest/signature. It uses
windowed GDI with game-tick limiting and single-CPU affinity disabled. No
configuration program is run. Existing files cause refusal, and changed files
are preserved rather than deleted during cleanup. This remains a compatibility
experiment, not proof of original timing or production art readiness.

Run `20260926T061356Z` created the game window, executed ShowWindow(10), started
a timer requesting 33 ms, then left menu display setup with raw return
`0x80004000` and terminated before the first screenshot sample. No native
exception was observed; detachment was process-terminated, before cleanup.
This return has its low byte cleared by the initializer and must NOT be quoted
as an exact DirectDraw HRESULT. Version 0.1.14 observes the called COM methods
without replacing them. A requested timer interval is not a measured physics tick.

The recorded 0.1.12 probe `ReferenceOnly/runtime-probes/20260926T060728Z`
did enter installation/options, virtualize the supplied installation path, and
open Palette.RAW and Families.RSC. There was no visible window at 3/8/15 seconds.
This supersedes the earlier installation-error observation for that instrumented
run only. It does not prove a successful game launch.

Version 0.1.13 adds bounded entry/exit observations for startup routines,
CreateWindowExA/ShowWindow, timer setup, ExitProcess and native exceptions.
Exception callbacks return false, preserving normal exception handling. Hidden
windows are recorded but not screen-captured. Detachment during cleanup is
distinguished from spontaneous process termination. Hooking adds overhead;
these diagnostics cannot establish original frame timings.

Version 0.1.12 resolves API addresses from the hash-pinned PE import-table
slots at runtime. The previous Frida import enumeration fell back to global
exports and did not observe registry calls. This experiment must establish
actual IAT coverage; it does not assume the installation blocker is fixed.
Unresolved required network hooks now prevent resume. Virtual registry reads
respect null/short buffers. API reference: https://frida.re/docs/javascript-api/

python tools/runtime_probe.py --virtual-media-root --seconds 25 executes only
the hash-pinned private copy in ReferenceOnly/runtime-sandbox. It replaces the
CD media-root result and virtualizes installation/options reads in process;
covered registry-write and network APIs are denied. No original executable is
modified. It is **not an operating-system security sandbox**. Probe output is
not proof that the unmodified distribution launches on this machine.

The process remains suspended unless hook initialization succeeds. Captures are
restricted to that PID's foreground window. It sends no gameplay input, changes
no physics constants, and terminates only its recorded spawned PID at timeout.
