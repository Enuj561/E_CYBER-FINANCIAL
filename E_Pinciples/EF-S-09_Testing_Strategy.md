# Chương 7 — EF-S-09: Testing Strategy (Chiến lược kiểm thử)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Test Double — dùng "diễn viên đóng thế" thay cho đối tượng thật trong test
> - **Nguồn gốc:** Gerard Meszaros — *xUnit Test Patterns*, 2007. Martin Fowler — *"Mocks Aren't Stubs"*, 2007.
> - **Giải thích:** Tên gọi "Test Double" lấy cảm hứng từ "stunt double" (diễn viên đóng thế) trong điện ảnh. Thay vì gọi API thật (tốn thời gian, tốn quota, kết quả thay đổi), ta tạo dữ liệu giả (mock) với kết quả cố định để test code nhanh và tin cậy.

## 1. Phân loại Test Double

| Loại | Vai trò | Ví dụ trong dự án |
|---|---|---|
| **Dummy** | Chỉ lấp chỗ tham số, không dùng thật | `symbol="TEST"` |
| **Fake** | Có logic thật nhưng đơn giản hóa | DataFrame tạo sẵn thay vì gọi API |
| **Stub** | Trả kết quả cố định, không quan tâm input | `return pd.DataFrame({"close": [100, 101, 102]})` |
| **Spy** | Ghi nhận hàm có được gọi đúng không | Kiểm tra `logging.error` có được gọi khi lỗi |
| **Mock** | Kiểm tra hành vi: hàm được gọi đúng tham số không? | Kiểm tra `safe_write_parquet` có được gọi khi cào xong |

## 2. Quy tắc Testing

| Quy tắc | Chi tiết |
|---|---|
| Mọi **Calculator** PHẢI có unit test kèm theo | File `test_*.py` đặt cùng thư mục |
| Test PHẢI chạy **offline** (không cần mạng) | Dùng Mock Data thay vì gọi API |
| Test PHẢI có kết quả **xác định** (deterministic) | Cùng input → cùng output, mọi lúc |
| KHÔNG test implementation detail | Test **kết quả**, không test "dùng hàm nào bên trong" |

## 3. Mock Data — Cấu trúc thư mục

Mock Data nằm trong `Phase_X_Data/Mock_Data/` — mỗi Phase có folder mock riêng:

```
Phase_1_Data/
├── E_OHLCV/                      ← Data thật (Giá + Khối lượng)
│   ├── From_vnstock/
│   └── From_FireAnt/
├── E_BCTC/                       ← Data thật (Báo cáo Tài chính)
│   ├── Balance_Sheet/
│   ├── Income_Statement/
│   ├── Cash_Flow/
│   ├── Ratio/
│   └── Note/
└── Mock_Data/                    ← Data giả lập cho test
    ├── VNM_mock_vnstock.parquet     (50 dòng OHLCV mẫu)
    ├── VNM_mock_fireant.parquet     (50 dòng khối ngoại mẫu)
    └── INVALID_mock.parquet         (Data sai để test error handling)

Phase_2_Data/
├── Features/                     ← Data thật
└── Mock_Data/                    ← Data giả lập cho test
    └── VNM_mock_features.parquet    (50 dòng RSI, MACD mẫu)
```

## 4. Code mẫu

```python
# test_indicators.py — Test Phase 2 Calculator với Mock Data
import pandas as pd
from indicator_calculator import compute_rsi

def test_rsi_basic():
    """RSI phải nằm trong khoảng [0, 100]."""
    mock_close = pd.Series([44, 44.34, 44.09, 43.61, 44.33,
                            44.83, 45.10, 45.42, 45.84, 46.08,
                            45.89, 46.03, 45.61, 46.28, 46.28])
    result = compute_rsi(mock_close, period=14)
    assert 0 <= result <= 100, f"RSI ngoài khoảng: {result}"

def test_rsi_all_up():
    """Giá tăng liên tục → RSI phải gần 100."""
    mock_close = pd.Series(range(100, 120))
    result = compute_rsi(mock_close, period=14)
    assert result > 90, f"RSI phải > 90 khi giá tăng liên tục: {result}"

def test_rsi_insufficient_data():
    """Dữ liệu không đủ → phải raise AssertionError."""
    mock_close = pd.Series([100, 101, 102])
    try:
        compute_rsi(mock_close, period=14)
        assert False, "Phải raise lỗi khi dữ liệu < period"
    except AssertionError:
        pass  # Expected
```

```python
# test_data_collector.py — Test Phase 1 Collector với Mock API
from unittest.mock import patch, MagicMock

@patch('data_collector.requests.get')
def test_fetch_fireant_success(mock_get):
    """FireAnt API trả data đúng → phải lưu file."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"date": "2026-01-01", "open": 100, "high": 105,
         "low": 98, "close": 103, "volume": 1000000}
    ]
    mock_get.return_value = mock_response
    
    result = fetch_fireant("VNM")
    assert result == True
```

## 5. Thư viện Testing

| Thư viện | Vai trò |
|---|---|
| **pytest** | Framework chạy test — thay thế unittest |
| **unittest.mock** | Tạo Mock, Stub, Spy — built-in Python |
