# Chương 10 — Phase 1: Chuẩn bị Data

> **Trạng thái:** PARTIALLY IMPLEMENTED — collector và một số validator đã có; chưa được coi là hoàn thành toàn Phase chỉ vì đã có nhiều file Parquet.
>
> **Agent phải đọc file này khi:** làm universe mã, cào vnstock/FireAnt/BCTC, làm sạch/kiểm tra Phase 1 hoặc thay output contract Phase 1.
>
> **Roadmap gốc:** [19-MONTH_PLANNING.md](../19-MONTH_PLANNING.md) — thời lượng 1 tháng, bắt buộc kiểm tra giá điều chỉnh và không bỏ qua mã đã hủy niêm yết/ngừng giao dịch.
>
> **Timeline suy ra:** Tháng 1 của roadmap 19 tháng.

## 10.1. Mục tiêu Phase

Phase 1 tạo nền móng dữ liệu đáng tin cho tất cả Phase sau:

1. Xác định đầy đủ universe chứng khoán, gồm cả mã còn hoạt động và mã đã chết/delisted khi nguồn cho phép.
2. Thu thập OHLCV, dữ liệu khối ngoại và BCTC với provenance rõ.
3. Xác minh cột giá dùng cho phân tích là giá điều chỉnh theo yêu cầu roadmap.
4. Làm sạch/chuẩn hóa mà không phá raw data.
5. Xuất data contract versioned cho Phase 2 và Phase 3.

“Cào xong” không đồng nghĩa “data đúng”. Phase chỉ đạt khi vượt quality gate ở §10.9.

## 10.2. Hiện trạng và mục tiêu

### Đã tồn tại trong repo

```text
Main Scripts/Phase 1/
├── 1.1_Data_OHLCV/
│   ├── E_data_collector.py
│   ├── E_data_raw_cross_check.py
│   └── E_Data_Checkers/
└── 1.2_Data_BCTC/
    ├── E_bctc_collector.py       File cũ, chỉ tham chiếu
    ├── E_fireant_bctc_client.py
    ├── E_vci_bctc_client.py
    ├── E_bctc_raw_repository.py
    ├── E_bctc_progress_repository.py
    ├── E_bctc_schema.py
    ├── E_bctc_normalizer.py
    ├── E_bctc_validator.py
    ├── E_bctc_cross_checker.py
    ├── E_bctc_manager.py
    └── E_bctc_pilot.py

tests/unit/phase_1/
├── test_ohlcv_validators.py
├── test_bctc_clients.py
├── test_bctc_repositories.py
├── test_bctc_normalizer.py
├── test_bctc_validator.py
├── test_bctc_cross_checker.py
└── test_bctc_manager.py

Phase_1_Data/
├── E_OHLCV/
└── E_BCTC/
```

### Chưa được mặc định coi là hoàn thành

- Chưa có `1.2_Data_Cleaner/` rõ ràng.
- Chưa có bằng chứng tự động rằng giá là adjusted price trên các ngày corporate action.
- Universe hiện tại chưa chứng minh bao phủ delisted symbols.
- Bộ test offline hiện đã phủ Client, ghi Raw, resume, Normalizer, Validator, Cross-check và Manager BCTC. Việc nguồn thật có đổi response hay không vẫn chỉ được chứng minh ở các bước chạy thử có kiểm soát, không được suy ra từ unit test.

Agent phải kiểm tra lại repo tại thời điểm làm task; danh sách trên là snapshot tài liệu, không thay thế việc kiểm tra.

`E_bctc_collector.py` trong `1.2_Data_BCTC/` là collector cũ, chỉ giữ để tham chiếu. Luồng BCTC mới không được tự gọi file này. Hai cổng lấy data hiện hành là `E_fireant_bctc_client.py` và `E_vci_bctc_client.py` cùng folder.

### Quyết định nguồn data hiện tại

Kết quả thử ngày 2026-08-09 đã chốt cách dùng nguồn cho Phase 1:

| Loại data | Nguồn chính | Nguồn thứ hai/kiểm tra | Quy tắc |
|---|---|---|---|
| OHLCV và data giao dịch bổ sung | vnstock theo collector hiện hành | FireAnt | Giữ hai nguồn riêng để phát hiện phần thiếu; không trộn âm thầm |
| BCTC trong nhánh vnstock | `VCI` | `KBS` | `VCI` là nguồn chính; `KBS` chỉ kiểm tra phụ khi tên kỳ đã được xác nhận |
| BCTC từ nguồn thứ hai | FireAnt | vnstock/VCI để đối chiếu độ phủ | Giữ raw riêng; hai nhánh có dấu hiệu dùng chung data nền nên không coi là hai xác nhận độc lập |

Lý do chọn `VCI`: bài thử trên doanh nghiệp thường và ngân hàng cho lịch sử dài hơn KBS, đủ bốn nhóm BCTC và tên kỳ đáng tin hơn KBS. KBS trong lần thử bị thiếu cân đối kế toán, thiếu chỉ số theo quý và gắn sai một số tên kỳ.

Bài thử 13 mã cho thấy FireAnt thường có lịch sử sâu và phủ mã nhỏ tốt hơn VCI. Tuy nhiên 27/27 giá trị đối chiếu giữa FireAnt và VCI giống nhau tuyệt đối. Đây là dấu hiệu mạnh hai nhánh có thể dùng chung data nền hoặc cùng cách chuẩn hóa. Agent vẫn giữ hai raw riêng để tăng độ phủ, nhưng không được gọi chúng là hai nguồn xác nhận độc lập. Muốn kiểm tra độ đúng thật sự cần BCTC công bố gốc hoặc nguồn thứ ba độc lập.

Quyết định này không có nghĩa VCI luôn đúng. VCI vẫn có mã mục trùng và lỗi cột trùng ở phần chỉ số theo năm. Agent phải giữ lỗi để làm sạch/kiểm tra, không xóa hoặc đổi tên lấp liếm.

## 10.3. Luồng chuẩn và hướng phụ thuộc

```text
Universe/Config
      ↓
Collector/Client → Raw/Latest Repository
      ↓
Cleaner/Normalizer
      ↓
Validator + Cross-check
      ↓
Curated Phase 1 output + Quality Report
```

- Manager điều phối flow; Collector không gọi ngược Manager/UI.
- Calculator/Validator nhận DataFrame qua tham số; không tự đọc path dự án.
- Repository chịu trách nhiệm đọc/ghi atomic.
- Cleaner không gọi API.
- Phase 2 đọc output qua data contract, không import Collector.

Riêng BCTC, luồng hiện hành là:

```text
Manager (viết ở bước sau)
      ↓
E_fireant_bctc_client.py ─┐
                          ├─→ Kết quả có tên nguồn và trạng thái
E_vci_bctc_client.py ─────┘
      ↓
E_bctc_raw_repository.py + E_bctc_progress_repository.py
      ↓
From_FireAnt/... hoặc From_vnstock/...
```

- Mỗi client chỉ gọi đúng nguồn của nó và trả kết quả; không tự ghi Parquet, không tự quản lý sổ tiến độ và không tự chuyển nguồn.
- File FireAnt ghi nguồn là `fireant/fireant_api`; file VCI ghi nguồn là `vnstock/vci`.
- VCI không tự chuyển sang KBS khi lỗi hoặc thiếu data.
- Test thay cổng gọi thật bằng data giả. Bộ test mặc định không gọi Internet.
- `E_bctc_raw_repository.py` ghi raw và metadata; không gọi nguồn, không normalized data và không giữ sổ tiến độ.
- `E_bctc_progress_repository.py` giữ sổ tiến độ; không gọi nguồn và không ghi raw.
- `E_bctc_normalizer.py` chỉ nhận raw qua tham số và trả bảng theo `bctc_v1.1.0`; không gọi nguồn, không đọc/ghi file và không sửa raw đầu vào.
- `E_bctc_schema.py` là nguồn duy nhất trong code cho version và danh sách cột BCTC; không chứa logic nghiệp vụ.
- `E_bctc_validator.py` chỉ nhận bảng/status/lỗi đọc qua tham số và trả báo cáo; không tự đọc/ghi file, không sửa data và không chọn nguồn thắng.
- `E_bctc_cross_checker.py` chỉ nhận hai bảng đã chuẩn hóa qua tham số và trả bảng đối chiếu; chỉ ghép mapping `confirmed`, không coi data thiếu là 0, không tự chọn nguồn thắng và không tự đọc/ghi file.
- `E_bctc_manager.py` là nơi duy nhất ráp thứ tự Client → Raw Repository → Normalizer → Validator → Cross-check → Progress Repository. Manager nhận mọi thành phần qua tham số, không viết lại logic của chúng và không tự chuyển VCI sang KBS.
- `E_bctc_pilot.py` là lệnh chạy thật có kiểm soát, mặc định chạy tuần tự từng mã, ghi summary JSON vào `E_BCTC/state/pilot_runs/` và dùng lại toàn bộ Manager/dependency hiện hành.
- Sổ tiến độ nằm tại `Phase_1_Data/E_BCTC/state/runs/{run_id}.json`. Mỗi item được nhận dạng bằng nguồn, provider, mã, loại báo cáo và quý/năm.

Tham chiếu: [EF-S-00 §0.2–0.7](./EF-S-00_Dependency_Direction.md), [EF-S-03 §3.2–3.6](./EF-S-03_Data_Pipeline.md).

## 10.4. Kế hoạch 1 tháng

| Chặng | Việc chính | Kết quả phải có |
|---|---|---|
| 1. Universe & contract | Chốt danh sách mã, nguồn, schema, adjusted-price definition | Universe snapshot + schema v1 |
| 2. Extract | Cào OHLCV/khối ngoại/BCTC có retry/resume | Raw/latest files + batch report |
| 3. Clean & normalize | Chuẩn tên cột, type, timezone, duplicate/null policy | Curated files không sửa raw |
| 4. Validate & close gate | Cross-check nguồn, adjusted price, delisted coverage | Quality report + test evidence |

Nếu thời gian thực tế thay đổi, roadmap được cập nhật; Agent không được lược bỏ quality gate chỉ để giữ mốc một tháng.

## 10.5. Hai constraint bắt buộc từ roadmap

### Giá điều chỉnh

Agent không được mặc định cột `close` từ API là adjusted price chỉ dựa vào tên cột.

Phải có:

- định nghĩa nguồn dùng loại điều chỉnh nào;
- sample có chia cổ tức/chia tách để cross-check;
- metadata ghi `price_adjustment` và source/version;
- test đảm bảo Series dùng cho return/indicator đúng contract.

Nếu nguồn không cung cấp adjusted price đáng tin, Agent phải báo và đề xuất cách điều chỉnh; không tự chế hệ số.

### Không bỏ qua mã đã chết/delisted

Chỉ lấy danh sách mã đang niêm yết hôm nay sẽ tạo **survivorship bias**: nhìn quá khứ bằng danh sách “người sống sót”, làm backtest đẹp giả.

Universe phải lưu theo snapshot và có khi có thể:

- symbol;
- sàn;
- ngày niêm yết/hủy niêm yết hoặc trạng thái;
- nguồn và thời điểm lấy danh sách;
- lý do thiếu data.

Mã không cào được không được xóa khỏi universe. Nó nằm trong failure report để điều tra.

## 10.6. Raw, latest và curated data

Không gọi toàn bộ `Phase_1_Data/` là immutable.

| Loại | Ý nghĩa | Được thay? |
|---|---|---:|
| Raw snapshot | Response/data gốc theo run/date nếu được lưu | Không |
| Latest/working | Bản hoàn chỉnh mới nhất cho một symbol/source | Có, bằng atomic replace |
| Curated | Bản đã chuẩn hóa cho Phase sau | Có thể rebuild theo schema/version |
| Quality report | Kết quả kiểm tra của một run | Không ghi đè run cũ |

Cleaner không sửa file raw tại chỗ. Output làm sạch phải có folder/schema version rõ trước khi triển khai.

## 10.7. Output contract tối thiểu

### OHLCV và khối ngoại

```text
Phase_1_Data/E_OHLCV/From_vnstock/{SYMBOL}_historical_vnstock.parquet
Phase_1_Data/E_OHLCV/From_FireAnt/{SYMBOL}_historical_fireant.parquet
```

Contract phải nêu: `symbol`, datetime/timezone, OHLCV columns, adjusted-price status, unit, null policy, source và `schema_version`.

### BCTC

```text
Phase_1_Data/E_BCTC/From_FireAnt/{Report_Type}/...
Phase_1_Data/E_BCTC/From_vnstock/{Report_Type}/...
```

Không hardcode “mỗi mã luôn có đúng 9 file”. Nguồn có thể thiếu report/period; completeness phải được đo và báo theo contract.

Mỗi file BCTC bắt buộc ghi rõ `source`. Trong nhánh vnstock, giá trị chuẩn hiện tại là `VCI`; `KBS` không được tự động thay thế khi VCI thiếu. Raw từ VCI, KBS và FireAnt phải tách riêng hoặc có tên file/metadata đủ rõ để không ghi đè lẫn nhau.

Folder BCTC mới phải tách nguồn giống OHLCV:

```text
Phase_1_Data/E_BCTC/From_FireAnt/...
Phase_1_Data/E_BCTC/From_vnstock/...
```

Folder nguồn nằm trước loại báo cáo. Dù đã tách folder, mỗi file vẫn phải có cột `source` và `provider`. Các folder loại báo cáo nằm trực tiếp dưới `E_BCTC` là cấu trúc cũ; collector mới không ghi thêm vào đó.

Trước khi ghép hai nguồn, phải xác nhận cùng mã, cùng loại báo cáo, cùng kỳ, cùng dạng báo cáo hợp nhất/riêng lẻ và cùng đơn vị tiền. Nếu một trong các phần này chưa rõ, giữ riêng và báo lỗi.

Mẫu dữ liệu BCTC hiện hành: [BCTC Data Contract `bctc_v1.1.0`](../E_Implementation/260809_BCTC_Data_Contract_v1.md). Phiên bản 1.1 thêm số thứ tự cột kỳ để giữ cột VCI bị trùng. Collector và phần ghi file mới phải theo contract này. Nếu cần đổi tên/xóa cột hoặc đổi ý nghĩa, phải nâng phiên bản; không sửa âm thầm.

Quy tắc sắp BCTC hiện hành:

- VCI đã biết loại báo cáo từ cổng gọi, nên có thể chuyển mỗi dòng mục tài chính và mỗi cột kỳ thành một record chung.
- Dòng VCI trùng `item_id` và cột kỳ trùng đều được giữ; `source_row_number` và `source_period_column_number` giúp phân biệt.
- FireAnt trả chung nhiều nhóm chỉ tiêu trong `financialValues`. Chỉ mục có bằng chứng mapping mới được gắn `report_type`, loại giá trị và đơn vị; mục còn lại giữ đầy đủ nhưng dùng `unknown`.
- Ba mục FireAnt đã xác nhận ở Bước 3 là `TotalAsset`, `ProfitAfterTax` và `CashflowFromOperatingActivity`.
- Không điền ngày công bố/ngày có thể sử dụng, không đoán hợp nhất/riêng lẻ và không đổi đơn vị khi chưa có rule xác nhận.
- Báo cáo tỷ lệ dùng `not_applicable` cho tiền tệ và không tạo `value_vnd`.

Quy tắc kiểm tra BCTC hiện hành:

- Báo cáo Validator tách `errors`, `warnings` và `skipped_checks`. Chỉ không có `errors` mới được coi là qua cổng cấu trúc.
- `is_valid = true` không có nghĩa mọi con số kế toán đã được xác nhận; cảnh báo và phép kiểm tra bị bỏ qua vẫn phải xuất trong quality report.
- File được Repository/Manager đọc; nếu đọc lỗi thì truyền lỗi vào Validator. Validator không tự mở path để giữ đúng hướng phụ thuộc.
- Chặn sai schema, mã/nguồn/provider, kỳ tương lai, quý/năm trộn, dòng/khóa trùng, parse lỗi, sai đơn vị/hệ số và trạng thái rỗng giả thành công.
- Công thức tài chính chỉ dùng `canonical_item_id` có `mapping_status = confirmed`. Thiếu hoặc trùng chỉ tiêu thì ghi skipped; không ghép theo tên gần giống.
- Sai số công thức dựa trên đơn vị làm tròn (`VND`, nghìn VNĐ, triệu VNĐ) và quy mô con số; không dùng một ngưỡng duy nhất.

Quy tắc đối chiếu BCTC hiện hành:

- Chỉ ghép cùng mã, `canonical_item_id` đã xác nhận, loại báo cáo, loại kỳ, kỳ báo cáo, dạng giá trị trong kỳ và trạng thái hợp nhất/riêng lẻ.
- Hai bên cùng ghi trạng thái hợp nhất là `unknown` vẫn được so nhưng kết quả phải mang cờ `unknown_consolidation`.
- Khác loại báo cáo, dạng giá trị trong kỳ hoặc trạng thái hợp nhất/riêng lẻ phải ghi `not_comparable` và lý do cụ thể; không giả thành data thiếu.
- Data chỉ có ở FireAnt hoặc vnstock phải giữ nguyên số phía có data; phía thiếu để trống, không điền 0.
- Mapping chưa xác nhận, đơn vị chưa rõ, giá trị chưa đổi được về VNĐ hoặc khóa so bị trùng đều phải ghi `not_comparable`.
- Kết quả giữ riêng số FireAnt, số vnstock, độ lệch tuyệt đối và phần trăm lệch; không tạo `final_value`.

VCI có thể trả cột năm lẫn trong bảng được yêu cầu theo quý, đặc biệt ở nhóm `ratio`. Raw phải giữ nguyên toàn bộ. Normalizer chỉ lấy đúng loại kỳ đang xử lý và gắn cờ `source_mixed_period_columns`; cột còn lại được xử lý ở work item năm/quý riêng. Không được đổi tên cột năm thành quý hoặc xóa dấu vết nguồn trộn kỳ.

Trong bảng `ratio`, các dòng `year`, `quarter`, `ratioTTMId` và `ratioType` là thông tin mô tả bảng, không phải chỉ số tài chính. Raw vẫn giữ chúng; Normalizer không tạo record tài chính từ các dòng này. Không được coi chữ `RATIO_TTM` là lỗi đổi số của một chỉ tiêu.

Nếu VCI trả nhiều cột trùng tên mà Parquet không chấp nhận, Repository thêm hậu tố kỹ thuật theo vị trí chỉ trong file lưu và ghi đầy đủ mapping tên gốc → tên lưu trong metadata. Không gộp, xóa hoặc chọn một cột đại diện.

Riêng `ratio` theo năm, nguồn có thể trả cột của năm hiện tại dưới dạng YTD. Validator giữ lại với cảnh báo `current_year_ratio_incomplete`; không được gọi đó là tỷ lệ cả năm đã chốt. BCTC năm hiện tại của cân đối/kết quả/dòng tiền và mọi kỳ lớn hơn năm hiện tại vẫn bị chặn như kỳ tương lai.

Quy tắc chạy Manager BCTC hiện hành:

- FireAnt dùng một work item `financial_data` cho mỗi mã và loại kỳ vì cổng này trả một gói chỉ tiêu tổng hợp; VCI dùng work item riêng cho từng loại báo cáo.
- Mục đã có trạng thái cuối hợp lệ trong sổ tiến độ không được gọi nguồn lần nữa.
- Data nhận ít kỳ hơn yêu cầu phải ghi `partial`; data rỗng hợp lệ ghi `no_data_confirmed` và không tạo raw rỗng.
- Lỗi tạm thời ở một nguồn ghi `failed_retryable` và không chặn nguồn còn lại. Lỗi token/config/schema/Validator hoặc ghi file ghi `failed_fatal` và dừng đợt hiện tại.
- Người dùng yêu cầu dừng hoặc nhấn ngắt phải kết thúc gọn; item đang dở được để ở trạng thái có thể làm lại khi mở tiếp.
- Manager trả kết quả từng item, bảng đối chiếu và tổng số theo trạng thái; log tổng kết dùng `E_BlackBox` cạnh file Manager.

Đối với BCTC, cần giữ cả **reporting period** và **public/available date** nếu nguồn cung cấp. Phase 3/4 chỉ được dùng thông tin đã công bố tại thời điểm dự đoán để tránh nhìn tương lai.

## 10.8. Error, retry, resume và logging

- Hai client BCTC thử tối đa 3 lần; chỉ thử lại khi mất mạng, hết thời gian chờ, nguồn báo gọi quá nhanh hoặc máy chủ tạm lỗi. Thời gian chờ tăng dần sau mỗi lần lỗi.
- FireAnt giới hạn chờ 30 giây. VCI/vnstock hiện giới hạn lần gọi chính ở 30 giây và bước bắt tay ở 10 giây; Finance API hiện chưa cho client truyền con số khác.
- Không retry schema sai, token sai hoặc request logic sai.
- Data rỗng hợp lệ trả `no_data_confirmed`, không bị coi là lỗi để thử lại.
- Raw FireAnt giữ JSON; raw VCI giữ Parquet. Mỗi raw có metadata cạnh bên, gồm nguồn, tham số không chứa secret, thời gian lấy, phiên bản thư viện, mã kiểm tra nội dung và đường dẫn raw.
- Raw cùng `run_id` không bị ghi đè. Nếu máy ngắt sau khi raw đã xong nhưng trước metadata, lần mở lại chỉ nhận file khi nội dung trùng hoàn toàn; nếu khác thì dừng để người kiểm tra.
- `complete` phải có file raw thật và đủ số kỳ. Có data nhưng thiếu kỳ dùng `partial`; data rỗng hợp lệ không tạo file giả.
- Khi resume, item đang `running` của lần bị ngắt chuyển thành `failed_retryable`. Sổ cũ có schema hoặc kế hoạch cào khác bị từ chối.
- Một symbol lỗi được ghi vào failure summary; batch có thể tiếp tục.
- Batch fail nếu không thu được output usable hoặc vượt ngưỡng thất bại đã duyệt.
- Resume phải kiểm tra output complete/schema đúng; không chỉ thấy file tồn tại là bỏ qua.
- Auto/batch ghi qua `E_BlackBox`; log nằm cạnh script sở hữu tính năng và có run ID, source, symbol, success/failure.

Tham chiếu: [EF-S-02 §2.5–2.8](./EF-S-02_Error_Handling.md), [EF-S-04 §4.2–4.11](./EF-S-04_Logging_Debug.md).

## 10.9. Cleaning, thư viện và config

Roadmap nhắc Scikit-Learn cho cleaning. Ý định bắt buộc là **data phải được làm sạch đúng**, không phải cài Scikit-Learn bằng mọi giá.

- Dùng pandas/validator cho parse type, duplicate, range và schema thông thường.
- Chỉ dùng Scikit-Learn khi cần transformer/imputation/scaling phù hợp và đã duyệt theo EF-S-06.
- Không impute raw financial data rồi ghi đè mà không lưu policy/indicator missingness.
- Secret nằm trong `System/.env`.
- Config không chứa secret và dùng tên/path tập trung từ `E_Helper/E_config.py`.

## 10.10. Testing và quality gate

Test/validation tối thiểu:

- schema, type, timezone và uniqueness theo symbol/date;
- `low <= open/close <= high`, volume không âm và các invariant nguồn;
- duplicate/missing date theo lịch giao dịch phù hợp;
- adjusted price cross-check trên corporate action sample;
- coverage của universe, gồm delisted/inactive khi có dữ liệu;
- BCTC period/publication date không đảo ngược;
- atomic write không làm hỏng file đích khi lỗi;
- parser dùng fixture/sample, default suite không gọi mạng.

Cross-source row count hoặc giá khác nhau không tự động nghĩa một nguồn sai; cần so cùng định nghĩa, timezone và adjusted status.

## 10.11. Definition of Done cho Phase 1

- [ ] Universe có snapshot, provenance và chiến lược delisted rõ.
- [ ] Adjusted price đã được chứng minh bằng tài liệu/source sample/test.
- [ ] Raw không bị Cleaner sửa tại chỗ.
- [ ] Latest/curated output có schema version và metadata.
- [ ] Collector có timeout/retry/resume/failure summary đúng EF-S.
- [ ] BCTC giữ thời điểm công bố nếu có.
- [ ] Quality report định lượng success/failure/missing/duplicate.
- [ ] Test mặc định chạy offline và kết quả thật được ghi nhận.
- [ ] Phase 2 có thể đọc output chỉ dựa vào data contract.
- [ ] Phần chưa lấy được, đặc biệt delisted/adjusted price, được báo rõ chứ không giấu.
