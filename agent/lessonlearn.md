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

## Cập nhật ngày 09/08/2026 (Xây luồng thu thập BCTC hai nguồn)

> Ghi chú: Không phải mọi lần dừng đều là code hỏng. Phần dưới tách rõ lỗi nguồn data, lỗi cách xử lý data và lỗi do môi trường/máy bị ngắt.

1. **Token FireAnt cũ trả về `401`**:
   - *Hiện tượng*: Cả cổng BCTC và cổng OHLCV dùng để kiểm tra đều từ chối yêu cầu.
   - *Nguyên nhân*: Token cũ đã hết hạn hoặc không còn hợp lệ. Chưa có bằng chứng để kết luận FireAnt không có BCTC hoặc tài khoản thiếu gói dịch vụ.
   - *Cách xử lý*: Dừng thử liên tục, lấy token mới rồi kiểm tra cổng OHLCV trước khi kiểm tra BCTC.
   - *Bài học*: `401` là lỗi xác thực. Không được biến nó thành kết luận “nguồn không có data”.

2. **Token mới bị dán thừa chữ `Bearer`**:
   - *Hiện tượng*: Giá trị cấu hình có dạng `Bearer <token>`, trong khi code đã tự thêm chữ `Bearer` vào phần gửi đi.
   - *Nguyên nhân*: Dán nguyên nội dung từ phần Authorization vào `.env` thay vì chỉ dán phần token.
   - *Cách xử lý*: Bỏ đúng tiền tố bị thừa mà không in hoặc ghi token vào log. Sau đó OHLCV và BCTC FireAnt đều chạy được.
   - *Bài học*: Trước khi gọi API, chỉ kiểm tra hình dạng token như có tồn tại, có tiền tố thừa hay có dấu nháy; tuyệt đối không hiển thị giá trị thật.

3. **Máy bị ngắt giữa lúc chạy Bước 2 và Bước 12**:
   - *Hiện tượng*: Luồng đang chạy bị mất kết nối/interrupt, không thể chắc chắn phần nào đã hoàn thành.
   - *Nguyên nhân*: Môi trường chạy bị ngắt, không phải bằng chứng cho thấy API hoặc logic code sai.
   - *Cách xử lý*: Kiểm tra tiến trình cũ; nếu không nối lại được thì đọc sổ tiến độ và file đã lưu trước khi chạy lại. Không xóa hoặc ghi đè kết quả cũ.
   - *Bài học*: Tác vụ dài phải có `run_id`, sổ tiến độ, ghi file an toàn qua file tạm và khả năng resume. Sau khi máy ngắt, phải kiểm kê trước khi chạy lại từ đầu.

4. **Không chạy được test bằng `pytest`**:
   - *Hiện tượng*: Lệnh `pytest` không dùng được trên máy.
   - *Nguyên nhân*: Môi trường hiện tại chưa cài package `pytest`; đây không phải test fail.
   - *Cách xử lý*: Dùng `unittest` có sẵn để kiểm tra. Kết quả cuối là 69/69 bài Phase 1 đạt.
   - *Bài học*: Phải phân biệt “test không chạy vì thiếu công cụ” với “test đã chạy và bị fail”. Không tự cài dependency khi chưa được duyệt.

5. **VCI có cột trộn cả số và chữ nên Parquet từ chối lưu**:
   - *Hiện tượng*: Data lấy được nhưng bước ghi Parquet bị lỗi kiểu dữ liệu.
   - *Nguyên nhân*: Một cột của VCI chứa lẫn giá trị số và giá trị chữ; Parquet cần kiểu cột nhất quán hơn.
   - *Cách xử lý*: Giữ raw, chuyển kiểu lưu theo quy tắc rõ ràng và ghi metadata về thay đổi đó.
   - *Bài học*: “API trả thành công” chưa có nghĩa là “file chắc chắn lưu được”. Cần test cả vòng lấy → ghi → đọc lại.

6. **Bảng ratio của VCI trộn kỳ năm và kỳ quý**:
   - *Hiện tượng*: Normalizer có thể hiểu nhầm cột năm thành quý hoặc ngược lại.
   - *Nguyên nhân*: Cấu trúc ratio khác ba nhóm báo cáo chính và không tuân theo một mẫu kỳ duy nhất.
   - *Cách xử lý*: Nhận diện kỳ bằng quy tắc riêng cho ratio; trường hợp chưa chắc chắn phải cảnh báo, không tự đoán.
   - *Bài học*: Không áp một cách đọc chung cho mọi loại báo cáo chỉ vì chúng cùng đến từ VCI.

7. **Ratio chứa dòng metadata và có cột năm trùng tên**:
   - *Hiện tượng*: Các dòng như `ratioType`, `ratioTTMId` bị hiểu nhầm thành chỉ tiêu tài chính; cột trùng tên làm bước ghi hoặc chuẩn hóa thất bại.
   - *Nguyên nhân*: Data thật có phần mô tả kỹ thuật nằm chung với bảng số liệu và có nhãn cột không duy nhất.
   - *Cách xử lý*: Tách metadata khỏi chỉ tiêu, tạo tên cột lưu trữ không trùng nhưng phải giữ dấu vết tên gốc.
   - *Bài học*: Không được âm thầm xóa dòng/cột gây vướng. Mọi thay đổi để lưu được data phải có dấu vết và bài test chống tái phát.

8. **Số ratio năm hiện tại có thể chỉ là số lũy kế YTD**:
   - *Hiện tượng*: Nguồn đặt dữ liệu vào nhánh năm nhưng kỳ hiện tại có thể chưa phải số cả năm đã chốt.
   - *Nguyên nhân*: Cách đặt nhãn của nguồn chưa đủ để khẳng định ý nghĩa kinh tế của con số.
   - *Cách xử lý*: Giữ data gốc, gắn cảnh báo YTD và chưa dùng như số cả năm hoàn chỉnh.
   - *Bài học*: Đúng kiểu dữ liệu chưa chắc đúng ý nghĩa tài chính. Khi thiếu bằng chứng thì ghi `unknown` hoặc cảnh báo, không tự diễn giải.

9. **Lần đầu push Git bị hết thời gian chờ**:
   - *Hiện tượng*: `git push` đứng lâu và bị dừng sau khoảng hai phút, trong khi commit trên máy đã tạo thành công.
   - *Nguyên nhân*: Khâu kết nối/xác thực hoặc truyền dữ liệu với GitHub phản hồi chậm; không phải commit bị hỏng.
   - *Cách xử lý*: So commit trên máy với `origin/main`, xác nhận remote còn thiếu một commit rồi mới push lại. Lần hai thành công.
   - *Bài học*: Khi push timeout, không tạo commit mới ngay. Trước tiên phải kiểm tra commit đã lên remote chưa để tránh thao tác trùng hoặc báo sai trạng thái.

### Quy tắc chung rút ra cho các lần chạy tiếp theo

- Luôn giữ bằng chứng lỗi: mã lỗi, bước đang chạy, nguồn, mã cổ phiếu và `run_id`; không ghi token.
- Không đổi lỗi thành “không có data”, không đổi cảnh báo thành “đã đúng”, không gọi timeout là code hỏng khi chưa kiểm tra.
- Sau mỗi lỗi thật phát hiện từ data live, thêm một bài test để lỗi đó không quay lại.
- Tác vụ dài phải có resume và ghi file an toàn; chạy lại chỉ phần chưa hoàn thành.
- Sau khi sửa, phải kiểm tra theo chuỗi đầy đủ: lấy data → lưu → đọc lại → chuẩn hóa → kiểm tra.
