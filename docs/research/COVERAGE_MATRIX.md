# Racing Bois — coverage matrix

Cập nhật phần cấu trúc và progression ngày 2026-09-26, tool 0.1.21. Bằng chứng tổng hợp: [Progression validation](PROGRESSION_VALIDATION.md); runtime có checkpoint riêng tại [PHASE0_CHECKPOINT.md](PHASE0_CHECKPOINT.md). Không có tuyên bố “100% logic recovered”.

## Coverage hiện hành

| Domain | Trạng thái | Bằng chứng cục bộ / đặc tả | Khoảng trống còn phải đóng |
|---|---|---|---|
| Corpus / SHA-256 | VERIFIED-STRUCTURE | evidence/corpus-0.1.21/summary.json: 374 file, 503.081.481 byte, 365 hash; nguyên trạng | Corpus mod không tự chứng minh đầy đủ canonical original |
| PE / native navigation | VERIFIED-STRUCTURE | PE headers, imports, 1.585 Ghidra exports; NATIVE_NAVIGATION.md | Inferred types/callback boundaries và semantics toàn game chưa đầy đủ |
| RSRC containers | VERIFIED-STRUCTURE | 13 containers / 429 entries, bounds và byte extraction | Nested payload không đồng nghĩa đã định danh asset |
| RRI / BMP | VERIFIED-STRUCTURE | 119 JPEG và 1 BMP được decode | Semantic uniqueness, usage và provenance phát hành |
| RRA / WAV | VERIFIED-STRUCTURE | 87 RIFF/WAVE | Loop/loudness, nghe kiểm tra, mapping sự kiện |
| MIDS / sfbk | VERIFIED-STRUCTURE | 11 MIDS, 6 soundfont banks; parser regressions | Music/instrument/event mapping; không có corpus SPK |
| AVI | VERIFIED-STRUCTURE | 61 file probe và decode frame đầu | Không phải full-duration decode hoặc xem hết nội dung |
| DAT sprite | VERIFIED-STRUCTURE / VERIFIED-NATIVE-SUBSET | 7 banks, 1.439 slots / 869 nonempty, exact EOF, native walker | Palette/transparency/orientation và semantic animation mapping |
| BOB / MIP | HYPOTHESIS-PARTIAL | 27 raw-indexed BOB, 1 MIP; rendering loader anchors | Dimensions/stride/palette/UV ý nghĩa, đối chiếu ảnh runtime |
| FAM | VERIFIED-STRUCTURE | 269 outer payload, 106 placeholders, 2.515 opaque leaves | Inner semantics; leaf hoặc placeholder không được đếm là production asset |
| SGS / NOD courses | VERIFIED-STRUCTURE | 5 course, 109 sections / 859 chunks | Geometry, units, elevation, topology, spawn/placement runtime |
| SPEC / 15 bike profiles | VERIFIED-NATIVE-SUBSET | Initializer trong 885 structural native cases | Tên/đơn vị trường, tuning và measured handling |
| CAR / ANIM / CEL / CANS / PAL | VERIFIED-STRUCTURE-PARTIAL | Resource identities và payload bounds | Frame timing, collision, palette, mapping object/scene |
| Save envelope / checksum | VERIFIED-STRUCTURE / VERIFIED-NATIVE-SUBSET | 14 RRS hợp lệ; 4 file zero-filled không phải saves | Profile field semantics, persistence/crash consistency |
| Bike name / result cash prefix | VERIFIED-NATIVE-SUBSET | evidence/gameplay-0.1.21/summary.json: 832/832; GAMEPLAY_SPEC.md | Full entry conditions, purchases, repairs, penalties, grant idempotency |
| Finish request / result screen | VERIFIED-NATIVE-SUBSET | PROGRESSION_SPEC.md: 1.354 + 1.036 cases | Finish-line detection, real elapsed-time units, full caller lifecycle |
| Qualification / result media | VERIFIED-NATIVE-SUBSET | PROGRESSION_SPEC.md: 2.116 cases | Actual playback, invalid-course native stack semantics deliberately excluded |
| Level acknowledgement | VERIFIED-NATIVE-SUBSET | PROGRESSION_SPEC.md: 1.760 cases + 3 synthetic call chains | Network callback, live race progression, actual save writes |
| Handling / braking / crash / recovery | UNVERIFIED-BEHAVIOR | Native navigation and research reference | Controlled input/trace, timings, units, repeatable comparisons |
| Combat / weapons / damage | UNVERIFIED-BEHAVIOR | Resource/code anchors | Active frames/range, left/right, block/counter, cooldown and damage |
| AI / traffic / police | UNVERIFIED-BEHAVIOR | Course/resource/code anchors | Decisions, perception, difficulty, pursuit/arrest runtime |
| Video reference | PARTIAL-OBSERVATION | 39 sparse frames / 4 contact sheets, earlier checkpoint | Full event annotation; a still is not a hit/recovery timing measurement |
| Runtime navigation | SEPARATE-EXPERIMENT | PHASE0_CHECKPOINT.md and private probe reports | Rendered frame / race setup does not prove advancing simulation |
| Unity / Blender / OCI / multiplayer | NOT-ACCEPTED | Architecture and production phase plan only | Correct-instance integration, build/runtime/network/performance evidence |
| Production art / baseline completeness | NOT-ACCEPTED | PROJECT_REQUIREMENTS and concept gate | Canonical content roster, rights/provenance, approved concepts and prefab QA |

## Ý nghĩa trạng thái

**VERIFIED-STRUCTURE:** parsing, bounds, hash, byte round-trip hoặc media decode đã có kiểm tra tương ứng. Không tự suy ra gameplay đúng hoặc release-eligible asset.

**VERIFIED-NATIVE-SUBSET:** pure model khớp mã máy gốc tại các boundary và miền input ghi rõ. Những globals/stack đầu vào là fixture giả lập; network/Win32 calls bị loại khỏi thí nghiệm. Không đồng nghĩa đã chơi race thật, hiểu mọi caller hoặc đạt toàn bộ behavioral coverage.

**VERIFIED-BEHAVIOR** chỉ được dùng cho một claim có controlled setup/input, live observation/trace, output đo và acceptance test phù hợp. Toàn bộ handling/combat/AI chưa đạt mức này.

**HYPOTHESIS / PARTIAL / UNVERIFIED / NOT-ACCEPTED:** còn thiếu bằng chứng hoặc gate. Không đổi nhãn thành PASS chỉ vì một parser/test khác thành công.

## Hồ sơ bắt buộc

Mỗi claim cần source hash/run ID, file/offset hoặc timestamp, input/setup, output, alternative explanations, confidence, limitations và test. Evidence runner phải thất bại khi tool version/code thay đổi giữa run. Asset cần thêm semantic ID, provenance và duplicate/variant grouping.

Không cộng số case, frame, leaf, LOD hoặc file trùng thành số asset độc lập hoặc phần trăm logic đã phục hồi. Phase 0A đạt phạm vi kiểm kê/cấu trúc; **Phase 0B vẫn mở**. Đối chiếu [requirements](../PROJECT_REQUIREMENTS.md), [architecture rules](../ARCHITECTURE_RULES.md) và [phase plan](../PHASE_PLAN.md).

