# Racing Bois — pipeline hình ảnh và asset

Ngày: 2026-09-26. Tất cả trạng thái APPROVED/PASS trong tương lai phải có ảnh hoặc kết quả test thực tế; tài liệu này không approve bất kỳ asset nào hiện tại.

## 1. Art direction đề xuất

Giữ cảm giác đua xe đối kháng tốc độ cao và khả năng đọc tình huống rõ. Hướng đề xuất là realistic-stylized PC: tỷ lệ và vật liệu thuyết phục, silhouette mạnh, màu/ánh sáng có chủ đích, đường/traffic/rider luôn dễ phân biệt. Không dùng bloom quá mức, noise, chi tiết ngẫu nhiên hoặc hàng loạt texture không thống nhất để tạo cảm giác “nhiều asset”. Hướng này phải được xác nhận bằng concept và vertical slice, chưa phải quyết định visual cuối.

Đẹp phải đúng camera gameplay: góc nghiêng xe, khoảng cách đối thủ, tay/chân ra đòn, contact, motion, HUD và visibility ở tốc độ cao. Một turntable đẹp nhưng gameplay rối vẫn fail.

## 2. Gate bắt buộc: generated 2D trước 3D/UI

Mỗi nhóm asset/màn hình bắt đầu bằng 2D concept được generate. Assistant trực tiếp xem ảnh, nhận xét và ghi quyết định **APPROVED** hoặc **REVISE**; không yêu cầu người dùng duyệt từng concept. Text prompt, moodboard chưa kiểm tra hoặc contact sheet trích từ game không thay thế concept đã duyệt.

Hồ sơ concept gồm `concept_id`, category, requirement/reference IDs, prompt/model/workflow thực dùng, image path/hash, version, view coverage, palette/material notes, silhouette/scale/readability notes, lỗi thấy được, revision reason và approval timestamp. Không auto-approve ảnh chỉ vì tool trả thành công. Phải kiểm tra anatomy, wheel count/geometry, perspective và text/UI legibility trước sản xuất.

Nhóm đầu cần concept: visual keyframe đường đua, bike/rider, traffic/police, props/landmarks, weapon/impact VFX direction, main menu/garage, HUD/lobby/results/settings. Orthographic/multiview chỉ là reference hướng dẫn; khi các view mâu thuẫn phải sửa, không lắp 3D theo các view lỗi.

## 3. Blender trên máy người dùng

Trước mỗi phiên, xác minh đúng scene/project và giữ work đang có. Asset lưu `.blend` nguồn theo semantic ID; export settings, unit scale và axis có quy ước được kiểm tra bằng test import. Không xóa scene đang dùng bởi phiên khác.

Sau concept approval: blockout -> silhouette/scale check -> mesh/UV -> bake/texture -> materials -> rig/animation nếu cần -> LOD/collider proxies -> export -> Unity import -> prefab -> visual/performance QA.

Dùng quy ước 1 Unity unit = 1 m cho world production, rồi kiểm tra conversion Blender/export thực tế; không chữa sai scale bằng root prefab khác (1,1,1). Wheel/rider/weapon pivot và contact sockets phải phục vụ gameplay, không chỉ thuận tiện khi model.

Asset lặp lại dùng modular kit, shared material/trim/atlas khi hợp lý. Mỗi material có channel convention, texture density, resolution class và compression policy. Không tạo một material mới cho mỗi bản sao nếu không cần. LOD tạo theo màn hình và silhouette, không chỉ decimate theo phần trăm.

## 4. Quality gates trên Unity

Checklist đầy đủ trong [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md) là bắt buộc; pipeline này không thay thế checklist đó.

Automated validation nên kiểm tra root transform/naming, missing refs/scripts/materials, renderer/material counts, texture importer flags/resolution/compression, mesh data/bounds, LODGroup, collider/layers, rig/Avatar và static flags phù hợp. Rule có exception list giải thích được; không sửa hàng loạt collider/static chỉ để hết cảnh báo.

Visual QA gồm sáng/tối, shadow/specular, tangent seams, silhouette ở gameplay distance, LOD transitions, attack contact, animation loop/root motion, UX readability và stress scene có nhiều bản sao. Mesh/texture round-trip test không thay thế review hình ảnh.

Performance QA trong player build với prefab xuất hiện ở mật độ gameplay thật; ghi CPU/GPU/memory/material/draw-call delta. Texture lớn và shader phức tạp cần justification theo screen coverage. Không duyệt asset chỉ vì một mình nó chạy mượt trong scene trống.

## 5. Definition of Done cho một asset

Có semantic ID/provenance/reference mapping, concept APPROVED đã xem, source `.blend` hoặc source UI/audio tương ứng, export tái lập, material/texture đầy đủ, prefab sạch, collider/LOD/rig đúng nếu cần, screenshot gameplay, test report và budget phù hợp.

Trạng thái đề xuất: `ReferenceCatalogued -> ConceptDraft -> ConceptApproved -> Production -> Imported -> TechnicalQA -> VisualQA -> PerformanceQA -> ReleaseEligible`. Fail ở bước nào quay lại bước liên quan; không đổi PASS bằng nhận xét chung “trông ổn”.

UI đặc biệt cần kiểm tra 1080p, 1440p, ultrawide theo scope; safe area, font/text overflow, keyboard/controller focus, localization-length stress và tất cả loading/error/disconnect states. Không dùng ảnh concept với text sai làm UI cuối; UI cần layout/text thật và interaction test.

## 6. Chống AI slop và thổi phồng số lượng

Tạo ít asset chuẩn làm benchmark trước. Chỉ nhân rộng khi vertical slice qua QA. Concept/asset giữ phong cách nhất quán, không pha lẫn silhouette/PBR scale/saturation hoặc environment density không có chủ đích. Variant phải có giá trị thiết kế; LOD/hi-lo/recolor không được dùng để đạt số lượng semantic giả.

Các ảnh/sprite legacy trong `ReferenceOnly/` không được di chuyển vào `Assets/` hàng loạt. Build audit loại mọi reference không đủ provenance và mọi draft. Xem [CONTENT_BASELINE.md](CONTENT_BASELINE.md) để nghiệm thu khối lượng thực.

