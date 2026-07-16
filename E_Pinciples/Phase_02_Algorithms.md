# Chương 11 — Phase 2: Thuật toán

> **Mô hình: Pure Transform (tính toán thuần)**
> **Thời lượng:** 3 tháng | **Tech stack:** TA-lib, pandas-ta

---

## 10.1. Dependency Flow

```
Data Reader (đọc parquet từ Phase 1) → Indicator Calculator (tính TA) → Validator (kiểm tra công thức)
                                                                              ↓
                                                                       DataFrame có features
                                                                       (output cho Phase 3)
```

Quy tắc:
- ✅ `Calculator` ĐƯỢC đọc output từ Phase 1 (`Phase_1_Data/`)
- ✅ `Validator` ĐƯỢC kiểm tra output của `Calculator`
- ❌ `Calculator` KHÔNG ĐƯỢC gọi API, ghi file, hiển thị UI
- ❌ `Calculator` KHÔNG ĐƯỢC biết Phase 3 tồn tại (không import)
- ❌ Module trong Phase 2 KHÔNG ĐƯỢC modify parquet gốc của Phase 1

---

## 10.2. Cấu trúc thư mục

```
Phase 2/
├── 2.1_Technical_Indicators/
│   ├── indicator_calculator.py        ← TỰ CODE công thức (pure functions)
│   ├── indicator_crosscheck.py        ← So sánh tự code vs thư viện
│   ├── indicator_validator.py         ← Validate output (range, NaN...)
│   └── test_indicators.py            ← Unit test mathematical correctness
│
└── 2.2_Library_Indicators/            ← GỌI THƯ VIỆN (pandas-ta)
    ├── lib_indicator_calculator.py    ← Wrapper gọi pandas-ta
    ├── feature_store.py              ← Build & lưu features → Phase_2_Data/
    └── test_lib_indicators.py        ← Test output consistency
```

---

## 10.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở [§3.2 — EF-S-01](./EF-S-01_Data_Structure.md), Phase 2 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_calculator` | Tự code công thức (pure function) | `indicator_calculator.py` |
| `lib_*_calculator` | Wrapper gọi thư viện | `lib_indicator_calculator.py` |
| `_crosscheck` | So sánh tự code vs thư viện | `indicator_crosscheck.py` |
| `_validator` | Kiểm tra correctness | `indicator_validator.py` |
| `_store` | Lưu trữ features ra disk | `feature_store.py` |

---

## 10.4. Error Handling

**Chiến lược: Strict — Crash ngay** (Xem thêm [EF-S-02](./EF-S-02_Error_Handling.md))

Sai 1 con số = sai cả model. Phase 2 là nền tảng toán học, PHẢI:
- KHÔNG dùng try/except để nuốt lỗi tính toán
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

## 10.5. Constraint đặc thù

- Mọi hàm tính toán PHẢI là **pure function**: cùng input → cùng output, KHÔNG side effect
- KHÔNG gọi API, KHÔNG ghi file, KHÔNG đọc config ngoài tham số đầu vào
- KHÔNG dùng biến global

---

## 10.6. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Output 1** | Python modules (pure functions) — được Phase 3 & hệ thống hàng ngày gọi tính toán |
| **Output 2** | `.parquet` trong `Phase_2_Data/Features/` — Phase 3 training đọc trực tiếp |
| **Tên file** | `{SYMBOL}_features.parquet` |
| **Tính chất** | Rebuild-able — xóa và tính lại bất cứ lúc nào |

> [!NOTE]
> Phase 2 cung cấp HAI output: module code để tính toán hàng ngày, và file `.parquet` lưu sẵn features để Phase 3 training đọc trực tiếp. `feature_builder.py` (Phase 3) sẽ `import` các hàm tính toán từ Phase 2 để tính technical indicators trên raw DataFrame từ Phase 1.
