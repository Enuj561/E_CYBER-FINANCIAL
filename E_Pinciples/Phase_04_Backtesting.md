# Chương 13 — Phase 4: Chiến trường Giả lập

> **Trạng thái:** PLANNED — chưa có backtester production trong repo.
>
> **Agent phải đọc file này khi:** thiết kế simulator/order/trade/portfolio, load model Phase 3, tính phí/trượt giá, stress test 2022 hoặc so với Buy & Hold VN-Index.
>
> **Roadmap gốc:** [19-MONTH_PLANNING.md](../19-MONTH_PLANNING.md) — thời lượng 6 tháng; trừ phí giao dịch; tính slippage; stress test năm 2022; so với Buy & Hold VN-Index.
>
> **Timeline suy ra:** Tháng 11–16.

## 13.1. Mục tiêu Phase

Phase 4 trả lời câu hỏi: “Nếu tín hiệu/model này tồn tại trong quá khứ và bị giới hạn như giao dịch thật, kết quả sẽ thế nào?”

Backtest phải:

1. Chỉ dùng thông tin có tại thời điểm ra quyết định.
2. Mô phỏng thời điểm đặt/lấp lệnh rõ ràng.
3. Trừ phí, thuế và slippage theo config/version.
4. Tôn trọng cash, position, liquidity và delisted universe.
5. So với benchmark trên cùng kỳ/capital/rule.
6. Giữ năm 2022 như stress regime độc lập theo roadmap.
7. Xuất run có thể tái hiện, không chỉ chart đẹp.

Backtest đẹp không chứng minh chiến lược sẽ có lời ngoài thực tế. Nó chỉ là bằng chứng mô phỏng dưới các giả định đã ghi.

## 13.2. Điều kiện bắt đầu

- Phase 3 bàn giao model bundle + preprocessing + feature/target schema.
- Phase 1/2 có point-in-time data usable và universe gồm inactive/delisted khi có thể.
- Prediction timestamp và execution timestamp đã chốt.
- Năm 2022 chưa bị dùng lặp để tune/chọn model nếu muốn gọi là stress test độc lập.
- Cost/slippage/benchmark assumptions được người dùng duyệt.

Nếu không đạt, Agent phải dừng ở mức prototype/research; không công bố performance như kết quả chính thức.

## 13.3. Kế hoạch 6 tháng

| Tháng | Trọng tâm | Kết quả phải có |
|---|---|---|
| 11 | Event timeline, orders, fills, portfolio accounting | Engine spec + hand-calculated tests |
| 12 | Data/model loading và signal execution | Deterministic baseline simulation |
| 13 | Fees, tax, slippage, liquidity/position rules | Realism assumptions v1 |
| 14 | Metrics/report và VN-Index benchmark | Comparable report |
| 15 | Walk-forward/retraining policy + 2022 stress | Stress/stability report |
| 16 | Robustness, audit, export/handoff | Versioned backtest bundle |

Không rút ngắn correctness gate để kịp roadmap. Nếu engine accounting sai, mọi tháng sau đều vô nghĩa.

## 13.4. Kiến trúc mục tiêu

```text
Run Config + Data Contract + Model Bundle
                  ↓
Backtest Manager
  ├─ Market Data Feed (point-in-time)
  ├─ Signal/Strategy Adapter
  ├─ Execution Model (order → fill)
  ├─ Portfolio/Accounting Engine
  ├─ Benchmark Engine
  └─ Metrics + Report + Artifact Repository
```

- Strategy quyết định ý định/order dựa trên signal và state hiện tại.
- Execution Model quyết định fill price/quantity/cost theo giả định.
- Portfolio Engine cập nhật cash/position/P&L; không quyết định strategy.
- Reporter chỉ đọc kết quả; không sửa trades để chart đẹp.
- Simulator không train/tune model.
- Phase 5 comparison đi qua versioned feature/model/backtest contracts, không import chéo tùy tiện.

Tham chiếu: [EF-S-00 §0.2–0.7](./EF-S-00_Dependency_Direction.md), [EF-S-03 §3.5–3.10](./EF-S-03_Data_Pipeline.md).

## 13.5. Cấu trúc mục tiêu tối thiểu

```text
Main Scripts/Phase 4/
├── Config/backtest_config.yaml
├── E_backtest_manager.py
├── E_market_data_feed.py
├── E_model_adapter.py
├── E_strategy.py
├── E_execution_model.py
├── E_portfolio_engine.py
├── E_benchmark_engine.py
├── E_metrics_evaluator.py
├── E_backtest_repository.py
└── E_backtest_reporter.py

Phase_4_Data/Results/{run_id}/
```

Không tạo tất cả file trước khi thiết kế trách nhiệm thật; tên cuối có thể đổi theo EF-S-01 khi implement.

## 13.6. Event timeline bắt buộc

Mỗi strategy phải ghi rõ:

- feature/news/BCTC cutoff time;
- lúc model tạo signal;
- lúc order được gửi;
- earliest fill time;
- giá fill dùng open/close/VWAP/mô hình nào;
- hành vi khi ngày nghỉ, halt, limit up/down hoặc thiếu thanh khoản.

Ví dụ an toàn thường là:

```text
Dữ liệu tới close ngày t → tạo signal sau close t → giao dịch sớm nhất ở ngày t+1
```

Không tạo signal bằng close ngày `t` rồi giả định mua đúng close đó nếu dữ liệu chỉ hoàn chỉnh sau thời điểm khớp lệnh.

## 13.7. Các bias phải chống

### Look-ahead bias

Không dùng future price, BCTC chưa công bố, news phát sau cutoff hoặc revised data tương lai.

### Survivorship bias

Không backtest quá khứ chỉ bằng danh sách mã còn sống hôm nay. Delisted/inactive symbol và membership theo thời gian phải được dùng khi nguồn cho phép; limitation phải ghi rõ nếu chưa đủ.

### Selection/overfitting bias

Không chạy hàng trăm config trên cùng 2022/holdout rồi chọn bản đẹp nhất và vẫn gọi đó là stress test độc lập.

### Data snooping

Mọi lần xem/kết hợp kết quả vào quyết định model đều làm tập đó bớt “unseen”; registry phải ghi lịch sử experiment/backtest.

## 13.8. Phí, thuế, slippage và liquidity

Roadmap bắt buộc phí và slippage. Config phải versioned và giải thích:

- commission/fee;
- tax khi bán nếu áp dụng;
- slippage model;
- lot size/rounding;
- max participation/liquidity rule;
- position/cash/leverage constraints;
- order rejection/partial fill policy.

Không hardcode một con số vĩnh viễn trong engine. Con số phải nằm ở config, có nguồn/ngày hiệu lực và sensitivity test.

Slippage không phải random number tùy ý. Nếu chưa có model đủ dữ liệu, dùng giả định đơn giản đã duyệt và báo limitation.

## 13.9. Accounting invariants

Portfolio Engine phải giữ:

- cash không tự sinh/mất ngoài trade/cost/corporate action;
- position bằng tổng fills đã xử lý;
- equity = cash + marked market value theo definition;
- realized/unrealized P&L không double-count;
- buy không vượt constraint; sell không vượt position nếu không cho short;
- trade/order/fill có ID và timestamp;
- corporate action policy rõ với adjusted/unadjusted series.

Vi phạm invariant nội bộ là fatal. Order bị từ chối theo rule là **sự kiện nghiệp vụ dự kiến**, phải record reason; không nhất thiết crash toàn run.

## 13.10. Benchmark Buy & Hold VN-Index

So sánh phải công bằng:

- cùng start/end và initial capital/return convention;
- cùng calendar/cash treatment;
- nói rõ VN-Index price return hay total-return/proxy;
- không áp trading fee cho index lý thuyết một cách mơ hồ; nếu dùng ETF/proxy phải ghi instrument/cost;
- báo CAGR/total return, volatility, max drawdown và risk-adjusted metric phù hợp.

Roadmap ghi VN-Index. Nếu dữ liệu benchmark không đủ hoặc không thể đầu tư trực tiếp, Agent phải ghi limitation thay vì thay benchmark âm thầm.

## 13.11. Stress test năm 2022

- Xác định chính xác khoảng ngày và lý do regime.
- Không dùng 2022 để tune model/config nếu muốn nó là stress test độc lập.
- Báo performance, drawdown, turnover, exposure, failure modes và recovery.
- So model/strategy với baseline/benchmark trên cùng period.
- Một kết quả tệ không được xóa/giấu; stress test tồn tại để tìm điểm yếu.

Nếu 2022 đã tham gia training, tài liệu phải phân biệt rõ “historical regime evaluation” với “untouched out-of-sample stress test”.

## 13.12. Error handling và run status

- Schema/model compatibility/invariant vi phạm → fail run.
- Invalid/rejected order theo rule → record và tiếp tục nếu state vẫn đúng.
- Missing market data không tự forward-fill giá một cách im lặng.
- Partial/incomplete data → run status partial/invalid theo policy, không completed.
- Fatal exception log traceback một lần ở boundary.
- Không bỏ trade lỗi rồi tiếp tục equity curve như chưa có chuyện gì.

Tham chiếu: [EF-S-02 §2.1–2.8](./EF-S-02_Error_Handling.md), [EF-S-04 §4.7–4.11](./EF-S-04_Logging_Debug.md).

## 13.13. Output contract

```text
Phase_4_Data/Results/{run_id}/
├── run_config.yaml/json
├── data_model_manifest.json
├── orders.parquet
├── fills.parquet
├── trades.parquet
├── equity_curve.parquet
├── metrics.json
├── benchmark_metrics.json
├── validation_report.json
└── report.html/md + charts
```

Manifest phải ghi model/feature/data versions, universe, period, cost/slippage assumptions, code version và run status.

## 13.14. Testing gate

- Hand-calculated one/two-trade scenarios.
- Fee/tax/slippage/rounding/partial fill tests.
- Cash/position/P&L invariants.
- No-look-ahead test bằng cách thay future data và kiểm tra past decisions không đổi.
- Delisted/halts/missing/limit scenario.
- Benchmark calculation test.
- Deterministic replay cùng input/config.
- Model bundle/schema incompatibility bị từ chối.
- Failed run không được xuất “success report”.

## 13.15. Definition of Done cho Phase 4

- [ ] Event timeline và execution rule rõ, không trade cùng dữ liệu chưa thể biết.
- [ ] Chống look-ahead/survivorship/selection bias và ghi limitation.
- [ ] Phí, thuế, slippage, liquidity và position constraints có config/source.
- [ ] Accounting invariants có test tính tay.
- [ ] VN-Index benchmark được so trên convention công bằng.
- [ ] Stress test 2022 được phân loại đúng mức độc lập.
- [ ] Run output có manifest/data/model/config versions.
- [ ] Invalid/partial/failed run không bị báo complete.
- [ ] Phase 5 A/B có thể chạy lại qua contract mà không sửa engine lõi.
