# Chương 1 — EF-S-01: Data Structure (SRP)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Single Responsibility Principle (SRP)
> - **Nguồn gốc:** *Agile Software Development, Principles, Patterns, and Practices* — Robert C. Martin, 2002. Chữ viết tắt SOLID do Michael Feathers đặt tên khoảng 2004.
> - **Giải thích:** Một module chỉ nên có duy nhất **MỘT LÝ DO ĐỂ THAY ĐỔI**. Nếu có 2 lý do, hãy tách ra 2 module. Điều này giúp code dễ đọc, dễ test, và dễ bảo trì khi hệ thống phình to.

> **Kim chỉ nam cho toàn bộ công cuộc phát triển và bảo trì dự án E_CYBER-FINANCIAL.**

---

## 1. Quy tắc vàng

> **1 File `.py` = 1 Module/Concern = 1 Trách nhiệm duy nhất.**

Nếu bạn đang viết hàm thứ 5 mà hàm đó phục vụ một "lý do thay đổi" khác với 4 hàm trước, hãy dừng lại và tạo file mới.

### 1.1. Triết lý "One Reason to Change"
SRP không có nghĩa là "1 file chỉ được có 1 hàm" hay "1 file chỉ làm 1 hành động". SRP được định nghĩa là **"Một module chỉ nên có duy nhất MỘT LÝ DO ĐỂ THAY ĐỔI"**.
- Ví dụ: Module `news_scraper.py` chứa nhiều hàm (config RSS, parse feed, lọc theo ngày) nhưng tất cả phục vụ chung một lý do duy nhất: *Thu thập tin tức thô từ RSS*. Nếu logic AI thay đổi, file này không bị ảnh hưởng. Nó tuân thủ tuyệt đối SRP.

### 1.2. High Cohesion vs Low Coupling (Chống phân mảnh)

Quá trình tách God File không phải là băm nát code thành hàng trăm mảnh vỡ vụn (Fragmentation). Đó là quá trình **Chống phân mảnh (Defragmentation)**:
- **High Cohesion (Độ gắn kết cao):** Gom những hàm có chung nghiệp vụ vào chung một module vừa đủ lớn để chúng phối hợp nhịp nhàng.
- **Low Coupling (Độ phụ thuộc thấp):** Tách bạch rõ ràng ranh giới giữa Thu thập (`scraper`), Xử lý (`manager`), và Trình bày (`renderer`) để code không dẫm chân lên nhau.

---

## 2. Cấu trúc thư mục tổng quan (Phase-first)

Dự án tổ chức theo **Phase** — tương ứng với lộ trình 19 tháng.

```
E_CYBER-FINANCIAL/
├── Main Scripts/
│   ├── Phase 1/                  # CHUẨN BỊ DATA (tháng 1)
│   ├── Phase 2/                  # THUẬT TOÁN (tháng 2-4)
│   ├── Phase 3/                  # ML TRAINING (tháng 5-10)
│   ├── Phase 4/                  # CHIẾN TRƯỜNG GIẢ LẬP (tháng 11-16)
│   ├── News/                     # Module tin tức (Phase 5 — xuyên suốt)
│   ├── Auto/                     # Scripts tự động (Task Scheduler)
│   └── IDE_UI/                   # Giao diện Desktop (PyQt6)
│
├── Phase_1_Data/                 # Data thô (Read-only sau khi cào)
│   ├── From_vnstock/                 (Parquet — giá cổ phiếu)
│   ├── From_FireAnt/                 (Parquet — khối ngoại)
│   └── Mock_Data/                    (Dữ liệu giả lập cho test)
│
├── Phase_2_Data/                 # Data xử lý (Tính năng, Indicators)
│   ├── Features/
│   ├── Snapshots/                    (Ảnh chụp features theo thời điểm)
│   └── Mock_Data/                    (Dữ liệu giả lập cho test)
│
├── Phase_3_Data/                 # Model ML đã train
│   ├── Models/
│   ├── Snapshots/                    (Ảnh chụp model input theo thời điểm)
│   └── Mock_Data/                    (Dữ liệu giả lập cho test)
│
├── Phase_4_Data/                 # Kết quả Backtest
│   ├── Results/
│   ├── Snapshots/                    (Ảnh chụp backtest results theo thời điểm)
│   └── Mock_Data/                    (Dữ liệu giả lập cho test)
│
├── Phase_5_Data/                 # Output tin tức (JSON)
│   └── Mock_Data/                    (Dữ liệu giả lập cho test)
├── Log_Debug/                    # Log hệ thống
│
├── System/                       # Entry point + Config
│   ├── Warden.py                     (App launcher — PyQt6)
│   └── .env                          (API keys — KHÔNG commit)
│
└── Helper/                       # Utilities dùng chung
    ├── config.py                     (Centralize paths, constants)
    └── __init__.py
```

### Quy tắc phân loại thư mục

| Thư mục | Chứa gì | KHÔNG chứa gì |
|:---|:---|:---|
| `Phase X/` | Code thuộc giai đoạn X trong lộ trình 19 tháng | Code dùng chung cho nhiều phase |
| `News/` | Module cào, xử lý, render tin tức | Business logic tính toán tài chính |
| `Auto/` | Scripts chạy ngầm bằng Task Scheduler | Logic xử lý phức tạp (phải delegate) |
| `IDE_UI/` | Giao diện PyQt6 — chỉ layout + event binding | Gọi API, tính toán, xử lý data |
| `Helper/` | Utilities độc lập, config, constants | Business logic của bất kỳ phase nào |
| `Phase_1_Data/` | Data thô (.parquet, .csv) | Code xử lý |
| `Phase_2_Data/` | Features Data (.parquet) | Code xử lý |
| `Phase_3_Data/` | Models (.pkl, .joblib) | Code xử lý |
| `Phase_4_Data/` | Backtest Results (.json) | Code xử lý |
| `System/` | Entry point, biến môi trường | Business logic |

---

## 3. Quy tắc đặt tên

### 3.1. Tên File phản ánh chức năng

```
✅ news_scraper.py        → Module cào tin tức từ RSS
✅ data_collector.py      → Module thu thập giá cổ phiếu
✅ ai_client.py           → Module giao tiếp với Gemini API
✅ indicator_calculator.py → Module tính RSI, MACD, Bollinger
❌ utils.py               → Quá chung chung, không rõ trách nhiệm
❌ helpers.py              → Tương tự, quá mơ hồ
❌ main.py (trong sub-folder) → Không rõ "main" của cái gì
❌ process.py              → Process cái gì? Dữ liệu nào?
```

### 3.2. Quy ước đặt tên file theo vai trò

| Hậu tố/Pattern | Ý nghĩa | Ví dụ |
|:---|:---|:---|
| `_collector` | Thu thập/cào data từ nguồn ngoài | `data_collector.py` |
| `_cleaner` | Làm sạch, chuẩn hóa data | `data_cleaner.py` |
| `_scraper` | Cào web/RSS cụ thể | `news_scraper.py` |
| `_manager` | Điều phối pipeline (Orchestrator) | `news_manager.py` |
| `_client` | Giao tiếp với API bên ngoài | `ai_client.py` |
| `_renderer` | Render output (HTML, chart, report) | `news_renderer.py` |
| `_calculator` | Tính toán thuần (pure function) | `indicator_calculator.py` |
| `_validator` | Kiểm tra chất lượng/correctness | `data_validator.py` |
| `_config` | Cấu hình, constants | `config.py` |
| `auto_` | Script chạy tự động (scheduled) | `auto_news.py` |
| `test_` | Unit test / Integration test | `test_phase1.py` |

> [!NOTE]
> Mỗi phase có thêm **kiểu module đặc thù riêng** — xem chương tương ứng ([Phase 01](./Phase_01_Data_Prep.md) - [Phase 05](./Phase_05_News.md)).

### 3.3. Package & Import
- Mỗi folder chứa module nên có `__init__.py` (có thể rỗng).
- Import theo đường dẫn tương đối khi ở cùng package, tuyệt đối khi cross-package.
- **KHÔNG** hardcode `sys.path.insert()` trong mỗi file. Centralize vào `Helper/config.py` hoặc dùng `setup.py`/`pyproject.toml`.

### 3.4. File Header Marker (Bắt buộc)

> **Nền tảng:** Tương đương E-S-01 §3.4 trong dự án Revit gốc.

Mọi file `.py` trong dự án **BẮT BUỘC** phải có docstring header ở đầu file, trước các dòng `import`. Mục đích: ai mở file lên cũng hiểu ngay module này làm gì mà không cần đọc code.

```python
"""
Module:  [Tên module — trùng tên file, bỏ .py]
Logic:   [Mô tả ngắn gọn bằng tiếng Anh — 1 dòng]
Detail:  [Mô tả chi tiết bằng tiếng Việt — 1 dòng]
"""
```

**Các trường bắt buộc:**

| Trường   | Ý nghĩa                                          | Ví dụ                                               |
| -------- | ------------------------------------------------ | ---------------------------------------------------- |
| `Module` | Tên module (trùng tên file, bỏ `.py`)            | `news_scraper`                                       |
| `Logic`  | Tóm tắt chức năng bằng **tiếng Anh** (1 dòng)    | `Scrape RSS feeds from Vietnamese news sources`      |
| `Detail` | Giải thích chi tiết bằng **tiếng Việt** (1 dòng) | `Cào tin từ VNExpress, CafeF, VietStock, TTTC`      |

**Các trường tuỳ chọn (thêm nếu cần):**

| Trường    | Khi nào dùng                   | Ví dụ                     |
| --------- | ------------------------------ | ------------------------- |
| `Status`  | Đánh dấu trạng thái hoàn thiện | `✅ v1.0.0` hoặc `🚧 WIP`  |
| `Updated` | Ngày cập nhật gần nhất         | `2026-07-08 (Refactored)` |

**Ví dụ thực tế:**
```python
"""
Module:  news_manager
Logic:   Orchestrate full news pipeline (scrape → AI → render → save)
Detail:  Điều phối toàn bộ pipeline tin tức: cào RSS, gọi Gemini AI phân tích, render HTML, lưu JSON
Status:  ✅ v1.0.0
"""
import os
import json
from datetime import datetime
```

### 3.5. Naming cho hằng số & tolerance (Chống số ma thuật)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** No Magic Numbers
> - **Nguồn gốc:** *Clean Code*, Chương 17 ("Smells and Heuristics") — Robert C. Martin
> - **Giải thích:** Số "ma thuật" (magic number) là những giá trị số xuất hiện trực tiếp trong code mà không có tên gọi hay chú thích. Chúng khiến người đọc không hiểu giá trị đó có ý nghĩa gì, và khi cần thay đổi thì phải grep tìm khắp nơi, rất dễ sót.

Mọi giá trị số không hiển nhiên (timeout, retry count, threshold...) **phải được khai báo** thành constant ở đầu module hoặc trong `Helper/config.py`, kèm tên mô tả rõ ý nghĩa.

```python
# ✅ ĐÚNG — Tên rõ ràng, có comment giải thích
RETRY_MAX = 3                          # Số lần retry tối đa khi API timeout
API_TIMEOUT_SECONDS = 30               # FireAnt API thường chậm
PRICE_DIFF_TOLERANCE = 0.001           # Chênh lệch giá ≤ 0.1% coi là bằng nhau
MIN_HISTORY_DAYS = 252                 # ~1 năm giao dịch

if retry_count > RETRY_MAX:
    time.sleep(API_TIMEOUT_SECONDS)

# ❌ SAI — Số ma thuật, không ai hiểu
if retry_count > 3:                    # 3 là cái gì???
    time.sleep(30)                     # 30 là gì???
if abs(price_a - price_b) < 0.001:    # 0.001 ở đâu ra???
```

**Ngoại lệ được phép:** Các giá trị hiển nhiên như `0`, `1`, `-1`, `0.5` (nửa), `2` (gấp đôi), `100` (phần trăm) thì không cần khai báo constant.

---

## 4. Giải phẫu 1 Pipeline Step chuẩn

Khi tạo mới module cho 1 step trong pipeline, nó phải được tách thành các thành phần nằm **CÙNG 1 FOLDER PHASE**:

```
Phase X/
├── x_collector.py           ← Thu thập data từ nguồn (tương đương Pre_Selection)
├── x_processor.py           ← Xử lý, làm sạch (tương đương Executor)
├── x_calculator.py          ← Tính toán thuần túy (tương đương Geometry)
├── x_validator.py           ← Kiểm tra chất lượng output
└── test_x.py                ← Unit test
```

### 4.1. Collector (Thu thập)
Chỉ làm đúng 1 việc: **lấy data thô từ nguồn ngoài**.

```python
# ✅ ĐÚNG — Collector thuần, không xử lý
def fetch_stock_data(symbol, start_date):
    """Cào data giá cổ phiếu từ vnstock API."""
    stock = Vnstock().stock(symbol=symbol, source="VCI")
    return stock.quote.history(start=start_date, end=today)
```

### 4.2. Calculator (Tính toán thuần)
Chỉ chứa pure functions. Không gọi API, không ghi file, không hiển thị UI.

```python
# ✅ ĐÚNG — Pure function, cùng input → cùng output
def compute_rsi(series, period=14):
    """Tính Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
```

### 4.3. Manager (Điều phối)
Gọi tới các module con, quản lý pipeline flow. Không tự implement thuật toán.

```python
# ✅ ĐÚNG — Manager gọi module con, không tự tính toán
class NewsManager:
    @staticmethod
    def run_full_pipeline(log_callback=print):
        raw_feeds = news_scraper.fetch_feeds(RSS_URLS)
        analysis = ai_client.analyze(raw_feeds)
        news_renderer.save_html(analysis)
        return debug_log
```

---

## 5. Các hành vi BỊ CẤM

### 5.1. God File (File quá lớn, đa trách nhiệm)
```python
# ❌ TUYỆT ĐỐI KHÔNG — File 26KB chứa nhiều concern
# data_raw_cross_check.py vừa đọc data, vừa tính toán, vừa render chart,
# vừa so sánh, vừa export... tất cả trong 1 file.
```

### 5.2. Module trộn lẫn nhiều concern
```python
# ❌ KHÔNG — 1 file trộn 3 trách nhiệm khác nhau:
# 1. Gọi API bên ngoài (networking)
# 2. Parse response data (data processing)
# 3. Render output cho người dùng (presentation)
# → Tách thành: _client.py (networking) + _renderer.py (presentation)
```

### 5.3. God Function (>80 dòng)
Một hàm không được vượt quá **~80 dòng** (soft limit). Nếu dài hơn, đó là dấu hiệu cần tách thành hàm con hoặc module riêng.

### 5.4. Hardcode đường dẫn tuyệt đối
```python
# ❌ KHÔNG — Hardcode path trong mỗi file
PROJECT_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"

# ✅ ĐÚNG — Centralize vào 1 nơi duy nhất
# Helper/config.py
from Helper.config import PROJECT_DIR, PHASE_1_DIR, PHASE_5_DIR
```

### 5.5. UI chứa business logic
Module trong `IDE_UI/` KHÔNG ĐƯỢC chứa business logic — chỉ layout, event binding, và hiển thị kết quả. Chi tiết xem [EF-S-07](./EF-S-07_UI_Backend.md).

### 5.6. Scheduled Script chứa logic phức tạp
Script trong `Auto/` chỉ là **trigger** — delegate MỌI logic sang Manager. KHÔNG ĐƯỢC vượt quá ~50 dòng. Tên file BẮT BUỘC bắt đầu bằng `auto_`.

```python
# ✅ ĐÚNG — Script tự động chỉ trigger, không chứa logic
def main():
    full_log = NewsManager.run_full_pipeline(log_callback=print)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_log)

if __name__ == "__main__":
    main()
```

```python
# ❌ KHÔNG — auto_news.py tự cào, tự parse, tự lưu
def main():
    feed = feedparser.parse(url)
    for entry in feed.entries:
        # ... 80 dòng xử lý ...
    with open(filepath, "w") as f:
        json.dump(data, f)
```

### 5.7. Nested class/function quá lớn

Python cho phép nested function phổ biến hơn C#. Tuy nhiên, nếu nested function **vượt quá ~20 dòng**, đó là dấu hiệu cần tách ra thành function cấp module hoặc module riêng.

```python
# ❌ KHÔNG NÊN — Nested function quá dài
def process_all(data):
    def _complex_inner_logic(item):
        # ... 40 dòng xử lý phức tạp ...
        pass
    return [_complex_inner_logic(d) for d in data]

# ✅ ĐÚNG — Tách ra function cấp module
def _complex_inner_logic(item):
    # ... 40 dòng xử lý phức tạp ...
    pass

def process_all(data):
    return [_complex_inner_logic(d) for d in data]
```

### 5.8. Đẻ thêm helper thay vì dùng hàng có sẵn
Trước khi tạo một hàm/module chức năng chung bên trong thư mục Phase, **BẮT BUỘC** phải kiểm tra kho `Helper/`.
- **Nếu đã có:** TUYỆT ĐỐI KHÔNG tạo mới. Phải tái sử dụng.
- **Nếu chưa có nhưng có khả năng dùng chung:** Tạo mới trong `Helper/` (xem [EF-S-05](./EF-S-05_Shared_Code.md)).

---

## 6. Quy tắc cho System modules

### 6.1. System/ — Entry Point (Warden.py)

Warden.py chỉ được phép:
- ✅ Import và khởi tạo `QApplication`
- ✅ Gọi `MainWindow()`
- ✅ Setup `sys.path` (nếu cần)

Warden.py KHÔNG ĐƯỢC:
- ❌ Chứa business logic
- ❌ Import trực tiếp các module Phase (phải qua `IDE_UI/`)
- ❌ Vượt quá ~50 dòng

### 6.2. Auto/ — Scripts tự động (Task Scheduler)

Dependency Flow:
```
Task Scheduler (Windows) → auto_*.py → Manager.run_pipeline() → ghi log
```

Quy tắc:
- Script trong Auto/ chỉ là **trigger** — delegate MỌI logic sang Manager
- PHẢI có error handling bao quanh `main()`
- PHẢI ghi log ra file (console output mất khi chạy ngầm)
- KHÔNG ĐƯỢC vượt quá **~50 dòng**
- Tên file BẮT BUỘC bắt đầu bằng `auto_`

---

## 7. Giới hạn kích thước (soft limit)

| Đơn vị | Soft limit | Khi vượt, cần review |
|---|---|---|
| Hàm | ~80 dòng | Tách thành sub-function hoặc module mới |
| File/Module | ~300 dòng | Kiểm tra xem module có đang làm > 1 việc không |
| Phase Folder | ~10 file | Kiểm tra xem phase có cần tách sub-step không |

---

## 8. Quy tắc Testing

- Tên file test BẮT BUỘC bắt đầu bằng `test_` (ví dụ: `test_phase1.py`, `test_indicators.py`)
- File test đặt **cùng folder** với module được test
- Mỗi phase có **kiểu test đặc thù riêng** — xem chương tương ứng ([Phase 01](./Phase_01_Data_Prep.md) - [Phase 05](./Phase_05_News.md))
- Test PHẢI chạy được độc lập (không phụ thuộc vào state của test khác)
- KHÔNG viết test trong file module chính — luôn tách file riêng

---

## 9. Khi nào ĐƯỢC PHÉP gộp?

Chỉ có **2 trường hợp duy nhất** được phép có nhiều concern trong 1 file:

1. **Config constants + small helper** đi kèm nhau trong cùng 1 file config, khi chúng có mối quan hệ 1:1 không thể tách rời.
   ```python
   # Chấp nhận được: constants đi kèm helper function nhỏ
   PROJECT_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"
   DATA_DIR = os.path.join(PROJECT_DIR, "Data_Main")

   def ensure_dirs():
       """Tạo thư mục nếu chưa tồn tại."""
       for d in [DATA_DIR, VNSTOCK_DIR, FIREANT_DIR]:
           os.makedirs(d, exist_ok=True)
   ```

2. **Dataclass/NamedTuple nhỏ** đi kèm module sử dụng nó (khi chỉ dùng nội bộ trong file đó).

---

## 10. Ví dụ thực tế refactor

### Trước: gemini_ai.py — 1 file trộn 2 concern

```
gemini_ai.py
├── def call_gemini_api()       ← Gọi API (networking)
├── def parse_response()        ← Parse JSON (data processing)
├── def render_html_summary()   ← Render HTML output (presentation)
└── def save_html_file()        ← Ghi file (I/O)
```

### Sau: Tách thành 2 file theo SRP

```
Main Scripts/News/
├── ai_client.py                ← Chỉ gọi Gemini API, trả về JSON thuần
│   ├── def call_gemini_api()
│   └── def parse_response()
│
└── news_renderer.py            ← Chỉ nhận JSON, render HTML output
    ├── def render_html_summary()
    └── def save_html_file()
```

---

## 11. Checklist trước khi commit

Trước khi commit bất kỳ file `.py` nào, kiểm tra:

- [ ] File chỉ phục vụ **1 trách nhiệm duy nhất**? (Thu thập ≠ Xử lý ≠ Render ≠ UI)
- [ ] Tên file **phản ánh rõ chức năng** (không phải `utils.py`, `helpers.py`, `main.py`)?
- [ ] File nằm đúng **Phase Folder** hoặc thư mục chức năng phù hợp?
- [ ] Có **File Header docstring** đúng format?
- [ ] **Không hardcode** đường dẫn tuyệt đối? (dùng `Helper/config.py`)
- [ ] **Không có magic numbers**? (hằng số có tên + comment)
- [ ] Không có hàm nào **vượt quá ~80 dòng**?
- [ ] File **không vượt quá ~300 dòng** (soft limit)?
- [ ] Các dependencies đi **đúng chiều** ([EF-S-00](./EF-S-00_Dependency_Direction.md))?
- [ ] Có `__init__.py` trong folder chứa module?

---

> **Ghi nhớ:** Nếu bạn phải giải thích "module này làm gì" bằng từ **"và"** (ví dụ: "module này cào tin **và** gọi AI **và** render HTML"), thì module đó đang vi phạm SRP và cần được tách ra.
