# Kiểm tra source Phase 1 theo EF-S

**Ngày:** 2026-08-09
**Kết luận:** Đạt một phần, chưa được phép gọi là tuân thủ toàn bộ EF-S.

## Phần đã đúng

- Source OHLCV và BCTC đã được tách thành hai folder dễ nhận biết.
- File test đã rời source production và nằm trong `tests/unit/phase_1/`.
- Hai client BCTC mới chỉ gọi nguồn và trả kết quả; không tự ghi Parquet, không tự đổi nguồn và không giấu tên nguồn thật.
- Hai client BCTC mới có giới hạn thử lại, phân biệt lỗi tạm thời với lỗi phải dừng và có thể kiểm tra bằng data giả.
- Source production có tiền tố `E_`; test dùng tên `test_*.py` để công cụ tự tìm.
- Log của mỗi tính năng tiếp tục nằm cạnh script sở hữu tính năng nhờ `E_BlackBox` nhận đường dẫn `__file__`.

## Phần chưa đúng, cần refactor riêng

### `E_data_collector.py` — OHLCV cũ

File này đang làm ba việc cùng lúc: gọi API, ghi Parquet và điều phối cả batch. Theo EF-S, ba việc này nên được tách thành client, phần ghi file và manager.

Ngoài ra, file bắt lỗi quá rộng rồi chỉ trả `False`. Cách này khiến phần gọi bên ngoài không biết rõ lỗi là mạng, token hay data sai. Retry và báo cáo tổng kết batch cũng chưa đạt chuẩn mới.

### `E_data_raw_cross_check.py` và `E_Data_Checkers/`

File cross-check vừa đọc file, gọi nhiều phép kiểm tra, sửa data và ghi ngược lại. Trách nhiệm còn bị trộn.

`E_volume_balance_validator.py` mang tên “validator” nhưng tự sửa DataFrame đầu vào. Theo luồng EF-S, validator nên chỉ báo sai; việc sửa thuộc cleaner/processor. Đây là nguy cơ sửa data lấp liếm nếu không có bản raw và báo cáo thay đổi rõ ràng.

### `E_bctc_collector.py` — BCTC cũ

File này đã được ghi rõ là tài liệu tham chiếu, không thuộc luồng mới. Nó đang trộn gọi API, retry, ghi Parquet, checkpoint và điều phối batch trong một file; đồng thời vẫn dùng cấu trúc BCTC cũ. Không được gọi file này cho đợt cào mới.

### Rủi ro còn lại của VCI

Client VCI phải dùng cổng nội bộ `_get_financial_report` để xin nhiều kỳ vì vnstock chưa mở cổng công khai tương đương. Code đã dừng rõ nếu cổng này biến mất, nhưng mỗi lần nâng phiên bản vnstock phải chạy lại bài kiểm tra tương thích.

## Cấu trúc sau khi sắp xếp

```text
Main Scripts/Phase 1/
├── 1.1_Data_OHLCV/
│   ├── E_data_collector.py
│   ├── E_data_raw_cross_check.py
│   └── E_Data_Checkers/
└── 1.2_Data_BCTC/
    ├── E_bctc_collector.py       Chỉ tham chiếu
    ├── E_fireant_bctc_client.py
    ├── E_vci_bctc_client.py
    ├── E_bctc_raw_repository.py
    ├── E_bctc_progress_repository.py
    ├── E_bctc_schema.py
    ├── E_bctc_normalizer.py
    └── E_bctc_validator.py

tests/unit/phase_1/
├── test_ohlcv_validators.py
└── test_bctc_clients.py
```

## Thứ tự sửa hợp lý tiếp theo

1. Hoàn thành luồng BCTC mới theo plan hiện tại; không sửa collector BCTC cũ để dùng lại.
2. Khi quay lại OHLCV, tách `E_data_collector.py` thành hai client nguồn, phần ghi file và manager.
3. Tách việc “kiểm tra” khỏi việc “sửa data”; raw không được sửa tại chỗ.
