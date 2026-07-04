# E_CYBER-FINANCIAL STANDARD (EF-S)
## EF-S-00: DATA STRUCTURE

### Nguyên tắc Single Responsibility Principle (SRP)

> **Kim chỉ nam cho toàn bộ công cuộc phát triển và bảo trì dự án E_CYBER-FINANCIAL.**

---

## 1. Quy tắc vàng

> **1 File `.py` = 1 Module/Concern = 1 Trách nhiệm duy nhất.**

Nếu bạn đang viết hàm thứ 5 mà hàm đó phục vụ một "lý do thay đổi" khác với 4 hàm trước, hãy dừng lại và tạo file mới.

### 1.1. Triết lý "One Reason to Change"
SRP không có nghĩa là "1 file chỉ được có 1 hàm" hay "1 file chỉ làm 1 hành động". SRP được định nghĩa là **"Một module chỉ nên có duy nhất MỘT LÝ DO ĐỂ THAY ĐỔI"**.
- Ví dụ: Module `news_scraper.py` chứa nhiều hàm (config RSS, parse feed, lọc theo ngày) nhưng tất cả phục vụ chung một lý do duy nhất: *Thu thập tin tức thô từ RSS*. Nếu logic AI thay đổi, file này không bị ảnh hưởng. Nó tuân thủ tuyệt đối SRP.

### 1.2. High Cohesion vs Low Coupling (Chống phân mảnh - Defragmentation)
Quá trình tách God File không phải là băm nát code thành hàng trăm mảnh vỡ vụn (Fragmentation). Đó là quá trình **Chống phân mảnh (Defragmentation)**:
- **High Cohesion (Độ gắn kết cao):** Gom những hàm có chung nghiệp vụ (ví dụ: cào RSS, parse HTML, lọc thời gian) vào chung một module vừa đủ lớn (như `news_scraper.py`) để chúng phối hợp nhịp nhàng.
- **Low Coupling (Độ phụ thuộc thấp):** Tách bạch rõ ràng ranh giới giữa Thu thập (`scraper`), Xử lý (`manager`), và Trình bày (`renderer`) để code không dẫm chân lên nhau.

---

## 2. Cấu trúc thư mục chuẩn (Phase-first)

Dự án E_CYBER-FINANCIAL tổ chức theo **Phase** — tương ứng với lộ trình 19 tháng. Mỗi Phase đại diện cho một giai đoạn phát triển độc lập.

```
E_CYBER-FINANCIAL/
├── Main Scripts/
│   ├── Phase 1/                  # CHUẨN BỊ DATA (tháng 1)
│   │   ├── 1.1_Data_Collector/       (Cào data giá cổ phiếu)
│   │   ├── 1.2_Data_Cleaner/         (Làm sạch data — Scikit-Learn)
│   │   └── ...
│   │
│   ├── Phase 2/                  # THUẬT TOÁN (tháng 2-4)
│   │   ├── 2.1_Technical_Indicators/ (TA-lib, pandas-ta)
│   │   └── ...
│   │
│   ├── Phase 3/                  # ML TRAINING (tháng 5-10)
│   │   ├── 3.1_PyCaret_Arena/        (Sàn đấu model)
│   │   ├── 3.2_Model_Config/         (Hyperparameters, split config)
│   │   └── ...
│   │
│   ├── Phase 4/                  # CHIẾN TRƯỜNG GIẢ LẬP (tháng 11-16)
│   │   ├── 4.1_Backtester/           (Mô phỏng đầu tư)
│   │   └── ...
│   │
│   ├── News/                     # Module tin tức (Phase 5 — xuyên suốt)
│   │   ├── news_scraper.py           (Cào RSS)
│   │   ├── news_manager.py           (Điều phối pipeline)
│   │   ├── ai_client.py              (Gọi API Gemini)
│   │   └── news_renderer.py          (Render HTML output)
│   │
│   ├── Auto/                     # Scripts tự động (Task Scheduler)
│   │   ├── auto_news.py              (Trigger cào tin 21:00 hàng ngày)
│   │   └── auto_sync.py              (Auto git push)
│   │
│   └── IDE_UI/                   # Giao diện Desktop (PyQt6)
│       ├── main_window.py            (Cửa sổ chính)
│       ├── center_workspace.py       (Workspace)
│       ├── left_panel.py             (Panel trái)
│       ├── right_panel.py            (Panel phải — system log)
│       └── custom_title_bar.py       (Title bar tùy chỉnh)
│
├── Data_Main/                    # Data thô (Read-only sau khi cào)
│   ├── From_vnstock/                 (Parquet — giá cổ phiếu)
│   └── From_FireAnt/                 (Parquet — khối ngoại)
│
├── News_JSON/                    # Output tin tức (JSON)
│
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

## 3. Quy tắc đặt tên

### 3.1. Tên File phản ánh chức năng
```
✅ news_scraper.py        → Module cào tin tức từ RSS
✅ data_collector.py      → Module thu thập giá cổ phiếu
✅ ai_client.py           → Module giao tiếp với Gemini API
❌ utils.py               → Quá chung chung, không rõ trách nhiệm
❌ helpers.py              → Tương tự, quá mơ hồ
❌ main.py (trong sub-folder) → Không rõ "main" của cái gì
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
| `_config` | Cấu hình, constants | `config.py` |
| `auto_` | Script chạy tự động (scheduled) | `auto_news.py` |
| `test_` | Unit test / Integration test | `test_phase1.py` |

### 3.3. Package & Import
- Mỗi folder chứa module nên có `__init__.py` (có thể rỗng).
- Import theo đường dẫn tương đối khi ở cùng package, tuyệt đối khi cross-package.
- **KHÔNG** hardcode `sys.path.insert()` trong mỗi file. Centralize vào `Helper/config.py` hoặc dùng `setup.py`/`pyproject.toml`.

---

## 4. Anatomy of a Pipeline (Giải phẫu 1 module chuẩn)

Dự án Financial hoạt động theo mô hình **Pipeline** — dữ liệu chảy qua các bước tuần tự. Mỗi bước trong pipeline là một module riêng biệt.

```
[Phase X]/
├── x.y_[StepName]/
│   ├── [step]_collector.py       ← Thu thập data thô (Input)
│   ├── [step]_cleaner.py         ← Làm sạch, chuẩn hóa (Transform)
│   ├── [step]_analyzer.py        ← Phân tích, tính toán (Process)
│   ├── [step]_config.json        ← Cấu hình (nếu có)
│   └── test_[step].py            ← Test (nếu có)
```

### 4.1. Collector (Thu thập)
Chỉ làm đúng 1 việc: **lấy data từ nguồn bên ngoài và lưu xuống ổ cứng**.

```python
# ✅ ĐÚNG — Collector thuần, không xử lý logic
def fetch_vnstock(symbol, start_date="2012-01-01"):
    """Kéo giá cổ phiếu từ vnstock API, lưu thành parquet."""
    q = Quote(symbol=symbol, source='VCI')
    df = q.history(start=start_date, end=None, interval='1D')
    df.to_parquet(out_path, index=False)
    return True
```

### 4.2. Manager / Orchestrator (Điều phối)
Chứa flow chính — gọi tới các module con nhưng **không tự implement logic**.

```python
# ✅ ĐÚNG — Manager gọi module con, không tự xử lý
class NewsManager:
    @staticmethod
    def run_full_pipeline(log_callback=None):
        missing_dates = NewsManager.find_missing_dates()     # Step 1
        if missing_dates:
            NewsManager.backfill_missing_days(missing_dates)  # Step 2
        all_news = NewsManager.collect_all_news()             # Step 3
        NewsManager.save_to_json(all_news, filename)          # Step 4
```

### 4.3. Scheduled Script (Script tự động)
Script chạy bằng Task Scheduler — chỉ là **trigger**, delegate mọi logic sang Manager.

```python
# ✅ ĐÚNG — Script tự động chỉ trigger, không chứa logic
def main():
    full_log = NewsManager.run_full_pipeline(log_callback=print)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_log)

if __name__ == "__main__":
    main()
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
# ❌ KHÔNG — gemini_ai.py hiện tại trộn 3 trách nhiệm:
# 1. Gọi API Gemini (networking)
# 2. Parse JSON response (data processing)
# 3. Render HTML gradient output (presentation)
# → Nên tách thành: ai_client.py + news_renderer.py
```

### 5.3. God Function (>80 dòng)
Một hàm không được vượt quá **~80 dòng** (soft limit). Nếu dài hơn, đó là dấu hiệu cần tách thành hàm con hoặc module riêng.

### 5.4. Hardcode đường dẫn tuyệt đối
```python
# ❌ KHÔNG — Hardcode path trong mỗi file
PROJECT_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"

# ✅ ĐÚNG — Centralize vào 1 nơi duy nhất
# Helper/config.py
from Helper.config import PROJECT_DIR, DATA_DIR, NEWS_JSON_DIR
```

### 5.5. UI chứa business logic
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

### 5.6. Scheduled Script chứa logic phức tạp
```python
# ❌ KHÔNG — auto_news.py tự cào, tự parse, tự lưu
def main():
    feed = feedparser.parse(url)
    for entry in feed.entries:
        # ... 80 dòng xử lý ...
    with open(filepath, "w") as f:
        json.dump(data, f)

# ✅ ĐÚNG — Delegate sang Manager
def main():
    NewsManager.run_full_pipeline()
```

---

## 6. Quy tắc hướng phụ thuộc chung (Dependency Flow)

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

## 7. [PACK CHỜ LỆNH] Kiến trúc và Dependency Flow cho Phase 3 (ML Pipeline)

> [!WARNING]
> **XEM LẠI KHI BẮT ĐẦU PHASE 3:** Đây là gói quy tắc SRP thiết kế riêng cho Phase 3 (ML Training) được bọc lại thành 1 pack. Các logic ở các phase khác vẫn giữ nguyên chờ lệnh. 

### Kiến trúc 4 tầng

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

### Dependency Flow (mũi tên = "được phép gọi/đọc")

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

### Cấu trúc thư mục đề xuất

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

### Hành vi chi tiết từng module

#### TẦNG 0: CONFIG (Read-only)

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

#### TẦNG 1: DATA PREP (Input)

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

#### TẦNG 2: ARENA (Core PyCaret)

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

#### TẦNG 3: OUTPUT (Evaluation + Export)

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

### Quy tắc Dependency Phase 3 — Tóm gọn

```
✅ ĐƯỢC PHÉP:
   auto_runner (scheduled) → arena_runner
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

## 8. Checklist trước khi commit

Trước khi commit bất kỳ file `.py` nào, kiểm tra:

- [ ] File chỉ phục vụ **1 trách nhiệm duy nhất**? (Thu thập ≠ Xử lý ≠ Render ≠ UI)
- [ ] Tên file **phản ánh rõ chức năng** (không phải `utils.py`, `helpers.py`, `main.py`)?
- [ ] File nằm đúng **Phase Folder** hoặc thư mục chức năng phù hợp?
- [ ] **Không hardcode** đường dẫn tuyệt đối? (dùng `Helper/config.py`)
- [ ] Không có hàm nào **vượt quá ~80 dòng**?
- [ ] File **không vượt quá ~300 dòng** (soft limit)?
- [ ] Các dependencies đi **đúng chiều** (§6)?
- [ ] Có `__init__.py` trong folder chứa module?

---

## 8. Khi nào ĐƯỢC PHÉP gộp?

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

## 9. Quy tắc "tốt nghiệp" (Promotion Rule)

Một file/hàm ĐƯỢC PHÉP chuyển sang `Helper/` khi và chỉ khi:
1. Có **≥ 2 Phase/Module** khác nhau cần import/sử dụng nó.
2. File đó **KHÔNG chứa** logic đặc thù của phase gốc.

Quy trình:
1. Copy file sang `Helper/`.
2. Xóa file gốc trong Phase Folder.
3. Cập nhật tất cả import path.
4. Chạy test kiểm tra.

---

## 10. Ví dụ thực tế (Đã và Cần refactor)

### Hiện trạng tốt: Module News ✅
```
Main Scripts/News/
├── news_scraper.py       ← Thu thập RSS (1 concern)
├── news_manager.py       ← Điều phối pipeline (1 concern)
└── gemini_ai.py          ← AI + Render (⚠️ cần tách)
```

### Cần refactor: `data_raw_cross_check.py` ❌
```
Hiện tại: 1 file 26KB chứa mọi thứ

Đề xuất tách:
Phase 1/1.1_Data_Collector/
├── data_collector.py             ← Thu thập (đã có, ✅)
├── data_validator.py             ← Validate data quality
├── data_comparator.py            ← So sánh vnstock vs FireAnt
├── data_report.py                ← Render báo cáo kết quả
└── test_phase1.py                ← Test (đã có, ✅)
```

### Cần refactor: `gemini_ai.py` ❌
```
Hiện tại: 1 file trộn API call + HTML rendering

Đề xuất tách:
Main Scripts/News/
├── news_scraper.py       ← Giữ nguyên ✅
├── news_manager.py       ← Giữ nguyên ✅
├── ai_client.py          ← Chỉ gọi Gemini API, trả về JSON thuần
└── news_renderer.py      ← Chỉ nhận JSON, render HTML output
```

---

> **Ghi nhớ cuối cùng:** Nếu bạn phải giải thích "module này làm gì" bằng từ **"và"** (ví dụ: "module này cào tin **và** gọi AI **và** render HTML"), thì module đó đang vi phạm SRP và cần được tách ra.
