# Bài học kinh nghiệm (Lesson Learned)

Danh sách các bài học rút ra trong quá trình làm việc:

## Cập nhật ngày 31/05/2026 (Phiên Big Update tính năng News)

1. **Bug tàng hình do thiếu `.format()` trong Prompt AI**: 
   - *Vấn đề*: AI Gemini bất ngờ tự bịa ra các tin tức từ năm cũ (2023, 2024) với các tên công ty giả định.
   - *Nguyên nhân*: Truyền chuỗi template `{content}` vào chuỗi nhiều dòng (`"""`) nhưng quên gọi hàm `.format(content=content)`. Hậu quả là AI nhận được chữ literal "{content}", và do bị ép xuất JSON nên nó đã tự "ảo giác" (hallucinate) ra dữ liệu giả.
   - *Bài học*: Luôn kiểm tra kỹ các biến được truyền vào chuỗi String dài, tốt nhất là debug in thẳng ra Console nội dung trước khi ném cho API. Truyền đủ Context (như Ngày Giờ) để khóa mỏ AI.

2. **Xung đột Style (Background Glitch) của `QTextEdit` trong PyQt**:
   - *Vấn đề*: Khi thay đổi text trạng thái ("Đang lấy tin..."), chữ bị viền background xám lem nhem.
   - *Nguyên nhân*: Hàm `setText()` của PyQt đôi khi không xóa sạch các thuộc tính CSS cũ từ thao tác `setHtml()` trước đó (ví dụ màu nền xám của khung báo lỗi).
   - *Bài học*: Khi muốn ép lại định dạng hoàn toàn sạch sẽ, hãy dùng luôn `setHtml()` kẹp thêm `background: transparent;` thay vì dùng `setText()`.

3. **Lưu ý vòng đời (Lifecycle) UI khi chèn Widget**:
   - *Vấn đề*: Bấm mở Tab News không phản hồi.
   - *Nguyên nhân*: Trong lúc tái cấu trúc hàm tạo Layout, đoạn code `stacked_widget.addWidget()` vô tình bị cắt nhầm ra ngoài hàm khởi tạo, khiến trang UI không được sinh ra.
   - *Bài học*: Phải đảm bảo luôn chốt hạ `.addLayout()` và `.addWidget()` cuối mỗi hàm setup UI.

4. **Sự phòng bị trước các "Báo Ngáo" (Stale RSS Data)**:
   - *Vấn đề*: Feed RSS của mảng Công nghệ báo Vietnamnet chứa tin từ 1-2 năm trước.
   - *Giải pháp*: Màng lọc thời gian (Timeframe Filter) dùng thư viện `datetime` đã chứng minh hiệu quả tuyệt đối khi tự động `continue` (chặn rác) thành công.
   - *Bài học*: Luôn cảnh giác với dữ liệu Cào (Scraping), không bao giờ được tin tưởng 100% vào nguồn cung mà phải tự xây dựng các "Kháng sinh" (Validation Logic) phía Client.

5. **Chiến thuật "Cố lỳ" (Retry/Backoff Strategy) khi xài API Chùa**:
   - *Vấn đề*: Sử dụng API Gemini Free Tier dễ bị dính lỗi `429 RESOURCE_EXHAUSTED` nếu gửi yêu cầu quá nhanh.
   - *Giải pháp*: Bọc hàm gọi API trong khối `try... except` vòng lặp `for`. Nếu bắt được lỗi 429, cho luồng chạy ngủ (`time.sleep(10)`) rồi thử lại (Retry) tối đa 3 lần.
   - *Bài học*: Kết hợp chiến thuật Retry với luồng chạy ẩn (`QThread`) của PyQt là một Combo hoàn hảo. UI không hề bị đóng băng, người dùng chỉ thấy quá trình tải lâu hơn một chút (đợi Retry), tạo cảm giác cực kỳ mượt mà và ẩn giấu hoàn toàn lỗi đứt gãy kết nối khỏi màn hình hiển thị.
