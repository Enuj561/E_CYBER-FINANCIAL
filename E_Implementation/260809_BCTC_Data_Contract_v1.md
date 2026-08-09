# Mẫu dữ liệu chung BCTC — phiên bản 1

Ngày chốt: **2026-08-09**
Phiên bản hiện hành: **`bctc_v1.1.0`**

## 1. Mục đích

File này là bản vẽ để Bước 5 viết collector FireAnt và collector vnstock/VCI.

Mục tiêu:

- Giữ nguyên data gốc của từng nguồn.
- Đổi hai nguồn về cùng một hình dạng để kiểm tra.
- Không làm mất tên mục gốc, vị trí dòng hoặc nguồn thật.
- Không tự điền thông tin chưa biết.
- Không tự chọn một nguồn thắng khi hai nguồn khác nhau.
- Dùng được cho doanh nghiệp thường, ngân hàng, chứng khoán và bảo hiểm.

File dùng cho máy đọc: [260809_BCTC_Data_Contract_v1.json](./260809_BCTC_Data_Contract_v1.json).

## 2. Ba lớp data

```text
Nguồn FireAnt / VCI
        ↓
Raw — giữ nguyên kết quả nguồn
        ↓
Normalized — cùng hình dạng, vẫn tách nguồn
        ↓
Curated — đã kiểm tra và được phép dùng ở Phase sau
```

### Raw

Raw là bằng chứng gốc. Không sửa giá trị, không đổi tên mục và không ghi đè giữa hai lần chạy.

### Normalized

Normalized đổi data về dạng **một dòng = một mục tài chính của một mã, một nguồn và một kỳ**.

Hai nguồn vẫn nằm ở hai dòng riêng. “Cùng hình dạng” không có nghĩa “trộn thành một giá trị”.

### Curated

Curated chỉ được tạo sau khi:

- kỳ báo cáo đã đúng;
- đơn vị đã đúng;
- mục tương đương giữa hai nguồn đã được xác nhận;
- dòng trùng đã được phân biệt;
- lỗi và phần thiếu đã được ghi nhận.

Bước 4 chưa tạo Curated thật.

## 3. Thông tin phải giữ ở Raw

Mỗi kết quả gốc cần có file data và metadata đi kèm.

| Thông tin | Ý nghĩa |
|---|---|
| `run_id` | Mã lần chạy |
| `source` | `fireant` hoặc `vnstock` |
| `provider` | `fireant_api`, `vci` hoặc `kbs` |
| `symbol` | Mã cổ phiếu |
| `requested_report_type` | Loại báo cáo đã yêu cầu |
| `requested_period_type` | Quý hay năm |
| `request_parameters` | Tham số gửi đi, đã bỏ token/mật khẩu |
| `endpoint_name` | Tên cổng gọi; không lưu secret trong URL |
| `collected_at` | Thời điểm lấy, bắt buộc có múi giờ |
| `http_status` | Mã phản hồi nếu có |
| `library_version` | Phiên bản vnstock/requests liên quan |
| `content_sha256` | Mã kiểm tra để biết raw có bị đổi không |
| `collection_status` | Thành công, thiếu, không có, chưa hỗ trợ hoặc lỗi |
| `error_type`, `error_message` | Lỗi đã bỏ token và thông tin bí mật |
| `raw_file` | Đường dẫn file raw |

Token FireAnt, mật khẩu, cookie và toàn bộ dòng `Authorization` không được ghi vào raw, metadata hoặc log.

## 4. Bảng chung `bctc_records`

### Nhận dạng và nguồn

| Cột | Kiểu | Được trống? | Ý nghĩa |
|---|---|---:|---|
| `schema_version` | string | Không | Luôn là `bctc_v1.1.0` ở phiên bản này |
| `run_id` | string | Không | Nối về lần cào |
| `source` | string | Không | `fireant` hoặc `vnstock` |
| `provider` | string | Không | `fireant_api`, `vci`, `kbs` |
| `symbol` | string | Không | Viết hoa, không tự đổi mã cũ sang mã mới |
| `company_type` | string | Không | `general`, `bank`, `securities`, `insurance`, `unknown` |

### Loại báo cáo và kỳ

| Cột | Kiểu | Được trống? | Ý nghĩa |
|---|---|---:|---|
| `report_type` | string | Không | `balance_sheet`, `income_statement`, `cash_flow`, `ratio`, `unknown` |
| `cash_flow_method` | string | Không | `direct`, `indirect`, `unknown`, `not_applicable` |
| `period_type` | string | Không | `quarter` hoặc `year` |
| `fiscal_year` | integer | Không | Năm báo cáo |
| `fiscal_quarter` | integer | Có | `1–4` cho quý; bắt buộc trống với báo cáo năm |
| `period_key` | string | Không | Quý: `YYYY-QN`; năm: `YYYY` |
| `source_period_column_number` | integer | Có | Lần xuất hiện của cột kỳ cùng tên, bắt đầu từ 1; normalizer 1.1 luôn ghi, data 1.0 cũ có thể trống |
| `period_value_mode` | string | Không | `point_in_time`, `standalone`, `cumulative`, `unknown` |

Quy tắc `period_value_mode`:

- Cân đối kế toán: `point_in_time`.
- Kết quả kinh doanh quý đã kiểm tra: `standalone`.
- Lưu chuyển tiền tệ quý đã kiểm tra: `standalone`, nhưng vẫn phải kiểm tra lại theo loại doanh nghiệp.
- Báo cáo năm: `cumulative` cho kết quả kinh doanh/dòng tiền; `point_in_time` cho cân đối kế toán.
- Chỉ số chưa rõ cách tính: `unknown`.

Nếu VCI trả lẫn cột năm và quý trong cùng raw, raw vẫn giữ nguyên. Mỗi lần normalize chỉ lấy loại kỳ đúng với `period_type` đang xử lý và thêm cờ `source_mixed_period_columns`. Không đổi cột năm thành quý; loại kỳ còn lại được xử lý bởi work item riêng.

Riêng bảng VCI `ratio`, các dòng `year`, `quarter`, `ratioTTMId` và `ratioType` là metadata của bảng. Chúng được giữ trong raw nhưng không chuyển thành record chỉ số tài chính.

Parquet không cho phép tên cột trùng. Nếu raw VCI có nhiều cột cùng tên kỳ, file lưu thêm hậu tố kỹ thuật theo vị trí cột; metadata cạnh file bắt buộc giữ `column_number`, `original_name` và `stored_name`. Không được gộp hoặc xóa cột trùng.

`ratio` năm hiện tại có thể là số YTD/current-year, không phải số cả năm đã chốt. Record được giữ với cảnh báo `current_year_ratio_incomplete`. Quy tắc này không áp dụng cho BCTC năm của cân đối, kết quả kinh doanh hoặc dòng tiền.

### Hợp nhất và thời điểm công bố

| Cột | Kiểu | Được trống? | Ý nghĩa |
|---|---|---:|---|
| `consolidation_status` | string | Không | `consolidated`, `separate`, `unknown` |
| `publication_date` | date | Có | Ngày doanh nghiệp công bố BCTC |
| `availability_date` | date | Có | Ngày data thực sự có thể được dùng |

Hai cổng đã thử không ghi hợp nhất/riêng lẻ và ngày công bố. Vì vậy mặc định hiện tại:

- `consolidation_status = unknown`;
- `publication_date = null`;
- `availability_date = null`.

Không được dùng ngày cuối quý thay cho ngày công bố.

### Tên mục và cách giữ dòng trùng

| Cột | Kiểu | Được trống? | Ý nghĩa |
|---|---|---:|---|
| `source_item_id` | string | Không | Mã mục đúng như nguồn/thư viện trả |
| `source_item_name` | string | Có | Tên tiếng Việt đúng như nguồn trả |
| `source_item_name_en` | string | Có | Tên tiếng Anh nếu có |
| `source_row_number` | integer | Không | Vị trí dòng trong báo cáo nguồn, bắt đầu từ 1 |
| `source_item_key` | string | Không | Khóa không trùng của dòng nguồn |
| `canonical_item_id` | string | Có | Mã chung sau khi đã xác nhận hai mục tương đương |
| `mapping_version` | string | Có | Phiên bản bảng ghép chỉ tiêu |
| `mapping_status` | string | Không | `confirmed`, `provisional`, `unmapped`, `rejected` |

`source_item_key` được tạo theo mẫu:

```text
provider|company_type|report_type|source_item_id|source_row_number|period_column=N
```

Không dùng riêng `source_item_id` làm khóa vì VCI có thể tạo hai dòng cùng mã sau khi đổi tên. `period_column=N` giữ riêng cả trường hợp VCI trả hai cột cùng tên kỳ; không xóa một cột để làm khóa đẹp.

Không xóa một dòng chỉ vì trùng mã. Giữ cả hai dòng, tên gốc và số thứ tự dòng.

### Giá trị và đơn vị

| Cột | Kiểu | Được trống? | Ý nghĩa |
|---|---|---:|---|
| `value_raw` | string | Có | Giá trị trước khi đổi kiểu, giúp điều tra lỗi parse |
| `value_numeric` | float | Có | Giá trị đổi sang số, chưa đổi đơn vị |
| `value_text` | string | Có | Giá trị dạng chữ nếu mục không phải số |
| `value_type` | string | Không | `money`, `ratio`, `count`, `text`, `unknown` |
| `currency` | string | Không | `VND`, `unknown`, `not_applicable` |
| `source_unit` | string | Không | Đơn vị nguồn công bố: `VND`, `thousand_VND`, `million_VND`, `unknown`, `not_applicable` |
| `unit_multiplier_to_vnd` | float | Có | `1`, `1000`, `1000000` hoặc null |
| `value_vnd` | float | Có | Chỉ có với mục tiền và đơn vị đã xác nhận |

Quy tắc đổi đơn vị:

```text
value_vnd = value_numeric × unit_multiplier_to_vnd
```

Data FireAnt và VCI đã thử đang ở dạng VNĐ đầy đủ nên dùng:

```text
currency = VND
source_unit = VND
unit_multiplier_to_vnd = 1
```

Chỉ số phần trăm/tỷ lệ dùng `currency = not_applicable` và không được đổi sang VNĐ.

Nếu đơn vị chưa rõ, để `unknown` và `value_vnd = null`; không tự đoán.

### Theo dõi chất lượng

| Cột | Kiểu | Được trống? | Ý nghĩa |
|---|---|---:|---|
| `record_status` | string | Không | `valid`, `source_null`, `parse_error`, `unmapped` |
| `quality_flags` | list[string] | Không | Danh sách cảnh báo; không có thì là danh sách rỗng |
| `collected_at` | datetime | Không | Có múi giờ |
| `raw_file` | string | Không | Đường dẫn về bằng chứng raw |

Ví dụ `quality_flags`:

- `duplicate_source_item_id`;
- `unknown_consolidation`;
- `missing_publication_date`;
- `unknown_unit`;
- `period_mismatch`;
- `cross_source_difference`.

## 5. Bảng trạng thái `bctc_collection_status`

Bảng này bắt buộc vì nguồn trả rỗng sẽ không tạo dòng trong `bctc_records`.

Một dòng được xác định bằng:

```text
source + provider + symbol + report_type + period_type
```

Các trạng thái:

| Trạng thái | Ý nghĩa |
|---|---|
| `pending` | Chưa làm |
| `running` | Đang làm |
| `complete` | Đã lấy đủ theo yêu cầu |
| `partial` | Có data nhưng thiếu một phần |
| `no_data_confirmed` | Nguồn trả hợp lệ nhưng không có data |
| `unsupported` | Nguồn không hỗ trợ loại yêu cầu này |
| `failed_retryable` | Lỗi tạm thời, có thể thử lại |
| `failed_fatal` | Token sai, yêu cầu sai, data lạ hoặc lỗi cần người xem |
| `cancelled` | Người dùng dừng |

Không đổi `no_data_confirmed` thành `failed`. Không đổi lỗi mạng thành `no_data_confirmed`.

## 6. Bảng ghép chỉ tiêu `bctc_item_mapping`

Bảng này dùng để nói mục FireAnt nào tương đương mục VCI nào.

Các cột tối thiểu:

- `mapping_version`;
- `canonical_item_id`;
- `provider`;
- `company_type`;
- `report_type`;
- `source_item_id`;
- `source_item_name`;
- `source_row_number` nếu cần phân biệt dòng trùng;
- `sign_multiplier` — mặc định `1`, không tự đảo dấu;
- `mapping_status`;
- `evidence` — lý do xác nhận;
- `reviewed_at`.

Quy tắc ghép:

1. Không ghép chỉ vì tên gần giống.
2. Phải cùng loại doanh nghiệp và loại báo cáo.
3. Phải hiểu cùng ý nghĩa kế toán.
4. Phải kiểm tra dấu âm/dương.
5. Phải kiểm tra ít nhất vài mã và vài kỳ.
6. Mapping chưa chắc chắn dùng `provisional` hoặc `unmapped`.
7. Không sửa raw để làm hai nguồn trông giống nhau.

## 7. Cách so hai nguồn

Chỉ so khi tất cả phần sau giống nhau:

- `symbol`;
- `canonical_item_id` đã `confirmed`;
- `period_key`;
- `period_value_mode`;
- `consolidation_status` hoặc cả hai đều `unknown` và báo rõ;
- `currency` và đơn vị đã đổi về cùng chuẩn.

Kết quả so sánh phải giữ hai cột riêng:

```text
fireant_value_vnd
vci_value_vnd
absolute_difference
difference_percent
```

Không tạo một cột `final_value` ở Bước 4. Chưa có quy tắc chọn nguồn thắng khi hai nguồn lệch.

## 8. Cách viết quý và năm

- Quý: `2026-Q2`.
- Năm: `2025`.
- Không dùng `Q2/2026`, `2Q2026` hoặc số `20262` trong bảng chung.
- `fiscal_quarter` chỉ nhận `1`, `2`, `3`, `4`.
- Báo cáo năm có `fiscal_quarter = null`.

## 9. Vị trí mục tiêu

Nguồn phải được phân folder giống cách dự án đang lưu OHLCV: `From_FireAnt` và `From_vnstock`.

**Folder nguồn nằm trước; loại báo cáo nằm bên trong.**

Các folder dưới đây là mục tiêu cho Bước 5–8, chưa được coi là đã triển khai chỉ vì có trong tài liệu:

```text
Phase_1_Data/E_BCTC/
├── From_FireAnt/
│   ├── Raw/{run_id}/{symbol}/...
│   └── Normalized/bctc_v1.1.0/
│       ├── Balance_Sheet/
│       ├── Income_Statement/
│       ├── Cash_Flow/
│       └── Ratio/
├── From_vnstock/
│   ├── Raw/{run_id}/{symbol}/...
│   └── Normalized/bctc_v1.1.0/
│       ├── Balance_Sheet/
│       ├── Income_Statement/
│       ├── Cash_Flow/
│       └── Ratio/
├── Curated/bctc_v1.1.0/...
├── Status/...
└── Mappings/...
```

Quy ước tên file Normalized:

```text
From_FireAnt/.../{SYMBOL}_{report_type}_{period_type}_fireant.parquet
From_vnstock/.../{SYMBOL}_{report_type}_{period_type}_vci.parquet
```

Ví dụ:

```text
Phase_1_Data/E_BCTC/From_FireAnt/Normalized/bctc_v1.1.0/Income_Statement/VNM_income_statement_quarter_fireant.parquet
Phase_1_Data/E_BCTC/From_vnstock/Normalized/bctc_v1.1.0/Income_Statement/VNM_income_statement_quarter_vci.parquet
```

Tên folder dùng `From_vnstock` để đồng bộ với kho OHLCV. Cột `provider` bên trong file vẫn phải ghi rõ `vci`; nếu sau này thử KBS, file KBS không được dùng hậu tố `_vci`.

Raw của FireAnt, VCI và KBS không được ghi đè lẫn nhau. Folder nguồn không thay thế cột `source` và `provider`; phải có cả hai để file bị di chuyển vẫn truy ra nguồn.

Các folder BCTC đang tồn tại trực tiếp như `Balance_Sheet`, `Income_Statement`, `Cash_Flow` và `Ratio` là cấu trúc cũ. Collector mới không được ghi thêm vào đó. Việc kiểm kê/chuyển data cũ phải là một tác vụ riêng, không tự di chuyển trong Bước 4.

## 10. Quy tắc thay đổi phiên bản

- Sửa mô tả nhưng không đổi cột/ý nghĩa: giữ nguyên phiên bản hiện hành.
- Thêm cột không bắt buộc: tăng phần giữa, ví dụ `bctc_v1.1.0`.
- Đổi tên, xóa cột hoặc đổi ý nghĩa: tăng phiên bản lớn, ví dụ `bctc_v2.0.0`.
- Collector, checkpoint và output phải ghi phiên bản đang dùng.
- Không tiếp tục checkpoint cũ nếu phiên bản không tương thích.

Lịch sử phiên bản:

- `bctc_v1.0.0`: mẫu ban đầu ở Bước 4.
- `bctc_v1.1.0`: thêm `source_period_column_number` để giữ và phân biệt cột kỳ trùng của VCI; không xóa data nguồn.

Khi đọc data 1.0 cũ không có cột này, phần migrate được phép thêm giá trị `1`. Quy tắc này chỉ dùng để tương thích với mẫu cũ; normalizer 1.1 bắt buộc tạo số thật từ vị trí cột nguồn.

## 11. Những điều bị cấm

- Không tự điền ngày công bố bằng ngày cuối quý.
- Không tự gọi báo cáo là hợp nhất.
- Không xóa dòng trùng chỉ để khóa trở nên đẹp.
- Không đổi dấu số tiền mà không có mapping được duyệt.
- Không lấy KBS bù vào VCI mà không ghi nguồn.
- Không coi FireAnt và VCI là hai xác nhận độc lập.
- Không ghi token, cookie hoặc mật khẩu vào data/log.
- Không tạo `final_value` khi chưa có quy tắc chọn nguồn.

## 12. Điều kiện Bước 4 đã đáp ứng

- Có thông tin cần giữ ở raw.
- Có cột của bảng chung.
- Có cách giữ dòng trùng.
- Có cách viết quý/năm.
- Có cách ghi và đổi đơn vị.
- Có cách ghi hợp nhất/riêng lẻ chưa biết.
- Có cách ghi quý riêng/cộng dồn.
- Có bảng trạng thái đầy đủ.
- Có bảng ghép chỉ tiêu giữa hai nguồn.
- Không chọn nguồn thắng khi data lệch.
- Mẫu dùng được cho bốn loại doanh nghiệp.
