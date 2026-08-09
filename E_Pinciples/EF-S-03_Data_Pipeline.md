# Chương 3 — EF-S-03: Data Pipeline (Quản lý luồng và file dữ liệu)

> **Trạng thái:** ACTIVE.
>
> **Agent phải đọc file này khi:** đọc/ghi Parquet hoặc JSON, thiết kế output của một Phase, thêm checkpoint/resume, chạy batch, snapshot, async hoặc quyết định khi nào train lại model.
>
> **Mục tiêu:** Không tạo file ghi dở, biết file nào là bản mới nhất, có thể chạy lại mà không làm hỏng dữ liệu và truy ra dữ liệu đã tạo từ đâu.

## 3.1. Bốn khái niệm chính

| Khái niệm | Hiểu đơn giản |
|---|---|
|---|---|
| Atomic replacement | Ghi xong file tạm rồi mới thay file đích; tránh file bị “nửa cũ nửa mới” |
| Idempotent | Chạy lại cùng input không tạo kết quả sai hoặc nhân đôi ngoài ý muốn |
| Checkpoint | Ghi nhớ đã làm tới đâu để chạy tiếp sau khi dừng |
| Data contract | Quy định rõ tên cột, kiểu dữ liệu, đơn vị, timezone và version |

Không gọi atomic file write là “Unit of Work”. Unit of Work thường nói về việc gom thay đổi của một transaction/database; không đúng với trường hợp file đơn giản của dự án này.

## 3.2. Ai được đọc/ghi?

| Module | Đọc data | Ghi data | Ghi chú |
|---|---:|---:|---|
| Collector / Client | Có | Chỉ khi nó được giao cả nhiệm vụ lưu raw data | Với pipeline lớn nên trả data cho Repository/Manager |
| Repository / Exporter | Có | Có | Tầng I/O chính |
| Manager | Có qua Repository | Điều phối, không tự rải `open()` khắp code | Quản lý flow và metadata |
| Calculator / Validator | Không tự đọc file | Không | Nhận data qua tham số và trả kết quả |
| Renderer | Chỉ nhận dữ liệu cần render | Chỉ output trình bày | Không sửa raw data |
| UI | Không đọc/ghi data nghiệp vụ trực tiếp | Không | Gọi Manager |

## 3.3. Ghi file an toàn

JSON và Parquet phải dùng hàm trong `E_Helper/E_io_utils.py` hoặc một Repository dùng các hàm đó:

- `safe_write_json(filepath, data)`
- `safe_write_parquet(filepath, df)`

Quy trình chuẩn:

1. Tạo folder đích.
2. Ghi file tạm trong cùng filesystem/folder.
3. Đóng và kiểm tra việc ghi đã thành công.
4. Dùng `os.replace()` thay file đích.
5. Xóa temp file trong `finally` nếu có lỗi.

Atomic replacement giúp chống file ghi dở, nhưng không phải backup và không đảm bảo chống mọi trường hợp mất điện/hỏng disk. Dữ liệu quan trọng vẫn cần snapshot/backup riêng.

## 3.4. Không gọi toàn bộ Phase 1 là immutable

Dự án hiện có file kiểu:

```text
Phase_1_Data/E_OHLCV/From_vnstock/VNM_historical_vnstock.parquet
```

Đây là **latest/working snapshot**: có thể được thay atomically khi cập nhật lịch sử mới. Nó không phải immutable.

Nếu cần tái hiện quá khứ để audit, tạo bản versioned riêng:

```text
Phase_1_Data/Snapshots/2026-08-09/E_OHLCV/...
```

Quy tắc:

- Working/latest file: được thay bằng bản hoàn chỉnh mới.
- Snapshot/versioned file: đã tạo thì không sửa.
- Không ghi đè snapshot trùng version/date; nếu chạy lại phải xác nhận nội dung giống nhau hoặc tạo run ID mới.

## 3.5. Output contract theo Phase

| Phase | Output chính | Vị trí mục tiêu | Tính chất |
|---|---|---|---|
| Phase 1 | Raw/normalized Parquet | `Phase_1_Data/E_OHLCV/...`, `Phase_1_Data/E_BCTC/...` | Latest file + snapshot khi cần audit |
| Phase 2 | Feature Parquet | `Phase_2_Data/Features/` khi Phase 2 được tạo | Có thể rebuild từ Phase 1; phải version schema |
| Phase 3 | Model + metadata | `Phase_3_Data/Models/` khi Phase 3 được tạo | Mỗi run có ID/version riêng, không chỉ lưu `.pkl` |
| Phase 4 | Backtest result + config | `Phase_4_Data/Results/` khi Phase 4 được tạo | Mỗi run có ID, không overwrite |
| Phase 5 | News JSON | `Phase_5_Data/` | File theo ngày; sửa/backfill phải lưu nguồn và thời điểm cập nhật |

Mỗi output quan trọng nên có metadata tối thiểu:

- `schema_version`;
- `created_at` có timezone;
- source/source version;
- input range hoặc input fingerprint;
- code version/commit nếu có;
- trạng thái complete/partial và danh sách lỗi.

## 3.6. Data contract bắt buộc

Trước khi Phase sau đọc output Phase trước, Agent phải ghi rõ:

- tên cột và ý nghĩa;
- type (`datetime`, `float`, `string`...);
- đơn vị giá/khối lượng;
- timezone;
- cột nào bắt buộc/được null;
- cách xử lý trùng ngày/trùng symbol;
- `schema_version` và cách migrate khi thay đổi.

Không chỉ dựa vào “DataFrame hiện đang trông như thế nào”.

## 3.7. Checkpoint và resume

Chỉ bắt buộc checkpoint khi tác vụ:

- chạy nhiều item hoặc mất nhiều phút/giờ;
- có thể tiếp tục độc lập từ item đã hoàn thành;
- có chi phí gọi API/train lớn.

Checkpoint mẫu:

```json
{
  "pipeline": "phase1_bctc",
  "run_id": "2026-08-09T21-00-00+07-00",
  "status": "in_progress",
  "completed": ["VNM"],
  "failed": {"HPG": "timeout"},
  "updated_at": "2026-08-09T21:10:00+07:00"
}
```

Checkpoint cũng phải ghi atomically. Khi resume, Agent phải xác minh config/schema của checkpoint còn tương thích; không tiếp tục mù quáng bằng config mới.

## 3.8. Async và concurrency

Async/concurrency là công cụ, không phải luật theo Phase.

Dùng khi:

- công việc chủ yếu chờ network/I/O;
- thư viện hỗ trợ async hoặc blocking call được đưa sang thread an toàn;
- API cho phép nhiều request đồng thời.

Không dùng khi:

- thuật toán CPU-bound mà không có multiprocessing/vectorization phù hợp;
- API có rate limit thấp;
- thư viện không thread-safe;
- concurrency làm khó kiểm soát thứ tự hoặc tính đúng.

Khi dùng phải có giới hạn concurrency, timeout, retry/backoff và kết quả lỗi theo từng task. Không để `asyncio.gather(..., return_exceptions=True)` rồi bỏ qua các exception chưa xử lý.

## 3.9. Khi nào train lại model?

Không có luật “OHLCV hàng ngày thì tuyệt đối không train lại”. Quyết định retrain dựa trên:

- lịch retrain đã định (tuần/tháng/quý);
- lượng dữ liệu mới đủ lớn;
- schema/feature thay đổi;
- performance trên dữ liệu mới giảm;
- phát hiện drift;
- yêu cầu nghiên cứu cụ thể.

Mọi lần train phải giữ input snapshot hoặc fingerprint, config, random seed, metric validation và model version để tái hiện.

## 3.10. Retention và backup

- Không quy định “giữ mọi log/snapshot vĩnh viễn” một cách mặc định.
- Working files được thay theo pipeline.
- Model/backtest/snapshot quan trọng giữ theo run/version.
- Agent phải đề xuất retention theo dung lượng và giá trị audit trước khi tự động xóa.
- Backup Google Drive chỉ được ghi là tiêu chuẩn khi script backup thật sự tồn tại và đã được kiểm thử.

## 3.11. Checklist cho Agent

- [ ] Đã phân biệt working/latest file và immutable snapshot?
- [ ] Dùng atomic write và cleanup temp khi lỗi?
- [ ] Chạy lại có idempotent hoặc có run ID rõ ràng?
- [ ] Output path khớp cấu trúc repo thật?
- [ ] Có schema/version/timezone/đơn vị rõ?
- [ ] Phase sau đọc qua data contract thay vì đoán cột?
- [ ] Chỉ dùng checkpoint cho tác vụ thật sự cần resume?
- [ ] Resume có kiểm tra config/schema tương thích?
- [ ] Concurrency có giới hạn, timeout và gom lỗi?
- [ ] Model/backtest có metadata để tái hiện?
