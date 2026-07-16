# Chương 4 — EF-S-04: Logging & Debug (Quy chuẩn ghi log)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Observability (Khả năng quan sát)
> - **Nguồn gốc:** *Site Reliability Engineering (SRE)* — Google, 2016
> - **Giải thích:** Một hệ thống tốt phải có khả năng tự mô tả trạng thái của nó thông qua log. Khi tool chạy sai, developer phải có đủ dữ liệu log để tái hiện vấn đề mà không cần chạy lại tool.

## 1. Khi nào BẮT BUỘC có log?

| Điều kiện | Bắt buộc log? |
|---|---|
| Script trong `Auto/` (chạy ngầm, không console) | ✅ BẮT BUỘC |
| Phase 3 training (chạy hàng giờ) | ✅ BẮT BUỘC |
| Phase 1 cào data (batch 1800 mã) | ✅ BẮT BUỘC |
| Phase 5 cào tin tức (batch nhiều nguồn) | ✅ BẮT BUỘC |
| Helper/ utilities đơn giản | ❌ Không cần |

## 2. Format tên file log

```
Log_Debug/{module}_{YYYY-MM-DD}.log
```

Ví dụ:
- `Log_Debug/data_collector_2026-07-11.log`
- `Log_Debug/auto_news_2026-07-11.log`
- `Log_Debug/arena_runner_2026-07-11.log`

## 3. Format 1 dòng log

```
[TIMESTAMP]  [LEVEL]  [MODULE]  Message

Ví dụ:
[2026-07-11 08:30:22] [INFO]    [data_collector]  Bắt đầu cào VNM...
[2026-07-11 08:30:23] [INFO]    [data_collector]  VNM: 3248 dòng, OK
[2026-07-11 08:30:24] [WARNING] [data_collector]  HPG: Retry lần 2/3 (timeout)
[2026-07-11 08:30:25] [ERROR]   [data_collector]  HPG: Thất bại sau 3 lần retry
[2026-07-11 08:31:00] [INFO]    [data_collector]  Hoàn thành: 1795/1800 mã OK, 5 lỗi
```

## 4. Khi nào dùng `print()` vs `logging`

| Tình huống | Dùng gì | Lý do |
|---|---|---|
| Dev/test trên IDE (interactive) | `print()` | Nhanh, thấy ngay trên console |
| Auto/ script chạy ngầm | `logging` + ghi file | Console output mất khi chạy ngầm |
| Phase 3 training dài | `logging` + ghi file | Cần review sau khi training xong |
| Hàm utility đơn giản | Không cần | Quá nhỏ, log sẽ noise |

## 5. Timing Marker (cho bước xử lý nặng)

Mọi bước xử lý nặng (ước tính > 100ms) **nên** có timing marker để phát hiện bottleneck.

```python
# ✅ ĐÚNG — Đo thời gian từng phase
import time

start = time.perf_counter()
# ... xử lý nặng ...
elapsed = time.perf_counter() - start
logging.info(f"⏱ [PHASE B] Feature engineering: {elapsed:.2f}s")
```

## 6. Cấu trúc log tổng hợp (cuối batch)

```
========================================================================
[ 2026-07-11 10:43:17 ] KẾT QUẢ CHẠY TOOL DATA COLLECTOR
========================================================================

Đã xử lý 1800 mã (45.6s):
✅ Thành công: 1795
❌ Lỗi: 5

── THỜI GIAN THỰC THI ──
⏱ [FETCH] vnstock API: 38.2s
⏱ [WRITE] Parquet files: 7.4s

── CHI TIẾT LỖI ──
❌ HPG: Timeout sau 3 lần retry
❌ VIC: API trả về empty DataFrame
...
```
