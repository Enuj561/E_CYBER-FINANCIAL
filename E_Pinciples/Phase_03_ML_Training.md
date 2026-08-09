# Chương 12 — Phase 3: ML Training

> **Trạng thái:** PLANNED — Phase lõi nhưng chưa được coi là đã chọn xong framework/model.
>
> **Agent phải đọc file này khi:** thiết kế target/features/split, thử PyCaret/XGBoost/LightGBM/CatBoost, train/tune/blend, lưu model/metrics hoặc đưa sentiment vào ML.
>
> **Roadmap gốc:** [19-MONTH_PLANNING.md](../19-MONTH_PLANNING.md) — thời lượng 6 tháng; so sánh ba dòng gradient boosting; bắt buộc walk-forward/time-series validation; theo dõi RAM/thời gian; xem xét blend; đổi investment context thì retrain.
>
> **Timeline suy ra:** Tháng 5–10, sau Phase 2.

## 12.1. Mục tiêu Phase

Phase 3 không chỉ tìm model có metric cao nhất. Nó phải tạo một experiment có thể tái hiện và không nhìn tương lai:

1. Định nghĩa prediction question, horizon và target.
2. Khóa data/features theo thời điểm thực tế có thể biết.
3. Chia train/validation/test theo thời gian.
4. So baseline với model candidates công bằng.
5. Tune/blend chỉ trên train/validation.
6. Đánh giá một lần trên holdout chưa đụng tới.
7. Lưu model **cùng preprocessing, feature schema, config và provenance**.

“Model mạnh nhất” là model tốt nhất theo mục tiêu đã chốt, không phải model thắng một metric duy nhất.

## 12.2. Điều kiện bắt đầu

Trước khi Phase 3 code chính thức:

- Phase 1 có data contract và point-in-time rule usable.
- Phase 2 có feature-set version, leakage test và output ổn định.
- Prediction horizon/context được người dùng duyệt: dài hạn, trung hạn hay lướt sóng.
- Target definition được duyệt trước khi chọn model.
- Chốt metric chính/phụ và chi phí sai lầm.
- Chọn/pin toolchain theo [EF-S-06 §6.4–6.9](./EF-S-06_Library_Catalog.md).

PyCaret, XGBoost, LightGBM và CatBoost hiện là roadmap candidates. Agent không được tự cài cả bộ trước bước audit/benchmark nhỏ.

## 12.3. Kế hoạch 6 tháng

| Tháng | Trọng tâm | Kết quả phải có |
|---|---|---|
| 5 | Prediction question, target, point-in-time dataset | Dataset specification + leakage review |
| 6 | Chronological split, baseline, experiment harness | Baseline report + reproducible run |
| 7 | XGBoost/LightGBM/CatBoost candidates | So sánh công bằng trên cùng split |
| 8 | Tuning, class imbalance, calibration | Tuning report không dùng holdout |
| 9 | Xem xét blend và stability/resource test | Blend decision có bằng chứng |
| 10 | Final holdout, export, handoff Phase 4 | Versioned model bundle + model card |

Đây là phân bổ làm việc suy ra từ roadmap, không phải lý do bỏ qua gate nếu data/leakage chưa đạt.

## 12.4. Kiến trúc mục tiêu

```text
Tầng 0 — Experiment Config (input, read-only)
                   ↓
Tầng 1 — Point-in-time Dataset Builder
  Phase 1 + Phase 2 + optional Phase 5 contracts
                   ↓
Tầng 2 — Experiment/Arena Service
  split → baseline → compare → tune → optional blend
                   ↓
Tầng 3 — Evaluation & Artifact Repository
  metrics + plots + model bundle + registry
```

Dependency direction:

- Dataset Builder đọc data contracts; không train model.
- Arena nhận dataset/config qua tham số; không tự đi cào/ghi rải rác.
- Artifact Repository lưu atomic/versioned output.
- Report đọc metrics/artifacts; không train lại ngầm.
- Phase 4 chỉ load bundle đã xuất; không gọi ngược Arena để train.

Tham chiếu: [EF-S-00 §0.2–0.7](./EF-S-00_Dependency_Direction.md), [EF-S-03 §3.5–3.10](./EF-S-03_Data_Pipeline.md).

## 12.5. Cấu trúc mục tiêu tối thiểu

```text
Main Scripts/Phase 3/
├── Config/
│   └── training_config.yaml
├── E_ml_dataset_builder.py
├── E_target_builder.py
├── E_experiment_manager.py
├── E_resource_monitor.py
├── E_metrics_evaluator.py
├── E_model_repository.py
└── E_report_renderer.py

Phase_3_Data/
├── Datasets/
├── Models/
├── Metrics/
└── Registry/
```

Tên/folder cuối cùng được chốt khi triển khai. Không tạo toàn bộ skeleton rỗng trước khi trách nhiệm thật xuất hiện.

Nếu dùng PyCaret, có thể có `E_pycaret_arena.py` làm adapter/facade tập trung. Mục đích là giữ config/run nhất quán và dễ thay công cụ, **không phải** vì import PyCaret ở file thứ hai tự động gây conflict.

## 12.6. Prediction question và target

Trước khi code `target_builder`, phải trả lời:

- Dự đoán gì: return, direction, buy/hold/sell hay risk?
- Tại thời điểm nào model phát tín hiệu?
- Horizon bao lâu?
- Giá dùng để tạo target là close/open/adjusted và thời điểm thực thi nào?
- Threshold/class definition là gì?
- Target có tính transaction cost hay không?
- Context dài/trung/ngắn khác nhau thế nào?

Target thường dùng future return để tạo nhãn trong dữ liệu lịch sử. Điều đó hợp lệ **chỉ ở cột target**; future information không được lọt vào feature.

Đổi context/horizon/target definition tạo một experiment family mới và thường yêu cầu rebuild dataset + retrain. Không chỉ đổi tên model file.

## 12.7. Point-in-time dataset và chống leakage

Mỗi row tại thời điểm `t` chỉ được chứa thông tin có thể biết tại `t`:

- Technical features chỉ dùng giá tới `t`.
- BCTC dùng ngày công bố/available date, không dùng quarter-end nếu báo cáo chưa công bố.
- News dùng published/received timestamp và aggregation window đã chốt.
- Normalization/imputation/feature selection chỉ fit trên training fold.
- Không tính scaler trên toàn dataset trước khi split.
- Không dùng revised/corrected data tương lai nếu live system tại `t` không có nó, trừ khi đánh dấu rõ limitation.

Dataset snapshot/fingerprint phải được lưu để experiment có thể tái hiện.

## 12.8. Split bắt buộc theo thời gian

Roadmap yêu cầu Time Series Split/Walk-forward validation.

Thiết kế tối thiểu:

```text
Train window → Validation window
      dịch thời gian → Train mở rộng/rolling → Validation tiếp theo
                                                     ↓
                                  Final untouched holdout
```

Quy tắc:

- Không random shuffle time-series rows.
- Symbol grouping/time overlap phải được xử lý để cùng sự kiện tương lai không lọt qua fold.
- Có gap/embargo nếu feature/target window chồng lấn gây leakage.
- Tuning/blending không được xem final holdout.
- Năm 2022 nếu dành cho Phase 4 stress test phải được bảo vệ khỏi quá trình tune/chọn model theo mục đích đó.

## 12.9. Baseline trước “sàn đấu”

Trước model phức tạp phải có baseline:

- dự đoán class phổ biến;
- rule đơn giản phù hợp nghiệp vụ;
- logistic/linear/tree baseline khi phù hợp.

Model candidate chỉ có ý nghĩa nếu thắng baseline ổn định trên nhiều fold sau khi tính variance/resource, không chỉ thắng một lần.

Ba model roadmap:

- XGBoost;
- LightGBM;
- CatBoost.

Không hardcode nhận xét “model A luôn chậm/nhanh/tốt hơn”. Kết quả phụ thuộc data, parameter, hardware và version; phải benchmark trong môi trường thật.

## 12.10. Metrics và chọn model

Metric phải khớp target/class imbalance và chi phí sai:

- classification: precision, recall, F1, ROC-AUC/PR-AUC khi phù hợp;
- probability: calibration/Brier score khi dùng confidence;
- stability: mean + spread qua folds/regimes;
- resource: training time, peak RAM, inference latency;
- Phase 4: return, drawdown, turnover, cost-adjusted performance.

Không chọn model chỉ theo accuracy nếu class imbalance. Không dùng backtest metric để tune lặp trên cùng stress period đến khi đẹp.

## 12.11. Tune và blend

Roadmap nói “xem xét blend”, không phải bắt buộc blend.

Chỉ blend khi:

- base models có lỗi/strength bổ sung nhau;
- cải thiện lặp lại qua folds/regimes;
- không tăng complexity/resource vượt lợi ích;
- weight/stacking được fit trong validation đúng cách;
- final holdout vẫn untouched.

Nếu blend không cải thiện ổn định, chọn model đơn giản hơn và ghi quyết định.

## 12.12. Reproducibility và resource

Mỗi experiment phải ghi:

- run/experiment ID;
- config + target/feature/split version;
- random seed;
- Python/package versions;
- input fingerprint/date range/symbol universe;
- model parameters;
- fold metrics + resource usage;
- status complete/failed/partial;
- code commit nếu Git state rõ.

Resource monitor đo peak RAM, CPU/time và artifact size; không tự kill training trừ khi policy/ngưỡng đã được duyệt.

## 12.13. Error, checkpoint và registry

- Expected model failure trong compare/tune có thể ghi theo candidate và tiếp tục nếu Arena vẫn còn kết quả usable.
- Dataset/schema/leakage violation là fatal; không skip rồi train tiếp.
- Fatal exception log traceback một lần ở boundary và run status phải là failed.
- Checkpoint lưu milestone/artifact đã hoàn thành; không tuyên bố có thể serialize toàn bộ state thư viện nếu chưa chứng minh restore hoạt động.
- Registry là output journal, không trộn với config input.
- Registry/checkpoint ghi atomic và không báo completed trước khi artifact/metrics đã lưu thành công.

Tham chiếu: [EF-S-02 §2.1–2.8](./EF-S-02_Error_Handling.md), [EF-S-04 §4.7–4.11](./EF-S-04_Logging_Debug.md).

## 12.14. Model bundle và output contract

Không chỉ lưu một file `.pkl` trần.

```text
Phase_3_Data/Models/{experiment_id}/
├── model artifact
├── preprocessing pipeline
├── config snapshot
├── feature_schema.json
├── target_definition.json
├── split_definition.json
├── metrics.json
├── environment/dependencies
└── model_card.md
```

Tên artifact chứa experiment ID/model/context/version. Exact extension phụ thuộc tool đã chọn.

Security:

- Pickle/joblib chỉ load artifact tin cậy do dự án tạo.
- Không load model file từ nguồn lạ.
- Phase 4 phải kiểm tra schema/version compatibility trước inference.

## 12.15. Testing và experiment gate

Test bắt buộc:

- target alignment/horizon bằng sample tính tay;
- leakage tests cho future price, BCTC release và news timestamp;
- split chronological/no overlap;
- preprocessing fit chỉ trên train;
- deterministic seed/config ở mức tool cho phép;
- small dataset pipeline end-to-end offline;
- artifact save/load/predict equivalence;
- incompatible feature schema bị từ chối;
- failed run không được ghi completed;
- resource smoke test.

Live/full training là test có chủ đích; không chạy tự động mọi commit.

## 12.16. Definition of Done cho Phase 3

- [ ] Prediction question, horizon, context và target được duyệt.
- [ ] Dataset point-in-time và leakage review đạt.
- [ ] Walk-forward/time split + untouched holdout rõ.
- [ ] Có baseline trước candidates.
- [ ] Candidates được so trên cùng data/split/metric.
- [ ] Blend chỉ dùng nếu có bằng chứng ổn định.
- [ ] RAM/time/inference cost được báo.
- [ ] Experiment có thể tái hiện từ config/data fingerprint/version.
- [ ] Model bundle chứa preprocessing/schema/metrics, không chỉ `.pkl`.
- [ ] Registry phân biệt complete/failed/partial đúng sự thật.
- [ ] Phase 4 có contract load/predict rõ và không cần gọi lại training code.
