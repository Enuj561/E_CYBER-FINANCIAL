# [EF-S-05](./EF-S-05_Shared_Code.md): Shared Code Promotion (Quy trình thăng cấp code)

> **Nền tảng lý thuyết:**
> - **Nguyên tắc:** DRY — Don't Repeat Yourself
> - **Nguồn gốc:** *The Pragmatic Programmer* — Andy Hunt & Dave Thomas, 1999
> - **Giải thích:** Mỗi đoạn logic chỉ nên tồn tại ở đúng 1 nơi duy nhất. Nếu cùng một hàm xuất hiện ở ≥ 2 Phase/Module khác nhau, đó là tín hiệu để "thăng cấp" nó lên thư mục `Helper/`, biến nó thành công cụ dùng chung.

## 1. Tiêu chí thăng cấp

| Điều kiện                                                          | Hành động                                                    |
| ------------------------------------------------------------------ | ------------------------------------------------------------ |
| Hàm/module chỉ dùng trong **1 Phase**                              | Giữ nguyên trong Phase folder                                |
| Hàm/module được gọi bởi **≥ 2 Phase/Module**                       | **BẮT BUỘC** chuyển lên `Helper/`                             |
| Hàm/module có tiềm năng dùng chung **nhưng hiện chỉ có 1 nơi gọi** | Giữ nguyên, đánh dấu `# TODO: Promote to Helper/ if reused` |

## 2. Quy trình di chuyển

1. Copy file sang `Helper/`
2. Xoá file gốc trong Phase Folder
3. Cập nhật tất cả import path
4. Chạy test kiểm tra
5. Commit với message: `"refactor: Promote {module} to Helper/"`

## 3. Ví dụ thực tế

| Hàm/Module | Xuất hiện ở | Đã thăng cấp? |
|---|---|---|
| `config.py` (paths, constants) | Mọi nơi | ✅ Đã nằm trong `Helper/` |
| `ensure_dirs()` | Phase 1, Phase 5 | ✅ Đã nằm trong `config.py` |
| *(Các ứng viên tương lai sẽ bổ sung khi dự án phát triển)* | | |
