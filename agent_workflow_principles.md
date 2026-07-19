# BỘ NGUYÊN TẮC LÀM VIỆC CỦA AI AGENT (AGENT WORKFLOW PRINCIPLES)

Tài liệu này quy định luồng công việc bắt buộc (Workflow) của AI Agent khi tương tác, đọc hiểu và chỉnh sửa mã nguồn (source code) trong dự án E_CYBER-REVIT.

Mục tiêu cốt lõi: Đảm bảo tính chính xác tuyệt đối khi sửa code, tránh các lỗi sai ngớ ngẩn do công cụ thay thế chuỗi tự động (auto-replace) gây ra, đồng thời tối ưu hóa tài nguyên Token/Context Window.

---

## 1. QUY TRÌNH 3 BƯỚC BẮT BUỘC (TELEPORT -> ĐỌC HIỂU -> CHỈNH SỬA)

AI Agent tuyệt đối **KHÔNG ĐƯỢC** dùng tool can thiệp/sửa code ngay lập tức khi chưa qua bước đọc hiểu thủ công ngữ cảnh xung quanh.

### Bước 1: Quét & Định vị (Search & Teleport)
- Sử dụng các công cụ rà quét diện rộng (`grep_search` hoặc `run_command`) để nhanh chóng tìm ra tọa độ (file name, line number) của đoạn code cần sửa.
- **Mục đích:** Tránh việc đọc toàn bộ file từ trên xuống dưới một cách mù quáng gây tràn bộ nhớ (Context Window) và hao tốn tài nguyên hệ thống.

### Bước 2: Đọc hiểu thủ công (Manual Context Review)
- Sau khi có tọa độ, bắt buộc phải dùng lệnh `view_file` để **đọc một vùng mã nguồn (khoảng 20 - 50 dòng) xung quanh tọa độ đó**.
- **Mục đích:** Nắm rõ ngữ cảnh, kiểm tra xem có biến cục bộ, logic lân cận hay các thẻ `using` nào bị ảnh hưởng nếu tiến hành chỉnh sửa hay không.

### Bước 3: Sửa đổi chính xác (Precise Manual Edit)
- Chỉ sau khi đã hiểu trọn vẹn ngữ cảnh ở Bước 2, mới được phép dùng các công cụ chỉnh sửa (`multi_replace_file_content`, `replace_file_content`, hoặc `write_to_file`) để đắp code mới vào.
- Đặc biệt cẩn thận khi xóa/thay thế các dòng code trong các file cấu hình như `.csproj` để không làm mất các file đang được đăng ký (compile).

---

## 2. QUẢN LÝ TÀI NGUYÊN (RESOURCE OPTIMIZATION)

- **Cấm đọc tràn lan:** Không dùng `view_file` để đọc các file dài hàng nghìn dòng nếu không có mục đích cụ thể. Luôn dùng tham số `StartLine` và `EndLine` để giới hạn phạm vi đọc.
- **Chắt chiu Token:** Nhận thức rõ bộ nhớ ngắn hạn là có giới hạn. Làm việc theo từng Module nhỏ, dứt điểm từng Feature thay vì xử lý nhiều Feature phức tạp cùng lúc dẫn đến quá tải bộ nhớ.

---

## 3. THÁI ĐỘ LÀM VIỆC (MINDSET)

- **"Thủ công" nhưng tốc độ máy tính:** Agent đóng vai trò là một Lập trình viên cấp cao. Quá trình di chuyển và tìm kiếm được thực hiện bằng Tool, nhưng quá trình ra quyết định thay đổi code bắt buộc phải dựa trên sự **ĐỌC HIỂU TƯ DUY** thủ công.
- **Hạn chế giả định:** Nếu định vị thấy dòng code nhưng chưa chắc chắn về logic lân cận, bắt buộc phải lùi lại thực hiện Bước 2 (đọc thêm dòng) hoặc hỏi lại User trước khi nhắm mắt dùng tool "Replace".

---

## 4. KỶ LUẬT THỰC THI (STRICT ADHERENCE TO THE PLAN)

- **Bám sát 100% Kế hoạch (Plan):** Khi User đã chốt và duyệt bản Kế hoạch (Implementation Plan), Agent phải thực thi **chính xác từng chữ** những gì đã cam kết trong đó.
- **Cấm tự tiện "sáng tạo":** Tuyệt đối KHÔNG ĐƯỢC tự ý sửa, thêm, hay bớt bất kỳ logic, class, hay chức năng nào ngoài phạm vi của Kế hoạch. 
- **Cấm tự ý thêm râu ria:** Kể cả những chi tiết vụn vặt nhất (như tự ý thêm dòng thông báo Notification, sửa text trong TaskDialog, hay dùng thư viện mà chưa xin phép) cũng bị nghiêm cấm.
- Nếu trong quá trình code phát sinh lỗi hoặc muốn cải tiến thêm, Agent phải dừng lại để **Báo cáo và Xin phép User (update Plan)** chứ không được "tiền trảm hậu tấu".
