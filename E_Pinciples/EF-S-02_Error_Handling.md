# Chương 2 — EF-S-02: Error Handling (Xử lý lỗi)

> **Trạng thái:** ACTIVE.
>
> **Agent phải đọc file này khi:** thêm `try/except`, retry, xử lý batch, báo lỗi lên UI/Auto hoặc quyết định tiếp tục hay dừng pipeline.
>
> **Mục tiêu:** Lỗi không bị giấu, nhưng cũng không bị ghi lặp lại ở mọi tầng. Hệ thống tiếp tục khi lỗi nhỏ có thể bỏ qua và dừng rõ ràng khi kết quả không còn đáng tin.

## 2.1. Trước tiên phải phân loại lỗi

| Loại lỗi | Ví dụ | Cách xử lý |
|---|---|---|
| Lỗi dự kiến của một item | Một mã cổ phiếu timeout, một RSS feed chết | Ghi trạng thái item, có thể retry/skip và chạy tiếp |
| Dữ liệu không hợp lệ | Thiếu cột `close`, OHLC sai | `Validator` báo lỗi rõ; Phase nghiêm ngặt có thể dừng |
| Lỗi cấu hình | Thiếu API key, sai path | Dừng use case và báo cách sửa |
| Lỗi hệ thống không dự kiến | Bug code, file hỏng, hết disk | Cho lỗi đi lên boundary, log traceback một lần, trả trạng thái thất bại |
| Người dùng hủy | Đóng app, `KeyboardInterrupt` | Dừng gọn, không báo như bug hệ thống |

## 2.2. Ai bắt lỗi ở đâu?

```text
Calculator/Validator → chỉ bắt nếu cần đổi lỗi kỹ thuật thành lỗi dễ hiểu
Collector/Client     → retry lỗi tạm thời; hết retry thì raise lỗi có context
Manager              → quyết định item nào được skip và khi nào cả pipeline phải fail
UI                   → hiển thị thông báo dễ hiểu; không nuốt lỗi
Auto/Entry point     → boundary cuối: log fatal và trả exit code khác 0
```

Không có luật “Calculator tuyệt đối không được `try/except`”. Calculator được bắt lỗi nếu nó có thể:

- thêm context hữu ích;
- chuyển exception thư viện thành exception nghiệp vụ dễ hiểu;
- dọn tài nguyên rồi `raise` lại.

Nếu không làm được một trong các việc trên thì để lỗi tự đi lên.

## 2.3. Log một lần ở nơi chịu trách nhiệm

Không bắt buộc mọi `except` đều log. Nếu một tầng chỉ thêm context rồi `raise`, tầng đó có thể không log; boundary sẽ log một lần đầy đủ.

```python
# Tầng client: thêm context, không log trùng
try:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
except requests.RequestException as exc:
    raise DataSourceError(f"FireAnt thất bại cho {symbol}") from exc
```

```python
# Boundary cuối: log traceback một lần
try:
    manager.run_pipeline()
except Exception:
    logger.exception("Pipeline thất bại")
    raise
```

## 2.4. Những hành vi bị cấm

```python
try:
    do_something()
except Exception:
    pass                  # Cấm: lỗi biến mất
```

```python
try:
    do_something()
except Exception:
    continue              # Cấm nếu không ghi nhận item thất bại
```

```python
try:
    do_something()
except:                   # Cấm bare except: bắt cả tín hiệu thoát hệ thống
    pass
```

Cũng không được bắt một `Exception` rất rộng rồi trả về “thành công” hoặc chuỗi lỗi khiến caller không biết tác vụ đã fail.

## 2.5. Batch: tiếp tục nhưng phải có kết quả rõ

Phase 1/News có thể tiếp tục khi một item lỗi:

```python
successes = []
failures = []

for symbol in symbols:
    try:
        collect_one(symbol)
        successes.append(symbol)
    except DataSourceError as exc:
        failures.append({"symbol": symbol, "error": str(exc)})

result = BatchResult(successes=successes, failures=failures)
```

Manager phải đặt ngưỡng fail cho toàn batch, ví dụ:

- Không lấy được bất kỳ item nào → pipeline fail.
- Tỷ lệ lỗi vượt ngưỡng đã cấu hình → pipeline fail hoặc cảnh báo nghiêm trọng.
- Một nguồn phụ lỗi nhưng còn nguồn thay thế → partial success và ghi rõ nguồn thiếu.

Không dùng một con số ngưỡng tùy ý mà không có constant và giải thích.

## 2.6. Retry đúng cách

Chỉ retry lỗi có khả năng tạm thời: timeout, mất mạng ngắn, HTTP 429 hoặc 5xx phù hợp.

Không retry lỗi logic/dữ liệu như thiếu cột, API key sai hoặc HTTP 400 do request sai.

Retry phải có:

- số lần tối đa;
- timeout mỗi lần;
- backoff tăng dần và jitter nếu gọi nhiều request;
- log ở mức `WARNING` cho lần retry;
- lỗi cuối cùng có context nguồn, symbol và số lần đã thử.

## 2.7. Chiến lược theo Phase

| Phase | Mặc định | Giải thích dễ hiểu |
|---|---|---|
| Phase 1 | Retry + resume theo item | Một mã lỗi không làm mất cả đợt cào |
| Phase 2 | Fail fast khi công thức/schema sai | Feature sai sẽ làm model sai |
| Phase 3 | Checkpoint + fail rõ | Không mất hàng giờ train nhưng không giấu model lỗi |
| Phase 4 | Fail fast với logic giao dịch | Một trade sai có thể làm sai toàn equity curve |
| Phase 5 | Resilient theo nguồn | Một báo lỗi vẫn có thể lấy báo khác; kết quả phải ghi nguồn thiếu |

Đây là mặc định. Agent được thay đổi cho một use case cụ thể nếu giải thích lý do trong plan.

## 2.8. UI và Auto

- UI hiển thị thông báo thân thiện cho người dùng và giữ chi tiết kỹ thuật trong log.
- Worker thread phải gửi signal lỗi riêng, không giả lỗi thành signal `finished` thành công.
- Auto script khi fatal phải `raise` lại hoặc `sys.exit(1)` sau khi log.
- Không ghi API key, token, dữ liệu nhạy cảm vào thông báo lỗi.

## 2.9. Checklist cho Agent

- [ ] Đã phân biệt lỗi dự kiến, lỗi dữ liệu và lỗi hệ thống?
- [ ] `except` này có mục đích cụ thể: recover, retry, translate, cleanup hoặc boundary?
- [ ] Không có `pass`, bare `except` hoặc `continue` làm mất dấu lỗi?
- [ ] Một exception không bị log lặp ở nhiều tầng?
- [ ] Retry chỉ áp dụng cho lỗi tạm thời và có giới hạn?
- [ ] Batch trả danh sách success/failure rõ ràng?
- [ ] Fatal error làm Auto trả exit code khác 0?
- [ ] UI nhận lỗi qua signal/result rõ, không hiểu nhầm là thành công?
- [ ] Log không chứa secret?
