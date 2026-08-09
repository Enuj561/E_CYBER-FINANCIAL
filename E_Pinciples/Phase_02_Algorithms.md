# Chương 11 — Phase 2: Thuật toán và Features

> **Trạng thái:** PLANNED — chưa được coi là đã triển khai chỉ vì roadmap đã nêu tên indicator/thư viện.
>
> **Agent phải đọc file này khi:** học/định nghĩa RSI, MACD, Bollinger hoặc indicator khác; tạo Calculator/Validator; build `Phase_2_Data`; kiểm tra độ chính xác công thức.
>
> **Roadmap gốc:** [19-MONTH_PLANNING.md](../19-MONTH_PLANNING.md) — thời lượng 3 tháng, học ý nghĩa thuật toán, viết và kiểm tra độ chính xác; TA-Lib/pandas-ta chỉ là phương án tham khảo.
>
> **Timeline suy ra:** Tháng 2–4, sau khi Phase 1 vượt quality gate.

## 11.1. Mục tiêu Phase

Phase 2 biến dữ liệu giá/BCTC đã chuẩn hóa thành features có ý nghĩa và có thể kiểm chứng:

1. Hiểu mỗi indicator đo cái gì và điều kiện dùng.
2. Ghi rõ công thức/biến thể trước khi code.
3. Implement theo pure function hoặc wrapper rõ ràng.
4. Cross-check với nguồn/thư viện độc lập.
5. Ngăn look-ahead leakage.
6. Xuất feature contract versioned cho Phase 3.

Mục tiêu không phải tạo càng nhiều indicator càng tốt. Feature chỉ được thêm khi có lý do, contract và test.

## 11.2. Hiện trạng và điều kiện bắt đầu

Tại snapshot tài liệu này, `Main Scripts/Phase 2/` và `Phase_2_Data/` chưa tồn tại.

Trước khi bắt đầu:

- Phase 1 phải có data contract usable.
- Adjusted-price definition phải rõ.
- Timezone, duplicate và missing-date policy phải rõ.
- Chọn/pin thư viện cross-check theo [EF-S-06 §6.4–6.9](./EF-S-06_Library_Catalog.md).
- Chốt danh sách indicator đầu tiên và định nghĩa từng biến thể.

Không cài đồng loạt TA-Lib, pandas-ta và pandas-ta-classic “để dành”.

## 11.3. Kế hoạch 3 tháng

| Tháng | Trọng tâm | Kết quả phải có |
|---|---|---|
| 2 | Học ý nghĩa, công thức, input và biến thể | Indicator specification + reference samples |
| 3 | Implement/cross-check RSI, MACD, Bollinger và nhóm ưu tiên | Calculator + Validator + unit tests |
| 4 | Feature pipeline, schema, versioning và performance | `Phase_2_Data/Features/` + quality report |

Roadmap có thể được cập nhật nếu accuracy gate chưa đạt. Không được chuyển Phase 3 chỉ vì hết tháng 4.

## 11.4. Luồng chuẩn và hướng phụ thuộc

```text
Phase 1 Repository/Data Contract
              ↓
Phase 2 Manager
      ↓               ↓
Calculator         Validator/Cross-check
      ↓               ↓
Feature Repository → Phase_2_Data/Features/
```

- Calculator nhận Series/DataFrame/config qua tham số.
- Calculator không đọc Parquet, không gọi API, không ghi file và không biết Phase 3.
- Repository/Manager đọc Phase 1 và ghi Phase 2.
- Validator so kết quả theo contract/tolerance.
- Phase 3 đọc feature output; không import chéo Calculator chỉ để tính lại ngầm.

Tham chiếu: [EF-S-00 §0.2–0.7](./EF-S-00_Dependency_Direction.md), [EF-S-01 §1.6–1.9](./EF-S-01_Data_Structure.md).

## 11.5. Cấu trúc mục tiêu tối thiểu

Chỉ tạo module khi có trách nhiệm thật:

```text
Main Scripts/Phase 2/
├── E_indicator_calculator.py        Canonical implementations/wrappers
├── E_indicator_validator.py         Range, alignment, NaN/warm-up checks
├── E_indicator_crosscheck.py        So với reference/library; không dùng làm production path
├── E_feature_manager.py             Điều phối build feature
└── E_feature_repository.py          Đọc/ghi feature contract

tests/unit/phase_2/
├── test_rsi.py
├── test_macd.py
└── test_bollinger.py
```

Nếu file calculator phình thành nhiều nhóm trách nhiệm, tách theo nhóm indicator có chủ đích; không tạo một file cho mỗi hàm vài dòng một cách máy móc.

## 11.6. Specification trước khi viết công thức

Mỗi indicator phải ghi:

- mục đích và ý nghĩa tài chính;
- input column và adjusted/raw status;
- parameter/default;
- công thức hoặc thư viện canonical;
- biến thể smoothing (`SMA`, `EMA`, Wilder...) nếu có;
- warm-up period và NaN policy;
- output column/type/unit/range;
- timestamp alignment;
- reference implementation/dataset;
- tolerance cross-check.

Ví dụ tên “RSI 14” chưa đủ: RSI dùng Wilder smoothing có thể khác RSI dùng rolling mean. Không được gọi hai biến thể khác nhau là bug chỉ vì số không giống nhau.

## 11.7. Tự code và dùng thư viện

Roadmap yêu cầu viết thuật toán và kiểm tra độ chính xác. Thực hiện theo hai đường:

1. **Learning/reference implementation:** tự code rõ công thức để hiểu và tạo test.
2. **Production candidate:** dùng implementation đã được benchmark/cross-check tốt nhất — có thể là code nội bộ hoặc wrapper thư viện đã duyệt.

Sau khi chốt production path, chỉ có **một nguồn canonical** cho mỗi indicator. Không giữ hai implementation production song song rồi chọn tùy lúc.

TA-Lib/pandas-ta/pandas-ta-classic là CANDIDATE theo EF-S-06. Agent phải so license, Python/Windows compatibility, công thức, performance và maintenance trước khi đề xuất chọn.

## 11.8. Correctness và leakage

Calculator phải xử lý rõ:

- input chưa sort hoặc duplicate timestamp;
- input ngắn hơn warm-up;
- NaN/inf/division by zero;
- gap ngày giao dịch;
- giá/volume không hợp lệ;
- index/timestamp bị lệch sau rolling calculation;
- không dùng dữ liệu tương lai để tạo feature tại thời điểm `t`.

Feature tại ngày `t` chỉ dùng dữ liệu có sẵn tới `t` theo contract. Nếu chiến lược chỉ được giao dịch ngày `t+1`, timestamp phải nói rõ để Phase 3/4 không hiểu sai.

Không tự động `dropna()` toàn DataFrame mà không báo số dòng bị mất; thao tác này có thể làm lệch symbol/date hoặc tạo bias.

## 11.9. Error handling

Phase 2 nghiêm ngặt với sai công thức/schema, nhưng không có nghĩa dùng `assert` cho mọi input production.

- `ValueError`/domain error cho input không hợp lệ.
- `assert` chủ yếu cho invariant nội bộ/test, vì Python có thể chạy với assert bị tắt.
- Không catch rồi trả Series rỗng/NaN để giấu lỗi schema.
- Warm-up NaN hợp lệ phải là contract, không log như exception.
- Batch nhiều symbol được phép gom failure theo symbol; output partial phải ghi rõ status và không được coi là complete dataset.

Tham chiếu: [EF-S-02 §2.1–2.7](./EF-S-02_Error_Handling.md).

## 11.10. Output contract

```text
Phase_2_Data/Features/{SYMBOL}_features.parquet
```

Mỗi output/run phải có:

- `schema_version` và feature-set version;
- symbol + timestamp/timezone;
- tên feature chứa parameter khi cần, ví dụ `rsi_14_wilder`;
- nguồn giá và adjusted-price status;
- warm-up/missing policy;
- input range/fingerprint và created_at;
- status complete/partial + failure summary.

Feature data là rebuildable từ Phase 1 + config + code version. Snapshot được tạo khi cần tái hiện một experiment Phase 3.

## 11.11. Testing và cross-check gate

Mỗi indicator cần:

- hand-calculated/reference sample nhỏ;
- property/invariant test phù hợp;
- cross-check với thư viện/source độc lập bằng tolerance đã giải thích;
- test constant/up/down/flat/short/NaN/gap/extreme input;
- test không nhìn tương lai: thay đổi dữ liệu sau `t` không được đổi feature tại/before `t`;
- test index/time alignment;
- performance smoke test trên data gần kích thước thật.

Với Series, dùng pandas-aware assertion như `.between(...).all()` trên phần valid; không viết chained boolean cho cả Series.

## 11.12. Definition of Done cho Phase 2

- [ ] Danh sách feature v1 có lý do và specification.
- [ ] Mỗi indicator có canonical implementation duy nhất.
- [ ] Library production/cross-check đã được audit và pin, hoặc code nội bộ có bằng chứng tương đương.
- [ ] Warm-up, NaN, adjusted price và timestamp alignment rõ.
- [ ] Không có look-ahead leakage trong feature generation.
- [ ] Cross-check/test biên đạt tolerance đã giải thích.
- [ ] Output có schema/feature-set version và provenance.
- [ ] Partial build không bị báo thành complete.
- [ ] Phase 3 có thể đọc feature output qua contract mà không import chéo Phase 2.
