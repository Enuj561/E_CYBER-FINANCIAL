# Chương 12 — Phase 3: ML Training

> [!WARNING]
> **PHASE LÕI CỦA DỰ ÁN.** Xem lại toàn bộ chương này khi chuẩn bị bắt đầu Phase 3.

> **Mô hình: Arena / Tournament (4 tầng)**
> **Thời lượng:** 6 tháng | **Tech stack:** PyCaret, XGBoost, LightGBM, CatBoost

---

## 11.1. Kiến trúc 4 tầng

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

## 11.2. Dependency Flow

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

## 11.3. Cấu trúc thư mục

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

## 11.4. Kiểu module đặc thù và hành vi chi tiết

Ngoài các hậu tố chung ở [§3.2 — EF-S-01](./EF-S-01_Data_Structure.md), Phase 3 bổ sung:

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
| **Trách nhiệm DUY NHẤT** | Đọc parquet từ `Phase_1_Data/` (Phase 1) và trả về raw DataFrame |
| **Input** | Đường dẫn tới `Phase_1_Data/From_vnstock/`, `Phase_1_Data/From_FireAnt/` |
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

## 11.5. Error Handling

**Chiến lược: Graceful + Checkpoint** (Xem thêm [EF-S-02](./EF-S-02_Error_Handling.md))

Training lâu (hàng giờ), crash = mất hết. Code PHẢI:
- Log progress sau mỗi bước chính (setup, compare, tune, blend)
- Checkpoint experiment state vào `experiment_registry.json`
- Catch exception ở tầng `arena_runner`, log đầy đủ rồi mới re-raise
- KHÔNG nuốt lỗi im lặng

---

## 11.6. Quy tắc Dependency Phase 3 — Tóm gọn

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

## 11.7. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.pkl` / `.joblib` (model) + `.json` (metrics + registry) |
| **Vị trí** | `Phase_3_Data/Models/` |
| **Tên file** | `exp_{ID}_{model_type}_{context}_{version}.pkl` |
| **Ai đọc?** | Phase 4 Backtester qua `model_exporter.load_model()` |

> [!IMPORTANT]
> **Constraints từ Planning:**
> - BẮT BUỘC dùng **Time Series Split** (Walk-forward validation)
> - Xem xét thời gian và **RAM tiêu thụ** khi training
> - Xem xét dùng **`blend_models`** để tránh sai số
> - Nếu thay đổi context (dài hạn → trung hạn), cần **train lại** model
