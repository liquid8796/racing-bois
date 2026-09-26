# Racing Bois — yêu cầu sản phẩm và tiêu chuẩn sản xuất

Ghi nhận: 2026-09-26. Đây là yêu cầu, chưa phải chứng nhận hoàn thành.

## Workspace và nguồn

- Project: `D:\Project\Unity\racing-bois-desktop`.
- Reference mod: `C:\Users\Liquid\Downloads\Unity\racing_bois_mod`.
- Gameplay: `C:\Users\Liquid\Downloads\prompt\Road Rash PC (1995) - Big Game Mode (All Levels).mp4`.
- Reverse-engineer thật sâu toàn bộ logic/dữ liệu/asset có thể truy cập, hướng tới coverage đầy đủ; ghi rõ phần chưa chứng minh. Không hứa phục hồi nguyên bản source, comments, tên biến hoặc tài sản không có trong distribution.
- Game mới tên **Racing Bois**, Unity, Windows 10/11 x64. Lối chơi bám sát Road Rash PC người dùng gọi bản 1996; tên video ghi 1995. Dùng hash để cố định reference, không suy ra edition chỉ từ tên file.
- Đồ họa và hiệu ứng chất lượng PC, sống động/bắt mắt, thống nhất art direction, performance tốt. Không AI slop; prototype không được trình bày như sản phẩm hoàn thiện.
- Khối lượng asset hoàn thiện ít nhất bằng baseline nội dung có nghĩa của bản gốc đã kiểm kê. Không đánh đồng dung lượng nén, bản sao, sprite frame và số model độc lập.

## Gameplay, multiplayer và OCI

- Single-player đầy đủ; multiplayer online và LAN.
- Người chơi trên Internet toàn thế giới có thể tìm/join cùng lobby; đo kết nối và độ trễ thật, không hứa một VM cho ping thấp toàn cầu.
- Backend quyết định realtime movement/collision/combat/damage/results; quản lý account, inventory, currency, lobby/create/join/leave/reconnect và progression.
- Production backend, database, user data đặt trên OCI VM/infrastructure đã xác minh, có backup/restore và bảo mật tài khoản.
- LAN cần chơi được khi Internet mất. Online persistent economy không nhận kết quả không đáng tin từ LAN/offline; LAN offline dùng local profile/cache và không tự hợp thức hóa tiền/vật phẩm online.

## Kiến trúc source code — yêu cầu bổ sung 2026-09-26

Yêu cầu của người dùng: “Source code của game cần được thiết kế theo design pattern chuẩn và phù hợp nhất sao cho source readable, cleanable, maintainable, dễ mở rộng vì sau này còn có thể thêm chức năng mới.”

Áp dụng cho client Unity, shared simulation, dedicated server, backend và công cụ nghiên cứu. Module có trách nhiệm rõ, dependency một chiều; ưu tiên composition, chọn pattern để giải quyết vấn đề cụ thể, không lạm dụng abstraction. Logic gameplay không phụ thuộc UI, transport hay database. Mỗi tính năng mới có điểm mở rộng, test và tài liệu kiến trúc. Chi tiết: [ARCHITECTURE_RULES.md](ARCHITECTURE_RULES.md).

## Quy tắc concept

**Generate concept 2D trước -> assistant tự duyệt -> mới tạo 3D assets hoặc UI.**

Mỗi nhóm asset có concept ID, prompt/version, ảnh đã kiểm tra, review silhouette/màu/chất liệu/tỷ lệ/readability, verdict APPROVED/REVISE và ràng buộc sản xuất. Text brief hoặc ảnh chưa nhìn không thay thế concept duyệt. Không yêu cầu user duyệt từng concept. Dùng Blender trên máy người dùng và Unity MCP. Lượt hiện tại chỉ nghiên cứu/lập plan, chưa sản xuất concept/3D/UI.

## Checklist bắt buộc: Unity production-ready

### Model
- Scale đúng, pivot hợp lý.
- Không mesh lỗi, mặt ngược, vertex thừa.
- Polycount phù hợp target platform/khoảng cách gameplay.
- Naming rõ ràng.

### UV & Texture
- UV không overlap ngoài chủ đích; ghi rõ overlap được phép. UV lightmap không overlap khi bake.
- Texture đúng resolution/texel density; không tăng 4K hàng loạt.
- Đủ Base Color / Normal / Metallic / Roughness hoặc Mask Map khi cần.
- Compression đúng Windows target; sRGB/linear, normal map, alpha, mipmap được cấu hình đúng.

### Material
- Shader đúng pipeline Built-in / URP / HDRP đã chốt, không trộn tùy tiện.
- Không missing material hoặc material duplicate không cần thiết.
- Quy ước roughness/smoothness và packed channels có tài liệu.

### Optimization
- LOD nếu asset lớn hoặc xuất hiện nhiều, kiểm tra silhouette/transition.
- Mesh compression hợp lý, không hỏng shading/rig.
- Static flags đúng asset tĩnh, không gắn cho vật thể chuyển động.
- Không texture/material quá nặng; có memory/draw-call/shader budgets.

### Collider
- Collider đúng hình dạng gameplay; ưu tiên Box/Sphere/Capsule/compound nếu đủ.
- Tránh MeshCollider khi không cần, không collider thừa/chồng ngoài chủ đích.
- Kiểm tra layer, fast-moving contact, server collision proxy.

### Prefab
- Có prefab, root Position (0,0,0), Rotation theo quy ước, Scale (1,1,1).
- Không Missing Script / Missing Reference hoặc phụ thuộc scene ngoài.

### Lighting
- Normal/tangent đúng, lightmap UV nếu baked.
- Không artifact khi chiếu sáng; kiểm tra daylight/shadow/night/rim và gameplay camera.

### Animation (nếu có)
- Rig đúng, clip sạch, transitions hợp lý.
- Loop / Root Motion theo yêu cầu; clip không tự quyết định damage/motion trái server.
- Avatar/Humanoid mapping đúng nếu character; kiểm tra retarget và contact tay/chân.

### Test cuối
- Drag prefab vào scene độc lập và chạy bình thường.
- Không Console Error/Warning liên quan asset.
- Quan sát tốt ở khoảng cách gameplay thật, trong chuyển động, không chỉ studio render.
- FPS/memory không ảnh hưởng bất thường; lưu profiler/QA evidence, không tự tick pass.

## Chất lượng và chứng cứ

- Hoàn thiện một vertical slice đạt chuẩn trước khi nhân rộng content.
- Mỗi feature truy được yêu cầu -> bằng chứng gốc -> spec -> implementation -> test.
- Performance numbers chỉ là mục tiêu cho đến khi đo trên hardware đã ghi nhận.
- Asset trích xuất không mặc nhiên đủ quyền phát hành; production chỉ dùng original/licensed/được cấp quyền rõ ràng.
- Không chỉnh registry, tắt Explorer, deploy OCI, tạo tài nguyên tính phí hoặc chạm project Unity khác trong phase nghiên cứu.
