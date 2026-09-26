# Racing Bois — project rules

Read `docs/PROJECT_REQUIREMENTS.md`, `docs/research/REVERSE_ENGINEERING_REPORT.md`, and `docs/PHASE_PLAN.md` before implementing. The latter two are produced by the initial audit; their absence is not permission to skip it.

- Workspace: `D:\Project\Unity\racing-bois-desktop`, never the Jarvis default.
- Reference mod and supplied video are read-only. Never execute legacy launch scripts: one terminates Explorer, another edits HKLM.
- Current task: execute Phase 0A and 0B research, reproducible tests and evidence. No game implementation/deployment/bulk art production yet.
- Name: **Racing Bois**. Unity Windows 10/11 x64; new 3D assets authored in the user's Blender and integrated through Unity MCP.
- Mandatory art gate: generated 2D concept -> assistant visual review with recorded APPROVED verdict -> 3D/UI production -> in-engine technical/visual QA. No user sign-off per concept required.
- Extracted assets belong in `ReferenceOnly/`, never Unity `Assets/`. Record origin/hash/release eligibility; unknown provenance blocks shipping, not private analysis.
- Enumeration, strings and disassembly are not proof of 100% recovered gameplay. Track observed/decoded/inferred/unverified coverage and tests.
- Authoritative online/LAN server: clients cannot award damage, results, currency or inventory. Offline LAN cannot award trusted online progression.
- OCI hosts production backend/database/user data. Verify architecture/region/capacity/network before deployment. No paid provisioning without authorization.
- Multiplayer is foundational, not a final retrofit. Asset completeness means meaningful unique content, not bytes, copies, LODs, recolors or filler.
- Inspect Unity/Blender project and scene before changes; never modify an unrelated shared instance.
- Never claim a trace, test, build, connection, image approval or performance result not actually obtained.
- Architecture requirement (user, 2026-09-26): keep source readable, clean, maintainable and extensible using appropriate established design patterns. Read docs/ARCHITECTURE_RULES.md before implementation; prefer simple composition and explicit dependencies, not pattern proliferation.
- Each completed patch updates relevant existing Markdown, CHANGELOG.md and tool/assembly versions in Directory.Build.props.
- Use type(scope): message commits and configured master only; no invented remote or force-push. Report unresolved push blockers.

