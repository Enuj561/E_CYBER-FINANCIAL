# Chương 9 — EF-S-08: UI Architecture — Frontend (C#)

> [!WARNING]
> **CHỜ CẬP NHẬT:** Nội dung chương này là bản draft khung sườn. Chủ dự án cần review và customize lại theo thiết kế mong muốn trước khi áp dụng chính thức. Cần bổ sung: chọn framework (WPF/WinUI/Avalonia?), giao thức FE↔BE, cấu trúc thư mục C# project.

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** Model-View-ViewModel (MVVM) + Frontend-Backend Separation
> - **Nguồn gốc:** John Gossman (Microsoft), 2005. Thiết kế riêng cho WPF/Silverlight.
> - **Giải thích:** Tách hoàn toàn giao diện C# (Frontend) ra khỏi logic Python (Backend). Frontend chỉ hiển thị + nhận input → gửi về Backend xử lý. Backend trả kết quả → Frontend render.

## 1. Triết lý: Tách Frontend (C#) / Backend (Python)

```
┌────────────────────┐          ┌────────────────────┐
│   C# FRONTEND      │          │   PYTHON BACKEND   │
│                    │          │                    │
│  ┌──────────────┐  │          │  ┌──────────────┐  │
│  │ View (.xaml)  │  │   giao   │  │ Manager      │  │
│  │ ViewModel    │  │◄═══════►│  │ Calculator   │  │
│  │ (MVVM)       │  │   thức   │  │ Pipeline     │  │
│  └──────────────┘  │  FE↔BE  │  └──────────────┘  │
│                    │          │                    │
│  CHỈ hiển thị      │          │  MỌI business      │
│  + nhận input      │          │  logic ở đây       │
└────────────────────┘          └────────────────────┘
```

## 2. Giao thức giao tiếp FE ↔ BE

*(Chờ quyết định: REST API? gRPC? File-based IPC? WebSocket?)*

## 3. Quy tắc chung cho Frontend C#

- Frontend KHÔNG ĐƯỢC chứa business logic
- Frontend chỉ hiển thị + nhận input → gửi về Backend xử lý
- Nếu dùng WPF: áp dụng MVVM (tham chiếu E-S-07 trong dự án Revit gốc)
- View (.xaml) không chứa logic C#
- ViewModel không gọi trực tiếp Python modules

## 4. Placeholder

Chi tiết sẽ bổ sung khi triển khai C# Frontend. Các mục cần quyết định:
- [ ] Chọn framework: WPF / WinUI 3 / Avalonia
- [ ] Giao thức FE↔BE
- [ ] Cấu trúc thư mục C# project
- [ ] Theme & Brand Identity (có giữ Cyberpunk aesthetic không?)
- [ ] Quản lý state: ViewModel hay Store pattern?
