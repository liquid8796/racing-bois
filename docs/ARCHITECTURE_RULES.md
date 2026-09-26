# Racing Bois — quy tắc kiến trúc và chất lượng source

Ngày: 2026-09-26. Yêu cầu bắt buộc; implementation sẽ được khóa bằng ADR ở Phase 1. Project memory đang tắt; AGENTS.md và tài liệu này là điểm tham chiếu bền vững trong repository.

## Mục tiêu

Source dễ đọc, dễ làm sạch/refactor, dễ bảo trì, dễ kiểm thử và mở rộng. Không có một pattern duy nhất tốt nhất cho mọi module. Mỗi pattern giải quyết nhu cầu cụ thể, có trade-off được giải thích; không tạo framework tổng quát chỉ vì dự đoán tương lai.

## Ranh giới đề xuất

- **Domain/Simulation:** dữ liệu, luật đua/combat/progression, bước mô phỏng thuần; không truy cập scene, transport, database, đồng hồ hệ thống hoặc global state ngầm.
- **Application:** điều phối use case, ownership và validation qua các port nhỏ có mục đích rõ.
- **Adapters/Infrastructure:** Unity presentation/input/physics adapter, network transport, OCI/database/filesystem. Dependency hướng vào contract/domain, không hướng ngược ra ngoài.
- **Composition root:** tạo và nối dependencies rõ tại bootstrap; không service locator hoặc Singleton GameManager chứa toàn bộ game.

Shared simulation phục vụ single-player, LAN và dedicated server. Visual prediction không tự cấp damage/currency/result. Định nghĩa bất biến (bike/weapon/course) tách khỏi trạng thái mỗi trận. Unit, tick, ID, schema/version và lifetime có tên, phạm vi, ownership rõ.

## Pattern dùng khi phù hợp

| Vấn đề | Pattern ứng viên | Giới hạn |
|---|---|---|
| Riding/attack/crash/recovery, lobby lifecycle | State machine | Transition tường minh; enum và hàm thuần đủ thì không tạo class cho mọi state |
| Steering, AI decision, attack thay thế được | Strategy/composition + dữ liệu | Interface tại điểm thay thế thật, không interface cho mọi class |
| Input/replay/server validation | Command/data message có tick/sequence | Tách transport DTO và domain; validate trust boundary |
| UI/audio/VFX phản ứng gameplay | Typed events/Observer phạm vi rõ | Unsubscribe/disposal; tránh global event bus khó truy vết |
| Persistence/economy | Repository cho aggregate cần thiết, transaction/idempotency | Không che transaction bằng generic repository; không ghi DB mỗi tick |
| Tạo entity theo catalog | Factory nhỏ, stable semantic IDs | Không reflection registry khi constructor đủ |
| Đối tượng lặp thường xuyên | Pool theo profiling | Reset ownership/state sạch; không pool tùy tiện |

Parser nghiên cứu cũng tách parsing thuần khỏi file I/O, CLI và báo cáo. Oracle độc lập với implementation được kiểm tra, không dùng cùng hàm làm expected và actual.

## Review mỗi thay đổi

Tên rõ nghĩa, trách nhiệm nhỏ hợp lý, không copy-paste logic hay magic number thiếu unit. Dependency/side effects/lifetime nhìn thấy được. Không nuốt lỗi hoặc biến input sai thành PASS. Input không tin cậy được kiểm bounds, size, identity và quyền truy cập.

Feature mới có test thành công/lỗi/edge case; bug fix có regression. Logic thuần có unit tests, ranh giới có integration/contract tests, scene có EditMode/PlayMode phù hợp. Có timeout/cancellation/cleanup cho công cụ và tác vụ ngoài. Không tạo test chỉ để tăng coverage số lượng.

Quyết định kiến trúc đáng kể ghi ADR: bối cảnh, lựa chọn, phương án khác, trade-off, dependency, cách kiểm chứng và điều kiện xem xét lại. Mỗi patch cập nhật Markdown hiện có, bump version assembly và dùng commit `type(scope): message`.

## Không được làm

Không god object, mutable static state ngầm, dependency vòng, domain logic trong UI MonoBehaviour hay SQL/HTTP callback. Không DI framework/ECS/event sourcing/microservices chỉ để có tên pattern; cần nhu cầu và spike. Tính dễ bảo trì không đổi bằng GC/CPU spikes không đo; performance cũng không biện minh code khó hiểu không có benchmark.

## Trạng thái

Đã lưu yêu cầu; chưa có implementation game để chứng nhận tuân thủ. Phase 0 tiếp tục nghiên cứu, không tự chuyển sang 3D/UI hoặc gameplay production.
