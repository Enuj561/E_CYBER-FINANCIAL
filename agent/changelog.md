# Changelog: Ngày 19/07/2026

## 1. Chuẩn hóa Naming Convention (Quy tắc đặt tên)
- Đổi tên hàng loạt các file script và helper theo đúng chuẩn prefix `E_` để đồng bộ toàn dự án.
- Ví dụ: 
  - `Helper/config.py` ➔ `E_Helper/E_config.py`
  - `data_collector.py` ➔ `E_data_collector.py`
  - Và các file UI/News khác.

## 2. Cấu trúc lại dữ liệu Phase 1 (Data Restructure)
- **Gom nhóm OHLCV:** Di chuyển 2 thư mục `From_vnstock` (giá cổ phiếu) và `From_FireAnt` (khối lượng, khối ngoại) vào thư mục chung `E_OHLCV/`.
- **Thêm cấu trúc BCTC:** Tạo thư mục mới `E_BCTC/` nhằm chuẩn bị hạ tầng lưu trữ Báo cáo Tài chính với 5 sub-folders:
  - `Balance_Sheet/` (Bảng cân đối kế toán)
  - `Income_Statement/` (Kết quả kinh doanh)
  - `Cash_Flow/` (Lưu chuyển tiền tệ)
  - `Ratio/` (Chỉ số tài chính)
  - `Note/` (Thuyết minh BCTC)

## 3. Cập nhật Constants và Configuration
- Cập nhật file `E_config.py` để trỏ đến đúng các thư mục mới tạo.
- Cấu hình `ensure_dirs()` đã được bổ sung toàn bộ các sub-folder BCTC để tự động khởi tạo khi hệ thống chạy.
- Các module cũ (như data validator, cross_check) đã tự động nhận path mới vì reference thông qua biến tập trung.

## 4. Cập nhật Tài liệu Kỹ thuật (Documentation)
- Sửa lại các đường dẫn trong output contracts và cây thư mục của:
  - `EF-S-01_Data_Structure.md`
  - `EF-S-09_Testing_Strategy.md`
  - `Phase_01_Data_Prep.md`
  - `Phase_03_ML_Training.md`
- Hoàn thiện bản nháp **Kế hoạch lấy dữ liệu BCTC Bất đồng bộ (Async BCTC Collector)** sử dụng `asyncio` và `Semaphore(5)` để tối ưu hóa thời gian từ 8-10h xuống còn 2-3h. (Chưa implement code).

---

# Changelog: Ngày 22/07/2026

## 1. Tạo mới `E_bctc_collector.py` (Bước 4 — Implementation Plan V3)

**File:** `Main Scripts/Phase 1/1.1_Data_Collector/E_bctc_collector.py` (+322 dòng)

Module async collector để cào Báo cáo Tài chính (BCTC) cho toàn bộ mã chứng khoán thông qua vnstock Fundamental API.

### Cấu trúc chính:
- **7 loại báo cáo:** balance_sheet (quarter/year), income_statement (quarter/year), cash_flow (quarter/year), ratio.
- **Kiến trúc Async:** `asyncio` + `Semaphore(5)` + `asyncio.to_thread()` (vnstock dùng `requests` nội bộ — blocking).
- **Concurrency:** Nhiều mã chạy đồng thời (Semaphore kiểm soát), 7 reports per mã chạy tuần tự (vnstock không thread-safe).
- **Checkpoint:** `checkpoint_bctc.json` — hỗ trợ Resume khi bị gián đoạn.
- **Retry:** Tối đa 3 lần, delay 5 giây giữa các lần retry.
- **Atomic Write:** Dùng `safe_write_parquet()` và `safe_write_json()` từ `E_io_utils.py`.
- **Orient fallback:** Ưu tiên `orient='time_series'`, fallback sang `orient='report'` nếu vnstock raise lỗi duplicate columns.

### Các hàm:
| Hàm | Async? | Trách nhiệm |
|---|---|---|
| `_call_vnstock_api()` | ❌ | Dispatch method vnstock theo report_type |
| `fetch_report_sync()` | ❌ | Gọi API + retry + orient fallback |
| `fetch_and_save_async()` | ✅ | Wrap sync call trong thread pool, ghi parquet |
| `collect_bctc_async()` | ✅ | Cào 7 reports tuần tự cho 1 mã |
| `run_all_async()` | ✅ | Entry point — xử lý toàn bộ danh sách mã |

## 2. Phát hiện từ Test thực tế (mã VNM)

- ✅ `cash_flow` (quarter + year): **Thành công**.
- ✅ `ratio`: **Thành công**.
- ❌ `balance_sheet`: vnstock API trả về DataFrame rỗng cho VNM (có thể là hạn chế bản Community).
- ❌ `income_statement`: vnstock raise lỗi `Duplicate column names` khi dùng `orient='time_series'` — fallback đang được debug.
- ❌ `note`: API `eq.note()` không tồn tại trong vnstock hiện tại → đã loại khỏi REPORT_TYPES.

## 3. Audit kết quả theo bộ tiêu chuẩn E_Principles

- **16/19 mục đạt chuẩn:** SRP, Naming (`E_` prefix + `_collector` suffix), Dependency Direction, Atomic Write, Checkpoint, Error Handling.
- **3 vi phạm EF-S-04 (Logging)** cần sửa ở phiên tiếp theo:
  1. Tên file log thiếu `_{YYYY-MM-DD}` (§2).
  2. Format dòng log thiếu `[MODULE]` (§3).
  3. Thiếu log tổng hợp cuối batch (§6).

## 4. Trạng thái Implementation Plan V3

| Bước | Trạng thái |
|---|---|
| 1. Migrate folder → `E_OHLCV/` | ✅ Đã xong (phiên trước) |
| 2. Cập nhật `E_config.py` | ✅ Đã xong (phiên trước) |
| 3. Verify code cũ | ✅ Đã xong (phiên trước) |
| 4. Tạo `E_bctc_collector.py` | 🔧 Đã tạo — đang fix lỗi vnstock |
| 5. Test 5 mã | ⏳ Chờ fix bước 4 |
| 6. Chạy full ~1,528 mã | ⏳ Chờ bước 5 |
| 7. Cập nhật documentation | ✅ Đã xong (phiên trước) |
