# Chương 10 — Phase 1: Chuẩn bị Data

> **Mô hình: ETL (Extract → Transform → Load)**
> **Thời lượng:** 1 tháng | **Tech stack:** vnstock, requests, pandas, Scikit-Learn

---

## 9.1. Dependency Flow

```
Collector (cào data) → Cleaner (làm sạch) → Validator (kiểm tra chất lượng)
      ↓                                              ↓
 API bên ngoài                                  Phase_1_Data/ (.parquet)
 (vnstock, FireAnt)                             [immutable sau khi cào]
```

Quy tắc:
- ✅ `Collector` ĐƯỢC gọi API bên ngoài (vnstock, FireAnt)
- ✅ `Cleaner` ĐƯỢC đọc output từ `Collector`
- ✅ `Validator` ĐƯỢC đọc output từ `Cleaner` và `Collector` (để so sánh)
- ❌ `Collector` KHÔNG ĐƯỢC gọi `Cleaner` hoặc `Validator`
- ❌ `Cleaner` KHÔNG ĐƯỢC gọi API (chỉ xử lý data đã có)
- ❌ Không module nào ĐƯỢC modify file trong `Phase_1_Data/` sau khi cào xong

---

## 9.2. Cấu trúc thư mục

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

## 9.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở [§3.2 — EF-S-01](./EF-S-01_Data_Structure.md), Phase 1 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_validator` | Validate chất lượng data (null, range, count) | `data_validator.py` |
| `_comparator` | So sánh data giữa các nguồn | `data_comparator.py` |

---

## 9.4. Error Handling

**Chiến lược: Retry + Resume** (Xem thêm [EF-S-02](./EF-S-02_Error_Handling.md))

Cào data từ ~1800 mã chứng khoán, bị gián đoạn là chuyện bình thường. Code PHẢI:
- Kiểm tra file đã tồn tại trước khi cào (resume mode)
- Retry khi API lỗi tạm thời (timeout, rate limit)
- Log chi tiết mã nào thành công/thất bại
- KHÔNG crash toàn bộ batch vì 1 mã lỗi

---

## 9.5. Config

`config.json` — cấu hình không chứa secrets:
```json
{
    "START_DATE": "2012-01-01",
    "SYMBOLS_FILE": "symbols_list.csv"
}
```

> [!WARNING]
> API keys và tokens (như `FIREANT_BEARER_TOKEN`) PHẢI nằm trong `System/.env`, KHÔNG được để trong `config.json`. Xem [§2 — EF-S-01](./EF-S-01_Data_Structure.md).

---

## 9.6. Testing

Kiểu test: **Data Quality Check**
- Kiểm tra null count trong DataFrame
- Kiểm tra date range (có đủ lịch sử không?)
- Kiểm tra row count giữa vnstock vs FireAnt
- So sánh giá từ 2 nguồn (chênh lệch có hợp lý không?)

---

## 9.7. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.parquet` |
| **Vị trí** | `Phase_1_Data/From_vnstock/`, `Phase_1_Data/From_FireAnt/` |
| **Tên file** | `{SYMBOL}_historical_{source}.parquet` |
| **Tính chất** | **Immutable** — không sửa sau khi cào xong |
| **Ai đọc?** | Phase 2 (tính indicators), Phase 3 (load vào ML) |

> [!IMPORTANT]
> **Constraint từ Planning:** BẮT BUỘC dùng **giá điều chỉnh**. Không bỏ qua các mã đã chết (delisted).
