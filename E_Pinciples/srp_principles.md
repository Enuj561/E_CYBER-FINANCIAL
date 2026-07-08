# E_CYBER-FINANCIAL STANDARD (EF-S)
## EF-S-00: DATA STRUCTURE — Nguyên tắc Single Responsibility Principle (SRP)

> **Kim chỉ nam cho toàn bộ công cuộc phát triển và bảo trì dự án E_CYBER-FINANCIAL.**

### Mục lục

| Chương | Nội dung | Phạm vi |
|---|---|---|
| **Chương 1** | Quy tắc SRP dùng chung | Áp dụng cho MỌI phase, MỌI module |
| **Chương 2** | Hệ thống (UI / Auto / System) | IDE_UI, Auto/, System/ |
| **Chương 3** | Phase 1 — Chuẩn bị Data | `Main Scripts/Phase 1/` |
| **Chương 4** | Phase 2 — Thuật toán | `Main Scripts/Phase 2/` |
| **Chương 5** | Phase 3 — ML Training | `Main Scripts/Phase 3/` |
| **Chương 6** | Phase 4 — Chiến trường Giả lập | `Main Scripts/Phase 4/` |
| **Chương 7** | Phase 5 — Tích hợp News | `Main Scripts/News/` |

---
---

# CHƯƠNG 1: QUY TẮC SRP DÙNG CHUNG

> Các quy tắc trong chương này áp dụng cho **MỌI phase, MỌI module** trong dự án. Không có ngoại lệ.

---

## 1.1. Quy tắc vàng

> **1 File `.py` = 1 Module/Concern = 1 Trách nhiệm duy nhất.**

Nếu bạn đang viết hàm thứ 5 mà hàm đó phục vụ một "lý do thay đổi" khác với 4 hàm trước, hãy dừng lại và tạo file mới.

## 1.2. Triết lý "One Reason to Change"

SRP không có nghĩa là "1 file chỉ được có 1 hàm" hay "1 file chỉ làm 1 hành động". SRP được định nghĩa là **"Một module chỉ nên có duy nhất MỘT LÝ DO ĐỂ THAY ĐỔI"**.
- Ví dụ: Module `news_scraper.py` chứa nhiều hàm (config RSS, parse feed, lọc theo ngày) nhưng tất cả phục vụ chung một lý do duy nhất: *Thu thập tin tức thô từ RSS*. Nếu logic AI thay đổi, file này không bị ảnh hưởng. Nó tuân thủ tuyệt đối SRP.

## 1.3. High Cohesion vs Low Coupling (Chống phân mảnh)

Quá trình tách God File không phải là băm nát code thành hàng trăm mảnh vỡ vụn (Fragmentation). Đó là quá trình **Chống phân mảnh (Defragmentation)**:
- **High Cohesion (Độ gắn kết cao):** Gom những hàm có chung nghiệp vụ vào chung một module vừa đủ lớn để chúng phối hợp nhịp nhàng.
- **Low Coupling (Độ phụ thuộc thấp):** Tách bạch rõ ràng ranh giới giữa Thu thập (`scraper`), Xử lý (`manager`), và Trình bày (`renderer`) để code không dẫm chân lên nhau.

---

## 1.4. Cấu trúc thư mục tổng quan (Phase-first)

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
├── Data_Main/                    # Data thô (Read-only sau khi cào)
│   ├── From_vnstock/                 (Parquet — giá cổ phiếu)
│   └── From_FireAnt/                 (Parquet — khối ngoại)
│
├── News_JSON/                    # Output tin tức (JSON)
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
| `Data_Main/` | Data thô (.parquet, .csv) | Code xử lý |
| `System/` | Entry point, biến môi trường | Business logic |

---

## 1.5. Cross-Phase Dependency Map

Các phase không tách biệt — output của phase trước là input của phase sau:

```
Phase 1 ──.parquet──→ Phase 2 ──DataFrame──→ Phase 3 ──.pkl model──→ Phase 4
                                                 ↑
                                          Phase 5 (feed sentiment data)
```

Quy tắc:
- ✅ Phase sau ĐƯỢC ĐỌC output của phase trước
- ❌ Phase trước KHÔNG ĐƯỢC biết phase sau tồn tại (không import ngược)
- ❌ Hai phase KHÔNG ĐƯỢC gọi chéo nhau (Phase 2 không gọi Phase 4)
- ✅ Phase 5 là NGOẠI LỆ — được feed data vào Phase 3 vì chạy xuyên suốt

---

## 1.6. Quy tắc đặt tên

### 1.6.1. Tên File phản ánh chức năng
```
✅ news_scraper.py        → Module cào tin tức từ RSS
✅ data_collector.py      → Module thu thập giá cổ phiếu
✅ ai_client.py           → Module giao tiếp với Gemini API
❌ utils.py               → Quá chung chung, không rõ trách nhiệm
❌ helpers.py              → Tương tự, quá mơ hồ
❌ main.py (trong sub-folder) → Không rõ "main" của cái gì
```

### 1.6.2. Quy ước đặt tên file theo vai trò

| Hậu tố/Pattern | Ý nghĩa | Ví dụ |
|:---|:---|:---|
| `_collector` | Thu thập/cào data từ nguồn ngoài | `data_collector.py` |
| `_cleaner` | Làm sạch, chuẩn hóa data | `data_cleaner.py` |
| `_scraper` | Cào web/RSS cụ thể | `news_scraper.py` |
| `_manager` | Điều phối pipeline (Orchestrator) | `news_manager.py` |
| `_client` | Giao tiếp với API bên ngoài | `ai_client.py` |
| `_renderer` | Render output (HTML, chart, report) | `news_renderer.py` |
| `_config` | Cấu hình, constants | `config.py` |
| `auto_` | Script chạy tự động (scheduled) | `auto_news.py` |
| `test_` | Unit test / Integration test | `test_phase1.py` |

> [!NOTE]
> Mỗi phase có thêm **kiểu module đặc thù riêng** — xem chương tương ứng (Chương 3-7).

### 1.6.3. Package & Import
- Mỗi folder chứa module nên có `__init__.py` (có thể rỗng).
- Import theo đường dẫn tương đối khi ở cùng package, tuyệt đối khi cross-package.
- **KHÔNG** hardcode `sys.path.insert()` trong mỗi file. Centralize vào `Helper/config.py` hoặc dùng `setup.py`/`pyproject.toml`.

---

## 1.7. Các hành vi BỊ CẤM (áp dụng mọi phase)

### 1.7.1. God File (File quá lớn, đa trách nhiệm)
```python
# ❌ TUYỆT ĐỐI KHÔNG — File 26KB chứa nhiều concern
# data_raw_cross_check.py vừa đọc data, vừa tính toán, vừa render chart,
# vừa so sánh, vừa export... tất cả trong 1 file.
```

### 1.7.2. Module trộn lẫn nhiều concern
```python
# ❌ KHÔNG — 1 file trộn 3 trách nhiệm khác nhau:
# 1. Gọi API bên ngoài (networking)
# 2. Parse response data (data processing)
# 3. Render output cho người dùng (presentation)
# → Tách thành: _client.py (networking) + _renderer.py (presentation)
```

### 1.7.3. God Function (>80 dòng)
Một hàm không được vượt quá **~80 dòng** (soft limit). Nếu dài hơn, đó là dấu hiệu cần tách thành hàm con hoặc module riêng.

### 1.7.4. Hardcode đường dẫn tuyệt đối
```python
# ❌ KHÔNG — Hardcode path trong mỗi file
PROJECT_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"

# ✅ ĐÚNG — Centralize vào 1 nơi duy nhất
# Helper/config.py
from Helper.config import PROJECT_DIR, DATA_DIR, NEWS_JSON_DIR
```

### 1.7.5. UI chứa business logic
Module trong `IDE_UI/` KHÔNG ĐƯỢC chứa business logic — chỉ layout, event binding, và hiển thị kết quả. Chi tiết và ví dụ code xem Chương 2 §2.1.

### 1.7.6. Scheduled Script chứa logic phức tạp
Script trong `Auto/` chỉ là **trigger** — delegate MỌI logic sang Manager. KHÔNG ĐƯỢC vượt quá ~50 dòng. Chi tiết và ví dụ code xem Chương 2 §2.2.

---

## 1.8. Giới hạn kích thước (soft limit)

| Đơn vị | Soft limit | Khi vượt, cần review |
|---|---|---|
| Hàm | ~80 dòng | Tách thành sub-function hoặc module mới |
| File/Module | ~300 dòng | Kiểm tra xem module có đang làm > 1 việc không |
| Phase Folder | ~10 file | Kiểm tra xem phase có cần tách sub-step không |

---

## 1.9. Quy tắc Testing

- Tên file test BẮT BUỘC bắt đầu bằng `test_` (ví dụ: `test_phase1.py`, `test_indicators.py`)
- File test đặt **cùng folder** với module được test
- Mỗi phase có **kiểu test đặc thù riêng** — xem chương tương ứng (Chương 3-7)
- Test PHẢI chạy được độc lập (không phụ thuộc vào state của test khác)
- KHÔNG viết test trong file module chính — luôn tách file riêng

---

## 1.10. Khi nào ĐƯỢC PHÉP gộp?

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

## 1.11. Quy tắc "tốt nghiệp" (Promotion Rule)

Một file/hàm ĐƯỢC PHÉP chuyển sang `Helper/` khi và chỉ khi:
1. Có **≥ 2 Phase/Module** khác nhau cần import/sử dụng nó.
2. File đó **KHÔNG chứa** logic đặc thù của phase gốc.

Quy trình:
1. Copy file sang `Helper/`.
2. Xóa file gốc trong Phase Folder.
3. Cập nhật tất cả import path.
4. Chạy test kiểm tra.

---

## 1.12. Checklist trước khi commit

Trước khi commit bất kỳ file `.py` nào, kiểm tra:

- [ ] File chỉ phục vụ **1 trách nhiệm duy nhất**? (Thu thập ≠ Xử lý ≠ Render ≠ UI)
- [ ] Tên file **phản ánh rõ chức năng** (không phải `utils.py`, `helpers.py`, `main.py`)?
- [ ] File nằm đúng **Phase Folder** hoặc thư mục chức năng phù hợp?
- [ ] **Không hardcode** đường dẫn tuyệt đối? (dùng `Helper/config.py`)
- [ ] Không có hàm nào **vượt quá ~80 dòng**?
- [ ] File **không vượt quá ~300 dòng** (soft limit)?
- [ ] Các dependencies đi **đúng chiều** (§1.5 + chương phase tương ứng)?
- [ ] Có `__init__.py` trong folder chứa module?

---

> **Ghi nhớ:** Nếu bạn phải giải thích "module này làm gì" bằng từ **"và"** (ví dụ: "module này cào tin **và** gọi AI **và** render HTML"), thì module đó đang vi phạm SRP và cần được tách ra.

---
---

# CHƯƠNG 2: HỆ THỐNG (UI / Auto / System)

> Quy tắc cho các module hệ thống chạy xuyên suốt: Giao diện, Scripts tự động, Entry point.

---

## 2.1. IDE_UI/ — Giao diện Desktop (PyQt6)

### Dependency Flow
```
IDE_UI/ → Manager (của phase tương ứng) → hiển thị kết quả
```

### Quy tắc
- ✅ UI chỉ làm **layout + event binding + hiển thị kết quả**
- ❌ UI KHÔNG ĐƯỢC chứa business logic

```python
# ❌ KHÔNG — File UI tự gọi API, xử lý data
class CenterWorkspace(QWidget):
    def on_click(self):
        response = requests.get("https://api.example.com/data")
        df = pd.DataFrame(response.json())
        # ... 50 dòng xử lý ...
        self.display(result)

# ✅ ĐÚNG — UI chỉ gọi Manager, hiển thị kết quả
class CenterWorkspace(QWidget):
    def on_click(self):
        result = SomeManager.process()
        self.display(result)
```

### Cấu trúc thư mục
```
IDE_UI/
├── main_window.py            ← Cửa sổ chính, dock layout
├── center_workspace.py       ← Workspace trung tâm
├── left_panel.py             ← Panel trái (navigation)
├── right_panel.py            ← Panel phải (system log)
└── custom_title_bar.py       ← Title bar tùy chỉnh
```

---

## 2.2. Auto/ — Scripts tự động (Task Scheduler)

### Dependency Flow
```
Task Scheduler (Windows) → auto_*.py → Manager.run_pipeline() → ghi log
```

### Quy tắc
- Script trong Auto/ chỉ là **trigger** — delegate MỌI logic sang Manager
- PHẢI có error handling bao quanh `main()`
- PHẢI ghi log ra file (console output mất khi chạy ngầm)
- KHÔNG ĐƯỢC vượt quá **~50 dòng**
- Tên file BẮT BUỘC bắt đầu bằng `auto_`

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

---

## 2.3. System/ — Entry Point (Warden.py)

### Quy tắc

Warden.py chỉ được phép:
- ✅ Import và khởi tạo `QApplication`
- ✅ Gọi `MainWindow()`
- ✅ Setup `sys.path` (nếu cần)

Warden.py KHÔNG ĐƯỢC:
- ❌ Chứa business logic
- ❌ Import trực tiếp các module Phase (phải qua `IDE_UI/`)
- ❌ Vượt quá ~50 dòng

---

## 2.4. Dependency Flow chung (Hệ thống)

> *Ví dụ minh họa từ module News. Pattern tương tự áp dụng cho mọi module nghiệp vụ khác trong dự án.*

```
Auto/ (Scheduler)  →  Manager  →  Collector / Scraper
                         ↓
                    Client (API)
                         ↓
                    Renderer (Output)

IDE_UI/  →  Manager  →  (same as above)

Mũi tên = "được phép gọi". Ngược chiều mũi tên = VI PHẠM.
```

Cụ thể:
- ✅ `auto_news.py` ĐƯỢC gọi `NewsManager`
- ✅ `NewsManager` ĐƯỢC gọi `news_scraper`, `ai_client`, `news_renderer`
- ✅ `IDE_UI/` ĐƯỢC gọi `NewsManager` để lấy data
- ❌ `news_scraper` KHÔNG ĐƯỢC gọi ngược `NewsManager`
- ❌ `ai_client` KHÔNG ĐƯỢC import `IDE_UI` hoặc `news_renderer`
- ❌ `Helper/config.py` KHÔNG ĐƯỢC import bất kỳ module nghiệp vụ nào (nó là config thuần)

---
---

# CHƯƠNG 3: PHASE 1 — CHUẨN BỊ DATA

> **Mô hình: ETL (Extract → Transform → Load)**
> **Thời lượng:** 1 tháng | **Tech stack:** vnstock, requests, pandas, Scikit-Learn

---

## 3.1. Dependency Flow

```
Collector (cào data) → Cleaner (làm sạch) → Validator (kiểm tra chất lượng)
      ↓                                              ↓
 API bên ngoài                                  Data_Main/ (.parquet)
 (vnstock, FireAnt)                             [immutable sau khi cào]
```

Quy tắc:
- ✅ `Collector` ĐƯỢC gọi API bên ngoài (vnstock, FireAnt)
- ✅ `Cleaner` ĐƯỢC đọc output từ `Collector`
- ✅ `Validator` ĐƯỢC đọc output từ `Cleaner` và `Collector` (để so sánh)
- ❌ `Collector` KHÔNG ĐƯỢC gọi `Cleaner` hoặc `Validator`
- ❌ `Cleaner` KHÔNG ĐƯỢC gọi API (chỉ xử lý data đã có)
- ❌ Không module nào ĐƯỢC modify file trong `Data_Main/` sau khi cào xong

---

## 3.2. Cấu trúc thư mục

```
Phase 1/
├── 1.1_Data_Collector/
│   ├── data_collector.py             ← Cào data từ vnstock + FireAnt
│   ├── config.json                   ← API token, start_date
│   └── test_phase1.py                ← Test data quality
│
└── 1.2_Data_Cleaner/                 ← [CHỜ TRIỂN KHAI]
    ├── data_cleaner.py               ← Làm sạch bằng Scikit-Learn
    ├── data_validator.py             ← Validate chất lượng data
    └── data_comparator.py            ← So sánh vnstock vs FireAnt
```

---

## 3.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở §1.6.2, Phase 1 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_validator` | Validate chất lượng data (null, range, count) | `data_validator.py` |
| `_comparator` | So sánh data giữa các nguồn | `data_comparator.py` |

---

## 3.4. Error Handling

**Chiến lược: Retry + Resume**

Cào data từ ~1800 mã chứng khoán, bị gián đoạn là chuyện bình thường. Code PHẢI:
- Kiểm tra file đã tồn tại trước khi cào (resume mode)
- Retry khi API lỗi tạm thời (timeout, rate limit)
- Log chi tiết mã nào thành công/thất bại
- KHÔNG crash toàn bộ batch vì 1 mã lỗi

---

## 3.5. Config

`config.json` — cấu hình không chứa secrets:
```json
{
    "START_DATE": "2012-01-01",
    "SYMBOLS_FILE": "symbols_list.csv"
}
```

> [!WARNING]
> API keys và tokens (như `FIREANT_BEARER_TOKEN`) PHẢI nằm trong `System/.env`, KHÔNG được để trong `config.json`. Xem §1.4.

---

## 3.6. Testing

Kiểu test: **Data Quality Check**
- Kiểm tra null count trong DataFrame
- Kiểm tra date range (có đủ lịch sử không?)
- Kiểm tra row count giữa vnstock vs FireAnt
- So sánh giá từ 2 nguồn (chênh lệch có hợp lý không?)

---

## 3.7. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.parquet` |
| **Vị trí** | `Data_Main/From_vnstock/`, `Data_Main/From_FireAnt/` |
| **Tên file** | `{SYMBOL}_historical_{source}.parquet` |
| **Tính chất** | **Immutable** — không sửa sau khi cào xong |
| **Ai đọc?** | Phase 2 (tính indicators), Phase 3 (load vào ML) |

> [!IMPORTANT]
> **Constraint từ Planning:** BẮT BUỘC dùng **giá điều chỉnh**. Không bỏ qua các mã đã chết (delisted).

---
---

# CHƯƠNG 4: PHASE 2 — THUẬT TOÁN

> **Mô hình: Pure Transform (tính toán thuần)**
> **Thời lượng:** 3 tháng | **Tech stack:** TA-lib, pandas-ta

---

## 4.1. Dependency Flow

```
Data Reader (đọc parquet từ Phase 1) → Indicator Calculator (tính TA) → Validator (kiểm tra công thức)
                                                                              ↓
                                                                       DataFrame có features
                                                                       (output cho Phase 3)
```

Quy tắc:
- ✅ `Calculator` ĐƯỢC đọc output từ Phase 1 (`Data_Main/`)
- ✅ `Validator` ĐƯỢC kiểm tra output của `Calculator`
- ❌ `Calculator` KHÔNG ĐƯỢC gọi API, ghi file, hiển thị UI
- ❌ `Calculator` KHÔNG ĐƯỢC biết Phase 3 tồn tại (không import)
- ❌ Module trong Phase 2 KHÔNG ĐƯỢC modify parquet gốc của Phase 1

---

## 4.2. Cấu trúc thư mục

```
Phase 2/
├── 2.1_Technical_Indicators/         ← [CHỜ TRIỂN KHAI]
│   ├── indicator_calculator.py           ← Tính SMA, RSI, MACD, Bollinger...
│   ├── indicator_validator.py            ← So sánh output với giá trị đã biết
│   └── test_indicators.py               ← Test mathematical correctness
│
└── 2.2_Feature_Store/                ← [CHỜ TRIỂN KHAI]
    └── feature_store.py                  ← Lưu trữ features đã tính (optional)
```

---

## 4.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở §1.6.2, Phase 2 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_calculator` | Tính toán indicator thuần (pure function) | `indicator_calculator.py` |
| `_validator` | Kiểm tra correctness của công thức | `indicator_validator.py` |
| `_store` | Lưu trữ features đã tính | `feature_store.py` |

---

## 4.4. Error Handling

**Chiến lược: Strict — Crash ngay**

Sai 1 con số = sai cả model. Phase 2 là nền tảng toán học, PHẢI:
- KHÔNG dùng try/catch để nuốt lỗi tính toán
- Để exception bay lên caller
- Dùng `assert` để kiểm tra pre-condition / post-condition

```python
# ✅ ĐÚNG — Strict, crash nếu sai
def compute_rsi(series, period=14):
    assert len(series) >= period, f"Cần ít nhất {period} điểm dữ liệu"
    # ... tính toán ...
    assert 0 <= result <= 100, f"RSI ngoài khoảng [0,100]: {result}"
    return result
```

---

## 4.5. Constraint đặc thù

- Mọi hàm tính toán PHẢI là **pure function**: cùng input → cùng output, KHÔNG side effect
- KHÔNG gọi API, KHÔNG ghi file, KHÔNG đọc config ngoài tham số đầu vào
- KHÔNG dùng biến global

---

## 4.6. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | Python modules chứa pure functions — không lưu file output riêng |
| **Tính chất** | Được Phase 3 `feature_builder.py` **import trực tiếp** để tính features |
| **Ai dùng?** | Phase 3 (`from Phase2 import indicator_calculator`) |

> [!NOTE]
> Phase 2 khác các phase khác: output không phải file data mà là **module code tái sử dụng**. `feature_builder.py` (Phase 3) sẽ `import` các hàm tính toán từ Phase 2 để tính technical indicators trên raw DataFrame từ Phase 1.

---
---

# CHƯƠNG 5: PHASE 3 — ML TRAINING

> [!WARNING]
> **PHASE LÕI CỦA DỰ ÁN.** Xem lại toàn bộ chương này khi chuẩn bị bắt đầu Phase 3.

> **Mô hình: Arena / Tournament (4 tầng)**
> **Thời lượng:** 6 tháng | **Tech stack:** PyCaret, XGBoost, LightGBM, CatBoost

---

## 5.1. Kiến trúc 4 tầng

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TẦNG 0: CONFIG                              │
│                   (Read-only, con người viết)                      │
│                                                                     │
│  training_config.yaml          experiment_registry.json             │
│  ┌─────────────────────┐       ┌────────────────────────┐          │
│  │ target: 'signal'    │       │ experiments:            │          │
│  │ fold_strategy: ts   │       │   - id: exp_001         │          │
│  │ fold: 5             │       │     date: 2027-01-15    │          │
│  │ context: 'long'     │       │     config: long_v1     │          │
│  │ models:             │       │     status: completed   │          │
│  │   - xgboost         │       │     best_model: blend   │          │
│  │   - lightgbm        │       │     metrics: {...}      │          │
│  │   - catboost         │       └────────────────────────┘          │
│  │ blend: true         │                                            │
│  │ optimize: 'AUC'     │                                            │
│  └─────────────────────┘                                            │
├─────────────────────────────────────────────────────────────────────┤
│                     TẦNG 1: DATA PREP (Input)                      │
│                                                                     │
│  data_loader.py         feature_builder.py      target_builder.py  │
│  ┌───────────────┐      ┌──────────────────┐    ┌───────────────┐  │
│  │ Đọc parquet   │  →   │ Tạo features từ  │ →  │ Tạo biến mục │  │
│  │ từ Phase 1-2  │      │ TA indicators    │    │ tiêu (signal)│  │
│  │ + News data   │      │ + Sentiment      │    │ buy/sell/hold│  │
│  └───────────────┘      └──────────────────┘    └───────────────┘  │
│                                                         ↓          │
│                                                   DataFrame       │
│                                                   (sẵn sàng)      │
├─────────────────────────────────────────────────────────────────────┤
│                     TẦNG 2: ARENA (Core PyCaret)                   │
│                 ⚔️ "Sàn đấu" — module DUY NHẤT gọi PyCaret ⚔️     │
│                                                                     │
│  arena_runner.py                      resource_monitor.py          │
│  ┌──────────────────────────────┐     ┌────────────────────────┐   │
│  │ 1. exp.setup(df, config)     │     │ Giám sát RAM + CPU     │   │
│  │ 2. exp.compare_models()      │  ←  │ Cảnh báo nếu vượt      │   │
│  │ 3. exp.tune_model() × top N  │     │ ngưỡng cho phép        │   │
│  │ 4. exp.blend_models()        │     └────────────────────────┘   │
│  │ 5. exp.finalize_model()      │                                   │
│  └──────────────────────────────┘                                   │
│                    ↓                                                │
│              Trained Model + Raw Metrics                           │
├─────────────────────────────────────────────────────────────────────┤
│                  TẦNG 3: OUTPUT (Evaluation + Export)               │
│                                                                     │
│  metrics_collector.py     report_generator.py    model_exporter.py │
│  ┌───────────────────┐    ┌──────────────────┐   ┌──────────────┐  │
│  │ Thu thập metrics  │ →  │ Tạo báo cáo so   │   │ Lưu model    │  │
│  │ từ Arena results  │    │ sánh giữa các    │   │ .pkl/.joblib │  │
│  │ AUC, F1, Recall  │    │ experiments      │   │ → Models/    │  │
│  └───────────────────┘    └──────────────────┘   └──────────────┘  │
│                                                         ↓          │
│                                                  Phase 4 đọc      │
│                                                  model từ đây     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5.2. Dependency Flow

```
Config ─────────────────────────────────────┐
   │                                         │
   ↓                                         │
Data Prep ──→ DataFrame (output)            │
                  │                          │
                  ↓                          ↓
              Arena Runner ←── reads Config + DataFrame
                  │
                  ↓
              Output Layer (Metrics → Report → Export)
                  │
                  ↓
              Models/ folder ──→ Phase 4 Backtester đọc
```

---

## 5.3. Cấu trúc thư mục

```
Phase 3/
├── 3.0_Config/                           # TẦNG 0 — CONFIG
│   ├── training_config.yaml                  # Hyperparameters, fold, context
│   └── experiment_registry.json              # Lịch sử tất cả experiments
│
├── 3.1_Data_Prep/                        # TẦNG 1 — DATA PREP
│   ├── data_loader.py                        # Đọc parquet từ Phase 1
│   ├── feature_builder.py                    # Tạo features (TA + Sentiment)
│   └── target_builder.py                     # Tạo biến mục tiêu (buy/sell)
│
├── 3.2_Arena/                            # TẦNG 2 — ARENA (PyCaret core)
│   ├── arena_runner.py                       # DUY NHẤT gọi PyCaret APIs
│   └── resource_monitor.py                   # Giám sát RAM + thời gian
│
├── 3.3_Output/                           # TẦNG 3 — OUTPUT
│   ├── metrics_collector.py                  # Thu thập AUC, F1, Recall...
│   ├── report_generator.py                   # Báo cáo so sánh experiments
│   └── model_exporter.py                     # Lưu/Load model (.pkl)
│
└── Models/                               # Folder chứa model artifacts
    ├── exp_001_blend_long_v1.pkl
    └── exp_002_xgboost_mid_v1.pkl
```

---

## 5.4. Kiểu module đặc thù và hành vi chi tiết

Ngoài các hậu tố chung ở §1.6.2, Phase 3 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_loader` | Đọc data từ phase trước | `data_loader.py` |
| `_builder` | Xây dựng/tạo mới (features, target) | `feature_builder.py`, `target_builder.py` |
| `arena_runner` | Module DUY NHẤT chạy PyCaret arena | `arena_runner.py` |
| `_monitor` | Giám sát tài nguyên (RAM, CPU, thời gian) | `resource_monitor.py` |
| `_collector` (metrics) | Thu thập và chuẩn hóa metrics | `metrics_collector.py` |
| `_generator` | Tạo báo cáo so sánh | `report_generator.py` |
| `_exporter` | Lưu/Load model artifacts | `model_exporter.py` |

### Hành vi chi tiết từng module

### TẦNG 0: CONFIG (Read-only)

**`training_config.yaml`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm** | Lưu trữ TẤT CẢ tham số cần thiết cho 1 experiment |
| **Ai đọc?** | `arena_runner.py`, `data_loader.py`, `feature_builder.py` |
| **Ai ghi?** | Chỉ CON NGƯỜI — không module nào được ghi vào đây |
| **Khi nào thay đổi?** | Khi chuyển context (dài hạn → trung hạn), khi thử hyperparameters mới |

**`experiment_registry.json`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm** | Ghi lại lịch sử TẤT CẢ experiments đã chạy (nhật ký sàn đấu) |
| **Ai đọc?** | `report_generator.py` (để so sánh giữa các experiments) |
| **Ai ghi?** | `arena_runner.py` (sau khi hoàn thành 1 experiment) |
| **Khi nào thay đổi?** | Sau mỗi lần chạy Arena |

> [!IMPORTANT]
> `experiment_registry.json` là ngoại lệ duy nhất trong tầng Config được ghi bởi code. Nó là **nhật ký**, không phải config input.

### TẦNG 1: DATA PREP (Input)

**`data_loader.py`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Đọc parquet từ `Data_Main/` (Phase 1) và trả về raw DataFrame |
| **Input** | Đường dẫn tới `Data_Main/From_vnstock/`, `Data_Main/From_FireAnt/` |
| **Output** | `pd.DataFrame` — data thô, chưa xử lý |
| **KHÔNG ĐƯỢC** | Tạo features, tính indicator, gọi API, modify data gốc |
| **Khi nào thay đổi?** | Chỉ khi cấu trúc data thô từ Phase 1 thay đổi |

**`feature_builder.py`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Tạo tất cả features cần thiết cho ML từ raw DataFrame |
| **Input** | Raw DataFrame từ `data_loader` + config (biết cần features nào) |
| **Output** | DataFrame đã có đầy đủ features (TA indicators, sentiment scores...) |
| **KHÔNG ĐƯỢC** | Train model, evaluate, gọi PyCaret, đọc file trực tiếp |
| **Khi nào thay đổi?** | Khi thêm/bớt technical indicators (Phase 2), khi tích hợp News data (Phase 5) |

**`target_builder.py`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Tạo biến mục tiêu (target variable) — tín hiệu mua/bán |
| **Input** | Featured DataFrame + config (biết context: dài hạn hay trung hạn) |
| **Output** | DataFrame có thêm cột `signal` (1 = buy, 0 = hold, -1 = sell) |
| **KHÔNG ĐƯỢC** | Tạo features, train model, đọc file trực tiếp |
| **Khi nào thay đổi?** | Khi thay đổi strategy/context (dài hạn ↔ trung hạn ↔ lướt sóng) |

> [!TIP]
> Tách riêng `target_builder.py` khỏi `feature_builder.py` là **cực kỳ quan trọng**. Planning nói rõ: *"Nếu thay đổi context từ dài hạn sang trung hạn, cần train lại model."* — Khi chuyển context, chỉ `target_builder` thay đổi, còn features giữ nguyên. Đây chính là SRP: **1 lý do thay đổi duy nhất**.

### TẦNG 2: ARENA (Core PyCaret)

**`arena_runner.py` ⚔️**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Là module **DUY NHẤT** trong toàn dự án được phép gọi PyCaret APIs |
| **Input** | DataFrame (từ Tầng 1) + Config (từ Tầng 0) |
| **Output** | Trained model object + raw metrics dict |
| **KHÔNG ĐƯỢC** | Đọc file data trực tiếp, tạo features, render báo cáo, lưu model ra disk |
| **Khi nào thay đổi?** | Chỉ khi PyCaret API thay đổi (upgrade version) hoặc thêm bước mới vào arena |

> [!WARNING]
> **Tại sao `arena_runner.py` phải là module DUY NHẤT gọi PyCaret?**
> PyCaret quản lý state nội bộ (experiment session, preprocessor pipeline, CV splits...). Nếu nhiều file cùng gọi PyCaret, state sẽ conflict → kết quả không reproducible. Tập trung PyCaret vào 1 file = kiểm soát state = kết quả tin cậy.

**`resource_monitor.py`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Giám sát RAM + CPU + thời gian trong quá trình training |
| **Input** | Được `arena_runner` gọi trước/sau mỗi bước |
| **Output** | Log cảnh báo nếu vượt ngưỡng + resource usage dict |
| **KHÔNG ĐƯỢC** | Gọi PyCaret, đọc data, can thiệp vào training |
| **Khi nào thay đổi?** | Khi thay đổi ngưỡng RAM/CPU cho phép |

### TẦNG 3: OUTPUT (Evaluation + Export)

**`metrics_collector.py`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Nhận raw metrics từ Arena, chuẩn hóa và lưu trữ có cấu trúc |
| **Input** | Metrics dict từ `arena_runner` |
| **Output** | Structured metrics (JSON/DataFrame) + ghi vào `experiment_registry.json` |
| **KHÔNG ĐƯỢC** | Gọi PyCaret, train model, render báo cáo visual |

**`report_generator.py`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Tạo báo cáo so sánh giữa các experiments |
| **Input** | `experiment_registry.json` (lịch sử experiments) |
| **Output** | Báo cáo markdown/HTML so sánh performance giữa các lần chạy |
| **KHÔNG ĐƯỢC** | Train model, gọi PyCaret, modify metrics |
| **Khi nào thay đổi?** | Khi muốn thêm loại chart/biểu đồ so sánh mới |

**`model_exporter.py`**
| Thuộc tính | Mô tả |
|---|---|
| **Trách nhiệm DUY NHẤT** | Lưu model ra disk (.pkl/.joblib) và load model từ disk |
| **Input** | Trained model object từ Arena |
| **Output** | File `.pkl` trong `Models/` folder |
| **KHÔNG ĐƯỢC** | Train model, evaluate, gọi PyCaret |
| **Ai đọc output?** | Phase 4 Backtester — load model để mô phỏng đầu tư |

---

## 5.5. Error Handling

**Chiến lược: Graceful + Checkpoint**

Training lâu (hàng giờ), crash = mất hết. Code PHẢI:
- Log progress sau mỗi bước chính (setup, compare, tune, blend)
- Checkpoint experiment state vào `experiment_registry.json`
- Catch exception ở tầng `arena_runner`, log đầy đủ rồi mới re-raise
- KHÔNG nuốt lỗi im lặng

---

## 5.6. Quy tắc Dependency Phase 3 — Tóm gọn

```
✅ ĐƯỢC PHÉP:
   arena_runner  → data_loader, feature_builder, target_builder (Tầng 1)
   arena_runner  → resource_monitor (giám sát)
   arena_runner  → reads training_config.yaml (Tầng 0)
   metrics_collector → reads arena results + writes experiment_registry
   report_generator  → reads experiment_registry
   model_exporter    → receives model from arena_runner
   Phase 4           → model_exporter.load_model()

❌ BỊ CẤM:
   data_loader       ✗ KHÔNG ĐƯỢC gọi feature_builder hoặc arena_runner
   feature_builder   ✗ KHÔNG ĐƯỢC gọi ngược data_loader
   target_builder    ✗ KHÔNG ĐƯỢC gọi feature_builder
   arena_runner      ✗ KHÔNG ĐƯỢC lưu model ra disk (delegate cho exporter)
   arena_runner      ✗ KHÔNG ĐƯỢC render báo cáo (delegate cho report_generator)
   resource_monitor  ✗ KHÔNG ĐƯỢC can thiệp training (chỉ quan sát + cảnh báo)
   metrics_collector ✗ KHÔNG ĐƯỢC gọi PyCaret
   report_generator  ✗ KHÔNG ĐƯỢC modify metrics
   training_config   ✗ KHÔNG ĐƯỢC import bởi bất kỳ module nào (chỉ đọc file)
```

---

## 5.7. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.pkl` / `.joblib` (model) + `.json` (metrics + registry) |
| **Vị trí** | `Phase 3/Models/` |
| **Tên file** | `exp_{ID}_{model_type}_{context}_{version}.pkl` |
| **Ai đọc?** | Phase 4 Backtester qua `model_exporter.load_model()` |

> [!IMPORTANT]
> **Constraints từ Planning:**
> - BẮT BUỘC dùng **Time Series Split** (Walk-forward validation)
> - Xem xét thời gian và **RAM tiêu thụ** khi training
> - Xem xét dùng **`blend_models`** để tránh sai số
> - Nếu thay đổi context (dài hạn → trung hạn), cần **train lại** model

---
---

# CHƯƠNG 6: PHASE 4 — CHIẾN TRƯỜNG GIẢ LẬP

> **Mô hình: Simulation (mô phỏng event loop)**
> **Thời lượng:** 6 tháng | **Tech stack:** Custom backtester

---

## 6.1. Dependency Flow

```
Model Loader ← đọc .pkl từ Phase 3
      ↓
Strategy Builder ← đọc sim_config.yaml
      ↓
Simulator (event loop) → Trade Engine (thực thi giao dịch)
      ↓                          ↓
 Equity Curve              Trade Log
      ↓                          ↓
Report Generator (so sánh vs Buy & Hold)
```

Quy tắc:
- ✅ `Model Loader` ĐƯỢC đọc `.pkl` từ `Phase 3/Models/`
- ✅ `Simulator` ĐƯỢC gọi `Trade Engine` để thực thi từng giao dịch
- ✅ `Report Generator` ĐƯỢC đọc trade log + equity curve
- ❌ `Simulator` KHÔNG ĐƯỢC gọi PyCaret hoặc train model
- ❌ `Trade Engine` KHÔNG ĐƯỢC quyết định chiến lược (chỉ thực thi)
- ❌ `Strategy Builder` KHÔNG ĐƯỢC biết kết quả tương lai (no look-ahead bias)

---

## 6.2. Cấu trúc thư mục

```
Phase 4/                                  ← [CHỜ TRIỂN KHAI]
├── 4.0_Config/
│   └── sim_config.yaml                       # Vốn, phí, trượt giá, thời gian stress test
│
├── 4.1_Backtester/
│   ├── model_loader.py                       # Load model từ Phase 3
│   ├── strategy_builder.py                   # Xây dựng chiến lược từ model signal
│   ├── simulator.py                          # Event loop mô phỏng
│   ├── trade_engine.py                       # Thực thi giao dịch (trừ phí, trượt giá)
│   └── backtest_reporter.py                  # Báo cáo equity curve, win rate, drawdown
│
└── Results/
    └── backtest_{date}_{strategy}.json       # Kết quả từng lần chạy
```

---

## 6.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở §1.6.2, Phase 4 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_loader` | Load model/data từ phase trước | `model_loader.py` |
| `_strategy` / `_builder` | Xây dựng chiến lược giao dịch | `strategy_builder.py` |
| `_simulator` | Event loop mô phỏng | `simulator.py` |
| `_engine` | Thực thi giao dịch đơn lẻ | `trade_engine.py` |
| `_reporter` | Tạo báo cáo kết quả backtest | `backtest_reporter.py` |

---

## 6.4. Error Handling

**Chiến lược: Zero Tolerance**

Sai 1 giao dịch = sai toàn bộ equity curve. Code PHẢI:
- KHÔNG dùng try/catch để bỏ qua lỗi giao dịch
- Assert balance đủ trước khi mua
- Assert giá hợp lệ trước khi tính P&L
- Crash ngay nếu data có lỗ hổng (missing dates, NaN price)

---

## 6.5. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.json` (trade log, metrics) + charts |
| **Vị trí** | `Phase 4/Results/` |
| **Ai đọc?** | Con người (review kết quả), Phase 5 (so sánh win rate có/không news) |

> [!IMPORTANT]
> **Constraints từ Planning:**
> - PHẢI **trừ chi phí giao dịch** (realistic)
> - PHẢI **tính trượt giá** (slippage)
> - PHẢI **Stress Test** model bằng năm 2022 (thị trường sụp)
> - PHẢI **so sánh** lợi nhuận với chiến lược Buy and Hold VN-Index

---
---

# CHƯƠNG 7: PHASE 5 — TÍCH HỢP NEWS

> **Mô hình: Pipeline xuyên suốt (Scrape → Score → Integrate)**
> **Thời lượng:** Xuyên suốt (Through) | **Tech stack:** feedparser, Gemini AI, NLP

---

## 7.1. Dependency Flow

```
Scraper (cào RSS) → Manager (điều phối) → AI Client (Gemini) → Renderer (HTML output)
                         ↓
                    News_JSON/ (lưu trữ)
                         ↓
                 Sentiment Scorer ← [CHỜ TRIỂN KHAI]
                         ↓
                 Anchor Builder (tạo điểm neo cho BCTC) ← [CHỜ TRIỂN KHAI]
                         ↓
                 Feed vào Phase 3 (feature_builder.py đọc sentiment)
```

Quy tắc:
- ✅ `Manager` ĐƯỢC gọi `Scraper`, `AI Client`, `Renderer`
- ✅ `Sentiment Scorer` ĐƯỢC đọc `News_JSON/`
- ✅ Phase 3 `feature_builder.py` ĐƯỢC đọc sentiment output
- ❌ `Scraper` KHÔNG ĐƯỢC gọi ngược `Manager`
- ❌ `AI Client` KHÔNG ĐƯỢC import `IDE_UI` hoặc `Renderer`
- ❌ `Sentiment Scorer` KHÔNG ĐƯỢC modify News JSON gốc

---

## 7.2. Cấu trúc thư mục

```
Main Scripts/News/
├── news_scraper.py           ← Cào RSS từ 4 nguồn báo
├── news_manager.py           ← Điều phối pipeline (backfill + cào + lưu)
├── ai_client.py              ← Gọi Gemini API, trả về JSON thuần ← [CẦN TÁCH TỪ gemini_ai.py]
├── news_renderer.py          ← Render HTML output ← [CẦN TÁCH TỪ gemini_ai.py]
├── sentiment_scorer.py       ← Chấm điểm sentiment ← [CHỜ TRIỂN KHAI]
└── anchor_builder.py         ← Tạo điểm neo news vs BCTC ← [CHỜ TRIỂN KHAI]
```

---

## 7.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở §1.6.2, Phase 5 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_scorer` | Chấm điểm (sentiment, quality) | `sentiment_scorer.py` |
| `_builder` | Xây dựng cấu trúc data (điểm neo) | `anchor_builder.py` |

---

## 7.4. Error Handling

**Chiến lược: Resilient — 1 nguồn lỗi không crash toàn bộ**

Cào tin tức từ 4+ nguồn báo, 1 nguồn die là chuyện bình thường. Code PHẢI:
- Catch exception cho TỪNG nguồn, log rồi tiếp tục nguồn tiếp theo
- KHÔNG crash toàn bộ batch vì 1 RSS feed lỗi
- Tạo file rỗng nếu không cào được bài nào (đánh dấu "đã xử lý")

```python
# ✅ ĐÚNG — Resilient, skip bad source
for url in urls_to_fetch:
    try:
        feed = feedparser.parse(url)
        # ... xử lý ...
    except Exception as e:
        debug_logs.append(f"❌ [{url}] Lỗi: {e}")
        continue  # Skip, không crash
```

---

## 7.5. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.json` (News JSON) + HTML (summary) |
| **Vị trí** | `News_JSON/` |
| **Tên file** | `News_{dd}_{mm}_{yy}.json` |
| **Ai đọc?** | Phase 3 `feature_builder.py` (sentiment data), IDE_UI (hiển thị), Phase 4 (so sánh win rate) |

> [!IMPORTANT]
> **Constraints từ Planning:**
> - Làm **càng sớm càng tốt** để tích lũy data cho training
> - Tin tức ở VN **luôn bị thao túng** — be careful
> - Data news theo **ngày** nhưng BCTC theo **quý/năm** → cần tạo **điểm neo** (anchor)
> - Sử dụng **NLP** cho sentiment scoring
> - Phase 4 sẽ chạy lại kèm news data → so sánh win rate **có news vs không news**

---

## 7.6. Ví dụ thực tế

### Hiện trạng tốt: news_scraper.py + news_manager.py ✅
```
news_scraper.py       ← Thu thập RSS (1 concern) ✅
news_manager.py       ← Điều phối pipeline (1 concern) ✅
```

### Cần refactor: gemini_ai.py ❌
```
Hiện tại: 1 file trộn API call + HTML rendering

Đề xuất tách:
├── ai_client.py          ← Chỉ gọi Gemini API, trả về JSON thuần
└── news_renderer.py      ← Chỉ nhận JSON, render HTML output
```
