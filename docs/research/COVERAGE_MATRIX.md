# Racing Bois — coverage matrix

> Xem [checkpoint hiện hành](PHASE0_CHECKPOINT.md). Số liệu ban đầu đã được đính chính; native comparisons không đồng nghĩa toàn bộ gameplay đã recovered. Phase0B vẫn mở.

Ngày: 2026-09-26. Không có chỉ số “100% logic recovered”. Mỗi dòng chỉ hoàn tất khi đạt đúng loại kiểm chứng cần thiết.

| Domain | Trạng thái hiện tại | Bằng chứng | Khoảng trống / gate đóng |
|---|---|---|---|
| Corpus và SHA-256 | VERIFIED-STRUCTURE | `evidence/inventory.json`, `evidence/FINAL_AUDIT_SNAPSHOT.json` | Giữ nguyên nguồn; thêm canonical baseline riêng khi có, không gọi mod là bản gốc đầy đủ |
| PE headers/imports/strings | VERIFIED-STRUCTURE | `evidence/pe_analysis.json`, `evidence/localization/` | Map call graph và ý nghĩa nhánh runtime; không coi linear disassembly là decompilation hoàn chỉnh |
| 13 resource containers / 429 entries | VERIFIED-STRUCTURE | `evidence/resource_tables.json` | Map nested schema, semantic IDs; kiểm tra lại inventory cùng run ID |
| RRI/BMP | Decode ảnh chuẩn đã chạy | `evidence/image_catalog.json` | Semantic uniqueness, chất lượng ảnh, nội dung thiếu và release provenance |
| RRA/WAV | RIFF/WAVE đã đọc | `evidence/audio_catalog.json` | Đối chiếu event sử dụng, loop/loudness và phần audio trong định dạng khác |
| SPK và audio corpus đầy đủ | UNVERIFIED | `evidence/inventory.json` | Schema/decompress/decode, đếm clip độc lập, kiểm tra nghe và event mapping |
| DAT sprite | Cấu trúc/pixel round-trip có kiểm tra; hình render chưa đạt | `evidence/sprite_catalog.json`, `evidence/sprite_layout_probe.jpg` | Layout/stride/orientation/palette/transparency phải khớp frame runtime; giữ slot rỗng |
| BOB | HYPOTHESIS preview | `evidence/bob_candidates.json` | Kích thước theo code, palette, transparency và so ảnh game; không tự approve |
| FAM | Pilot decoder; coverage chưa hòa giải | `evidence/family_decode.json`, `evidence/resource_tables.json` | 7 pilot entries chưa map đủ 269 FAM inventory; decode toàn corpus và inner schema |
| SPEC / 15 profile xe | Raw fields + code anchors một phần | `evidence/resource_tables.json`, `evidence/RacingBois.text.asm` | Units, fixed-point/rounding, curve mapping, acceleration/brake/turn runtime |
| Course SGS/NOD | HYPOTHESIS chưa pass bounds toàn bộ | `evidence/course_section_tables.json` | Bác bỏ/sửa schema candidate; topology/elevation/length/spawn phải được kiểm tra |
| CAR/ANIM/CEL/GLOB/BKR | Extracted bytes, semantic partial/unknown | `evidence/resource_tables.json`, `evidence/inventory.json` | Quan hệ ID, sprite/frame timing, collision/AI/scene placements |
| Save/profile | Dump mẫu, chưa hoàn thiện schema | `evidence/save_samples.json` | Field offsets, ranges, checksums, controlled diff và round-trip an toàn |
| Reference video | 39 frame trích xuất / metadata | `evidence/video/video_samples.json` | Event annotation toàn video và review các clip hành động; không coi sample là full watch |
| Handling/collision/crash | UNVERIFIED-BEHAVIOR | Code navigation + reference corpus | Golden scenarios có input/trace, repeated measurements, spec units/state machines |
| Combat/weapon/damage | UNVERIFIED-BEHAVIOR | Chuỗi/code anchors chưa đủ | Active frames, range, left/right, block/counter, stacking/cooldown và damage formula |
| AI/traffic/police | UNVERIFIED-BEHAVIOR | Dữ liệu/strings tham chiếu | Quyết định theo state/perception, difficulty, determinism cần có/không cần |
| Career/economy/progression | UNVERIFIED-BEHAVIOR | Resource/help/save chưa phải runtime proof | Qualify/unlock/results/prices/repair/penalties; phân biệt bản mod và reference video |
| Original asset completeness | UNVERIFIED | Chỉ có distribution mod hiện được cung cấp | Đối chiếu canonical asset roster trước tuyên bố >= toàn bộ game gốc |
| Unity/Blender production integration | Chưa xác nhận sẵn sàng ở lượt thăm dò | Tool probes trong phiên | Handshake đúng project/scene, không sửa nhầm instance; client/server smoke builds |
| Multiplayer/OCI readiness | Chưa triển khai/kiểm thử | Kiến trúc đề xuất | Kiểm tra VM, binary architecture, ports, authority, LAN offline, nhiều mạng thật |
| Production asset quality/performance | Chưa bắt đầu nghiệm thu | `../PROJECT_REQUIREMENTS.md` | Concept APPROVED + checklist + gameplay visual QA + profiler evidence |

## Định nghĩa trạng thái

**VERIFIED-STRUCTURE:** parsing/bounds/hash/round-trip đã có bằng chứng tương ứng. Không tự suy ra gameplay.

**VERIFIED-BEHAVIOR:** có setup tái lập, quan sát runtime hoặc trace, kết quả đo và test tương ứng với spec. Chưa có hệ thống gameplay nào được tuyên bố hoàn tất mức này ở lượt static audit.

**HYPOTHESIS:** giả thuyết đang thử; dữ liệu phản ví dụ được giữ lại. Nếu bounds/visual test fail thì không dùng output như asset/schema đúng.

**UNVERIFIED:** thiếu bằng chứng; phải có task đóng khoảng trống, không ghi PASS.

## Hồ sơ bắt buộc cho một kết luận mới

`claim_id`, source hash/run ID, file/offset hoặc timestamp, experiment ID, input biết được, output đo được, alternative explanations, confidence, acceptance test và ảnh/trace thực tế. Đối với asset thêm provenance, semantic ID, variant/duplicate group và trạng thái release.

Coverage phải gắn với requirement trong `../PROJECT_REQUIREMENTS.md` và phase trong `../PHASE_PLAN.md`. Một blocker chưa đóng chỉ có thể được thay bằng quyết định thay đổi yêu cầu rõ ràng, không bằng việc đổi tên thành “done”.

