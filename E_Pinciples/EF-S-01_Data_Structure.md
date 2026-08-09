# Chương 1 — EF-S-01: Code Structure & SRP (Chia code đúng trách nhiệm)

> **Trạng thái:** ACTIVE — tiêu chuẩn bắt buộc cho code mới và khi refactor.
>
> **Agent phải đọc file này khi:** tạo/đổi tên file, chọn thư mục, tách một file lớn, tạo class/function mới hoặc tổ chức package.
>
> **Mục tiêu:** Mỗi file có một nhiệm vụ dễ gọi tên. Chủ dự án có thể nhìn tên file và biết nó chịu trách nhiệm việc gì.

## 1.1. Quy tắc cốt lõi

> **Một file = một trách nhiệm chính = một lý do chính để thay đổi.**

Ví dụ:

- `E_news_scraper.py` thay đổi khi cách lấy RSS thay đổi.
- `E_ai_client.py` thay đổi khi Gemini API thay đổi.
- `E_news_renderer.py` thay đổi khi giao diện HTML thay đổi.

Nếu một file phải sửa vì cả ba lý do trên, file đó cần được tách.

SRP không có nghĩa “mỗi file chỉ có một hàm”. Nhiều hàm được phép ở chung nếu cùng phục vụ một trách nhiệm.

## 1.2. Cấu trúc dự án: hiện tại và tương lai

Agent phải phân biệt hai khái niệm:

- **Hiện tại:** thư mục/file đang thật sự tồn tại trong repo.
- **Mục tiêu:** thư mục được tạo khi Phase tương ứng bắt đầu.

Không được viết tài liệu hoặc import như thể một thư mục mục tiêu đã tồn tại.

```text
E_CYBER-FINANCIAL/
├── System/                         Entry point và biến môi trường
│   └── Warden.py
├── Main Scripts/
│   ├── Phase 1/                    Code Phase 1 hiện có
│   ├── News/                       Code Phase 5/News hiện có
│   ├── Auto/                       Task Scheduler entry points
│   └── IDE_UI/                     PyQt6 UI hiện có
├── E_Helper/                       Config, E_BlackBox và tiện ích dùng chung
├── Phase_1_Data/                   Data Phase 1 hiện có
├── Phase_5_Data/                   Data News hiện có
└── E_Pinciples/                    Tiêu chuẩn thiết kế
```

Log runtime nằm cạnh script sở hữu tính năng theo [EF-S-04](./EF-S-04_Logging_Debug.md); `Log_Debug/` nếu còn tồn tại chỉ chứa log lịch sử.

Các thư mục `Main Scripts/Phase 2`, `Phase 3`, `Phase 4` và `Phase_2_Data` đến `Phase_4_Data` chỉ được tạo khi triển khai Phase đó.

## 1.3. Chọn đúng thư mục

| Nơi đặt | Chứa gì | Không chứa gì |
|---|---|---|
| `Main Scripts/Phase X/` | Code nghiệp vụ của một Phase | Utility dùng chung toàn dự án |
| `Main Scripts/News/` | Scraper, AI client, manager, renderer của News | Logic thuật toán tài chính không liên quan News |
| `Main Scripts/Auto/` | Script khởi động tác vụ tự động | Pipeline dài hoặc thuật toán |
| `Main Scripts/IDE_UI/` | Widget, layout, signal, hiển thị | Cào API, tính toán, ghi data nghiệp vụ |
| `E_Helper/` | Config, atomic I/O, utility độc lập | Business logic của Phase/News/UI |
| `Phase_X_Data/` | File data/output | Python xử lý nghiệp vụ |
| `System/` | Entry point và `.env` | Business logic |
| `tests/` | Test và fixture/mock nhỏ | Data production |

## 1.4. Quy tắc đặt tên file

### File production

Mọi file Python do dự án tạo dùng tiền tố `E_`:

```text
E_data_collector.py
E_indicator_calculator.py
E_news_manager.py
E_ai_client.py
```

Ngoại lệ:

- `__init__.py` — file đặc biệt của Python.
- `Warden.py` — entry point đã được dự án đặt tên riêng.
- `test_*.py` — dùng tên chuẩn để pytest tự tìm test.

### Hậu tố thể hiện vai trò

| Hậu tố | Vai trò |
|---|---|
| `_collector`, `_scraper` | Thu thập dữ liệu |
| `_client` | Gọi dịch vụ/API ngoài |
| `_repository` | Đọc/ghi data theo hợp đồng |
| `_cleaner`, `_processor` | Làm sạch hoặc biến đổi dữ liệu |
| `_calculator` | Tính toán thuần |
| `_validator` | Kiểm tra tính hợp lệ |
| `_manager`, `_service` | Điều phối use case/pipeline |
| `_renderer`, `_exporter` | Tạo output trình bày hoặc xuất file |

Không dùng tên mơ hồ như `utils.py`, `helpers.py`, `process.py`, `new.py` hoặc `final.py`.

## 1.5. Header bắt buộc

Mọi file Python production phải có docstring đầu file:

```python
"""
Module:  E_news_manager
Logic:   Orchestrate the news collection pipeline
Detail:  Điều phối cào tin, lọc trùng và lưu JSON; không tự parse RSS.
"""
```

- `Module` trùng tên file bỏ `.py`.
- `Logic` là một câu tiếng Anh ngắn.
- `Detail` là một hoặc hai câu tiếng Việt, nói rõ làm gì và không làm gì.
- Không bắt buộc ghi ngày/version trong header; Git đã lưu lịch sử đó.

## 1.6. Chia vai trò trong một pipeline

```text
Collector/Client → lấy dữ liệu
Processor        → làm sạch/chuyển đổi
Calculator       → tính toán thuần
Validator        → kiểm tra đầu vào/đầu ra
Manager          → gọi các phần trên theo đúng thứ tự
Repository       → đọc/ghi data
Renderer         → trình bày kết quả
```

Một project nhỏ không cần tạo đủ mọi loại file ngay lập tức. Agent chỉ tạo file khi trách nhiệm đó có thật. Không tạo “khung rỗng” để cho đẹp sơ đồ.

## 1.7. Khi nào phải tách file/hàm?

Các con số dưới đây là **còi báo để review**, không phải luật máy móc:

| Dấu hiệu | Agent phải làm gì |
|---|---|
| Hàm khoảng trên 80 dòng | Kiểm tra có nhiều bước/trách nhiệm hay không |
| File khoảng trên 300 dòng | Kiểm tra có nhiều lý do thay đổi hay không |
| Nested function khoảng trên 20 dòng | Cân nhắc đưa ra function/module riêng |
| Tên file phải mô tả bằng nhiều chữ “và” | Gần như chắc chắn cần tách |

Không được tách chỉ vì số dòng nếu việc tách làm code khó đọc hơn. Ưu tiên ranh giới trách nhiệm, không chạy theo chỉ tiêu file ngắn.

## 1.8. Constant và “số bí ẩn”

Giá trị có ý nghĩa nghiệp vụ hoặc vận hành phải có tên:

```python
RETRY_MAX = 3
FIREANT_TIMEOUT_SECONDS = 30
PRICE_DIFF_TOLERANCE = 0.001
```

Các giá trị hiển nhiên trong phép tính như `0`, `1`, `2`, `100` có thể viết trực tiếp nếu người đọc hiểu ngay ý nghĩa.

Constant chỉ dùng trong một module đặt ở đầu module đó. Constant dùng chung nhiều nơi mới đưa vào `E_Helper/E_config.py`.

## 1.9. Import và package

- Không thêm `sys.path.insert()` rải rác trong module nghiệp vụ.
- Trong cấu trúc hiện tại, chỉ entry point (`Warden.py`, `Auto/`) được setup path nếu cần.
- `E_Helper/E_config.py` chỉ chứa config/path; không dùng nó để âm thầm sửa `sys.path`.
- Khi dự án ổn định hơn, Agent nên đề xuất `pyproject.toml` và package import chuẩn trước khi mở rộng nhiều Phase.
- Mỗi folder package có `__init__.py` khi cần import như package.

## 1.10. Những hành vi bị cấm

- UI trực tiếp gọi API, xử lý DataFrame hoặc ghép pipeline.
- Auto script chứa toàn bộ logic thay vì gọi Manager.
- Calculator đọc file hoặc ghi output.
- Hardcode đường dẫn tuyệt đối tới máy của chủ dự án.
- Tạo utility mới mà chưa kiểm tra `E_Helper/` và [EF-S-05](./EF-S-05_Shared_Code.md).
- Tạo sẵn nhiều abstraction/class không có nhu cầu thật.
- Trộn cấu trúc “dự kiến tương lai” với cấu trúc đang tồn tại mà không ghi rõ trạng thái.

## 1.11. Checklist cho Agent

Trước khi tạo hoặc sửa lớn một file:

- [ ] Có thể mô tả trách nhiệm file trong một câu ngắn?
- [ ] File nằm trong thư mục đang tồn tại hoặc được tạo có chủ đích?
- [ ] Tên file có `E_` và hậu tố đúng vai trò, trừ ngoại lệ?
- [ ] Header đúng tên module và mô tả thật?
- [ ] Không có hardcode path hoặc `sys.path` hack trong business module?
- [ ] Không trộn UI, API, tính toán và ghi file trong cùng một module?
- [ ] Các con số quan trọng có constant dễ hiểu?
- [ ] Nếu file dài, đã review theo trách nhiệm thay vì tách máy móc?
- [ ] Import đi đúng chiều theo [EF-S-00](./EF-S-00_Dependency_Direction.md)?
- [ ] Test được đặt tên theo [EF-S-09](./EF-S-09_Testing_Strategy.md)?
