# Racing Bois — baseline nội dung và khối lượng asset

**Ngu?n hi?n h?nh:** [Phase0 checkpoint](research/PHASE0_CHECKPOINT.md). Phase0B c?n m?; kh?ng c? SPK. S? li?u v? gi?i h?n ph?i theo checkpoint, kh?ng theo b?n t?ng k?t c?.

Ngày: 2026-09-26. Baseline hiện tại là **distribution mod được cung cấp**, chưa phải chứng nhận đầy đủ cho mọi asset của bản game gốc chưa mod.

## 1. Không đo content bằng dung lượng hoặc số file

374 file và khoảng 295 MB là số liệu lưu trữ. 1439 slot sprite không tương đương 899 nhân vật/model; hi/lo, LOD, texture resolution, bản sao byte-identical và góc render không được tính thành nội dung gameplay độc lập.

Mỗi category có ba đơn vị riêng: **semantic asset** (một xe/nhân vật/loại prop/clip), **variant có ý nghĩa** (khác silhouette/hành vi/chất liệu cần riêng), và **representation** (LOD, mip, low-res/high-res, frame, platform compression). Chỉ hai nhóm đầu được dùng theo quy tắc đã định trước để so độ phong phú nội dung.

## 2. Baseline tạm thời có căn cứ

| Category | Đã quan sát trong corpus | Mục tiêu làm mới / việc cần khóa |
|---|---|---|
| Xe có thông số | 15 profile SPEC | Ít nhất 15 profile gameplay được xác minh; số model/silhouette độc lập phải đối chiếu semantic catalog, không chỉ reskin |
| Bộ tuyến đường | 5 bộ tên CANYN/CITY/HIWAY/MEDLY/NAPA | Tối thiểu phủ 5 route families sau khi map đúng; tất cả variant/event thực có trong reference phải được thống kê |
| Still images / menu / portrait | 121 ảnh đọc được | Map từng vai trò màn hình/portrait/backdrop; không nhất thiết sao một JPEG thành một texture production |
| Rider và animation | 7 bank DAT, 1439 slots / 869 nonempty | Catalog rider/pose/action/loop/transition; hi/lo không cộng hai lần |
| Environment / traffic / scenery | Resource containers và nhiều payload con | Chưa có số unique đáng tin; cần semantic mapping FAM/CAR/CEL/ANIM/SGS/NOD |
| Audio | 11 RIFF/WAVE đã đọc; 112 SPK còn cần nghiên cứu | Chưa chốt tổng clip/track/loop độc lập; không lấy 11 làm baseline đầy đủ |
| UI/HUD/icon | RRI/BMP/HUD/BOB và executable resources | Danh sách screen/state và thông tin bắt buộc; tất cả UI mới qua concept gate |
| Character/dialogue/police | Chuỗi bản địa hóa và dữ liệu tham chiếu | Map roster, lines, reactions, police/traffic personalities và gameplay role |

Các con số này là sàn nghiên cứu tạm thời, không tự động là backlog cuối cùng. Không công bố “đủ asset như bản gốc” khi FAM/animation/roster hoặc canonical coverage vẫn chưa khóa.

## 3. Semantic catalog cần lập ở Phase 0B

Mỗi dòng có: `semantic_id`, category, reference file/entry/timestamp, tên vai trò, variant group, duplicate group, usage frequency, gameplay importance, remake deliverable, concept ID, production prefab/audio/UI ID, provenance và QA state.

Giữ bảng mapping nhiều-nhiều: nhiều frame có thể thành một animation; một texture atlas có thể phục vụ nhiều prop; một landmark có nhiều LOD nhưng chỉ một semantic asset. Đếm thêm số tình huống gameplay và màn hình hoàn chỉnh để tránh cách đạt số lượng bằng asset ít giá trị.

Đối chiếu theo từng category, không bù thiếu nhân vật/đường đua bằng thêm hàng nghìn viên đá. Cần review silhouette, vật liệu, animation và khoảng cách camera để xác định variant có thật sự mang ý nghĩa.

## 4. Định hướng danh mục sản xuất

Route kit gồm road surface/shoulder/markings, terrain, vegetation, landmarks, barriers, signs, buildings và roadside set dressing; mỗi route có đặc điểm nhận diện và nhịp địa hình riêng, không chỉ đổi màu skybox.

Vehicle kit gồm bike silhouette, wheel/brake/suspension detail theo screen coverage, rider contact points, damage/impact presentation và server collider proxy. Traffic cần vai trò, kích thước và chuyển động đọc được ở tốc độ cao.

Character kit gồm rider/police, rig, locomotion/lean, attacks, reactions, crashes, recovery và transitions. Animation phải diễn đạt anticipation/contact/recovery, không phụ thuộc ragdoll để che thiếu clip.

Audio kit gồm engine RPM/load, tire/road surface, wind, pass-by, contact, weapon hits, UI, ambience và music phù hợp. SFX/nhạc chỉ vào release khi provenance rõ ràng và mix được QA.

UI kit gồm boot/menu/profile, bike selection/shop/garage, HUD, race results, progression, lobby/join/reconnect, settings/accessibility, error/network states. Một main menu đẹp không thay cho toàn bộ flow hoàn chỉnh.

## 5. Gate phát hành về content

Mỗi category phải có baseline finalized, đủ semantic coverage, không mất chức năng thiết yếu, không có placeholder còn sót và không có production asset thiếu concept approval/provenance/QA. Content tổng phải ít nhất bằng baseline semantic đã xác minh; độ dài/đa dạng route và gameplay event phải được đối chiếu riêng.

Tài nguyên legacy trích xuất chỉ nằm trong `ReferenceOnly/`. Production dùng tài sản original, licensed hoặc được cấp quyền rõ ràng; đây là yêu cầu quản trị provenance, không phải tuyên bố đã có quyền sử dụng distribution mod. Khi thiếu quyền, tái tạo mới vẫn phải giữ coverage gameplay/content theo baseline mà không đưa file tham chiếu vào build.

Nguồn số liệu: `research/evidence/corpus-0.1.11/summary.json`. Liên quan: [coverage](research/COVERAGE_MATRIX.md), [pipeline](ASSET_PIPELINE.md), [phase plan](PHASE_PLAN.md).

