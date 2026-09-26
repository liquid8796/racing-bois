# Racing Bois — checkpoint Phase 0 ngày 2026-09-26

Đây là nguồn tổng kết hiện hành, thay cho các số liệu mâu thuẫn trong báo cáo ban đầu. **Phase 0A đạt phạm vi kiểm kê/cấu trúc; Phase 0B chưa đạt toàn bộ gameplay và semantic assets.**

## Bằng chứng đã chạy

`evidence/corpus-0.1.11/summary.json`: 374 file, 503.081.481 byte, 365 hash độc nhất; source không thay đổi, errors rỗng. 13 resource containers chứa 429 entries. 120 ảnh JPEG/BMP; 87 RIFF/WAVE; 11 MIDS; 6 sfbk; 61 AVI đã probe và decode frame đầu. Không có SPK.

7 DAT banks chứa 1439 slots, 869 nonempty; exact EOF và native walker được kiểm thử. 269 FAM outer payload được decode, gồm 106 placeholders và 2515 opaque leaves chưa định danh semantic. 5 course chứa 109 sections/859 chunks; geometry, units và placement runtime còn phải xác minh. 15 SPEC profiles; 14 RRS save hợp lệ; 4 file zero-filled không phải save.

**Rút lại các số liệu sai cũ:** 295.029.847 byte, 121 ảnh, 11 WAVE, 899/893 sprite và 112 SPK. Không dùng số file, frame, leaf, LOD hoặc dữ liệu trùng để tăng số lượng assets.

885/885 bounded native comparisons khớp cho SPEC initializer, DAT walker và save checksum. `evidence/gameplay-0.1.11/summary.json` bổ sung 832/832 cases: 256 byte bike IDs và 576 result-prefix cases. Tổng 1717 không phải số trận hoặc tỷ lệ whole-game coverage. 52 unit/regression tests đã PASS trước checkpoint; kiểm tra chốt phiên được ghi riêng.

## Logic đã xác minh một phần

Bike index 0..14 ánh xạ name IDs: 112,113,114,116,115,122,125,123,126,124,117,120,118,121,119. SPEC ID = index + 1 theo loader. **Thứ tự profile không bằng showroom order.** Byte index 15..255 trả name ID112 theo fallback, không chứng minh profile hợp lệ.

Result prefix tại 0x421290..0x421384 chỉ cộng cash ở mode2: base prize nhân level index + 1, với wrap u32 kiểu cũ. Prizes place0..13: 1000,750,500,400,300,250,200,160,130,100,70,50,30,20. Preconditions là routine đã được gọi; chưa xác minh finish/DNF/qualification/reentry/persistence. Economy mới không sao chép lỗi overflow, cần range validation và transaction/idempotency.

Pure models tách khỏi native oracle. Executable SHA-256 được pin: 66ab853c5b7b73b82a7c22a0478f5ba5b1066ed27028ef96449f5fe36a6101c5. Oracle giới hạn code/time/instructions/write ranges, không chạy Win32 imports. 1585 hàm Ghidra xuất chỉ là navigation, không phải tất cả semantics đã hiểu.

## Runtime và video

Probe v0.1.13 dừng ở menu display setup với raw return0x80004000. Không mặc định initializer return là HRESULT của COM call bên trong.

Probe `ReferenceOnly/runtime-probes/20260926T062849Z/report.json` v0.1.16 dùng compatibility wrapper hash-pinned trong bản sao private, ghi visible_window_observed=true, gameplay_observed=false, source không sửa, harness/script/cleanup errors rỗng. Chưa xác nhận một trận chạy được hoặc native timing. Đây là instrumentation, không phải OS sandbox; không chạy BAT/REG, không thay gameplay constants.

Video đã lấy 39 sparse stills và xem 4 contact sheets. Đây không phải full watch hoặc exhaustive event log. Các mẫu có đường đồi/cua, dashboard/mirrors, city/forest/coast/tunnel, on-foot pose và rider sát nhau; một still không chứng minh hit/damage hoặc recovery timing. Research screenshots không thay generated concept được duyệt.

## Điều kiện còn phải hoàn thành

Controlled handling/brake/off-road/crash; combat frames/range/damage; AI/traffic/police; finish/qualification/shop/repair/progression; semantic FAM/CAR/CEL/ANIM/course, palette/transparency. Mỗi claim cần source hash, run ID, input/setup, địa chỉ/timestamp, output, giới hạn và test. Chưa đánh dấu Phase0B hoàn tất.

Source readable, dễ refactor, maintainable, testable và extensible là yêu cầu bắt buộc tại [Architecture rules](../ARCHITECTURE_RULES.md). Pattern giải quyết vấn đề thật, không pattern vì hình thức. Generated concept2D phải được assistant trực tiếp duyệt trước mọi production3D/UI.
