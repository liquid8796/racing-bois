# Racing Bois — kiến trúc đề xuất

Ngày: 2026-09-26. Trạng thái: **proposed, chưa triển khai hoặc benchmark**. Các con số về tick, người chơi, FPS và backup dưới đây là mục tiêu thử nghiệm, không phải kết quả đã đạt.

## 1. Quyết định nền tảng

Client: Unity 6, C#, Windows 10/11 x64. URP là lựa chọn mặc định đề xuất để chủ động visual/performance budgets; không chọn HDRP chỉ vì tên pipeline. Pin chính xác editor, package lock, render pipeline và build modules sau compatibility spike. Phiên bản cài trên máy không tự trở thành phiên bản production đã kiểm định.

Chia thành các lớp `Game.Simulation`, `Game.Content`, `Game.Networking`, `Game.Presentation`, `Game.Client`, `Game.Server`, `Game.Tests`. Simulation không phụ thuộc camera/UI/VFX. Quy tắc movement/combat/race shared cho local single-player, LAN host và dedicated online; authority khác nhau nhưng không copy ba bộ logic dễ lệch.

Unity có Dedicated Server build target [S1]. Kiến trúc đề xuất dùng Unity headless worker để giữ collision/game simulation gần client, còn account/lobby/persistence là service riêng. Không giả định PhysX replay luôn deterministic giữa mọi OS/CPU hoặc giao cho ragdoll quyết định kết quả combat.

## 2. Mạng và server authority

Mục tiêu đầu tiên: 8 người chơi thật trong một room; 16 chỉ được nâng thành yêu cầu release sau tải thử và quality review. AI count, traffic count và budget mỗi room được ghi trong benchmark scenario, không bỏ AI khỏi benchmark rồi tuyên bố hỗ trợ đủ trận.

Client gửi input có sequence và simulation tick; không gửi “tôi đã gây X damage” như sự thật. Server kiểm tra session ticket, tốc độ input, state hợp lệ, cooldown, khoảng cách, giới hạn movement và race progress. Server quyết định health, hit, knockdown, checkpoints, finish order và result.

Tick đề xuất ban đầu 60 Hz, so trực tiếp phương án 30 Hz trong spike. Snapshot target 20–30 Hz, delta compression và interest management tùy đo tải. Client prediction/reconciliation cho xe mình, interpolation cho đối thủ, bounded lag compensation cho combat. Giới hạn rewind, input age và correction magnitude phải được đo, có metric; không cho client chọn timestamp tùy ý.

Road movement ưu tiên mô hình arcade có tham số được rút từ reference; rigidbody/presentation không được gây nondeterministic damage. Visual hit feedback có thể dự đoán nhưng damage ledger theo server; reconcile không tạo double hit/SFX lặp hay teleport nguy hiểm.

Chưa khóa networking package. Spike phải so ứng viên phù hợp Unity hiện dùng về prediction, physics interaction, Linux server build, license, maintenance và memory/CPU; chỉ chọn sau hai-client combat thực tế. Không thêm ECS hoặc tự viết transport mới chỉ để kiến trúc trông phức tạp.

## 3. Flow online

Client -> HTTPS gateway -> account/session -> lobby directory -> room allocation -> short-lived join ticket -> game worker -> race result commit -> profile refresh.

Lobby hỗ trợ create/list/join/code/password nếu dùng, ready/unready, map/rules/version check, slot reservation, countdown, leave, kick theo quyền và timeout. Join ticket gắn user, room, protocol/content version, expiry và nonce. Worker không nhận profile/currency do client tự khai.

Race lifecycle có `Waiting`, `Loading`, `Countdown`, `Racing`, `Finishing`, `Settling`, `Closed`. Từng transition có timeout và idempotency. Không start hai lần, settle hai lần hoặc làm người vào muộn xuất hiện giữa track mà không có policy.

Disconnect/reconnect giữ slot trong thời gian cấu hình, issue ticket mới và trả authoritative snapshot. DNF và thay bằng AI cần rule rõ ràng. Không xem offline tick/client replay là nguồn kết quả đáng tin. Host migration không thuộc online MVP vì online dùng dedicated worker; LAN host mất kết nối phải hiển thị rõ trận kết thúc, không âm thầm hứa migration.

## 4. LAN thực sự không phụ thuộc Internet

LAN chạy listen-host hoặc local dedicated process từ cùng simulation code; discovery trên subnet và direct-IP join làm fallback. Firewall guidance phải rõ ràng. LAN không cần gọi OCI để bắt đầu trận, không bắt buộc đăng nhập online khi mạng Internet mất.

**Trust boundary:** máy host LAN có thể bị người sở hữu sửa đổi, nên authoritative trên LAN chỉ giải quyết đồng bộ giữa các client, không tạo độ tin cậy tương đương worker OCI. Offline/LAN progression thuộc local/unranked profile; không tự nhập phần thưởng/currency/item vào online economy.

Production accounts/database/player data online vẫn nằm trên OCI. Local save/cache cần thiết cho offline là ngoại lệ vận hành có chủ đích, không phải chuyển backend online khỏi OCI. Có thể dùng garage snapshot được tải trước cho LAN nhưng không coi những chỉnh sửa sau đó là giao dịch online hợp lệ.

## 5. Backend và database

Đề xuất một backend modular monolith giai đoạn đầu, HTTPS API, PostgreSQL và game workers riêng process/container. Account/profile/inventory/wallet/lobby có ranh giới module rõ, chưa cần chia hàng chục microservice. Redis chỉ bổ sung khi có nhu cầu cache/coordination đo được; không dùng nó thay nguồn dữ liệu giao dịch.

Các bảng/logical models: users/auth identities, profiles, owned bikes/items, wallet ledger, inventory ledger, rooms, race participants, race results, reward grants, moderation/audit, schema migrations. Tiền dùng số nguyên theo đơn vị được định nghĩa. Mỗi grant có idempotency key và transaction; unique race/user/reward key ngăn nhân phần thưởng do retry.

Worker ký hoặc xác thực service-to-service result; backend xác minh worker/room/version trước commit. User client không có endpoint tự cộng tiền. Save offline và dữ liệu migration từ game cũ không được tự coi là sở hữu online hợp lệ.

Auth chọn phương án ít quản trị rủi ro sau threat model; không tự chế cryptography. Mật khẩu nếu tự host phải dùng thư viện password hashing phù hợp, không plaintext; token có expiry/revocation, admin phân quyền, rate limiting, recovery flow và log không lộ secret/PII. Chưa có security audit nên không ghi hệ thống “an toàn tuyệt đối”.

## 6. OCI: kiểm tra trước khi deploy

Phải xác minh instance/region/shape/architecture/OS, available OCPU/RAM/disk, service đang chạy, public IP/DNS, VCN/NSG/security lists, OS firewall, SSH access và quy trình rollback. Không in private key/password vào tài liệu. Không thay backend Jarvis hoặc service khác trên VM khi triển khai game.

**Architecture gate:** OCI có cả shape x86 và Ampere ARM [S3]. Không mặc định VM hiện tại chạy được Unity Linux server binary. Tài liệu Unity 6.0 liệt kê yêu cầu server theo platform/CPU [S2]; phải kiểm tra lại chính editor/build target đã pin. Nếu VM hiện tại là ARM mà build worker yêu cầu x86-64, API/database có thể vẫn chạy trên ARM nhưng worker cần host/build tương thích, hoặc quyết định kiến trúc khác đã qua spike. Không xem emulation chưa benchmark là giải pháp production.

Đề xuất expose HTTPS 443 cho API và một dải UDP có giới hạn cho game worker sau khi transport được chốt. PostgreSQL không mở public. SSH chỉ từ nguồn quản trị được cho phép. NSG/security-list rule và firewall trong OS phải cùng đúng; rule cloud không thay thế mọi điều kiện ở host [S4]. Không mở toàn bộ cổng chỉ để thử cho nhanh.

Global connectivity dùng public dedicated endpoint: người chơi outbound đến server, không yêu cầu từng người tự port-forward router. Vẫn phải thử trên nhiều ISP/NAT và trường hợp UDP bị chặn. Không hứa một VM cho ping thấp toàn cầu; hiển thị region/ping, dùng latency-aware room selection. Mở thêm region OCI là lộ trình sau đo p95 RTT, tải, capacity và ngân sách, không tự tạo tài nguyên tính phí.

Một VM có thể làm pilot nếu đủ tài nguyên đo được; chưa đủ cơ sở bảo đảm production concurrency. Isolate CPU/RAM worker khỏi DB/API, đo contention, crash recovery và disk/IO. Admission control phải từ chối room mới rõ ràng thay vì quá tải toàn bộ máy.

## 7. Backup, vận hành và quan sát

Database có volume bền vững, migration versioning và backup mã hóa ra vị trí OCI tách khỏi VM chính; snapshot nằm duy nhất cùng disk không được coi là chống mất VM. Restore drill trên database cách ly là điều kiện nghiệm thu. RPO/RTO và retention chốt sau kiểm tra hạ tầng/chi phí; mục tiêu ban đầu để lập kế hoạch: RPO <= 15 phút, RTO <= 60 phút, chưa phải khả năng đã có.

Metrics: room count, active users, RTT/jitter/loss, corrections, tick p50/p95/p99, queue/backlog, CPU/RAM, GC, DB latency/pool, failed auth, duplicate reward prevention, disconnect/reconnect và crash count. Log có request/room/race IDs, không chứa token hoặc password. Alert thresholds và runbooks phải gắn với tác động người chơi.

Version protocol/content manifest có negotiation và fail message dễ hiểu. Deploy worker mới drain room cũ; DB migration tương thích phiên bản đang chạy; rollback đã thử. Không shutdown tất cả trận đang chơi để cập nhật đơn giản.

## 8. Performance và chất lượng — mục tiêu phải đo

Client target ban đầu: 1080p/60 FPS ở preset và hardware reference được khóa ở Phase 1; đo player build, không chỉ Editor. Trong steady-state scenario định nghĩa trước: p95 frame time <= 16,7 ms, p99 <= 33,3 ms; loading/shader warmup ghi riêng và không dùng trung bình che stutter. Min-spec hardware và RAM/VRAM budget chưa chốt; không suy từ “máy cài Unity được”.

Server target: p99 tick work <= 70% tick budget khi đầy room gồm AI/traffic và combat; tick queues không tăng mãi. Soak và profiler phải có build/hash/scenario/OS/hardware, player count, duration, histogram và failures.

Network matrix gồm RTT 50/100/150/250 ms, jitter 0/20/50 ms và loss 0/1/3/5%; đây là test conditions, không hứa trải nghiệm 250 ms giống LAN. Đặt giới hạn RTT cho competitive/ranked, feedback rõ và không âm thầm ưu tiên người ping cao.

## 9. Nguồn kỹ thuật chính thức

Tra cứu ngày 2026-09-26; cần đối chiếu lại cho phiên bản production được pin.

- [S1] Unity Dedicated Server: `https://docs.unity3d.com/6000.0/Documentation/Manual/dedicated-server.html`
- [S2] Unity system requirements, server platform: `https://docs.unity3d.com/6000.0/Documentation/Manual/system-requirements.html`
- [S3] Oracle OCI compute shapes: `https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm`
- [S4] Oracle OCI security rules: `https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm`

Liên quan: [yêu cầu](PROJECT_REQUIREMENTS.md), [kế hoạch](PHASE_PLAN.md), [baseline](CONTENT_BASELINE.md).

