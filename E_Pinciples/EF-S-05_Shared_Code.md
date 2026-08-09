# Chương 5 — EF-S-05: Shared Code (Code dùng chung)

> **Trạng thái:** ACTIVE.
>
> **Agent phải đọc file này khi:** định tạo helper/utility, thấy code giống nhau ở nhiều nơi, muốn chuyển file vào `E_Helper/` hoặc tạo abstraction dùng chung.
>
> **Mục tiêu:** Tránh copy một logic quan trọng nhiều nơi, nhưng cũng tránh gom quá sớm thành một helper khó hiểu.

## 5.1. DRY không có nghĩa “thấy hai đoạn giống là gom ngay”

DRY nên được hiểu là:

> Một **quy tắc/kiến thức quan trọng** của hệ thống chỉ nên có một nguồn sự thật.

Hai đoạn code nhìn giống nhau nhưng phục vụ hai nghiệp vụ khác nhau có thể thay đổi theo hai hướng khác nhau. Gom chúng quá sớm sẽ khiến sửa một bên làm hỏng bên kia.

## 5.2. Quy tắc mặc định: Rule of Three

| Tình huống | Hành động mặc định |
|---|---|
| Chỉ dùng ở một nơi | Giữ gần nơi sử dụng |
| Xuất hiện ở hai nơi | Ghi nhận duplication; chỉ gom nếu chắc chắn cùng một quy tắc |
| Xuất hiện ở từ ba nơi | Review nghiêm túc để đưa thành shared code |
| Là quy tắc trung tâm dù mới hai nơi | Có thể gom sớm nếu một thay đổi bắt buộc phải áp dụng đồng thời cho cả hai |

Đây là mặc định, không phải máy đếm cứng. Agent phải giải thích “vì sao đây là cùng một kiến thức”, không chỉ nói “code giống nhau”.

## 5.3. Điều kiện để đưa vào `E_Helper/`

Một helper dùng chung phải thỏa tất cả:

- Không chứa business logic riêng của một Phase/News/UI.
- Không import Manager, UI hoặc module nghiệp vụ.
- Có input/output rõ ràng.
- Tên mô tả chức năng cụ thể.
- Có test nếu xử lý logic không đơn giản.
- Việc dùng chung làm giảm rủi ro lệch logic, không chỉ giảm vài dòng code.

Ví dụ phù hợp:

- `E_config.py`: đường dẫn/constant chung.
- `E_io_utils.py`: atomic write JSON/Parquet.
- Logger setup chung nếu mọi module dùng cùng format.

Ví dụ không phù hợp:

- `calculate_rsi_for_phase2()` — business logic Phase 2.
- `render_news_card()` — presentation riêng của News/UI.
- `helpers.py` chứa hàng chục hàm không liên quan.

## 5.4. Chọn nơi đặt shared code

Không phải code dùng bởi hai file đều phải lên root `E_Helper/`.

```text
Dùng trong một file                 → giữ trong file
Dùng trong một feature/folder       → module private trong feature đó
Dùng trong một Phase                → module chung của Phase
Dùng thật sự xuyên nhiều Phase      → E_Helper/
```

Đặt code ở phạm vi nhỏ nhất vẫn phục vụ đủ người dùng của nó.

## 5.5. Quy trình thăng cấp

1. Tìm tất cả nơi đang dùng/đang copy logic.
2. So sánh xem chúng có thật sự cùng quy tắc và cùng hướng thay đổi không.
3. Thiết kế API nhỏ, tên cụ thể; không tạo “god helper”.
4. Thêm hoặc cập nhật test cho hành vi chung.
5. Di chuyển code sang phạm vi phù hợp.
6. Cập nhật tất cả import/caller.
7. Chạy test và tìm lại để chắc không còn bản copy cũ.
8. Xóa code cũ chỉ sau khi caller đã chuyển xong.

Không copy sang `E_Helper/` rồi xóa file gốc trước khi kiểm tra caller; việc di chuyển phải là một thay đổi hoàn chỉnh.

## 5.6. Khi không nên gom

Không gom nếu:

- chỉ giống nhau tình cờ;
- cần nhiều cờ `if phase == ...` để phục vụ các caller khác nhau;
- helper phải import ngược business module;
- API chung khó hiểu hơn hai đoạn code nhỏ;
- chưa biết hai logic sẽ thay đổi theo hướng nào.

Trong trường hợp chưa chắc, chấp nhận duplication nhỏ trong thời gian ngắn và ghi issue/TODO cụ thể. Không thêm TODO chung chung vào mọi function “có thể dùng lại”.

## 5.7. Shared code cũng phải có owner/ràng buộc

Khi sửa một helper chung, Agent phải:

- tìm toàn bộ caller;
- kiểm tra ảnh hưởng tới từng Phase;
- giữ backward compatibility hoặc cập nhật tất cả caller trong cùng thay đổi;
- chạy test của helper và các caller chính;
- không thay đổi hành vi ngầm mà chỉ đổi tên “refactor”.

## 5.8. Checklist cho Agent

- [ ] Đây là cùng một quy tắc/kiến thức hay chỉ giống cú pháp?
- [ ] Đã có bao nhiêu caller thật sự?
- [ ] Nơi đặt mới có phải phạm vi nhỏ nhất phù hợp?
- [ ] Shared module có độc lập với business/UI?
- [ ] Tên có cụ thể hơn `utils`/`helpers`?
- [ ] Có cần test cho logic chung?
- [ ] Đã tìm và cập nhật tất cả caller?
- [ ] Đã chạy test trước khi xóa bản cũ?
- [ ] Có đang tạo abstraction sớm chỉ để giảm vài dòng code?
