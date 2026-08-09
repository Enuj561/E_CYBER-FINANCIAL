# Walkthrough và To-do — 2026-08-09

## 16. Walkthrough ngày làm việc 2026-08-09

### Kết quả chung

Trong ngày đã đi từ kiểm kê kho cũ đến chạy thật dây chuyền mới trên 13 mã. Luồng BCTC hiện có hai nguồn tách riêng, raw không ghi đè, sổ tiến độ có resume, kiểm tra data không giấu lỗi và có lệnh pilot thật. Bước 0–12 đã hoàn thành theo baseline chạy tuần tự. Bước 13–16 chưa triển khai.

### Tổng hợp Bước 0–3: hiểu nguồn và chốt phạm vi

1. **Bước 0 — Kiểm kê:** Chốt 1.529 mã nền; giữ snapshot CSV/Parquet và mã kiểm tra SHA-256; không xóa data/checkpoint cũ. Có 9 mã trong OHLCV không còn ở listing hiện tại nhưng chưa đủ bằng chứng gọi là hủy niêm yết; có 5 mã listing mới chưa có trong kho OHLCV cũ.
2. **Bước 1 — FireAnt:** Xác nhận FireAnt có cổng BCTC nhưng token cũ trả `401`. Lỗi được giữ đúng là lỗi xác thực, không gọi nhầm thành nguồn không có data.
3. **Bước 1.1 — Token mới:** Token ban đầu bị dán thừa chữ `Bearer`; đã sửa định dạng mà không ghi lộ token. FireAnt trả thành công BCTC quý cho VNM/VCB.
4. **Bước 2 — Nguồn con vnstock:** So VCI và KBS. VCI phủ tốt hơn rõ rệt và được chọn làm nguồn chính; KBS chỉ để kiểm tra phụ, không tự động bù vào chỗ VCI thiếu.
5. **Bước 3 — Mẫu đại diện:** Thử 13 mã thuộc doanh nghiệp thường, ngân hàng, chứng khoán, bảo hiểm, mã hạn chế và mã lệch giữa hai kho OHLCV. FireAnt phủ lịch sử sâu hơn ở nhiều mã nhỏ. FireAnt và VCI có dấu hiệu dùng chung data nền nên không được gọi là hai xác nhận độc lập.

### Tổng hợp Bước 4–6: chốt mẫu data và cách lưu

1. **Bước 4 — Data Contract:** Chốt ba lớp Raw → Normalized → Curated, tách `From_FireAnt` và `From_vnstock`. Một record là một mục tài chính của một nguồn, mã và kỳ. Không tự điền hợp nhất/riêng lẻ, ngày công bố hoặc `final_value`.
2. **Bước 5 — Hai Client:** Tạo Client FireAnt và VCI độc lập. Chỉ retry lỗi mạng, timeout, rate limit hoặc máy chủ tạm lỗi; token/config/schema lạ không retry lấp liếm.
3. **Bước 6 — Repository và sổ tiến độ:** Raw FireAnt lưu JSON; VCI lưu Parquet; mọi lần ghi dùng file tạm rồi mới thay file chính. Data rỗng hợp lệ chỉ ghi trạng thái, không tạo raw rỗng. Resume không cào lại item đã có trạng thái cuối hợp lệ.

### Tổng hợp Bước 7–9: chuẩn hóa, kiểm tra và đối chiếu

1. **Bước 7 — Normalizer:** Chuyển hai nguồn về `bctc_v1.1.0` mà không sửa raw. Dòng/cột trùng được giữ và có số thứ tự. Mục chưa đủ bằng chứng giữ `unknown`, không đoán.
2. **Bước 8 — Validator:** Chặn sai schema, sai mã/nguồn, kỳ tương lai, dòng/khóa trùng, lỗi đổi số, sai đơn vị và trạng thái rỗng giả. Phân biệt rõ lỗi, cảnh báo và kiểm tra bị bỏ qua.
3. **Bước 9 — Cross-check:** Chỉ ghép `canonical_item_id` có mapping `confirmed`, cùng mã/kỳ/loại/dạng giá trị/hợp nhất. Giữ riêng hai số và độ lệch; data thiếu không thành 0; không chọn nguồn thắng.

### Tổng hợp Bước 10–11: ráp dây chuyền và test

1. **Bước 10 — Manager:** Ráp Client → Raw Repository → Normalizer → Validator → Cross-check → Progress Repository. Mọi thành phần được đưa vào qua tham số để test bằng data giả. Một nguồn lỗi tạm thời không xóa kết quả nguồn kia; lỗi nghiêm trọng dừng đợt.
2. **Bước 11 — Test tự động:** Bộ test phủ doanh nghiệp thường/ngân hàng/chứng khoán/bảo hiểm, hai nguồn, data trùng/thiếu/rỗng, lỗi mạng/rate limit/token, resume, ghi file bị ngắt, đổi đơn vị và cross-check. Sau các lỗi thật phát hiện ở Bước 12, tổng hiện tại là 69 test Phase 1 đạt.

### Tổng hợp Bước 12: pilot thật 13 mã

- Chạy tuần tự 13 mã, mỗi lúc chỉ có một request API.
- 130 phần: FireAnt 26, VCI 104.
- Kết quả cuối: 22 `complete`, 99 `partial`, 9 `no_data_confirmed`, không còn lỗi trong các run đạt.
- 130/130 lần gọi thành công ngay lần đầu, không retry.
- 121 raw đọc lại được, khoảng 15,24 MB; không có raw rỗng giả và không còn `.tmp`.
- Thời gian baseline tuần tự: khoảng 1.186 giây, tức 19 phút 46 giây.
- Hộp đen đã ghi log theo Manager, Client, Repository và Progress; chưa đo RAM/CPU theo thời gian.
- Pilot phát hiện bốn đặc điểm thật của VCI và đã thêm rule + test: cột trộn số/chữ, ratio trộn cột năm/quý, dòng metadata trong ratio và cột năm trùng tên khi ghi Parquet.
- Ratio của năm hiện tại có thể là YTD; giữ với cảnh báo, không gọi là số cả năm đã chốt.
- Có 452.491 dòng cross-check nhưng đều `not_comparable` vì mapping confirmed chưa đủ. Đây là giới hạn đang biết, không phải hai nguồn đã khớp hoặc đã lệch.
- Các run thử bị lỗi được giữ làm bằng chứng; run đạt không ghi đè chúng.

---

## 17. To-do ngày làm việc tiếp theo

### Việc A — Thiết kế lại luồng chạy song song hai nguồn

#### A1. Các đầu mục data hiện có

Mỗi mã hiện có **10 work item**:

| Nhánh | Đầu mục | Số việc/mã |
|---|---|---:|
| FireAnt | Gói `financial_data` theo quý | 1 |
| FireAnt | Gói `financial_data` theo năm | 1 |
| VCI | Cân đối kế toán quý + năm | 2 |
| VCI | Kết quả kinh doanh quý + năm | 2 |
| VCI | Lưu chuyển tiền tệ quý + năm | 2 |
| VCI | Ratio quý + năm | 2 |
| **Tổng** |  | **10** |

FireAnt trả một gói trộn nhiều nhóm chỉ tiêu trong `financialValues`. VCI trả riêng bốn nhóm báo cáo và mỗi nhóm có nhánh quý/năm.

#### A2. Kiến trúc async cần cùng chủ dự án chốt

Baseline đề xuất để thảo luận, chưa phải quyết định cuối:

```text
Một mã
├─ Worker nguồn FireAnt: quý → năm
└─ Worker nguồn VCI: 8 work item chạy tuần tự

Đợi hai worker kết thúc
→ chuẩn hóa
→ kiểm tra
→ đối chiếu
→ tổng kết/checkpoint
→ sang mã tiếp theo
```

Các quyết định cần chốt trước khi code:

1. Dùng hai worker/thread cho hai thư viện đồng bộ hiện tại, hay chuyển Client sang `asyncio` thật sự.
2. Trong FireAnt có cho quý và năm chạy đồng thời không, hay giữ tuần tự.
3. Trong VCI có cho chạy đồng thời các nhóm báo cáo không; nếu có thì giới hạn 2 hay mức khác.
4. Giai đoạn đầu có giữ một mã tại một thời điểm không. Khuyến nghị: **có**, để tổng concurrency chỉ là hai nguồn.
5. Rate limit riêng từng nguồn, timeout, retry và thời gian chờ phải tách riêng; lỗi một nguồn không hủy kết quả nguồn kia.
6. Repository và Progress Repository phải an toàn khi hai worker cùng cập nhật; không cho hai worker ghi cùng item/path.
7. Thứ tự kết quả phải ổn định dù thứ tự hoàn thành khác nhau; không phụ thuộc worker nào về trước.
8. Khi người dùng dừng: ngừng nhận việc mới, chờ/huỷ gọn request đang chạy, ghi checkpoint đủ để resume.
9. Thêm backpressure để không giữ quá nhiều DataFrame trong RAM; chỉ giữ data cần cho một mã.
10. `E_BlackBox` phải ghi thời điểm bắt đầu/kết thúc từng worker, số request đang chạy, thời gian chờ, retry, RAM, CPU và dung lượng ghi.

#### A3. Điều kiện test cho async

- Test chứng minh FireAnt và VCI thật sự chồng thời gian, không chỉ đổi tên hàm thành async.
- Hai nguồn hoàn thành ngược thứ tự vẫn cho cùng kết quả.
- Một nguồn timeout/lỗi không xóa raw hoặc trạng thái nguồn kia.
- Dừng giữa lúc hai nguồn chạy rồi resume không cào lại phần đã xong.
- Không có race condition khi ghi raw/checkpoint/log.
- Peak RAM có số đo; không chỉ nhận xét bằng cảm giác.
- Test mặc định vẫn offline; live test chạy bằng lệnh riêng.

### Việc B — Chạy lại Bước 12 bằng luồng async

Sau khi thiết kế và test async đạt:

1. Chạy lại đúng 13 mã của baseline tuần tự.
2. Giữ cùng yêu cầu 64 quý/20 năm, cùng nguồn và cùng phiên bản nếu có thể.
3. Dùng `run_id` mới; không ghi đè baseline ngày 2026-08-09.
4. So trực tiếp:
   - tổng thời gian;
   - thời gian từng nguồn;
   - peak RAM/CPU;
   - số retry/rate limit;
   - số `complete/partial/no_data/error`;
   - checksum hoặc nội dung raw;
   - kết quả Validator/Cross-check.
5. Async chỉ được chấp nhận nếu nhanh hơn mà không làm đổi/mất data, không tăng lỗi bất thường và resume vẫn đúng.

### Việc C — Hoàn thiện mapping trước khi tăng quy mô

452.491 dòng pilot hiện chưa so được vì mapping chưa đủ `confirmed`. Trước hoặc song song với Bước 13 cần:

- chốt mapping tối thiểu cho các chỉ tiêu quan trọng ở bốn nhóm doanh nghiệp;
- ghi bằng chứng, phiên bản mapping và quy tắc dấu;
- chạy lại cross-check từ raw đã lưu, không gọi API lại;
- không ghép theo tên gần giống và không gọi FireAnt/VCI là hai xác nhận độc lập.

### Việc D — Các bước còn lại trong kế hoạch

1. **Bước 13:** Chạy thử 100 mã sau khi async và mapping tối thiểu đạt; thử dừng/resume, lỗi tạm thời và so lại từ file đã lưu.
2. **Bước 14:** Cào toàn bộ 1.529 mã theo batch khoảng 100 mã; dừng nếu lỗi/rate limit/schema tăng bất thường.
3. **Bước 15:** Kiểm tra toàn bộ sau khi cào: độ phủ, file hỏng, kỳ tương lai, trạng thái giả, phần chỉ một nguồn có và phần hai nguồn lệch.
4. **Bước 16:** Thiết kế cập nhật BCTC về sau theo quý/năm, chỉ gọi phần mới/thiếu và so lại khi nguồn đổi số.

### Việc E — Chưa làm trong đợt đầu

- Chưa nối nút IDE hoặc lịch tự động.
- Chưa đưa BCTC vào ML/backtest khi ngày công bố còn thiếu.
- Chưa cào thuyết minh BCTC.
- Chưa xóa collector/checkpoint/data cũ.
- Chưa chọn nguồn thắng hoặc tạo `final_value`.
