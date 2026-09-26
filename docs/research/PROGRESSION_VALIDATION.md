# Racing Bois — validation receipt cho progression 0.1.21

Ngày 2026-09-26. Đây là bản tổng hợp được review để commit; dump byte, executable, native cases, save samples, trace và screenshot vẫn chỉ ở thư mục evidence/ReferenceOnly cục bộ. Không có chứng nhận hoàn tất Phase 0B.

## Kết quả canonical

| Hạng mục | Kết quả | Evidence cục bộ |
|---|---:|---|
| Finish request | 1.354 / 1.354 khớp | evidence/progression-0.1.21/native_cases.json |
| Offline outcome-screen tail | 1.036 / 1.036 khớp | Cùng native_cases.json |
| Qualification và media prefix | 2.116 / 2.116 khớp | Cùng native_cases.json |
| Acknowledgement và progression | 1.760 / 1.760 khớp | Cùng native_cases.json |
| Chuỗi gọi giả lập nối các boundary | 3 / 3 khớp | Cùng native_cases.json; không phải race runtime |
| Tổng progression | **6.269 / 6.269 khớp**, không error/failure | evidence/progression-0.1.21/summary.json |
| Native regression cấu trúc trước đó | 885 / 885 khớp | evidence/corpus-0.1.21/summary.json |
| Bike-name và reward-prefix regression | 832 / 832 khớp | evidence/gameplay-0.1.21/summary.json |
| Unit/regression thuộc tập nguồn commit này | **93 PASS**, 0 failures/errors/skips | evidence/release-0.1.21.json |
| Trong đó tests progression mới | 36 PASS | compatibility 5 + gameplay 10 + phase0 42 + progression 36 |
| Release build AuditVerifier | PASS, exit 0 | evidence/build-release-0.1.21.log |
| Assembly thực thi kiểm kê nguồn | **0.1.21.0**, verified=true | evidence/release-0.1.21.json |

Progression run ID: **2026-09-26T07:05:10.469399+00:00**. Corpus recheck run ID: **20260926T071444Z**. Gameplay subset run ID: **20260926T070908Z**. Source: 374 file, 503.081.481 byte, 365 hash độc nhất; không thay đổi source. Cả version file và các nguồn của progression harness đều không đổi trong canonical run.

Hash executable: **66ab853c5b7b73b82a7c22a0478f5ba5b1066ed27028ef96449f5fe36a6101c5**.

## Phạm vi bằng chứng

Đọc [PROGRESSION_SPEC](PROGRESSION_SPEC.md) cho địa chỉ, preconditions, trường quan sát và giới hạn. Oracle và model độc lập; native execution giới hạn vùng lệnh/ghi, thời gian và số instruction, dừng trước các call network/Win32/media. Từng outcome là kết quả của một boundary với fixture đầu vào, không phải video toàn cảnh hoặc một phiên chơi hoàn chỉnh.

Kết quả 885 và 832 kiểm tra các phần khác đã tồn tại; chúng không phải 1.717 case mới do patch progression tạo ra. Suite toàn working tree từng qua 99 tests khi có thêm sáu runtime-scenario tests từ continuation khác. **93 là tập test được ghi nhận cho nguồn thuộc patch này**; không nhận các test/runtime work đang làm song song là của progression patch.

Build release 0.1.21.0 đã thực thi, kiểm tra đủ 374 file/503.081.481 byte và trả failures rỗng. Đây là build tool AuditVerifier, **không phải build game Unity**.

## Tính toàn vẹn và tái lập

Run đầu dưới tên evidence/progression-0.1.19 đã khớp số học nhưng version working tree thay đổi khi chạy. Nó được giữ làm lịch sử và không dùng làm canonical evidence. Runner 0.1.21 chụp fingerprint trước/sau; chỉ cần version hoặc source tool đổi, kết quả tổng phải FAIL dù native cases vẫn khớp. Có unit test chủ động tạo tình huống này.

Canonical run giữ inventory-before/after, tool-inputs-before/after, failures và summary. Hash các source chính lúc chạy:

~~~text
legacy_progression.py    05192da3af8acf5e861d72f46892300bff8cc62fa8f392d26ab93e974c0f0d62
progression_oracle.py    74bd4a578e5eab90c70f3691da132878c8ddcf5c05121af0086930ecb2b99751
validate_progression.py  428f495ef7cd4eb1c5bce12cbe5f7a1c4ba9e56575aac51b31ca0733952f5276
native_oracle.py         939b1d2aa0e631967f7f0dfd19c3a989d50ec07801b04d8a8b185b48a5eaea17
~~~

Các dependency nghiên cứu khác cũng được fingerprint trong summary. Chạy lại với thư mục output mới, không ghi đè evidence cũ:

~~~powershell
python tools/validate_progression.py --out docs/research/evidence/progression-new-run
python -m unittest discover -s tools -p '*_tests.py' -v
dotnet build tools/AuditVerifier/AuditVerifier.csproj --configuration Release --nologo
~~~

Máy cần dependency nghiên cứu đã pin trong toolchain hiện có; script từ chối executable khác hash. Version tool đang mở có thể khác phiên bản của bằng chứng lịch sử này khi continuation runtime tiếp tục. Không tự đổi nhãn run cũ theo version mới.

## Trạng thái phase

Phase 0A đạt phạm vi kiểm kê/cấu trúc. Phase 0B bổ sung verified-native subsets cho finish request, qualification và chuyển level. Còn mở: chứng minh simulation tiến triển, controlled handling/brake/crash/combat, damage/AI/police, finish-line/caller lifecycle, shop/repair/penalty, persistence/network và semantic asset completeness. Xem [coverage](COVERAGE_MATRIX.md), [phase plan](../PHASE_PLAN.md) và checkpoint runtime riêng.

Yêu cầu code readable, dễ refactor/maintain/test/extend đã được lưu tại [Architecture rules](../ARCHITECTURE_RULES.md) và AGENTS.md. Không tạo 3D/UI hay deployment ngoài phạm vi nghiên cứu này.
