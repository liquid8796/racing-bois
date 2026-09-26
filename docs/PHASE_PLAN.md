# Racing Bois — kế hoạch từng phase

**Nguồn hiện hành:** [Phase0 checkpoint](research/PHASE0_CHECKPOINT.md), [kiểm chứng progression 0.1.21](research/PROGRESSION_VALIDATION.md) và [coverage](research/COVERAGE_MATRIX.md). Phase 0A đạt phạm vi kiểm kê/cấu trúc; Phase 0B còn mở. Không có corpus SPK.

Version 1, ngày 2026-09-26. Đây là kế hoạch production có điều kiện nghiệm thu, không phải báo cáo các phase đã hoàn tất. Yêu cầu gốc: [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md). Bằng chứng: [RE report](research/REVERSE_ENGINEERING_REPORT.md) và [coverage](research/COVERAGE_MATRIX.md).

## Nguyên tắc điều hành

Mỗi phase có đầu vào, deliverables, test và exit gate. Không chuyển phase bằng cách chỉ đánh dấu todo; lưu bằng chứng thực. Khi có blocker ảnh hưởng kiến trúc/gameplay, đóng hoặc có quyết định thay đổi scope được ghi rõ trước khi triển khai phần phụ thuộc.

Ưu tiên: **đúng cảm giác chơi -> đúng authority/network -> một lát cắt đẹp và mượt -> mở rộng content -> hoàn thiện/release**. Đồ họa không được dùng để che handling/combat chưa đạt; multiplayer không được để đến cuối.

Mọi asset 3D và UI mới tuân thủ generated concept 2D -> assistant xem/duyệt -> sản xuất. Technical tests trước phase concept dùng project/test harness không tạo production art/UI bỏ qua gate. Không có asset nào được coi là APPROVED chỉ vì tài liệu đã mô tả nó.

Chưa ấn định lịch theo tuần/ngày khi chưa có throughput art, benchmark hardware và capacity OCI. Sau vertical slice mới cập nhật effort/cost bằng số liệu thực. “Chất lượng tốt nhất” được chuyển thành kiểm thử cụ thể, không thành lời hứa đồ họa/FPS tuyệt đối.

## Tổng quan

| Phase | Mục tiêu | Trạng thái hiện tại |
|---|---|---|
| 0A | Static audit, extractor, evidence và kế hoạch | Đạt phạm vi kiểm kê/cấu trúc; 374 file nguyên trạng, không phải full RE |
| 0B | Deep RE có kiểm chứng, golden scenarios và canonical content baseline | **Đang thực hiện**; các native subset đã đối chiếu, whole-game semantics còn mở |
| 1 | Toolchain, Unity/Blender MCP, build/test nền, OCI feasibility | Chưa nghiệm thu |
| 2 | Generated concepts, assistant approval và art bible | Chưa sản xuất |
| 3 | Core handling/combat/race simulation | Chưa triển khai |
| 4 | Authoritative multiplayer LAN/online sớm | Chưa triển khai |
| 5 | Vertical slice đạt chuẩn PC | Chưa triển khai |
| 6 | Career/economy/persistence/backend hoàn chỉnh | Chưa triển khai |
| 7 | Content production đạt baseline gốc đã xác minh | Chưa triển khai |
| 8 | Feature-complete integration và UX/accessibility | Chưa triển khai |
| 9 | Optimization, compatibility, network/security/soak QA | Chưa chạy |
| 10 | Release candidate, OCI vận hành và phát hành | Chưa chạy |

## Phase 0A — static audit và khởi tạo hồ sơ

**Đã làm:** kiểm kê và hash nguồn, PE/strings/code anchors, resource extraction có bounds/round-trip, decode ảnh/audio chuẩn, parser sprite và 269 FAM outer payload, lấy mẫu video; lưu yêu cầu/checklist/coverage/plan.

**Không tuyên bố:** 100% logic/assets, full runtime trace, video full-watch, Unity game playable, online globally tested hoặc asset production-ready.

**Output:** các tài liệu hiện tại, `tools/`, `research/evidence/`, `ReferenceOnly/`. Các khoảng trống cụ thể được chuyển vào Phase 0B, đặc biệt palette/transparency, semantics của 2.515 FAM leaves, geometry/units của course, native gameplay và caller lifecycle. Mâu thuẫn FAM pilot cũ đã được thay bằng full outer-payload manifest; không còn task SPK không tồn tại.

## Phase 0B — hoàn thiện deep reverse-engineering và đặc tả

**Đầu vào:** corpus đã khóa hash, report và coverage matrix. Không sửa nguồn gốc; tạo bản sao nghiên cứu riêng khi cần chạy game.

**Công việc:** hòa giải mọi parser/manifest với cùng run ID; định danh semantic nested resources; xác minh sprite layout/palette, geometry/units/placement của SGS/NOD bằng code + visual/runtime evidence. Map 15 bike profiles, các course/event/variants, traffic, rider, animation, UI/audio vào semantic catalog. Khóa edition của video/mod/canonical distribution và ghi các khác biệt.

Chạy thí nghiệm controlled cho acceleration/braking/turning/off-road, collisions, punch/kick/weapons/block, crash/recovery, AI/traffic/police, finish/progression/economy/save. Lập event log toàn video thay vì dùng 39 sample như bằng chứng đầy đủ. Annotate disassembly và callsites; số liệu lấy từ help text được gắn nhãn riêng cho tới khi runtime xác nhận.

**Deliverables:** `GameBehaviorSpec` có state machines/formulas/units/parameters và confidence; phần [PROGRESSION_SPEC](research/PROGRESSION_SPEC.md) đã có bounded-native evidence nhưng chưa thay full behavior spec; `ReferenceEventLog`; semantic asset catalog; parser tests trên toàn corpus; golden scenarios với input/setup/raw trace. Tên file deliverable này là mục tiêu tương lai, chưa có nghĩa chúng đã tồn tại.

**Exit:** không còn assumption quan trọng chưa ghi nhận; schema trọng yếu qua bounds/round-trip/visual tests; mỗi core mechanic có scenario tái lập và tiêu chí so sánh. Chưa đóng formula/schema quan trọng thì chưa được nói “giống y chang” hoặc full RE. Vấn đề provenance/canonical completeness phải có quyết định rõ trước bulk content, không âm thầm hạ baseline xuống những file dễ decode.

## Phase 1 — toolchain và nền kỹ thuật

**Phụ thuộc:** các ràng buộc gameplay chính của 0B. Có thể làm kiểm tra môi trường song song, không dùng nó để bỏ qua gate RE.

**Công việc:** kiểm tra workspace hiện có trước thay đổi; pin Unity/editor/packages/render pipeline; xác minh Unity MCP instance đúng `racing-bois-desktop`, Blender addon đúng scene và khả năng round-trip không phá project khác. Cấu trúc assemblies, serialization/version IDs, tests, build scripts, logs, source control và backup. Build Windows client rỗng cùng Linux dedicated-server smoke test; không tạo art/UI chưa có concept.

Kiểm kê min/recommended test hardware và Windows builds; kiểm tra OCI architecture/capacity/network/services đang chạy. Quyết định x86/ARM compatibility trước kiến trúc deployment. Secrets không vào repo/log.

**Deliverables:** toolchain lockfile, build/test harness, instance-binding record, hardware matrix, OCI feasibility/architecture decision record, baseline budgets và rollback approach.

**Exit:** mở đúng project, MCP read/write test giới hạn thành công, build client/server tái lập, tests chạy, không missing packages; target server binary thực sự chạy trên môi trường kiến trúc phù hợp. Mọi cloud provision có chi phí được phê duyệt trước.

## Phase 2 — concept 2D và chuẩn hình ảnh

**Phụ thuộc:** reference gameplay/spec và rendering constraints.

**Công việc:** generate concept thật cho route keyframe, bike/rider/police/traffic, weapon/props, HUD/menu/garage/lobby/results. Assistant trực tiếp xem và tự approve/revise; lưu ảnh/prompt/hash/nhận xét. Chốt art bible: scale, silhouette, palette, materials, lighting, camera, VFX, UI typography/layout và texel density.

**Deliverables:** concept registry, các ảnh APPROVED, art bible, asset budgets và prototype production briefs theo semantic ID. Không sử dụng ảnh research contact-sheet để giả làm concept generated.

**Exit:** từng asset/UI đầu tiên có concept approval thực, orthographic/multiview không mâu thuẫn nghiêm trọng, silhouette/UX đọc rõ trong camera gameplay. Concept đẹp nhưng không khả thi trong budget phải revise.

## Phase 3 — lõi đua xe đối kháng

**Phụ thuộc:** 0B/1/2, concept gate cho asset/UI sử dụng trong game.

**Công việc:** shared authoritative simulation cho movement, steering/lean, road/elevation, grip/off-road, collisions và damage. State machine rider/bike: riding, attacking, hit reaction, crash, recovery, remount và race states theo spec. Attack trái/phải, window/range/block/weapons; AI racer/traffic/police; race start/checkpoints/finish và camera/input remapping cơ bản.

Tách visual feedback khỏi gameplay truth, không để animation event phía client tự trừ máu. RNG seed/tick logs đủ tái lập lỗi quan trọng; không hứa full physics determinism khi chưa kiểm tra.

**Deliverables:** core simulation modules, tuning assets có units, playable handling/combat test track, golden scenario comparisons, automated tests và debug telemetry.

**Exit:** mỗi cơ chế cốt lõi so được với reference trong controlled scenario; không có teleport/hit lặp/checkpoint bỏ qua/soft lock crash-recovery. Sai số đo/tuning được ghi rõ, không chấm “giống” bằng cảm giác chung. Chưa làm hàng loạt course để che core chưa đạt.

## Phase 4 — multiplayer nền: LAN và online OCI

**Phụ thuộc:** shared simulation Phase 3; OCI feasibility Phase 1. Đây là phase nền, trước bulk content.

**Công việc:** chọn network package qua spike; implement server authority, input sequence/ticks, prediction/reconciliation, opponent interpolation, bounded hit validation, lobby lifecycle và reconnect. Backend tối thiểu có session/join ticket/lobby, worker allocation và result path chưa có economy phức tạp.

LAN discovery + direct-IP join, offline local profiles và trust boundary. Online dedicated endpoint trên môi trường OCI được phép dùng; database không public. Thử từ ít nhất hai mạng ngoài LAN; không coi hai process trên một máy là Internet test.

**Deliverables:** 2-client proof trước, sau đó mục tiêu 8 human slots với AI/traffic cấu hình, LAN build, OCI pilot, protocol spec, auth/authority tests và latency/loss reports.

**Exit:** cùng state/result giữa client/server sau reconnect; client giả damage/currency/finish bị từ chối; lobby duplicate/timeout xử lý đúng; LAN khởi động được khi ngắt Internet; online join từ các mạng thật; đủ telemetry để đánh giá RTT/correction/tick cost. Không cần hứa low-ping toàn cầu để vượt gate connectivity, nhưng phải công bố vùng/ping đo được.

## Phase 5 — vertical slice chất lượng PC

**Phụ thuộc:** 2/3/4. Đây là cổng chất lượng quan trọng nhất trước mở rộng asset.

**Scope giới hạn nhưng hoàn chỉnh:** một tuyến/đoạn đua được author trọn flow, hai bike profile/silhouette phù hợp, hai rider, traffic/police, combat/crash/recovery, HUD, lobby, results, engine/impact/ambience audio, lighting và VFX. Cùng slice chạy SP, LAN và online. Không giả “đầy đủ” bằng menu không kết nối vào gameplay.

Blender production theo concept APPROVED; mesh/UV/PBR/LOD/collider/rig/prefab đủ checklist. Road surface, materials, contact shadows, reflections, weather chỉ thêm khi phục vụ art direction và budget; không nhồi hiệu ứng làm mất readability.

**Deliverables:** slice build có version, source assets, prefab QA reports, gameplay captures, reference comparisons, CPU/GPU/network profiles và UX test report.

**Exit:** đẹp và rõ khi đang lái/đánh nhau, không chỉ screenshot; core feel vượt golden tests, multiplayer không làm combat mất công bằng rõ rệt, full play loop không lỗi, performance mục tiêu trên hardware khóa. Asset chưa pass concept/technical/visual/performance gate không được nhân rộng. Nếu slice fail, sửa slice trước Phase 7.

## Phase 6 — career, tài khoản và economy bền vững

**Phụ thuộc:** spec economy/progression 0B, network/result path 4, slice 5.

**Công việc:** career events/unlocks/difficulty, garage/shop/repair và các reward/penalty thực được xác minh trong reference. Backend accounts/profiles/inventory/wallet ledger; authoritative result grants, idempotency, transaction/retry, migration/versioning; UI đầy đủ success/error/offline states. Không suy ra giá/nợ/công thức từ một chuỗi text rồi coi đúng bản gốc.

Threat model, account recovery, admin/moderation access, rate limiting, secret handling; database backup và restore drill. Offline/LAN progress tách khỏi online trusted profile, không có đường tự cộng tiền từ save local.

**Deliverables:** career spec/tests, schema migrations, economy tests, restore/runbook, account flows và service health metrics.

**Exit:** disconnect/retry/crash không nhân item/tiền hoặc mất giao dịch đã commit; grant từ client bị chặn; concurrency tests đúng; backup restore vào DB cách ly thành công; auth/session flows và lỗi mạng hiểu được với người dùng.

## Phase 7 — sản xuất content đạt baseline

**Phụ thuộc:** canonical/semantic catalog 0B, approved concepts 2, slice đạt chuẩn 5, progression 6.

**Công việc:** mở rộng route families, event variants, 15 bike profiles và các model/roster/traffic/props/landmarks/weapons/animations/UI/audio theo baseline đã khóa. Mỗi route có silhouette, nhịp đua, traffic/terrain và set dressing khác có chủ đích. Không chỉ đổi màu/copy một đường để đạt số lượng.

Mọi batch đi qua concept -> Blender/UI production -> import -> prefab -> QA. Dùng modular kit/material sharing/LOD/streaming dựa trên scene budgets. Hoàn thiện SFX engine/tire/wind/weapon, music và dialogue khi provenance rõ; các opaque resource leaves chưa định danh không có nghĩa nội dung đó được phép bỏ.

**Deliverables:** semantic coverage dashboard, release-eligible asset catalog, source `.blend`, export/import settings, complete routes/events và asset QA evidence.

**Exit:** mỗi category >= baseline semantic đã xác minh, không bù thiếu category bằng prop filler; tất cả gameplay states có animation/audio/UI; không reference asset không đủ provenance trong build; không missing refs/materials/scripts. Mật độ content không phá budget slice đã khóa.

## Phase 8 — feature complete và trải nghiệm đầu-cuối

**Phụ thuộc:** 6/7 và ổn định network.

**Công việc:** toàn bộ career/difficulty/traffic/police scenarios, race edge cases, lobby moderation, rejoin/version mismatch, save/quit/resume policy, settings, keyboard/controller rebinding, audio/graphics presets, accessibility/readability, onboarding và support diagnostics.

Test flow từ cài game -> first run -> account/offline -> chọn xe -> lobby/race -> result/progression -> quit/relaunch. Cả lỗi DNS, server full, auth expired, connection lost và maintenance phải có UI rõ ràng, không chỉ stacktrace. Mọi UI bổ sung cần concept duyệt trước production.

**Deliverables:** feature-complete build, requirement traceability matrix, end-to-end tests, known-issues severity list và content manifest.

**Exit:** không blocker/progression soft-lock; toàn bộ yêu cầu có implementation/test tương ứng hoặc quyết định thay đổi scope rõ; SP/LAN/online không phải ba trải nghiệm lệch luật ngoài các khác biệt đã thiết kế.

## Phase 9 — performance, compatibility và multiplayer QA

**Phụ thuộc:** feature complete; vẫn profiling liên tục từ slice, không đợi phase này mới tối ưu.

**Công việc:** đo Windows 10/11 player builds trên min/recommended hardware; GPU/CPU/frame-time/memory/streaming/GC/shader variants; đồ họa ở gameplay density và 8-player room có AI/traffic/combat. Test LOD/culling/occlusion/instancing/light baking theo đo đạc, không bật mọi optimization tùy tiện.

Network test matrix RTT 50/100/150/250 ms, jitter 0/20/50 ms, loss 0/1/3/5%, reconnect, reorder/duplication, host/server crash và lobby abuse. Test người chơi ở các vị trí địa lý/mạng thật có log region/RTT; mock latency không thay toàn bộ kiểm thử Internet.

Mục tiêu ban đầu: 1080p/60 trên hardware/preset khóa, steady-state p95 <= 16,7 ms và p99 <= 33,3 ms; server p99 tick <= 70% tick budget. RAM/VRAM budgets phải được chốt từ Phase 1/5; không dùng con số giả đã đo. Soak mục tiêu tối thiểu 4 giờ client và 24 giờ backend với workload ghi rõ; kiểm tra tăng bộ nhớ, room cleanup, DB và data consistency.

**Deliverables:** benchmark reproducible, profiler captures, security/abuse test report, compatibility matrix, fixes và residual-risk list.

**Exit:** không crash/blocker/asset warnings liên quan chưa xử lý; budgets qua trên hardware thực; không mất/nhân dữ liệu; không desync kéo dài hoặc queue tick tăng mãi; high-latency limitations hiển thị rõ. 16-player và nhiều region chỉ bật khi có kết quả tương ứng.

## Phase 10 — release candidate và vận hành OCI

**Phụ thuộc:** content/provenance gate, feature gate và QA gate đều qua.

**Công việc:** đóng gói build Windows, version/update flow, deployment staging -> production có approval, secret/config separation, backup/restore, maintenance/drain rooms, rollback binary/DB strategy, monitoring/alerts, support logs, release notes và installer/uninstall checks. Kiểm tra không package `ReferenceOnly`, draft concept, keys hoặc development endpoints vào release.

Closed beta với người chơi từ nhiều mạng/khu vực, sau đó tăng tải có kiểm soát. Capacity/region mở rộng theo đo đạc và ngân sách được chấp thuận, không tự nâng tiền cloud. Một VM không được quảng cáo khả năng chịu tải vô hạn hoặc low-ping toàn cầu.

**Deliverables:** release candidate ký/đóng gói theo phương án đã chọn, OCI deployment/runbooks, restore/rollback evidence, provenance/license manifest, telemetry và checklist phát hành.

**Exit:** fresh install chơi được SP/LAN/online, backup restore và rollback đã diễn tập, không secret/reference không đủ quyền trong build, còn room đang chạy không bị deploy phá, các yêu cầu chất lượng/baseline có evidence PASS. Chỉ lúc đó mới gọi là sản phẩm hoàn thiện.

## Các quyết định còn mở nhưng không được bỏ qua

Min-spec hardware; số người chơi release cuối (8 là mục tiêu đầu, 16 có điều kiện); network package/editor exact version; VM OCI shape/region/capacity và chi phí; canonical original asset roster; nội dung cần quyền/licensing; RPO/RTO cuối; giới hạn RTT cho chế độ cạnh tranh. Mỗi quyết định có chủ sở hữu và phase khóa tương ứng trong tài liệu kiến trúc/coverage, không mặc định giải quyết bằng một lựa chọn ngẫu nhiên.

**Hành động kế tiếp:** thực hiện Phase 0B theo danh sách thí nghiệm trong RE report, ưu tiên chứng minh simulation tiến triển, controlled input và golden scenarios handling/combat; nối các native progression subset với caller/runtime thật. Không bắt đầu bulk 3D/UI, deploy production hoặc tuyên bố full RE từ kết quả static audit hiện có.
