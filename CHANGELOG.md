# Changelog

## 0.1.18 - Research publication hygiene

Keep raw extraction, traces and machine-specific research output local; only
explicitly reviewed aggregate proof is committed. Correct remaining content
baseline/phase-plan counts and nonexistent SPK work, retaining private old prose.


## 0.1.17 - Evidence-backed research checkpoint

Add the canonical Phase0 checkpoint with corrected corpus counts, 1717 bounded
native comparisons and the visible-window-only compatibility experiment. Mark
the initial contradictory reports as superseded and retain the explicit open
Phase0B behavior/semantic gates and clean architecture requirements.

## 0.1.16 - Owned-process teardown and window-only capture

The compatibility run reached successful display/surface creation and a visible
intro-video window. Fix asynchronous teardown by waiting on the owned Windows
process handle before releasing the DLL lease, and retry transient file locks
for at most two seconds. Capture only an owned window by HWND, without requiring
or changing desktop focus. Preserve the failed 0.1.15 cleanup report.

## 0.1.15 - Private compatibility experiment

Add an opt-in, hash-pinned cnc-ddraw v7.1.0.0 lease for the private reference
copy. Refuse existing DLL/config files, keep the license, disable game-tick
limiting, use windowed GDI and clean up only unchanged files owned by the lease.
Record wrapper hashes/configuration in each probe. No wrapper enters Unity or
the original distribution; compatibility runs do not establish native timing.

## 0.1.14 - DirectDraw startup failure observation

The 0.1.13 experiment reached native window creation and the 33 ms timer but
exited after menu display setup returned a false low byte. Add read-only
DirectDraw method observations to distinguish display-mode and surface failures.
Do not treat the masked initializer return value as the original HRESULT.

## 0.1.13 - Observable bounded runtime lifecycle

Observe startup function entry/exit, native exceptions without swallowing them,
window creation/visibility and process exit. Persist detach reasons, script
errors and cleanup outcomes separately from gameplay success. Include hidden
windows in diagnostics but only capture the spawned process's visible foreground
window. No gameplay constants or controls are changed.

## 0.1.12 - Pinned import-table launch diagnostics

Resolve runtime hooks from actual PE IAT slots, reject unresolved executable
addresses, require network hook initialization, and bound virtual registry
reads for null/short buffers. Trace the native installation entry. No launch
success claim until a recorded probe confirms it. Source files remain read-only.

## 0.1.11 - Bike identity and result arithmetic oracles

Separate pure research models from bounded x86 oracles. Add exhaustive byte
identity checks and deterministic result-screen tests, including mode gating,
selection and legacy unsigned overflow. Explicit per-experiment emulated
write ranges preserve fail-closed isolation; no OS imports execute. Test
success is recorded separately, not inferred from code creation.

## 0.1.10 - Maintainable architecture requirement

Persist the user's clean, readable, maintainable and extensible source-code
requirement in AGENTS.md and PROJECT_REQUIREMENTS.md. Add architecture review
rules with explicit module boundaries and problem-driven pattern selection.
This establishes requirements, not a claim that the game architecture exists.

## 0.1.9 - Import-target-aware instrumentation

Resolve hook addresses from the executable's actual imports before falling back
to global exports. Log registry opens and hook bindings to distinguish missed
forwarders from a true installation-state failure. The first virtual-media
attempt stopped before gameplay at the installation check; do not call it a
successful launch.

## 0.1.8 - Fail-closed launch initialization

Do not resume a spawned reference process until instrumentation reports all
initialization complete. A hook failure leaves the process suspended and cleanup
terminates only its recorded PID. Add the reproducible Ghidra analysis command.

## 0.1.7 - Native navigation and bounded launch probe

Export 1,585 automatically identified functions with Ghidra into ReferenceOnly;
none is counted as semantically verified solely because decompilation succeeded.
Add a hash-pinned, opt-in virtual-media/registry launch experiment with bounded
duration, guarded registry writes and process-scoped captures. The experiment
is not an operating-system security sandbox and does not alter source files.

## 0.1.6 - Save-envelope classification correction

The stricter 0.1.5 audit exposed four extensionless 160-byte files containing only zeros. Their checksum arithmetic matches, but they are not saves: only the 14 RRS files have valid magic and checksum. Preserve these four in inventory and native checksum tests, exclude them from valid-save counts, and add negative regression tests. Pin the measured Pillow version.


## 0.1.5 - Phase 0 evidence reconciliation

Correct two regression fixtures against their actual schema (MIDS buffer-length offset and save-envelope return fields). Replace obsolete Phase 0 narratives with corpus-backed results, isolated-function coverage, and the observed CD-ROM launch blocker. Add reproducible public aggregate reports without reference payloads.


## 0.1.4 ? Validation failure safety

Reject output/source overlap and writes outside the research evidence directory. AVI decode failures/timeouts and invalid save envelopes now fail the corpus gate. Add malformed-resource, MIDS, checksum, path and arithmetic regression tests. No new whole-game claims.


## 0.1.3 ? Corpus conformance runner

Correct DCL vector capacity to 13 bytes, empty-family header, and introduce reproducible native/structural validation.

## 0.1.2 â€” Save checksum oracle and evidence reconciliation

Recover the save checksum at native VA 0x42efc0 with a bounded x86 oracle,
parse the 160-byte save envelope, and add bounded nested family offset tables.
Reconcile earlier prose against a fresh read-only corpus manifest. Never infer
full gameplay equivalence from these isolated function tests.

## 0.1.1 â€” Native function validation and independent verifier

Add isolated Unicorn oracles for SPEC initialization and DAT walking, synthetic negative tests, and the .NET SHA-256 inventory verifier. Each oracle pins the executable hash, limits instruction ranges/time/count, and prevents writes outside synthetic object/stack memory. This is not a full-game runtime test.

## 0.1.0 â€” Research parser foundation

Bounded, read-only RSRC/DAT/FAM/RSGS/RIFF/MIDI/font-metadata parsing. No gameplay-completion claim. Central tool/assembly version initialized; original media and derived reference assets remain private and excluded from release.
