# Chương 8 — EF-S-08: C# Frontend (Giao diện tương lai)

> **Trạng thái:** INACTIVE DRAFT — chưa được phép dùng để tự triển khai C# frontend.
>
> **Agent chỉ mở file này khi:** chủ dự án yêu cầu nghiên cứu, thiết kế hoặc triển khai C# frontend.
>
> **Nếu task đang sửa PyQt6:** đóng nhánh này và dùng [EF-S-07](./EF-S-07_UI_Backend.md).
>
> **Mục tiêu:** Ghi các quyết định cần chốt trước khi tách giao diện C# khỏi backend Python; không giả vờ rằng kiến trúc đã được chọn.

## 8.1. Trạng thái hiện tại

- Dự án hiện dùng PyQt6.
- Chưa có C# solution/project trong repo.
- Chưa chọn WPF, WinUI 3 hay Avalonia.
- Chưa chọn giao thức C# ↔ Python.
- Vì vậy Agent **không được tự tạo C# project, REST server hoặc gRPC service** chỉ dựa trên file draft này.

Khi có task thật, Agent phải lập plan và yêu cầu chủ dự án duyệt các quyết định ở §8.3 trước.

## 8.2. Ranh giới dự kiến

```text
C# Frontend                              Python Backend
──────────────────────────               ──────────────────────────
View: XAML/layout                        Manager/Application Service
ViewModel: state, command                Collector/Client/Repository
Presentation validation/formatting       Calculator/Validator
IPC client                               ML/News/Data pipeline
             ↕  API/IPC contract  ↕
```

Frontend được chứa **presentation logic**, ví dụ:

- trạng thái tab/nút;
- format ngày/số để hiển thị;
- kiểm tra input đơn giản như ô bắt buộc;
- loading, cancel, retry UI;
- mapping kết quả backend thành card/chart.

Backend giữ **business logic**, ví dụ:

- công thức tài chính;
- chọn nguồn data;
- retry/rate limit API;
- pipeline/training/backtest;
- ghi data/model.

“Frontend không có bất kỳ logic nào” là không thực tế. Luật đúng là frontend không được trở thành nơi chứa business rule của Python backend.

## 8.3. Các quyết định bắt buộc trước khi ACTIVE

### 1. Framework

| Lựa chọn | Phù hợp khi | Trade-off chính |
|---|---|---|
| WPF | Chỉ Windows, hệ sinh thái ổn định | UI technology cũ hơn nhưng tài liệu nhiều |
| WinUI 3 | Muốn Windows UI hiện đại | Deployment/tooling phức tạp hơn |
| Avalonia | Muốn khả năng cross-platform | Hệ sinh thái nhỏ hơn WPF |

### 2. Cách chạy backend Python

Cần chọn một mô hình:

- Python service chạy nền lâu dài;
- frontend khởi chạy Python worker process khi cần;
- backend đóng gói thành service riêng.

### 3. Giao thức IPC/API

| Lựa chọn | Ưu điểm | Điểm cần cẩn thận |
|---|---|---|
| REST local | Dễ debug, phổ biến | Port, lifecycle, authentication local |
| gRPC | Contract/type rõ, streaming tốt | Tooling và setup nặng hơn |
| stdio/JSON process | Không cần mở port, đơn giản cho app local | Quản lý process, framing, crash/restart |
| File-based | Dễ hình dung | Chậm, khó progress/cancel/concurrency; không nên là lựa chọn mặc định |

### 4. Contract

Phải định nghĩa:

- request/response schema và version;
- progress event;
- success/partial/error result;
- timeout/cancel;
- backend version compatibility;
- đường dẫn file lớn hoặc streaming;
- timezone, number/date format.

### 5. Phân phối và license

Phải chốt:

- cách bundle Python runtime/dependencies;
- auto-update/versioning;
- nơi lưu `.env`/secret;
- license của PyQt6 có còn liên quan sau chuyển đổi không;
- license của các package data/ML khi phân phối app.

## 8.4. MVVM nếu chọn framework phù hợp

- View/XAML: layout và binding.
- ViewModel: state/command/presentation logic, gọi IPC client abstraction.
- Service/IPC client: giao tiếp backend, không để HTTP/gRPC rải trong ViewModel.
- Model/DTO: dữ liệu theo contract, không nhét business algorithm vào DTO.

Code-behind không bị cấm tuyệt đối. Nó được dùng cho hành vi thuần View khó biểu diễn bằng binding (focus, animation, window chrome), nhưng không chứa business logic hoặc gọi Python trực tiếp.

## 8.5. Hướng phụ thuộc dự kiến

```text
View → ViewModel → Application/IPC Client Interface → IPC implementation
```

- View không gọi Python/process/HTTP trực tiếp.
- ViewModel không biết chi tiết khởi chạy executable/port nếu có thể che sau interface.
- Python backend không import hoặc phụ thuộc C# frontend.
- Hai bên chỉ cùng biết contract/version.

## 8.6. Điều kiện chuyển thành ACTIVE

File này chỉ được đổi từ `INACTIVE DRAFT` sang `ACTIVE` khi:

- [ ] Chủ dự án đã chọn framework.
- [ ] Đã chọn process model và IPC.
- [ ] Có sơ đồ lifecycle: start, health check, crash, restart, shutdown.
- [ ] Có schema request/response/error/progress đầu tiên.
- [ ] Có spike/prototype chứng minh C# gọi Python thành công.
- [ ] Có kế hoạch packaging và license.
- [ ] Có cấu trúc C# project được duyệt.
- [ ] Có kế hoạch chuyển từng màn hình từ PyQt6, không big-bang rewrite mù quáng.

## 8.7. Checklist cho Agent khi nhánh này được gọi

- [ ] Task thật sự nói về C# frontend, không phải PyQt6?
- [ ] File vẫn là INACTIVE DRAFT?
- [ ] Nếu chưa có quyết định bắt buộc, Agent đã dừng ở mức proposal/prototype?
- [ ] Không tự chọn framework/IPC thay chủ dự án?
- [ ] Frontend/backend có contract version rõ?
- [ ] Business logic vẫn ở Python backend?
- [ ] Presentation logic được phép ở ViewModel thay vì cấm mọi logic?
- [ ] Có tính tới progress, cancel, crash/restart và packaging?
