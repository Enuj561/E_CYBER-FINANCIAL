# Chương 6 — EF-S-06: Library Catalog (Kho thư viện có sẵn)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Don't Reinvent the Wheel (Không phát minh lại bánh xe)
> - **Giải thích:** Trước khi viết bất kỳ thuật toán hay pipeline nào từ đầu, **BẮT BUỘC** phải kiểm tra xem dự án đã có sẵn thư viện nào giải quyết bài toán đó chưa. Tự code lại thuật toán đã có sẵn trong thư viện chuyên nghiệp = lãng phí thời gian + dễ có bug.

## 1. Bảng thư viện đang dùng

| Thư viện | Giấy phép | Chuyên môn | Phase sử dụng |
|---|---|---|---|
| **vnstock** | MIT | Cào giá cổ phiếu VN (VCI, TCBS) | Phase 1 |
| **requests** | Apache-2.0 | HTTP calls (FireAnt API) | Phase 1 |
| **pandas** | BSD-3 | DataFrame xử lý dữ liệu | All Phases |
| **Scikit-Learn** | BSD-3 | Data cleaning, preprocessing | Phase 1 |
| **pandas-ta** | MIT | Technical indicators (chính, production) | Phase 2 |
| **TA-Lib** | BSD-3 | Technical indicators (crosscheck tùy chọn) | Phase 2 |
| **PyCaret** | MIT | AutoML arena (setup, compare, tune, blend) | Phase 3 **DUY NHẤT** |
| **XGBoost** | Apache-2.0 | Gradient boosting model (qua PyCaret) | Phase 3 |
| **LightGBM** | MIT | Gradient boosting model (qua PyCaret) | Phase 3 |
| **CatBoost** | Apache-2.0 | Gradient boosting model (qua PyCaret) | Phase 3 |
| **aiohttp** | Apache-2.0 | Async HTTP client | Phase 1, Phase 5 |
| **pytest** | MIT | Testing framework | All Phases |
| **unittest.mock** | (Built-in) | Mock/Stub/Fake objects cho test | All Phases |
| **feedparser** | BSD-2 | Parse RSS feeds | Phase 5 |
| **google-generativeai** | Apache-2.0 | Gemini AI API | Phase 5 |
| **PyQt6** | GPL-v3 | Desktop UI framework | IDE_UI |

## 2. Khi nào dùng cái nào?

| Bài toán | Dùng thư viện |
|---|---|
| Cào giá cổ phiếu VN | **vnstock** (⭐) — native API cho thị trường VN |
| HTTP request tuỳ chỉnh (FireAnt) | **requests** (⭐) |
| Tính RSI, MACD, Bollinger Bands | **pandas-ta** (⭐) chính, **TA-Lib** crosscheck tùy chọn. Giai đoạn thiết kế cơ sở: tự code → crosscheck → chuyển sang thư viện |
| ML pipeline: setup → compare → tune → blend | **PyCaret** (⭐) — DUY NHẤT qua `arena_runner.py` |
| Parse RSS feeds | **feedparser** (⭐) — đừng dùng requests + regex |
| Phân tích text bằng AI | **google-generativeai** (Gemini) |
| Data manipulation | **pandas** (⭐) — mọi thao tác DataFrame |

## 3. Quy tắc sử dụng

### 3.1. BẮT BUỘC kiểm tra trước khi tự code

```python
# ❌ SAI — Tự code thuật toán RSI từ đầu
def my_rsi(prices, period=14):
    # ... 30 dòng code tự viết, dễ bug ...

# ✅ ĐÚNG — Dùng thư viện chuyên nghiệp
import pandas_ta as ta
df['RSI'] = ta.rsi(df['close'], length=14)
```

### 3.2. PyCaret chỉ được gọi từ 1 nơi duy nhất

PyCaret quản lý state nội bộ (experiment session, preprocessor pipeline, CV splits...). **CHỈ** `arena_runner.py` (Phase 3) được phép `import pycaret`. Nếu nhiều file cùng gọi PyCaret, state sẽ conflict.

### 3.3. Ghi lại version trong requirements.txt

Mọi thư viện mới thêm **BẮT BUỘC** phải ghi version vào `requirements.txt`:
```
vnstock==2.0.0
pandas==2.0.3
pycaret==3.3.1
```

## 4. Security Audit — Kiểm tra bảo mật thư viện (BẮT BUỘC)

> Dự án xử lý dữ liệu tài chính nhạy cảm (API keys, giá cổ phiếu, chiến lược giao dịch). **BẮT BUỘC** kiểm tra bảo mật trước khi dùng bất kỳ thư viện mới nào.

### Checklist trước khi `pip install`

- [ ] Thư viện có repo chính thức trên **GitHub/PyPI** không? Bao nhiêu stars?
- [ ] README có ghi rõ thư viện **LÀM GÌ** không?
- [ ] Kiểm tra: thư viện chỉ **DOWNLOAD** data (GET), KHÔNG tự động **UPLOAD/POST** data đi đâu
- [ ] Kiểm tra: thư viện KHÔNG yêu cầu **API key/token** mà không giải thích rõ dùng để làm gì
- [ ] Kiểm tra: KHÔNG có **telemetry/tracking ẩn** (gửi usage data về server của tác giả)
- [ ] Kiểm tra: thư viện KHÔNG ghi file **ngoài project folder** (chỉ ghi trong thư mục được chỉ định)
- [ ] Nếu thư viện ít stars (<1000): **đọc qua source code** trước khi dùng

### Hành vi CẤM

```python
# ❌ CẤM — pip install thư viện lạ không kiểm tra
pip install some-random-finance-lib  # Ai viết? Làm gì? Gửi data đi đâu?

# ❌ CẤM — Dùng thư viện tự động gửi data ra ngoài
import sketchy_lib
sketchy_lib.upload_portfolio(my_data)  # Data tài chính bị leak!

# ✅ ĐÚNG — Chỉ dùng thư viện đã qua audit, có trong bảng §6.1
from vnstock import Vnstock  # Repo chính thức, 1000+ stars, chỉ GET
```
