# Chương 9 — EF-S-09: Testing Strategy (Chiến lược kiểm thử)

> **Trạng thái:** ACTIVE cho mọi code mới/sửa logic.
>
> **Agent phải đọc file này khi:** viết/sửa Calculator, Validator, Manager, Collector/Client, data contract, bug fix hoặc test.
>
> **Mục tiêu:** Agent chứng minh code hoạt động bằng test phù hợp, không chỉ nói “nhìn có vẻ đúng”. Test mặc định phải nhanh và ổn định; test gọi mạng được tách riêng.

## 9.1. Quy tắc tên để pytest tìm được

Test là ngoại lệ của tiền tố `E_`:

```text
test_phase1.py
test_indicators.py
test_news_manager.py
```

Pytest mặc định tìm `test_*.py` và `*_test.py`. Không đặt file mới tên `E_test_*.py` trừ khi dự án đã cấu hình `python_files` rõ trong `pyproject.toml`/`pytest.ini`.

Khuyến nghị cấu trúc mục tiêu:

```text
tests/
├── unit/
│   ├── phase_1/
│   └── news/
├── integration/
│   ├── phase_1/
│   └── news/
└── fixtures/
    ├── phase_1/
    └── news/
```

Trong lúc chưa chuyển cấu trúc, test được phép nằm gần module nhưng vẫn phải tên `test_*.py`.

## 9.2. Các loại test

| Loại | Kiểm tra gì? | Network? | Chạy mặc định? |
|---|---|---:|---:|
| Unit | Một function/class với dependency giả | Không | Có |
| Integration local | Nhiều module, file/schema/Parquet thật trong temp folder | Không | Có hoặc marker riêng |
| Contract | Response/schema của nguồn/API theo sample đã lưu | Thường không | Có |
| Live integration | API/RSS/Gemini thật | Có | Không; chỉ chạy khi opt-in |
| UI smoke | App/widget mở và flow chính không crash | Không hoặc mock backend | Marker riêng |
| End-to-end | Một pipeline gần giống thật | Có thể | Chạy có chủ đích, không phải mọi commit |

Luật “mọi test tuyệt đối offline” chỉ đúng với unit test/default suite. Live integration test được phép gọi mạng nhưng phải:

- có marker như `@pytest.mark.live`;
- bị skip nếu chưa có flag/secret;
- không chạy mặc định;
- có timeout/rate-limit;
- không ghi đè data production.

## 9.3. Logic nào bắt buộc có test?

- Mọi Calculator và Validator.
- Bug fix: phải có regression test tái hiện bug trước khi xác nhận sửa xong.
- Data contract/schema transformation.
- Manager có nhánh success/partial/fatal đáng kể.
- Atomic write/checkpoint logic.
- Parser của response bên ngoài với sample fixture.
- Code xử lý tiền, giá, tỷ lệ, backtest hoặc model metric.

Layout/style thuần UI không bắt buộc unit test từng pixel.

## 9.4. Test kết quả và test tương tác

Ưu tiên test kết quả người dùng/module quan tâm:

```python
def test_rsi_stays_in_valid_range():
    result = compute_rsi(close_prices, period=14)
    valid = result.dropna()

    assert not valid.empty
    assert valid.between(0, 100).all()
```

Không viết `assert 0 <= result <= 100` nếu `result` là `pandas.Series`; biểu thức đó không tạo một boolean duy nhất.

Test tương tác được phép khi interaction chính là contract, ví dụ:

- Repository phải được gọi đúng một lần để lưu output.
- Client phải gửi timeout/token đã che đúng.
- Logger/alert phải được gọi ở fatal boundary.

Không mock mọi function nội bộ chỉ để test code gọi đúng từng bước implementation; cách đó làm test vỡ dù hành vi bên ngoài vẫn đúng.

## 9.5. Contract cho dữ liệu thiếu phải được chọn rõ

Với RSI thiếu dữ liệu, dự án có thể chọn một trong hai contract:

### Contract A — trả Series chứa NaN

```python
def test_rsi_short_input_returns_nan():
    result = compute_rsi(pd.Series([100, 101, 102]), period=14)
    assert result.isna().all()
```

### Contract B — raise `ValueError`

```python
def test_rsi_short_input_is_rejected():
    with pytest.raises(ValueError, match="at least 14"):
        compute_rsi(pd.Series([100, 101, 102]), period=14)
```

Agent không được viết test kỳ vọng `AssertionError` nếu function không có contract đó. Với input/user data không hợp lệ, `ValueError` thường rõ nghĩa hơn `AssertionError`.

## 9.6. Test Double — hiểu đúng, dùng vừa đủ

| Loại | Hiểu đơn giản | Ví dụ |
|---|---|---|
| Dummy | Giá trị lấp chỗ, test không quan tâm | `request_id="test"` |
| Stub | Luôn trả câu trả lời đã chuẩn bị | Client stub trả một DataFrame mẫu |
| Spy | Ghi lại cách nó được gọi | Kiểm tra progress callback nhận các message |
| Mock | Được lập trình trước để kiểm tra interaction | `repository.save.assert_called_once()` |
| Fake | Bản thay thế có hoạt động đơn giản nhưng thật | In-memory repository thay vì ghi disk |
| Fixture/sample | Dữ liệu test cố định | File RSS JSON/Parquet nhỏ trong `tests/fixtures` |

Một DataFrame tạo sẵn thường là fixture/sample, không tự động là Fake.

## 9.7. Mock đúng ranh giới

Nên mock:

- HTTP/Gemini/vnstock/FireAnt;
- clock/date hiện tại;
- filesystem khi unit test, hoặc dùng `tmp_path` cho integration local;
- random source;
- UI callback/signal;
- repository/client interface.

Patch tại nơi symbol **được lookup**, dùng đúng tên module thật có tiền tố `E_`. Nếu import path khó patch vì cấu trúc folder, Agent nên đưa dependency qua tham số/interface thay vì thêm `sys.path` hack trong test.

## 9.8. Mock data và fixture

- Fixture nhỏ đặt trong `tests/fixtures/`, không trộn với data production dưới `Phase_X_Data/`.
- Mỗi fixture ghi nguồn/schema và mục đích test.
- Không chứa API key, dữ liệu riêng tư hoặc file quá lớn.
- Dùng `tmp_path` cho output test để test không sửa workspace.
- Có fixture cả happy path và dữ liệu lỗi: thiếu cột, duplicate, NaN, timezone, giá trị biên.

## 9.9. Tính ổn định và tái hiện

Test mặc định phải deterministic:

- pin/freezing thời gian thay vì dùng `date.today()` trực tiếp;
- đặt random seed;
- không phụ thuộc thứ tự file/API ngẫu nhiên;
- không dùng sleep thật nếu có thể dùng fake clock;
- so sánh float bằng tolerance phù hợp (`pytest.approx`, pandas/numpy testing);
- ML test kiểm tra invariant/metric threshold hợp lý, không đòi từng bit giống nhau nếu backend không đảm bảo.

## 9.10. Quy trình khi sửa bug

1. Viết test nhỏ tái hiện bug và thấy nó fail.
2. Sửa code tối thiểu.
3. Chạy test mới và suite liên quan.
4. Kiểm tra không ghi data production/log bẩn.
5. Báo chính xác test nào đã chạy; nếu không chạy được phải nói lý do.

Không được nói “đã test” khi chỉ đọc code hoặc khi pytest chưa được cài.

## 9.11. Lệnh chuẩn dự kiến

Sau khi `pytest` được thêm vào dev dependencies:

```powershell
python -m pytest -q
python -m pytest tests/unit -q
python -m pytest -m "not live" -q
python -m pytest --collect-only -q
```

Live test phải có lệnh/flag riêng được tài liệu hóa; không chạy tự động làm tốn quota Gemini/API.

## 9.12. Checklist cho Agent

- [ ] File test dùng `test_*.py` để được collect?
- [ ] Calculator/Validator hoặc bug fix có unit/regression test?
- [ ] Default suite không gọi mạng/secret?
- [ ] Live test có marker và opt-in?
- [ ] Test kiểm tra contract/kết quả thay vì implementation detail không cần thiết?
- [ ] Series/DataFrame được assert bằng pandas/numpy-aware assertions?
- [ ] Contract cho thiếu data/error được định nghĩa rõ?
- [ ] Mock đúng boundary và đúng import path?
- [ ] Fixture nằm trong `tests/fixtures`, output dùng `tmp_path`?
- [ ] Time/random/float được kiểm soát để deterministic?
- [ ] Agent báo đúng test đã chạy và không nói quá kết quả?
