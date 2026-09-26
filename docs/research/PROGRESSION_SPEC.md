# Racing Bois — đặc tả qualification và progression đã đối chiếu

Ngày 2026-09-26. Phạm vi: bốn đoạn mã được thực thi trong emulator x86 có giới hạn, không phải toàn bộ một cuộc đua. Xem [validation receipt](PROGRESSION_VALIDATION.md) cho run ID và kết quả canonical; [checkpoint](PHASE0_CHECKPOINT.md) ghi các thí nghiệm runtime riêng.

## Nguồn và phương pháp

Executable tham chiếu có SHA-256 **66ab853c5b7b73b82a7c22a0478f5ba5b1066ed27028ef96449f5fe36a6101c5**. Không chỉnh byte executable. Pure model nằm trong tools/legacy_progression.py; oracle độc lập nằm trong tools/progression_oracle.py; runner là tools/validate_progression.py. Oracle không import các hàm expected của model.

Mỗi case tạo memory mô phỏng riêng, khai báo vùng lệnh/vùng ghi, giới hạn 2.000 instruction và timeout. Các call Win32, network, playback, registry và filesystem của game không được chạy. Hash toàn bộ source tham chiếu được đối chiếu trước/sau; version và các file nghiên cứu cũng phải không đổi trong run.

| Claim | Native boundary | Trạng thái được quan sát | Không bao gồm |
|---|---|---|---|
| RB-PROG-001 | 0x416010 → 0x416079 hoặc guard tại 0x4160B6 | Outcome, countdown, exit latch | Phát hiện vượt vạch đích; network notification |
| RB-PROG-002 | 0x416237 → return; CL=DL=0 | Mã màn hình kết quả offline | Cleanup/registry phía trước; kết quả network |
| RB-PROG-003 | 0x449150 → 0x4491EB | Qualification mask, media prefix, số biến thể | Phát video; thưởng tiền; tăng level |
| RB-PROG-004 | 0x41F6D0 → return hoặc trước call tại 0x41F735 | Level, mask, dirty byte, next-screen | Network callback; save/persistence thực tế |

## 1. Chấp nhận yêu cầu kết thúc

Đoạn 0x416010 chỉ nhận yêu cầu mới khi countdown tại 0x4753C4 và exit latch tại 0x4753B4 đều bằng 0. Một trong hai khác 0 thì giữ nguyên trạng thái. Đây là guard cục bộ, không phải giao dịch chống nhận thưởng hai lần của backend mới.

Request status 0x7F phân loại kết quả dựa trên rank byte tại 0x4C5D78. Rank là zero-based và instruction MOVSX đọc nó có dấu. Khi hai cờ tại 0x4C5B00, 0x4C5AF9 đều tắt, rank 0–2 trả outcome 2, rank 3 trở lên trả outcome 3 trong miền rank bình thường. Khi một cờ bật, chỉ rank 0 trả outcome 2. Tham số mode không được đọc để chọn ngưỡng này.

Request khác 0x7F ghi nguyên bit-pattern của outcome được yêu cầu. Delay dương được lưu vào countdown và không bật latch; delay không dương bật latch 1, countdown giữ 0. Đơn vị countdown chưa được xác minh, không gọi nó là milliseconds hoặc ticks.

**Biên không an toàn của bản cũ:** rank byte 128–255 bị đọc thành số âm và qua ngưỡng như kết quả đủ điều kiện. Đây là hành vi byte-level với input lỗi, không phải thứ hạng hợp lệ, không phải bằng chứng exploit online và không được mang sang validation server mới.

## 2. Outcome → màn hình kết quả

Trong tail offline với CL=DL=0: mode 0 trả màn hình 9. Với mode 1–3, outcome 2 → screen 0x1E; outcome 3 → 0x1F; outcome 4 → 0x1D; outcome khác → 0x1C. Đây là diễn giải trong điều kiện giả lập tail, không chứng minh lifecycle caller hoàn chỉnh.

Các mã 0x1C/0x1D/0x1F chọn prefix Wreck/Busted/Lose ở đoạn media tiếp theo; 0x1E vào nhánh qualification. Không suy từ phép ánh xạ này ra toàn bộ điều kiện té, hỏng xe hoặc bị bắt.

## 3. Qualification và media selection

Screen 0x1E, mode khác 3: course ID 1–5 OR lần lượt bit 1, 2, 4, 8, 16 vào mask tại 0x4B8A13. Đạt lại cùng một course không tạo thêm tiến độ. Course ID chưa được gán tên địa danh chỉ dựa trên thứ tự bit.

Mode 3 bỏ qua thao tác OR; vì vậy course 0 được chấp nhận trong thí nghiệm mode 3 mà không mở thêm chặng. Tuy nhiên nhánh chọn media vẫn kiểm tra mask có bằng chính xác 0x1F hay không.

| Điều kiện | Prefix | Giá trị variants |
|---|---|---:|
| Wreck screen 0x1C | Wreck | 6 |
| Busted screen 0x1D | Busted | 6 |
| Lose screen 0x1F | Lose | 10 |
| Qualified screen, mask chưa bằng 0x1F | Win | 6 |
| Qualified screen, mask=0x1F, level index 0–3 | Level | 6 |
| Qualified screen, mask=0x1F, level index 4 | FinalWin | 0 |

Giá trị variants là thanh ghi truyền vào caller media, không được cộng thành số lượng asset độc lập. Mask 0xFF không bằng 0x1F, nên không được coi là hoàn thành. Các bit trên được giữ, không tự sửa dữ liệu lỗi.

**Precondition bắt buộc:** qualified screen ngoài mode 3 cần course ID 1–5. ID khác đọc một byte stack chưa khởi tạo tại 0x4491AE. Model và oracle từ chối miền này; không tự tạo fallback giả rồi ghi PASS.

## 4. Xác nhận kết quả và chuyển level

Callback 0x41F6D0 được tìm thêm từ disassembly và 17 con trỏ callback trong bảng giao diện; nó không có một function export riêng trong catalog Ghidra ban đầu. Do đó số hàm tự nhận diện không phải độ phủ semantics.

Acknowledgement=0 trả screen 0 và không đổi state. Nếu acknowledgement khác 0 và mask chính xác 0x1F, callback đặt dirty byte tại 0x4753AC thành 1 rồi xóa mask. Level index 0–3 tăng một và trả screen 0x20. Level index 4 giữ 4 và trả screen 0x23: không tự tăng thành level thứ sáu.

Check hoàn thành nằm trước dispatch mode. Với mask chưa hoàn thành: mode 0 → screen 9, mode 1 → 10, mode 2 → 14 khi character byte=0, ngược lại 15. Mode 3 chạm boundary 0x41F735; oracle dừng trước call và trả next_screen=null, boundary=network_callback. Không giả vờ đã thực thi callback này.

Lần acknowledgement kế tiếp không tiếp tục tăng level vì mask đã được xóa. Trường dirty byte chỉ là một byte đã quan sát, chưa xác nhận cơ chế ghi save hoặc bảo toàn dữ liệu khi crash.

## 5. Regression và phần chưa đóng

Bộ ca kiểm tra mọi giá trị rank byte; bốn cấu hình cờ mạng 0/1; request/latch/delay biên; mọi mask hợp lệ 0–31, các mask có bit trên; năm course/năm level; character byte và acknowledgement. Ba chuỗi giả lập nối kết quả của từng phía độc lập, có lặp course, thua một race và hoàn thành level. Chúng là synthetic call chains, không phải ba race runtime đã chơi.

Các test về input lỗi, state bất biến và thay đổi version/code giữa run là test harness, không được cộng vào phần trăm logic game. Build mới cần validate rank/course/session từ server, còn signed wrap và uninitialized-read của bản cũ chỉ giữ trong tài liệu đối chiếu.

Vẫn còn mở: finish-line detection, thời điểm/lifecycle gọi callback, cửa sổ điều khiển thật, handling/braking/crash, combat/damage/AI/police, mua bán/sửa xe/phạt, save transaction, native network và semantic asset completeness. Phase 0B chưa hoàn tất.
