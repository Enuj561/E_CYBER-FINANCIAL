# Chương 3 — EF-S-03: Data Pipeline Management (Quản lý luồng dữ liệu)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Unit of Work Pattern — "tất cả hoặc không gì cả" (all-or-nothing)
> - **Nguồn gốc:** Tương tự *Patterns of Enterprise Application Architecture* — Martin Fowler, 2002
> - **Giải thích:** Mọi thao tác ghi/thay đổi dữ liệu phải được quản lý chặt chẽ. Dữ liệu không được ở trạng thái "ghi được một nửa" — hoặc ghi thành công toàn bộ, hoặc không ghi gì.

## 1. Ai được ghi file output?

| Module               | Được phép? | Ghi chú                                      |
| -------------------- | ---------- | -------------------------------------------- |
| **Collector**        | ✅ CÓ       | Ghi data thô vào `Phase_1_Data/`             |
| **Feature Store**    | ✅ CÓ       | Ghi features vào `Phase_2_Data/Features/`    |
| **Manager**          | ✅ CÓ       | Điều phối ghi file qua Collector/Exporter     |
| **Calculator**       | ❌ KHÔNG    | Chỉ tính toán thuần túy, chỉ return          |
| **IDE_UI**           | ❌ KHÔNG    | Chỉ hiển thị, không ghi data                 |
| **Renderer**         | ✅ CÓ       | Ghi output HTML/report                       |
| **Exporter**         | ✅ CÓ       | Ghi model .pkl ra disk (Phase 3)             |

## 2. Atomic File Write — Ghi file an toàn

Ghi trực tiếp vào file đích có rủi ro corrupt nếu crash giữa chừng.
> [!IMPORTANT]
> **BẮT BUỘC:** Sử dụng các hàm trong `Helper/io_utils.py` để ghi file an toàn.
> - `safe_write_json(filepath, data)`: Cho file JSON
> - `safe_write_parquet(filepath, df)`: Cho file Parquet

## 3. Checkpoint Pattern

Đặc biệt quan trọng cho Phase 1 (cào 1800 mã), Phase 2 (tính features) và Phase 3 (training hàng giờ):
- Lưu tiến trình vào các file `checkpoint_*.json` tại thư mục của mỗi Phase.
- Cấu trúc mẫu: `{"module": "...", "started_at": "...", "updated_at": "...", "completed": [], "failed": {}, "status": "in_progress"}`
- Code PHẢI kiểm tra checkpoint lúc bắt đầu để resume. Phase 5 không cần vì đã có check file tồn tại theo ngày.

## 4. Immutability Rule

| Thư mục output | Tính chất | Ghi chú |
|---|---|---|
| `Phase_1_Data/` | **Immutable** | Không sửa, không ghi đè file cũ sau khi cào xong |
| `Phase_2_Data/` | **Rebuild-able** | Có thể xóa và tính lại từ dữ liệu Phase 1 bất cứ lúc nào |
| `Phase_3_Data/Models/`| **Versioned** | Mỗi model là 1 file riêng, không overwrite |
| `Phase_4_Data/Results/`| **Append-only** | Tạo file mới cho mỗi lần chạy backtest |
| `Phase_5_Data/` | **Append-only** | Thêm file mới mỗi ngày, không sửa file cũ |
| `Log_Debug/` | **Append-only** | Không được xóa (audit trail), thêm file mỗi ngày |

## 5. Output Contract tổng hợp

| Phase | Format | Vị trí | Tên file | Tính chất | Ai đọc? |
|---|---|---|---|---|---|
| **Phase 1** | `.parquet` | `Phase_1_Data/From_*/` | `{SYMBOL}_historical_{source}.parquet` | Immutable | Phase 2, Phase 3 |
| **Phase 2** | `.parquet` | `Phase_2_Data/Features/` | `{SYMBOL}_features.parquet` | Rebuild-able | Phase 3 |
| **Phase 3** | `.pkl` + `.json` | `Phase_3_Data/Models/` | `exp_{ID}_{model}_{context}.pkl` | Versioned | Phase 4 |
| **Phase 4** | `.json` + charts | `Phase_4_Data/Results/` | `backtest_{date}_{strategy}.json` | Append-only | Con người |
| **Phase 5** | `.json` + HTML | `Phase_5_Data/` | `News_{dd}_{mm}_{yy}.json` | Append-only | Phase 3, IDE_UI |

## 6. Re-training Triggers (Khi nào train lại model?)

| Trigger | Hành động | Lý do |
|---|---|---|
| Có Báo Cáo Tài Chính mới (Quý/Năm) | **Train lại** model | Dữ liệu cơ bản thay đổi → patterns thay đổi |
| Thêm/Sửa Technical Indicators | **Train lại** model | Feature set đầu vào thay đổi |
| Model accuracy giảm rõ rệt | **Train lại** model | Concept drift |
| Cập nhật OHLCV hàng ngày | **KHÔNG train lại** | Model dùng để predict/warning trực tiếp. Chỉ tính toán lại indicators (Phase 2) cho ngày mới. |

## 7. Asynchronous Processing (Xử lý bất đồng bộ)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Asynchronous I/O — xử lý nhiều tác vụ I/O đồng thời mà không chờ tuần tự
> - **Nguồn gốc:** PEP 3156 — Guido van Rossum, 2012. Python `asyncio` module.
> - **Giải thích:** Khi gọi API hoặc đọc file, CPU chỉ chờ response mà không làm gì. Async cho phép CPU chuyển sang xử lý tác vụ khác trong lúc chờ, tăng tốc đáng kể cho các công việc I/O-bound.

### 7.1. Phase nào dùng Async?

| Phase | Dùng Async? | Loại tác vụ | Lý do |
|---|---|---|---|
| **Phase 1** (Cào data) | ✅ CÓ | I/O-bound | Gọi API vnstock, FireAnt — chờ network response |
| **Phase 2** (Tính toán) | ❌ KHÔNG | CPU-bound | Tính toán thuần túy, asyncio không giúp gì |
| **Phase 3** (ML Training) | ❌ KHÔNG | CPU-bound | PyCaret tự quản lý concurrency |
| **Phase 4** (Backtesting) | ❌ KHÔNG | CPU-bound | Mô phỏng giao dịch = tính toán tuần tự |
| **Phase 5** (Cào tin) | ✅ CÓ | I/O-bound | Gọi RSS feeds, Gemini API — chờ network |

### 7.2. Quy tắc khi dùng Async

1. **Semaphore bắt buộc** — Giới hạn số request đồng thời để tránh bị API ban:

```python
# ✅ ĐÚNG — Giới hạn tối đa 5 request đồng thời
import asyncio
import aiohttp

SEM = asyncio.Semaphore(5)

async def fetch_one(session, symbol):
    async with SEM:
        url = f"https://api.example.com/{symbol}"
        async with session.get(url) as resp:
            return await resp.json()
```

2. **Error Handling trong async** — Mỗi task phải tự bắt lỗi, không để 1 task chết cả batch:

```python
# ✅ ĐÚNG — Mỗi task tự bắt lỗi
async def safe_fetch(session, symbol):
    try:
        return await fetch_one(session, symbol)
    except Exception as e:
        logging.error(f"[{symbol}] {e}")
        return None
```

3. **Thay thế thư viện blocking** — KHÔNG dùng `requests` trong async, dùng `aiohttp`:

| Blocking (KHÔNG dùng trong async) | Async (thay thế) |
|---|---|
| `requests.get()` | `aiohttp.ClientSession.get()` |
| `time.sleep()` | `asyncio.sleep()` |
| `open().read()` | `aiofiles.open()` *(tùy chọn)* |

## 8. Data Snapshot (Ảnh chụp dữ liệu)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Snapshot Pattern — lưu giữ trạng thái dữ liệu tại 1 thời điểm cụ thể
> - **Nguồn gốc:** *Patterns of Enterprise Application Architecture* — Martin Fowler, 2002
> - **Giải thích:** Thay vì chỉ biết "trạng thái hiện tại", hệ thống cần có khả năng "nhớ lại chuyện gì đã xảy ra" tại bất kỳ thời điểm nào trong quá khứ. Điều này giúp debug, audit, và so sánh kết quả qua thời gian.

### 8.1. Phase nào cần Snapshot?

| Phase | Cần Snapshot? | Lý do | Trigger |
|---|---|---|---|
| Phase 1 | ❌ KHÔNG | Data thô đã immutable | — |
| Phase 2 | ✅ CẦN | Features thay đổi khi thêm/sửa indicator | Mỗi lần rebuild features |
| Phase 3 | ✅ CẦN | Model input cần tái hiện để debug | Mỗi lần train model |
| Phase 4 | ✅ CẦN | Backtest results cần so sánh qua thời gian | Mỗi lần chạy backtest |
| Phase 5 | ❌ KHÔNG | News JSON đã append-only theo ngày | — |

### 8.2. Cấu trúc thư mục Snapshot

```
Phase_2_Data/
├── Features/                      ← Data hiện tại (working copy)
│   ├── VNM_features.parquet
│   └── FPT_features.parquet
└── Snapshots/                     ← Ảnh chụp theo thời điểm
    ├── 2026-07-12/
    │   ├── VNM_features.parquet
    │   └── FPT_features.parquet
    └── 2026-08-15/
        ├── VNM_features.parquet
        └── FPT_features.parquet
```

### 8.3. Quy tắc Snapshot

| Quy tắc | Chi tiết |
|---|---|
| **Format tên folder** | `Snapshots/{YYYY-MM-DD}/` |
| **Retention policy** | **Vĩnh viễn** — KHÔNG được xóa snapshot |
| **Tính chất** | **Immutable** — snapshot một khi đã tạo, KHÔNG được sửa |
| **Backup** | Sync lên Google Drive qua script riêng |
