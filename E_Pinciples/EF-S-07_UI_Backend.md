# Chương 8 — EF-S-07: UI Architecture — Backend (PyQt6)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Separation of Concerns — Tách View khỏi Logic
> - **Giải thích:** Giao diện (View) không được chứa business logic. View chỉ layout, hiển thị kết quả, và bắt event từ user → delegate cho module xử lý (Manager).

> **Kim chỉ nam cho việc phát triển giao diện Desktop (PyQt6) hiện tại. Khi chuyển sang C# Frontend, xem [EF-S-08](./EF-S-08_UI_Frontend.md).**

## 1. Quy tắc chung cho IDE_UI/

| Được phép ✅ | Không được phép ❌ |
|---|---|
| Layout: QWidget, QVBoxLayout, QHBoxLayout... | Gọi API bên ngoài (requests, vnstock) |
| Event binding: `button.clicked.connect(...)` | Xử lý data (pandas, tính toán) |
| Hiển thị kết quả từ Manager | Import trực tiếp module Phase |
| Style: QSS, colors, fonts | Ghi file data |
| Gọi Manager để lấy kết quả | Chứa vòng lặp xử lý business logic |

```python
# ❌ KHÔNG — File UI tự gọi API, xử lý data
class CenterWorkspace(QWidget):
    def on_click(self):
        response = requests.get("https://api.example.com/data")
        df = pd.DataFrame(response.json())
        # ... 50 dòng xử lý ...
        self.display(result)

# ✅ ĐÚNG — UI chỉ gọi Manager, hiển thị kết quả
class CenterWorkspace(QWidget):
    def on_click(self):
        result = SomeManager.process()
        self.display(result)
```

## 2. Cấu trúc thư mục

```
IDE_UI/
├── main_window.py            ← Cửa sổ chính, dock layout
├── center_workspace.py       ← Workspace trung tâm
├── left_panel.py             ← Panel trái (navigation)
├── right_panel.py            ← Panel phải (system log)
└── custom_title_bar.py       ← Title bar tùy chỉnh
```

## 3. Dependency Flow

```
IDE_UI/ → Manager (của phase tương ứng) → hiển thị kết quả
```

- ✅ `IDE_UI/` ĐƯỢC gọi `Manager` để lấy data
- ❌ `Manager` KHÔNG ĐƯỢC import `IDE_UI`
- ❌ `IDE_UI/` KHÔNG ĐƯỢC import trực tiếp module Phase
