# Chương 7 — EF-S-07: PyQt6 UI (Giao diện desktop hiện tại)

> **Trạng thái:** ACTIVE cho giao diện PyQt6 hiện tại.
>
> **Agent phải đọc file này khi:** sửa `IDE_UI/`, thêm nút/panel/thread/signal, nối UI với Manager hoặc hiển thị lỗi/tiến độ.
>
> **Không dùng file này cho:** C# frontend tương lai; khi đó mở [EF-S-08](./EF-S-08_UI_Frontend.md).
>
> **Mục tiêu:** UI chỉ nhận thao tác và hiển thị. Mọi việc cào, AI, tính toán và lưu data đi qua Manager/Application Service.

## 7.1. Hình dung đơn giản

```text
Người dùng bấm nút
       ↓
PyQt Widget phát yêu cầu
       ↓
Worker gọi một Manager method
       ↓
Manager điều phối Scraper / AI / Repository / Renderer
       ↓
Worker phát progress/result/error signal
       ↓
Widget cập nhật màn hình
```

UI giống bảng điều khiển. Nó không tự tháo máy ra để làm việc bên trong.

## 7.2. UI được và không được làm

| Được làm | Không được làm |
|---|---|
| Tạo `QWidget`, layout, màu, font | Gọi `requests`, `vnstock`, `feedparser`, Gemini trực tiếp |
| Nhận click/input | Xử lý DataFrame hoặc tính indicator |
| Validate input đơn giản để hỗ trợ người dùng | Validate business rule phức tạp |
| Gọi Manager/facade qua worker | Import Scraper, AI Client, Calculator, Repository trực tiếp |
| Hiển thị progress/result/error | Ghi JSON/Parquet nghiệp vụ |
| Lưu UI preference nhỏ nếu được thiết kế rõ | Quyết định pipeline/backfill/retry nghiệp vụ |

## 7.3. Cấu trúc `IDE_UI/`

Tên file production vẫn theo [EF-S-01](./EF-S-01_Data_Structure.md):

```text
Main Scripts/IDE_UI/
├── E_main_window.py
├── E_center_workspace.py
├── E_left_panel.py
├── E_right_panel.py
├── E_custom_title_bar.py
├── E_workers.py                 Tạo khi có nhiều worker dùng chung
└── __init__.py
```

Không bắt buộc tạo `E_workers.py` nếu chỉ có một worker rất nhỏ và rõ ràng. Khi một widget chứa nhiều class worker hoặc pipeline logic, phải tách.

## 7.4. UI chỉ gọi Manager/facade

```python
# Đúng: worker chỉ biết một cổng điều phối
from News.E_news_manager import NewsManager

class NewsWorker(QThread):
    progress = pyqtSignal(str)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def run(self):
        try:
            result = NewsManager.run_summary(
                source=self.source,
                category=self.category,
                progress_callback=self.progress.emit,
            )
            self.succeeded.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
```

```python
# Sai: UI tự ghép pipeline
from News.E_news_scraper import fetch_news
from News.E_ai_client import summarize_news_json
from News.E_news_renderer import render_news_html
```

Nếu Manager chưa có method phục vụ UI, Agent phải bổ sung use case ở Manager/Application Service. Không đi tắt trong UI.

## 7.5. Thread và giữ UI không bị treo

Mọi tác vụ network hoặc xử lý đáng kể phải chạy ngoài GUI thread.

Worker phải có signal tách biệt:

- `progress`: cập nhật tiến độ;
- `succeeded`: kết quả thành công;
- `failed`: lỗi;
- `cancelled`: nếu use case hỗ trợ hủy.

Không gửi chuỗi “Lỗi: ...” qua signal `finished` rồi để UI tưởng là thành công.

Widget chỉ được cập nhật từ GUI thread thông qua signal. Worker không trực tiếp sửa widget.

## 7.6. Trạng thái nút và tác vụ

Khi bắt đầu:

- disable nút có thể chạy trùng;
- hiển thị trạng thái đang chạy;
- giữ reference tới worker để không bị garbage collected.

Khi success/error/cancel:

- enable lại nút;
- dọn worker/reference;
- hiển thị thông báo phù hợp;
- log chi tiết kỹ thuật theo [EF-S-04](./EF-S-04_Logging_Debug.md).

Không để exception làm nút bị khóa vĩnh viễn.

## 7.7. Hiển thị lỗi

- Người dùng thấy câu dễ hiểu: “Không kết nối được FireAnt sau 3 lần thử”.
- Log giữ traceback và chi tiết kỹ thuật.
- Không hiển thị API key/token/path nhạy cảm.
- Nếu kết quả partial, UI phải nói rõ nguồn/item nào thiếu; không chỉ hiện “Hoàn tất”.

## 7.8. Renderer và HTML

- UI được hiển thị HTML đã nhận từ Manager/use case.
- Business manager có thể gọi Renderer phù hợp để tạo presentation output.
- Nếu UI nhận dữ liệu thuần và tự render, renderer phải là thành phần presentation của UI, không được đi cào/AI/ghi data.
- Text lấy từ nguồn ngoài phải được escape/sanitize trước khi nhúng HTML để tránh phá giao diện hoặc chèn nội dung nguy hiểm.

## 7.9. Test UI

Ưu tiên test:

- Manager/use case bằng unit test không cần PyQt;
- worker phát đúng success/error signal;
- widget bật/tắt nút đúng khi success/error;
- một số smoke test chính cho MainWindow.

Không cố test toàn bộ business logic qua click UI.

## 7.10. Checklist cho Agent

- [ ] Widget chỉ layout, input, signal và hiển thị?
- [ ] UI/worker chỉ import Manager/facade, không import module con?
- [ ] Network/heavy work chạy ngoài GUI thread?
- [ ] Có signal success/error riêng?
- [ ] Mọi đường success/error đều mở lại nút và cleanup worker?
- [ ] UI không đọc/ghi JSON/Parquet nghiệp vụ trực tiếp?
- [ ] Error message dễ hiểu, log vẫn có chi tiết?
- [ ] HTML từ nguồn ngoài được escape/sanitize?
- [ ] Import đi đúng [EF-S-00](./EF-S-00_Dependency_Direction.md)?
