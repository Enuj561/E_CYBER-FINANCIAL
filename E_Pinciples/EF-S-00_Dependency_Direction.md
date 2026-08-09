# Chương 0 — EF-S-00: Dependency Direction (Hướng gọi giữa các phần)

> **Trạng thái:** ACTIVE — tiêu chuẩn bắt buộc cho code mới và code được sửa lớn.
>
> **Agent phải đọc file này khi:** tạo module mới, thêm `import`, nối UI với backend, nối hai Phase, hoặc xử lý circular import.
>
> **Mục tiêu:** Mỗi phần chỉ biết những phần nằm phía dưới nó. Nhờ vậy, sửa giao diện không làm hỏng thuật toán và sửa thuật toán không kéo theo sửa toàn hệ thống.

## 0.1. Hình dung đơn giản

Hãy coi phần mềm như một dây chuyền:

```text
Người dùng / Task Scheduler
          ↓
Warden / Auto / UI                 Khởi động hoặc nhận yêu cầu
          ↓
Manager / Application Service      Điều phối các bước
          ↓
Collector / Client / Repository    Đọc dữ liệu, gọi API
Calculator / Validator             Tính toán, kiểm tra
Renderer / Exporter                Tạo báo cáo, ghi kết quả
          ↓
E_Helper                           Công cụ chung, không có nghiệp vụ riêng
```

Mũi tên trên là **hướng được phép gọi/import**. Một module ở dưới không được import ngược module ở trên.

Đây là kiến trúc phân tầng một chiều của dự án. Nó có cùng mục tiêu giảm phụ thuộc với Clean Architecture, nhưng không được hiểu sai rằng mọi lệnh chạy lúc nào cũng chỉ đi một chiều. Callback, signal hoặc interface có thể gửi kết quả ngược lên mà không cần import ngược.

## 0.2. Vai trò của từng tầng

| Tầng | Được làm | Không được làm |
|---|---|---|
| `System/Warden.py`, `Auto/` | Khởi động app hoặc gọi một Manager | Chứa thuật toán, cào API, xử lý DataFrame |
| `IDE_UI/` | Layout, nhận thao tác, hiển thị kết quả, gọi Manager | Import trực tiếp Scraper, AI Client, Calculator hoặc ghi data nghiệp vụ |
| Manager / Application Service | Quyết định thứ tự các bước, gom kết quả/lỗi | Tự viết thuật toán dài hoặc tự vẽ UI |
| Collector / Client / Repository | Gọi API, đọc/ghi dữ liệu đúng hợp đồng | Import Manager hoặc UI |
| Calculator / Validator | Nhận dữ liệu qua tham số, tính và trả kết quả | Gọi API, đọc đường dẫn dự án, ghi file, import Manager/UI |
| Renderer / Exporter | Nhận dữ liệu đã xử lý và tạo output | Tự đi cào data hoặc gọi ngược Manager/UI |
| `E_Helper/` | Path, I/O an toàn, tiện ích thật sự dùng chung | Import module nghiệp vụ của Phase, News hoặc UI |

## 0.3. Luật import bắt buộc

### Được phép

```python
# UI chỉ gọi cổng điều phối
from News.E_news_manager import NewsManager

# Manager gọi các thành phần thực thi
from News.E_news_scraper import fetch_news
from E_Helper.E_io_utils import safe_write_json
```

### Không được phép

```python
# Calculator gọi ngược Manager
from News.E_news_manager import NewsManager

# Helper biết một module nghiệp vụ cụ thể
from News.E_news_scraper import fetch_news

# UI tự ghép toàn bộ pipeline
from News.E_news_scraper import fetch_news
from News.E_ai_client import summarize_news_json
```

Nếu UI cần một luồng chưa có trong Manager, Agent phải thêm một method/facade phù hợp ở tầng Manager; không được đi tắt bằng cách import mọi module con vào UI.

## 0.4. Callback và signal không phải gọi ngược

Tầng dưới được báo tiến độ bằng callback/signal do tầng trên truyền vào:

```python
def run_pipeline(progress_callback=None):
    if progress_callback:
        progress_callback("Đã xử lý 50%")
```

Module chạy pipeline không cần biết callback thuộc PyQt, console hay Task Scheduler. Vì nó không import UI nên hướng phụ thuộc vẫn đúng.

## 0.5. Quy tắc giữa các Phase

Phase sau dùng **output đã lưu theo hợp đồng dữ liệu** của Phase trước:

```text
Phase 1 data → Phase 2 features → Phase 3 model → Phase 4 backtest
Phase 5 news/sentiment ───────────────→ Phase 3 input
```

- Phase sau được đọc output của Phase trước.
- Phase trước không import code của Phase sau.
- Không import chéo chỉ để lấy một hàm tiện ích. Nếu hàm thực sự dùng chung, xem [EF-S-05](./EF-S-05_Shared_Code.md).
- Phase 5 không phải ngoại lệ cho luật import. Nó cung cấp dữ liệu qua file/schema hoặc một interface rõ ràng.

## 0.6. Data và config không phải “ai cũng tùy ý đọc”

- Module I/O như Collector/Repository chịu trách nhiệm đọc file dữ liệu.
- Calculator nhận DataFrame/object qua tham số để có thể test dễ dàng.
- Path và constant chung được lấy từ `E_Helper/E_config.py`.
- `E_config.py` không được import module nghiệp vụ và không tự sửa `sys.path`.
- Chỉ entry point như `Warden.py` hoặc script `Auto/` được tạm thời setup `sys.path` cho đến khi dự án có package/`pyproject.toml` chuẩn.

## 0.7. Khi cần đi ngược chiều

Nếu tầng dưới cần yêu cầu tầng trên làm gì đó, Agent chọn một trong ba cách:

1. Trả dữ liệu hoặc lỗi về cho caller.
2. Nhận callback/signal qua tham số.
3. Nhận một interface/Protocol nhỏ qua tham số (dependency injection).

Không giải quyết bằng import ngược.

## 0.8. Checklist cho Agent

Trước khi thêm một `import`, kiểm tra:

- [ ] Module đang gọi module cùng tầng hoặc tầng thấp hơn?
- [ ] UI chỉ gọi Manager/facade?
- [ ] Calculator/Validator không đọc file, gọi API hoặc ghi output?
- [ ] `E_Helper` không biết module nghiệp vụ?
- [ ] Hai Phase trao đổi qua data contract thay vì import chéo?
- [ ] Nếu dùng callback/signal, module dưới không import UI?
- [ ] Không tạo circular import?

Nếu có một câu trả lời “không”, Agent phải dừng và chỉnh thiết kế trước khi viết tiếp.
