# Racing Bois — báo cáo reverse-engineering

> **Bản nghiên cứu ban đầu có số liệu đã bị rút lại.** Dùng [PHASE0_CHECKPOINT.md](PHASE0_CHECKPOINT.md) làm tổng kết hiện hành: 374file/503.081.481byte; không có SPK. Các giả thuyết và số cũ dưới đây không được dùng làm baseline nghiệm thu.

Ngày: 2026-09-26. Loại công việc: static audit, structural extraction, decoder prototypes và lấy mẫu video. **Đây chưa phải xác nhận hoàn tất reverse-engineering toàn bộ game.**

## 1. Nguồn chuẩn của lượt nghiên cứu

Workspace: `D:\Project\Unity\racing-bois-desktop`.

Nguồn nhị phân: `C:\Users\Liquid\Downloads\Unity\racing_bois_mod`.

Nguồn gameplay: `C:\Users\Liquid\Downloads\prompt\Road Rash PC (1995) - Big Game Mode (All Levels).mp4`.

Snapshot đối chiếu cuối: `evidence/FINAL_AUDIT_SNAPSHOT.json`, ghi nhận thời điểm `2026-09-26T10:59:42.6748392+07:00`. Hash của các file nguồn khớp inventory; danh sách file thêm, xóa và thay đổi đều rỗng tại lần đối chiếu này. Việc đối chiếu không chứng minh một bản mod giống mọi bản phát hành gốc; nó chỉ cố định chính corpus được cung cấp.

Tên video ghi 1995 trong khi yêu cầu gọi Road Rash 1996. Không suy ra edition hoặc version executable từ hai nhãn này. Phase 0B phải khóa reference edition và ghi rõ khác biệt do mod.

## 2. Kết quả kiểm kê đã ghi nhận

| Hạng mục | Snapshot hiện dùng | Ý nghĩa đúng |
|---|---:|---|
| File nguồn | 374 | File distribution, không phải 374 asset độc lập |
| Tổng dung lượng | 295.029.847 byte | Không dùng làm chỉ tiêu chất lượng/độ đầy đủ game mới |
| Hash file độc nhất | 373 | Có ít nhất một nhóm trùng byte |
| Container resource | 13 | Đã đọc bảng descriptor |
| Entry resource | 429 | Đã kiểm tra bounds và trích xuất khớp byte |
| Ảnh đọc được | 121 | 116 `.RRI` và 5 `.BMP`; chưa phải asset 3D |
| Audio RIFF/WAVE đọc được | 11 | 8 `.RRA` và 3 `.WAV`; không bao gồm toàn bộ `.SPK` |
| Mẫu save | 9 | Có dump dữ liệu; chưa hoàn thiện schema/checksum |
| PE executable/DLL | 15 | Phân tích header, imports, resource và chuỗi |
| File `.SPK` | 112 | Khoảng 268,3 MB; vẫn là khoảng trống decode đáng kể |

Ví dụ trùng byte trong inventory: `DATA/CARS/CANYN.CAR` và `DATA/CARS/HIWAY.CAR`. Không tính hai bản này thành hai bộ asset độc lập chỉ vì tên file khác nhau.

Nguồn số liệu: `evidence/inventory.json`, `evidence/inventory.csv`, `evidence/summary.json`, snapshot cuối. Các tổng số trong log thăm dò trước đó không thay thế snapshot cuối.

## 3. Những gì thực sự đã giải được

### 3.1 Cấu trúc chương trình

Executable được phân tích là chương trình native Windows x86, không phải project Unity/C# có thể mở trực tiếp bằng Unity Editor. Đã thu thập PE sections, imports, resource strings và địa chỉ tham chiếu chuỗi trong code. Có disassembly tuyến tính để điều hướng nghiên cứu.

**Giới hạn:** disassembly tuyến tính không tự xác lập ranh giới hàm, đường chạy thực tế, kiểu dữ liệu, tên biến gốc hoặc ý nghĩa đầy đủ của các thuật toán. Số instruction không phải số logic đã phục hồi. Chưa có bằng chứng mọi nhánh executable đã chạy hoặc mọi trạng thái gameplay đã được giải thích.

Bằng chứng: `evidence/pe_analysis.json`, `evidence/code_string_xrefs.json`, `evidence/code_import_xrefs.json`, `evidence/RacingBois.text.asm`, `evidence/localization/`.

### 3.2 Resource containers: byte-exact extraction

Đã xác định lớp container có magic `CRSR` trên đĩa, tương ứng tag RSRC theo thứ tự little-endian. Pointer bảng tại offset 16; bảng có magic `LBTR`. Descriptor dài 32 byte, các trường đầu gồm type, ID, payload offset và payload size.

Điểm quan trọng: **offset trong descriptor trỏ trực tiếp vào payload, không phải một generic header type/size dài 8 byte.** Parser thử nghiệm ban đầu có giả thuyết prefix không đúng; đã chỉnh lại và kiểm tra round-trip sau trích xuất.

429 entry được kiểm tra nằm trong file và bản xuất bằng đúng byte nguồn. Điều này chứng minh lớp đóng gói, **không chứng minh 429 entry đã trở thành 429 hình/model/animation hoàn chỉnh**. Một entry có thể chứa nhiều tài nguyên con hoặc bảng dữ liệu.

Bằng chứng: `evidence/resource_tables.json`; bản trích xuất ở `ReferenceOnly/decoded/resources/`; công cụ `tools/audit_reference.py`.

### 3.3 Ảnh và audio chuẩn được đổi đuôi

Các `.RRI` đã đọc là JPEG đổi đuôi; đã giải mã bằng thư viện ảnh và ghi PNG để nghiên cứu. Các `.RRA` đã nhận dạng là RIFF/WAVE và có bản WAV nghiên cứu. File có thể mở được chưa đảm bảo quyền phát hành, tính duy nhất, chất lượng texture hay khả năng dùng làm material PBR.

Khối `.SPK` lớn chưa được chứng minh có thể giải mã đầy đủ. Không báo cáo đã lấy toàn bộ nhạc/SFX chỉ vì `.RRA` đọc được.

Bằng chứng: `evidence/image_catalog.json`, `evidence/audio_catalog.json`, `ReferenceOnly/decoded/images/`, `ReferenceOnly/decoded/audio/`.

### 3.4 Sprite DAT: cấu trúc đọc đã có đối chiếu code

Parser đọc lặp `uint8 width`, `uint8 height`, rồi `width*height` byte chỉ số palette; giữ nguyên cả slot rỗng. Đoạn code tại VA `0x443758..0x443785` là điểm neo đối chiếu việc đọc kích thước và bước qua record.

Decoder snapshot ghi 7 bank, 899 record, 893 record có pixel; đọc đúng EOF cả 7 bank. Các cặp HIBOB/LOBOB, HISHADOW/LOSHADOW, HISHADOC/LOSHADOC có số record tương ứng và quan hệ kích thước 2× theo kiểm tra cấu trúc.

**Chưa qua visual acceptance:** byte pixel được bảo toàn trong PNG không chứng minh layout, stride, palette, transparency hoặc hướng render đúng. Preview HIBOB có biểu hiện chưa đúng khi dùng giả thuyết row-major. Đã tạo probe layout; chưa có kết luận được phép coi toàn bộ sprite là ảnh phục hồi chuẩn. Cần đối chiếu renderer và frame game chạy. Các bank hi/lo không được cộng thành các nhân vật/animation độc lập.

Bằng chứng: `evidence/sprite_catalog.json`, `evidence/asset_decode_summary.json`, `evidence/sprite_layout_probe.jpg`, `ReferenceOnly/decoded/sprites/`.

### 3.5 FAM: decoder pilot, chưa đóng coverage

Đã viết decoder thử nghiệm cho payload DCL binary-mode có giới hạn output và kiểm tra test vector tham chiếu; các entry pilot có kiểm tra kích thước đầu ra. Snapshot decoder báo 7 entry thử nghiệm thành công.

**Blocker cần xử lý:** inventory resource ghi 269 entry FAM nhưng manifest decoder pilot chỉ có 7 entry. Chưa có ánh xạ chứng minh 7 này đại diện/bao phủ 269 entry. Không được ghi 100% FAM decoded. Phải hòa giải ID, file nguồn, nested payload và phiên bản manifest trước khi mở rộng kết luận. Kể cả giải nén thành công, schema bên trong và ý nghĩa model/texture vẫn là bước riêng.

Bằng chứng: `evidence/family_decode.json`, `evidence/resource_tables.json`; công cụ `tools/decode_reference_assets.py`. Phần decoder dựa trên tài liệu/test vector blast của Mark Adler; bản Python đã ghi là bản thay đổi tại `THIRD_PARTY_NOTICES.md`.

### 3.6 Thông số xe và đường đua

Bảng `BIKESPEC.RSC` chứa 15 profile SPEC. Đã xuất các trường raw và xác định code đọc/biến đổi một số giá trị. Điểm neo nghiên cứu quanh VA `0x405e0c..0x405f60` có chuyển đổi số nguyên; các phép chia/shift phải được hiểu cùng kiểu signedness, rounding và call path, không tùy tiện đổi một dword thành m/s hay Newton.

Năm tên bộ course trong corpus: `CANYN`, `CITY`, `HIWAY`, `MEDLY`, `NAPA`. Đây là baseline tên file, chưa là xác nhận năm tuyến đã dựng lại đúng topology, chiều dài, độ cong, elevation, vật cản và spawn.

Giả thuyết record bảng SGS 52 byte chưa qua toàn bộ kiểm tra bounds; đánh dấu **UNVERIFIED**, không dùng trực tiếp làm road mesh. NOD, CAR, ANIM, CEL, GLOB, BKR và các dữ liệu phụ cần schema/call-site mapping tiếp.

Bằng chứng: `evidence/resource_tables.json`, `evidence/course_section_tables.json`, `evidence/code_string_xrefs.json`, disassembly.

### 3.7 Gameplay video

Metadata snapshot: 9.278,8 giây, tương đương 2 giờ 34 phút 38,8 giây. SHA-256 video: `e8c56045a66f097736aa2b33a5d6d329c40fb1194c74ad5be3d17e0304b667837b62`.

Đã trích 39 frame ở timestamp cố định, các file đều tồn tại trong lần kiểm tra. Đây là **lấy mẫu thưa**, không phải xem hết video hoặc đo frame-by-frame các pha tăng tốc, ra đòn, crash, police, chiến thắng và economy. Contact sheet không tự trở thành concept art được duyệt.

Cần lập event log theo từng cuộc đua và đoạn hành động: thời điểm vào/ra state, tốc độ HUD, camera, mục tiêu, input biết được/không biết được và độ tin cậy. Video không có input telemetry nên không đủ để một mình xác định công thức handling.

Bằng chứng: `evidence/video/video_samples.json`, ảnh `evidence/video/`, công cụ `tools/sample_reference_video.py`.

## 4. Những gì chưa làm hoặc chưa chứng minh

Chưa chạy executable cũ trong lượt này; chưa có trace runtime có kiểm soát. Không chạy batch launcher có thao tác tắt Explorer/chỉnh registry. Chưa phục hồi đầy đủ state machine và công thức physics/combat/AI/police/economy/progression/save. Chưa kiểm định đầy đủ palette/layout sprite, asset con trong FAM hoặc `.SPK`.

Chưa có canonical unmodified distribution để chứng minh corpus mod chứa đủ mọi asset của game gốc. Chưa xây Unity client/server mới, chưa deploy backend, chưa đo FPS/tick/memory hoặc kết nối ngoài Internet. Các kiểm tra Unity/Blender ở thời điểm thăm dò chưa xác nhận một cặp instance sẵn sàng làm việc đúng workspace; phải handshake lại trước phase sản xuất.

Không có cơ sở đưa ra một tỷ lệ phần trăm tổng thể về “logic đã hiểu”. Dùng [coverage matrix](COVERAGE_MATRIX.md) theo từng hệ thống thay cho một con số gây hiểu lầm.

## 5. Phase 0B: thí nghiệm cần có để khóa đặc tả

Mỗi experiment có input/setup, save ban đầu, executable hash, video/timestamp, raw trace, phép đo, lặp lại, kết luận và độ tin cậy. Viết vào vùng nghiên cứu riêng; không sửa corpus nguồn. Chạy bản sao làm việc/sandbox với cách khởi động đã kiểm tra, không dùng nguyên batch có tác dụng phụ.

| Nhóm | Trường hợp cần khảo sát | Đặc tả cần thu được |
|---|---|---|
| Lái xe | Xuất phát, tăng tốc, nhả ga, phanh, cua ở nhiều tốc độ, lề đường | Đường cong gia tốc/phanh, steering response, grip, camera và giới hạn trạng thái |
| Va chạm | Xe cùng chiều/ngược chiều, vật cản, địa hình, tốc độ tương đối | Impulse/giảm tốc, điều kiện té, damage, ưu tiên và thời gian hồi phục |
| Chiến đấu | Trái/phải, punch/kick/weapon/block, nhiều khoảng cách và tốc độ | Windup/active/recovery, hit volume, damage, cooldown, stagger, chống double hit |
| Crash/recovery | Té, trượt, chạy về xe, xe nằm xa, bị tông tiếp | State transitions, timer, input lock, vị trí respawn và hình phạt |
| AI/traffic/police | Bám đuổi, tránh xe, trả đòn, vượt, truy đuổi/bắt | State machine, perception, tham số theo difficulty và điều kiện chuyển state |
| Cuộc đua | Start/countdown, checkpoint, finish, cùng lúc, DNF, pause | Quy tắc hợp lệ, xếp hạng, progression, cách chống shortcut |
| Tiền/xe/save | Mua/bán/sửa chữa, phần thưởng/phạt, nợ nếu có, hết tiền, reload | Schema và công thức được đối chiếu; không suy ra toàn bộ từ help text |
| Content | Toàn bộ course/variant, rider, xe, weapon, animation, audio | ID semantic, duplicate mapping và baseline thực sự cần làm lại |

Không thể khẳng định “giống y chang” chỉ từ screenshot đẹp. Phải tạo golden scenarios và đo hành vi trên cùng tình huống. Sai số chấp nhận được được chốt sau khi biết nhiễu của phép đo, trước khi tuning implementation.

## 6. Tái lập và quản lý bằng chứng

Chạy từ workspace với Python và các dependency đã kiểm tra. Đây là công cụ nghiên cứu có các giả thuyết còn mở; không xem mọi output là sự thật semantic.

```powershell
python tools/audit_reference.py
python tools/sample_reference_video.py
python tools/decode_reference_assets.py
```

Trước khi chạy lại, lưu manifest cũ với run ID riêng. Sau chạy, đối chiếu hash nguồn và gắn tất cả output vào cùng run ID; không trộn count từ các phiên khác nhau. Khi parser thay đổi schema, chạy lại toàn corpus và không ghi đè các bằng chứng phủ định mà không có ghi chú.

Phân biệt bốn mức: **VERIFIED-STRUCTURE**, **VERIFIED-BEHAVIOR**, **HYPOTHESIS**, **UNVERIFIED**. Không nâng từ structure lên behavior vì file xuất mở được.

