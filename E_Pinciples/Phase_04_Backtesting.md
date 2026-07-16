# Chương 13 — Phase 4: Chiến trường Giả lập

> **Mô hình: Simulation (mô phỏng event loop)**
> **Thời lượng:** 6 tháng | **Tech stack:** Custom backtester

---

## 12.1. Dependency Flow

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
- ✅ `Model Loader` ĐƯỢC đọc `.pkl` từ `Phase_3_Data/Models/`
- ✅ `Simulator` ĐƯỢC gọi `Trade Engine` để thực thi từng giao dịch
- ✅ `Report Generator` ĐƯỢC đọc trade log + equity curve
- ❌ `Simulator` KHÔNG ĐƯỢC gọi PyCaret hoặc train model
- ❌ `Trade Engine` KHÔNG ĐƯỢC quyết định chiến lược (chỉ thực thi)
- ❌ `Strategy Builder` KHÔNG ĐƯỢC biết kết quả tương lai (no look-ahead bias)

---

## 12.2. Cấu trúc thư mục

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

## 12.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở [§3.2 — EF-S-01](./EF-S-01_Data_Structure.md), Phase 4 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_loader` | Load model/data từ phase trước | `model_loader.py` |
| `_strategy` / `_builder` | Xây dựng chiến lược giao dịch | `strategy_builder.py` |
| `_simulator` | Event loop mô phỏng | `simulator.py` |
| `_engine` | Thực thi giao dịch đơn lẻ | `trade_engine.py` |
| `_reporter` | Tạo báo cáo kết quả backtest | `backtest_reporter.py` |

---

## 12.4. Error Handling

**Chiến lược: Zero Tolerance** (Xem thêm [EF-S-02](./EF-S-02_Error_Handling.md))

Sai 1 giao dịch = sai toàn bộ equity curve. Code PHẢI:
- KHÔNG dùng try/except để bỏ qua lỗi giao dịch
- Assert balance đủ trước khi mua
- Assert giá hợp lệ trước khi tính P&L
- Crash ngay nếu data có lỗ hổng (missing dates, NaN price)

---

## 12.5. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.json` (trade log, metrics) + charts |
| **Vị trí** | `Phase_4_Data/Results/` |
| **Ai đọc?** | Con người (review kết quả), Phase 5 (so sánh win rate có/không news) |

> [!IMPORTANT]
> **Constraints từ Planning:**
> - PHẢI **trừ chi phí giao dịch** (realistic)
> - PHẢI **tính trượt giá** (slippage)
> - PHẢI **Stress Test** model bằng năm 2022 (thị trường sụp)
> - PHẢI **so sánh** lợi nhuận với chiến lược Buy and Hold VN-Index
