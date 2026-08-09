# Hướng dẫn lấy token FireAnt mới

Mục tiêu: lấy token mới mà **không cần biết code** và không đưa mật khẩu/token cho Agent.

## Trước khi làm

- Chỉ làm trên máy cá nhân của fen.
- Không chụp ảnh hoặc gửi token vào chat.
- Token có giá trị gần giống mật khẩu tạm thời. Ai có token có thể dùng quyền của tài khoản trong thời gian token còn sống.
- Nếu đang livestream hoặc chia sẻ màn hình, dừng chia sẻ trước.

## Cách dễ nhất: lấy từ trình duyệt

Ví dụ dưới đây dùng Chrome hoặc Edge.

### Phần A — Đăng nhập FireAnt

1. Mở [FireAnt](https://fireant.vn/) và đăng nhập bình thường.
2. Mở một trang có data, ví dụ trang chi tiết mã `VNM`.
3. Nhấn `F12` để mở bảng dành cho người phát triển.
4. Chọn tab **Network**. Nếu không thấy, bấm dấu `»` để tìm.
5. Bấm biểu tượng xóa danh sách cũ, sau đó tải lại trang bằng `Ctrl + R`.

### Phần B — Tìm token

1. Trong ô lọc của tab Network, thử gõ `historical-quotes`.
2. Nếu không có kết quả, xóa từ lọc rồi gõ `symbols`.
3. Chọn một dòng có địa chỉ bắt đầu bằng `api.fireant.vn` hoặc `restv2.fireant.vn`.
4. Ở khung bên phải, mở phần **Headers**.
5. Tìm phần **Request Headers**, rồi tìm dòng `Authorization`.
6. Dòng đó thường có dạng:

   ```text
   Bearer eyJ...
   ```

7. Chỉ sao chép phần nằm sau chữ `Bearer` và một dấu cách. Không chép luôn chữ `Bearer`.

Nếu không thấy dòng `Authorization`, thử một yêu cầu FireAnt khác trong danh sách. Nếu tất cả đều không có, dừng lại; không lấy token từ cookie và không cài tiện ích trình duyệt lạ.

## Thay token trong dự án

1. Mở file `System/.env` bằng trình soạn thảo văn bản.
2. Tìm dòng bắt đầu bằng:

   ```text
   FIREANT_BEARER_TOKEN=
   ```

3. Xóa token cũ ở sau dấu `=` và dán token mới vào. Kết quả có dạng:

   ```text
   FIREANT_BEARER_TOKEN=eyJ...
   ```

4. Không thêm chữ `Bearer` vào file.
5. Lưu file rồi đóng lại.
6. Chỉ cần báo cho Agent: **“T đã thay token FireAnt mới.”** Không gửi kèm token.

## Nếu cách trên không tìm thấy token

Tài liệu API chính thức của FireAnt có cổng đăng nhập và cổng làm mới token, nhưng cách này cần dùng tài khoản/mật khẩu trực tiếp với API. Để tránh lộ mật khẩu trong cửa sổ lệnh hoặc lịch sử chat, **không tự gõ mật khẩu vào lệnh PowerShell và không gửi mật khẩu cho Agent**.

Khi gặp trường hợp này, ta sẽ làm một công cụ đăng nhập nhỏ có ô nhập mật khẩu được che đi. Công cụ chỉ lưu token vào `System/.env`, không lưu mật khẩu.

## Sau khi thay token

Agent sẽ thực hiện Bước 1.1 theo thứ tự:

1. Thử 1 yêu cầu OHLCV cũ.
2. Nếu thành công, thử BCTC `VNM` và `VCB`, mỗi mã 2 quý.
3. Ghi báo cáo ngay dưới Bước 1.1.
4. Chỉ gạch Bước 1.1 khi đã có kết luận rõ.

Nguồn kiểm tra: [tài liệu API chính thức của FireAnt](https://api.fireant.vn/) mô tả cách xác thực OAuth2, cổng đăng nhập và cổng làm mới token.
