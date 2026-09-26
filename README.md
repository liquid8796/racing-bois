# Racing Bois

**Checkpoint hiện hành:** [Phase0 evidence và đính chính](docs/research/PHASE0_CHECKPOINT.md). Không sử dụng các số liệu mâu thuẫn của bản tổng kết ban đầu. Phase0B vẫn chưa hoàn tất toàn bộ gameplay/semantic assets.

Game Unity mới cho Windows 10/11 x64, lấy trải nghiệm đua xe đối kháng của bản Road Rash PC được cung cấp làm tham chiếu; có single-player, LAN và online authoritative trên OCI.

Workspace duy nhất: `D:\Project\Unity\racing-bois-desktop`.

## Trạng thái ngày 2026-09-26

Đã thực hiện kiểm kê có SHA-256, phân tích nhị phân tĩnh, trích xuất tài nguyên theo cấu trúc và một số bộ giải mã thử nghiệm. **Chưa phục hồi hoặc kiểm chứng 100% logic game.** Chưa có bản game mới hoàn thiện, benchmark hay kiểm thử online toàn cầu. Không xem các PNG/reference trích xuất là asset production-ready.

Đọc theo thứ tự:

1. [Yêu cầu sản phẩm và checklist bắt buộc](docs/PROJECT_REQUIREMENTS.md).
2. [Báo cáo reverse-engineering và giới hạn bằng chứng](docs/research/REVERSE_ENGINEERING_REPORT.md).
3. [Ma trận coverage và các phần chưa xác minh](docs/research/COVERAGE_MATRIX.md).
4. [Baseline nội dung và cách nghiệm thu khối lượng asset](docs/CONTENT_BASELINE.md).
5. [Kiến trúc Unity, multiplayer, LAN và OCI](docs/TECHNICAL_ARCHITECTURE.md).
6. [Pipeline concept 2D → Blender → prefab Unity](docs/ASSET_PIPELINE.md).
7. [Kế hoạch từng phase và điều kiện chuyển phase](docs/PHASE_PLAN.md).

**Phase 0B đang thực hiện:** [Đặc tả finish/qualification/progression](docs/research/PROGRESSION_SPEC.md) và [kết quả kiểm chứng 0.1.21](docs/research/PROGRESSION_VALIDATION.md). Đã khớp 6.269 ca đối chiếu có giới hạn; chưa phải full gameplay. Tiếp tục controlled handling/combat và semantics assets. Không nhảy thẳng sang sản xuất hàng loạt asset, không thêm multiplayer vào cuối dự án.

## Nguồn và bằng chứng

Bản mod: `C:\Users\Liquid\Downloads\Unity\racing_bois_mod`.

Video: `C:\Users\Liquid\Downloads\prompt\Road Rash PC (1995) - Big Game Mode (All Levels).mp4`.

Corpus kiểm chứng lại: `docs/research/evidence/corpus-0.1.21/summary.json`; progression: `docs/research/evidence/progression-0.1.21/summary.json`. Snapshot `FINAL_AUDIT_SNAPSHOT.json` là hồ sơ lịch sử, không phải nguồn mới nhất. Các file trong `docs/research/evidence/` và `ReferenceOnly/` là bằng chứng nghiên cứu cục bộ; không mặc định được đưa vào bản phát hành. Mọi tổng số phải gắn với snapshot, không lấy số liệu từ log cũ bị thay thế.

Các công cụ tái lập nằm trong `tools/`; chúng đọc nguồn tham chiếu và ghi kết quả vào workspace. Không chạy các batch launcher của bản mod vì có thao tác ngoài phạm vi phân tích như tắt Explorer hoặc chỉnh registry.

Quy tắc làm việc cho agent nằm trong [AGENTS.md](AGENTS.md). Thông báo thư viện nghiên cứu nằm trong [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Source readable, dễ refactor, maintainable, testable và extensible theo [Architecture rules](docs/ARCHITECTURE_RULES.md); dùng pattern để giải quyết nhu cầu thật, không thêm abstraction chỉ vì hình thức.

