# Chương 4 — EF-S-04: Logging & Debug (Ghi dấu để tìm lỗi)

> **Trạng thái:** ACTIVE.
>
> **Agent phải đọc file này khi:** thêm log/print, làm Auto/batch/training, đo thời gian, ghi lỗi hoặc thiết kế màn hình log.
>
> **Mục tiêu:** Khi một tác vụ hỏng, chỉ cần xem log là biết tác vụ nào, lúc nào, input nào và hỏng ở bước nào; không cần đoán.

## 4.1. Log là gì và không phải là gì?

Log là nhật ký sự kiện. Observability đầy đủ còn có metric và trace, nhưng dự án cá nhân hiện tại ưu tiên:

1. Log có cấu trúc và context rõ.
2. Số đếm/timing cơ bản cho batch.
3. Run ID để nối các dòng của cùng một lần chạy.

Không cần dựng hệ thống monitoring phức tạp khi chưa có nhu cầu.

## 4.2. Khi nào bắt buộc log?

- Script `Auto/` chạy không có người nhìn console.
- Batch nhiều item ở Phase 1 hoặc Phase 5.
- Training/backtest chạy lâu.
- Gọi API ngoài, retry hoặc partial failure.
- Ghi file output quan trọng.
- Thay đổi schema/config có ảnh hưởng kết quả.

Pure helper nhỏ không cần tự log mọi lần gọi. Caller chịu trách nhiệm log use case để tránh noise.

## 4.3. Nơi lưu và tên file

Mọi code production ghi log qua [E_BlackBox](../E_Helper/E_BlackBox.py). Log của tính năng nằm cạnh script chính sở hữu tính năng đó:

```text
Main Scripts/News/E_news_manager.py  → Main Scripts/News/E_news_manager.log
Main Scripts/Auto/E_auto_news.py     → Main Scripts/Auto/E_auto_news.log
System/Warden.py                     → System/Warden.log
```

- Không tự tạo `FileHandler`, `basicConfig()`, `*_log.txt` hoặc một folder log thứ hai.
- Không truyền đường dẫn log tùy ý. `get_black_box(__file__)` tự xác định đúng nơi và tên file.
- Các file cũ trong `Log_Debug/` hoặc `*_log.txt` chỉ là lịch sử; code mới không được tiếp tục ghi vào đó.
- `E_BlackBox` xoay file theo kích thước để log không tăng vô hạn. Không tự xóa log cũ nếu chưa có chính sách retention được duyệt.

## 4.4. Format một dòng

Mỗi dòng là một JSON object độc lập (`JSON Lines`):

```json
{"timestamp":"2026-08-09T21:15:22+07:00","level":"INFO","feature":"E_data_collector","run_id":"a12b34c56d78","message":"Saved OHLCV","context":{"symbol":"VNM","rows":3248}}
```

Tối thiểu cần có:

- timestamp ISO 8601 có timezone;
- level;
- logger/module;
- message;
- `run_id` cho batch dài;
- context như symbol, source, phase khi liên quan.

Không cần nhét mọi thứ vào câu văn dài. Dữ kiện quan trọng nên có key rõ như `symbol=VNM`.

## 4.5. Chọn level

| Level | Dùng khi |
|---|---|
| `DEBUG` | Chi tiết phục vụ điều tra, thường tắt ở chế độ bình thường |
| `INFO` | Bắt đầu/kết thúc bước, số item, output đã lưu |
| `WARNING` | Retry, thiếu một nguồn, kết quả partial nhưng pipeline còn chạy |
| `ERROR` | Một use case/item thất bại và cần được ghi nhận |
| `CRITICAL` | Toàn ứng dụng hoặc pipeline chính không thể tiếp tục |

Không dùng `ERROR` cho sự kiện bình thường như “không có file hôm nay” nếu đó chỉ là tín hiệu để bắt đầu cào.

## 4.6. `print()` và `logging`

- Code production dùng `logging`.
- CLI/UI có thể hiển thị tiến độ qua callback/signal; không thay logging bằng `print`.
- Test có thể dùng `print` tạm khi debug, nhưng phải bỏ trước commit nếu không cần.
- Auto không dựa vào console vì Task Scheduler có thể không giữ output.

## 4.7. Error logging

Theo [EF-S-02](./EF-S-02_Error_Handling.md), một exception nên được log đầy đủ **một lần ở boundary chịu trách nhiệm**:

```python
try:
    manager.run_pipeline()
except Exception:
    logger.exception("News pipeline failed", extra={"run_id": run_id})
    raise
```

`logger.exception()` tự giữ traceback. Không chỉ log `str(e)` rồi làm mất vị trí gây lỗi.

## 4.8. Timing và batch summary

Đo các bước có ý nghĩa vận hành, không cần timing mọi function trên 100 ms.

```python
start = time.perf_counter()
result = run_feature_engineering(data)
elapsed = time.perf_counter() - start
logger.info("Feature engineering completed", extra={"elapsed_s": round(elapsed, 2)})
```

Cuối batch cần có summary:

```text
run=20260809-211500 status=partial
total=1800 success=1795 failed=5 elapsed_s=45.6
output=Phase_1_Data/...
```

Chi tiết từng lỗi có thể nằm ở các dòng trước hoặc file report riêng nếu danh sách quá dài.

## 4.9. Bảo mật log

Tuyệt đối không ghi:

- API key, bearer token, password;
- toàn bộ request header có `Authorization`;
- nội dung `.env`;
- dữ liệu tài chính cá nhân nếu sau này dự án có dữ liệu này.

URL có query chứa token phải được che trước khi log.

## 4.10. Rotation và retention

- Tách file theo ngày hoặc dùng rotating handler để tránh file log tăng vô hạn.
- Không gọi log local là “audit trail vĩnh viễn”. Log có thể hỏng/mất và không thay thế backup.
- Trước khi thêm tự động xóa, Agent phải đề xuất thời gian giữ và xin chủ dự án duyệt.
- Log của run/model/backtest quan trọng có thể archive cùng artifact tương ứng.

## 4.11. Cấu hình tập trung

Nguồn duy nhất là `E_Helper/E_BlackBox.py`:

```python
from E_Helper.E_BlackBox import get_black_box

black_box = get_black_box(__file__)
black_box.info("Đã lưu dữ liệu", symbol=symbol, rows=len(data))
```

Panel IDE đăng ký nhận event từ BlackBox để hiển thị. Panel không tự ghi thêm file và BlackBox không import PyQt, nhờ đó vẫn đúng [EF-S-00](./EF-S-00_Dependency_Direction.md) và [EF-S-07](./EF-S-07_UI_Backend.md).

## 4.12. Checklist cho Agent

- [ ] Module dùng `get_black_box(__file__)` và log nằm cạnh script sở hữu tính năng?
- [ ] Timestamp có timezone và có run ID cho batch?
- [ ] Level phản ánh đúng mức độ?
- [ ] Có context source/symbol/phase khi cần?
- [ ] Exception có traceback và không bị log trùng nhiều tầng?
- [ ] Auto dùng logging thay vì chỉ `print`/`.txt` riêng?
- [ ] Cuối batch có total/success/failure/time/output?
- [ ] Không lộ secret hoặc Authorization header?
- [ ] Không tạo file log tăng vô hạn?
- [ ] Không còn `basicConfig()`, `FileHandler` hoặc `*_log.txt` riêng?
