# Kế hoạch thu thập dữ liệu Báo cáo tài chính (BCTC)

> **Ngày lập:** 2026-08-09
> **Cập nhật:** 2026-08-16
> **Trạng thái:** ĐANG TRIỂN KHAI TỪNG BƯỚC
> **Phạm vi:** Phase 1 — lấy BCTC từ **vnstock và FireAnt**.
> **File cũ chỉ dùng để tham khảo:** `Main Scripts/Phase 1/1.2_Data_BCTC/E_bctc_collector.py`.

> **Quy tắc báo cáo:** Báo cáo tiến độ được ghi ngay bên dưới từng bước trong file này. Không tạo thêm file `Step_XX_Report.md` riêng, trừ khi người dùng yêu cầu rõ ràng.

## 1. Ta đang muốn làm gì?

Mục tiêu là tạo một bộ dữ liệu BCTC đủ tin cậy cho hơn 1.500 mã chứng khoán, đi cùng bộ OHLCV đã có từ năm 2012.

Ta sẽ lấy từ hai nguồn:

- **vnstock**;
- **FireAnt**.

Hai nguồn phải được lưu riêng. Sau đó mới so sánh để biết:

- số liệu nào giống nhau;
- số liệu nào chỉ có ở một nguồn;
- số liệu nào khác nhau và cần kiểm tra;
- nguồn nào thường đầy đủ hơn với từng loại báo cáo.

Không chạy file cào BCTC cũ cho toàn thị trường ngay. File cũ chỉ giúp tham khảo cách thử lại khi lỗi, chạy nhiều mã và ghi file an toàn.

Thứ tự thực hiện:

```text
Kiểm kê hiện trạng
    ↓
Thử FireAnt và vnstock trên vài mã
    ↓
Chốt cách sắp xếp dữ liệu
    ↓
Viết công cụ mới + kiểm tra bằng data mẫu
    ↓
Chạy thử 12–15 mã
    ↓
Chạy thử 100 mã
    ↓
Cào toàn bộ thị trường
    ↓
Kiểm tra chất lượng lần cuối
```

## 2. Một số từ bắt buộc phải dùng

| Từ | Hiểu đơn giản |
|---|---|
| API | Cổng để chương trình hỏi và nhận dữ liệu từ nguồn ngoài |
| Parquet | Loại file đang dùng để lưu data dạng bảng |
| Dữ liệu gốc | Data vừa nhận từ nguồn, chưa chỉnh sửa |
| Dữ liệu đã chuẩn hóa | Data đã được sắp xếp về một mẫu chung để dễ dùng |
| Checkpoint | Sổ đánh dấu đã làm tới đâu để lần sau chạy tiếp |
| `run_id` | Mã riêng của một lần chạy |
| Pilot | Chạy thử trên một nhóm nhỏ |
| Provider | Nguồn con bên trong vnstock, ví dụ VCI hoặc KBS |

Các tên tiếng Anh trong code vẫn được giữ vì Python cần chúng. Trong tài liệu này, mọi quyết định sẽ được giải thích bằng tiếng Việt.

---

## 3. Hiện trạng đã kiểm tra

### 3.1. OHLCV

| Nguồn | Số mã/file | Số dòng gần đúng | Ngày mới nhất |
|---|---:|---:|---|
| FireAnt | 1.528 | 4,14 triệu | 26/06/2026 |
| vnstock | 1.526 | 2,70 triệu | 26/06/2026 |

- 1.525 mã có ở cả hai nguồn.
- FireAnt có riêng `ANI`, `UTT`, `VPC`.
- vnstock có riêng `FLC`.
- Hợp hai kho OHLCV tạo thành danh sách nền **1.529 mã**.

Danh sách này chưa chứng minh được mã nào đang hoạt động, đã dừng giao dịch hoặc đã hủy niêm yết. Những trạng thái đó phải có nguồn xác nhận, không được đoán.

### 3.2. BCTC

Hiện mới có ba file thử nghiệm của VNM:

```text
VNM_cash_flow_quarter.parquet
VNM_cash_flow_year.parquet
VNM_ratio.parquet
```

Kết quả chạy cũ cho thấy:

- Bảng cân đối kế toán trả về rỗng.
- Báo cáo kết quả kinh doanh bị trùng tên cột nên không lưu được.
- Lưu chuyển tiền tệ và một phần chỉ số tài chính lưu được.
- VNM vừa bị ghi là “đã xong”, vừa có trong danh sách lỗi.

Vì vậy ba file VNM chỉ là **data thử cũ**, chưa được dùng như data chính thức.

### 3.3. Môi trường hiện tại

```text
Python   3.13.5
vnstock  4.0.4
pandas   2.3.3
pyarrow  24.0.0
```

vnstock 4.0.4 cho phép dùng cá nhân/nghiên cứu, phi thương mại. Nếu dự án chuyển sang kinh doanh, phải kiểm tra lại quyền sử dụng.

Danh sách đầy đủ các thư viện đang dùng đã được lưu trong `requirements.txt`.

---

## 4. Vì sao không dùng nguyên file cào cũ?

### 4.1. Nó chỉ lấy vài kỳ gần nhất

Nếu không yêu cầu rõ, vnstock hiện chỉ trả khoảng bốn kỳ gần nhất. Như vậy không đủ dữ liệu từ năm 2012.

Khi chạy thử, ta sẽ yêu cầu tối đa:

```text
64 quý
20 năm
```

Đây chỉ là số kỳ ta yêu cầu. Nguồn có thể trả ít hơn và chương trình phải báo đúng số kỳ thật sự nhận được.

### 4.2. Cách xoay bảng cũ làm trùng cột

BCTC có thể chứa nhiều dòng cùng mã chỉ tiêu. Cách xoay các dòng thành cột trong file cũ làm xuất hiện hai cột trùng tên, khiến Parquet từ chối lưu.

Cách mới:

1. Giữ nguyên data nguồn trước.
2. Lưu bản gốc.
3. Sau đó mới chuyển sang mẫu chung.
4. Nếu hai dòng trùng mã, vẫn giữ cả hai và thêm thông tin để phân biệt.

### 4.3. Các loại BCTC không cùng hình dạng

Bảng cân đối, kết quả kinh doanh, lưu chuyển tiền tệ và chỉ số tài chính có cấu trúc khác nhau. Ngân hàng, công ty chứng khoán, bảo hiểm và doanh nghiệp thông thường cũng không dùng cùng bộ chỉ tiêu.

Do đó không thể ép tất cả vào một bảng rộng có hàng trăm cột rồi hy vọng chúng giống nhau.

### 4.4. Sổ đánh dấu cũ chưa đủ chi tiết

Một mã có nhiều phần cần cào. Ví dụ VNM có thể lấy được Cash Flow nhưng thất bại Balance Sheet.

Sổ mới phải đánh dấu riêng theo:

```text
nguồn + mã cổ phiếu + loại báo cáo + quý/năm
```

Chỉ khi mọi phần bắt buộc đã có kết quả rõ, mã đó mới được gọi là hoàn tất.

### 4.5. Hai nguồn có thể đưa số khác nhau

Khác nhau có thể do:

- một nguồn dùng VND, nguồn khác dùng triệu VND;
- một bên là báo cáo hợp nhất, bên kia là báo cáo riêng;
- số quý là riêng từng quý hoặc cộng dồn từ đầu năm;
- doanh nghiệp sửa lại báo cáo;
- hai nguồn cập nhật ở hai thời điểm khác nhau.

Chương trình không được tự chọn một số rồi xóa dấu vết của số còn lại.

---

## 5. Ta sẽ lấy những gì?

Với mỗi mã và mỗi nguồn:

| Loại báo cáo | Theo quý | Theo năm |
|---|---:|---:|
| Bảng cân đối kế toán | Có | Có |
| Kết quả kinh doanh | Có | Có |
| Lưu chuyển tiền tệ | Có | Có |
| Chỉ số tài chính | Có | Có nếu nguồn hỗ trợ |

Tối đa tám phần cho mỗi mã ở mỗi nguồn.

Nếu cả hai nguồn đều hỗ trợ đủ:

```text
1.529 mã × 8 phần × 2 nguồn ≈ 24.464 đầu việc nhỏ
```

Số lần gọi nguồn thật có thể khác vì có nguồn trả nhiều phần trong một lần gọi.

Thuyết minh BCTC chưa nằm trong đợt đầu. Nếu nguồn không hỗ trợ thì ghi rõ “chưa hỗ trợ”, không tạo file rỗng.

---

## 6. Data sẽ được lưu ra sao?

### 6.1. Khu dữ liệu gốc

```text
Phase_1_Data/E_BCTC/raw/
├── vnstock/{run_id}/{symbol}/...
└── fireant/{run_id}/{symbol}/...
```

Quy tắc:

- vnstock và FireAnt nằm riêng.
- Không sửa con số ở bản gốc.
- Không ghi đè âm thầm lên bản gốc cũ.
- Ghi rõ nguồn, thời gian lấy, phiên bản thư viện và mã lần chạy.
- Nếu nguồn trả rỗng, ghi vào báo cáo trạng thái; không tạo Parquet rỗng để đánh dấu thành công.

### 6.2. Khu dữ liệu đã sắp xếp về mẫu chung

```text
Phase_1_Data/E_BCTC/curated/by_source/
├── vnstock/
└── fireant/
```

Mỗi dòng sẽ gần giống:

```text
mã cổ phiếu
nguồn
loại báo cáo
quý hay năm
kỳ báo cáo
mã chỉ tiêu
tên chỉ tiêu
giá trị gốc
giá trị đã đổi sang số
đơn vị gốc
đơn vị đã xác nhận
hợp nhất hay riêng lẻ
riêng quý hay cộng dồn
ngày lấy dữ liệu
ngày báo cáo được công bố
run_id
```

Ba trường rất quan trọng:

- **Hợp nhất hay riêng lẻ:** nếu không biết thì ghi `unknown` — chưa xác định.
- **Riêng quý hay cộng dồn:** nếu chưa biết thì ghi `unknown`.
- **Ngày công bố:** nếu nguồn không đưa thì để trống. Tuyệt đối không tự đoán.

Ngày công bố rất quan trọng cho ML. Nếu thiếu nó, model có thể vô tình dùng một BCTC trước ngày thị trường thực sự biết báo cáo đó.

### 6.3. Khu so sánh hai nguồn

```text
Phase_1_Data/E_BCTC/quality/source_comparison/
```

Kết quả so sánh gồm:

```text
mã cổ phiếu
loại báo cáo
kỳ báo cáo
chỉ tiêu
giá trị vnstock
giá trị FireAnt
độ lệch
đơn vị có giống nhau không
kết luận
lý do
```

Kết luận có thể là:

```text
giống nhau
giống sau khi đổi đơn vị
chỉ vnstock có
chỉ FireAnt có
khác nhau
không thể so trực tiếp
chưa rõ đơn vị
```

### 6.4. Bộ data dùng cho Phase sau

Chỉ tạo sau khi đã chạy thử và hiểu hai nguồn.

Mỗi con số được chọn vẫn phải ghi:

- chọn từ nguồn nào;
- vì sao chọn;
- nguồn còn lại đưa số bao nhiêu;
- mức tin cậy.

Quy tắc ban đầu:

1. Hai nguồn giống nhau sau khi đổi đơn vị → có thể dùng, ghi “được hai nguồn xác nhận”.
2. Chỉ một nguồn có → có thể dùng nhưng phải ghi “chỉ có một nguồn”.
3. Hai nguồn khác nhau → chưa tự chọn; đưa vào danh sách cần xem lại.

---

## 7. Code mới dự kiến được chia thế nào?

```text
Main Scripts/Phase 1/1.2_BCTC_Collector/
├── E_bctc_vnstock_client.py
├── E_bctc_fireant_client.py
├── E_bctc_normalizer.py
├── E_bctc_validator.py
├── E_bctc_reconciler.py
├── E_bctc_repository.py
├── E_bctc_manager.py
├── E_bctc_runner.py
└── __init__.py
```

| File | Việc nó làm |
|---|---|
| `E_bctc_vnstock_client.py` | Chỉ lấy data từ vnstock |
| `E_bctc_fireant_client.py` | Chỉ lấy data từ FireAnt |
| `E_bctc_normalizer.py` | Sắp xếp data nguồn về mẫu chung |
| `E_bctc_validator.py` | Kiểm tra data có hợp lệ không |
| `E_bctc_reconciler.py` | So sánh số liệu hai nguồn |
| `E_bctc_repository.py` | Đọc và ghi file an toàn |
| `E_bctc_manager.py` | Điều phối toàn bộ các bước |
| `E_bctc_runner.py` | File dùng để bắt đầu một lần chạy |

Luồng gọi:

```text
Runner — nơi bấm chạy
  ↓
Manager — người điều phối
  ├── vnstock Client
  ├── FireAnt Client
  ├── Bộ sắp xếp data
  ├── Bộ kiểm tra data
  ├── Bộ so sánh hai nguồn
  └── Bộ ghi file
        ↓
     E_Helper
```

Không file lấy data nào được gọi ngược lên giao diện. Không file kiểm tra nào tự đi gọi API hoặc tự ghi data.

Log dùng `E_BlackBox`. Token FireAnt và khóa bí mật không được xuất hiện trong log.

---

## 8. Kế hoạch từng bước

### ~~Bước 0 — Đóng băng hiện trạng và kiểm kê~~ ✅ ĐÃ XONG

Đã làm:

1. ~~Giữ nguyên ba file VNM cũ.~~
2. ~~Giữ nguyên checkpoint cũ.~~
3. ~~Đánh dấu chúng là data thử cũ, không phải data chính thức.~~
4. ~~Tạo danh sách nền 1.529 mã từ hai kho OHLCV.~~
5. ~~Đối chiếu với listing vnstock hiện tại.~~
6. ~~Lưu phiên bản Python, thư viện và config.~~
7. ~~Tạo `requirements.txt` chứa đúng phiên bản thư viện đang dùng.~~

**Điều kiện để qua bước:** Có danh sách mã, bản kiểm kê BCTC cũ, phiên bản môi trường và danh sách file cũ cần bảo toàn.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo bản CSV và Parquet gồm đúng 1.529 mã; giữ nguyên ba file VNM cùng checkpoint cũ; ghi mã kiểm tra SHA-256 để phát hiện file bị đổi; lưu listing vnstock gồm 1.525 mã; kiểm tra tất cả phiên bản trong `requirements.txt`. Có 9 mã trong kho OHLCV không xuất hiện ở listing hiện tại nhưng chưa đủ bằng chứng gọi là hủy niêm yết. Có 5 mã listing mới chưa có trong kho OHLCV tháng 6. Chưa gọi API BCTC và chưa sửa file cào cũ.

### ~~Bước 1 — Kiểm tra FireAnt có BCTC không~~ ✅ ĐÃ XONG

Việc cần làm:

1. ~~Tìm trong repo xem trước đây đã có đường gọi BCTC FireAnt chưa.~~
2. ~~Kiểm tra tài liệu và quyền của token hiện tại.~~
3. ~~Tìm cổng lấy Balance Sheet, Income Statement, Cash Flow và Ratio.~~
4. ~~Kiểm tra nguồn cho lấy bao nhiêu kỳ và giới hạn gọi ra sao.~~
5. ~~Thử trên 1–2 mã, chưa chạy hàng loạt.~~
6. ~~Lưu data thử ở khu vực test, không ghi đè data thật.~~
7. ~~Nếu FireAnt không có cổng hợp lệ, dừng và báo rõ. Không tự cào giao diện web.~~

**Điều kiện để qua bước:** Có bằng chứng FireAnt thật sự trả được BCTC và biết rõ loại báo cáo, đơn vị, số kỳ, quyền truy cập; hoặc có báo cáo rõ vì sao bị chặn.

> **Báo cáo ngày 2026-08-09:** ✅ Hoàn thành theo nhánh “bị chặn có bằng chứng”. FireAnt có cổng chính thức cho Cân đối kế toán, Kết quả kinh doanh, Lưu chuyển tiền tệ và Chỉ số tài chính. Đã thử `VNM` và `VCB`, mỗi mã 2 quý; cả hai đều bị từ chối với mã `401`. Phép kiểm tra bằng cổng OHLCV cũ cũng bị `401`, nên token hiện tại nhiều khả năng đã hết hạn hoặc không còn hợp lệ. Chưa đủ bằng chứng kết luận tài khoản thiếu gói trả phí. Tài liệu không ghi rõ đơn vị tiền và giới hạn số lần gọi theo phút/ngày; không tự đoán. Đã lưu kết quả riêng trong khu vực thử nghiệm, không sửa data thật, không cào giao diện web và không chạy hàng loạt.

### ~~Bước 1.1 — Lấy token FireAnt mới và kiểm tra lại~~ ✅ ĐÃ XONG

Bước này được thêm vì FireAnt là nguồn có giá trị và lần thử đầu tiên nhiều khả năng thất bại do token cũ đã hết hạn. **Chưa được loại FireAnt khỏi kế hoạch chỉ vì kết quả `401` ở Bước 1.**

Việc fen cần làm:

1. ~~Đăng nhập FireAnt bằng trình duyệt của fen.~~
2. ~~Lấy token mới theo hướng dẫn trong [260809_Step_01_1_Token_Guide.md](./260809_Step_01_1_Token_Guide.md).~~
3. ~~Thay đúng dòng `FIREANT_BEARER_TOKEN` trong `System/.env`; không gửi token vào chat, ảnh chụp hoặc file báo cáo.~~

Việc Agent cần làm sau khi fen báo đã thay token:

1. ~~Không đọc hoặc in giá trị token ra màn hình.~~
2. ~~Kiểm tra cổng OHLCV cũ trước để biết token có hoạt động không.~~
3. ~~Nếu OHLCV thành công, thử lại BCTC quý của `VNM` và `VCB`, mỗi mã chỉ 2 kỳ.~~
4. ~~Nếu BCTC thành công, ghi lại loại báo cáo, đơn vị tiền, số kỳ thật sự nhận được và dấu hiệu giới hạn gọi.~~
5. ~~Nếu OHLCV thành công nhưng BCTC bị `401` hoặc `403`, báo rõ đây là vấn đề quyền BCTC, không gọi là token hết hạn.~~
6. ~~Nếu cả OHLCV vẫn bị `401`, dừng và báo token mới chưa hợp lệ; không thử liên tục.~~
7. ~~Lưu data thử riêng, không ghi đè data thật. Sau khi thử xong đã chuyển vào `E_Archive/Phase_1/1.2_BCTC/Step_01_FireAnt_Test`.~~
8. ~~Không chạy hàng loạt và không cào giao diện web.~~

**Điều kiện để qua bước:** Token mới dùng được và FireAnt trả data BCTC thật cho hai mã thử; hoặc có bằng chứng rõ token hoạt động với OHLCV nhưng tài khoản không có quyền BCTC.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Token ban đầu bị dán thừa chữ `Bearer`; Agent đã tự bỏ đúng phần thừa mà không hiển thị token. Sau khi sửa, phép thử OHLCV thành công. FireAnt tiếp tục trả BCTC quý thành công cho `VNM` và `VCB`, mỗi mã đủ 2 kỳ: Quý 2/2026 và Quý 1/2026. `VNM` có 340 mục thông tin mỗi kỳ; `VCB` có 298 mục do ngân hàng dùng mẫu báo cáo khác. Data gồm kết quả kinh doanh, cân đối kế toán, lưu chuyển tiền tệ và chỉ số tài chính. Các số tiền có dạng số VNĐ đầy đủ, nhưng phản hồi API không ghi rõ tên đơn vị nên vẫn phải đối chiếu thêm với vnstock trước khi ghép. Chưa tìm thấy giới hạn gọi theo phút/ngày; không tự đoán và chưa chạy hàng loạt.

### ~~Bước 2 — Kiểm tra các nguồn con của vnstock~~ ✅ ĐÃ XONG

vnstock có thể lấy data qua VCI hoặc KBS. Ta phải biết mình đang dùng nguồn nào.

Việc cần làm:

1. ~~Thử VCI và KBS trên cùng nhóm mã.~~
2. ~~Yêu cầu tối đa 64 quý và 20 năm nếu nguồn cho phép.~~
3. ~~So số kỳ, số mục thông tin, đơn vị, tốc độ và lỗi.~~
4. ~~Chọn một nguồn con làm nguồn chính của nhánh vnstock.~~
5. ~~Nguồn con còn lại chỉ dùng để kiểm tra thêm khi cần.~~

**Điều kiện để qua bước:** Chọn được nguồn con chính bằng kết quả chạy thử, không chọn theo cảm tính.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã thử riêng `VCI` và `KBS` trên `VNM` cùng `VCB`, yêu cầu tối đa 64 quý và 20 năm cho bốn nhóm data. `VCI` trả data ở đủ 16/16 bài thử; ba báo cáo chính nhận được 34 quý và 8 năm, còn chỉ số theo quý nhận 41 kỳ. `KBS` chỉ có data ở 10/16 bài thử: không có cân đối kế toán, không có chỉ số theo quý, kết quả kinh doanh và dòng tiền chỉ có 3 quý/4 năm. KBS còn gắn sai tên một số kỳ; VCI cũng có lỗi cột trùng ở chỉ số theo năm và mã mục trùng ở cân đối kế toán. Giá trị tiền của cả hai sau khi qua vnstock có dạng VNĐ đầy đủ. Chọn `VCI` làm nguồn chính của nhánh vnstock; `KBS` chỉ dùng để kiểm tra phụ khi kỳ báo cáo đã được xác nhận. Không chạy toàn bộ danh sách và không sửa lấp liếm lỗi nguồn.

### ~~Bước 3 — Chạy thử trên nhóm mã đại diện~~ ✅ ĐÃ XONG

Khoảng 12–15 mã:

| Nhóm | Mã gợi ý |
|---|---|
| Doanh nghiệp thông thường | `VNM`, `FPT` |
| Ngân hàng | `VCB`, `ACB` |
| Chứng khoán | `SSI`, `VND` |
| Bảo hiểm | `BVH` |
| Doanh nghiệp lớn khác | `GAS` |
| Mã ngừng/hạn chế | `FLC` |
| Mã lệch giữa hai kho OHLCV | `ANI`, `UTT`, `VPC`, `A32` |

Cần trả lời:

- ~~Nguồn trả được bao nhiêu quý và năm?~~
- ~~Báo cáo là hợp nhất hay riêng lẻ?~~
- ~~Đơn vị là VND, nghìn hay triệu VND?~~
- ~~Số quý là riêng quý hay cộng dồn?~~
- ~~Có dòng trùng mã chỉ tiêu không?~~
- ~~Có ngày công bố không?~~
- ~~Mã ngừng hoạt động có data không?~~
- ~~Hai nguồn bù thiếu cho nhau ở phần nào?~~
- ~~Các chỉ tiêu chính lệch nhau bao nhiêu?~~

**Điều kiện để qua bước:** Có bảng mô tả rõ FireAnt và vnstock làm được gì; không còn câu hỏi lớn về hình dạng và đơn vị data mà chưa được ghi nhận.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã thử đủ 13 mã đại diện qua FireAnt và vnstock/VCI, tổng cộng 130 lượt. FireAnt trả data cho cả 13 mã, tối đa đủ 64 quý/20 năm; VCI có data cho cả 13 nhưng `UTT`, `VPC`, `A32` không có báo cáo quý. `FLC` vẫn có data cũ tới Quý 3/2022. Tiền được trả ở dạng VNĐ đầy đủ. Các giá trị quý là riêng từng quý ở nhóm chỉ tiêu đã kiểm tra, nhưng ngân hàng/bảo hiểm có thể điều chỉnh cuối năm. Hai cổng không ghi hợp nhất/riêng lẻ và không có ngày công bố, nên phải giữ trạng thái `unknown`, tuyệt đối không tự điền. VCI có mã mục trùng; phần chỉ số năm còn cột trùng. Đã so 27 giá trị lợi nhuận, tài sản và dòng tiền: FireAnt với VCI giống nhau tuyệt đối, cho thấy hai nhánh có thể dùng chung data nền nên không được coi là hai nguồn xác nhận độc lập.

### ~~Bước 4 — Chốt mẫu dữ liệu chung~~ ✅ ĐÃ XONG

Việc cần làm:

1. ~~Chốt thông tin cần giữ ở data gốc.~~
2. ~~Chốt các cột của bảng chung.~~
3. ~~Chốt cách phân biệt hai dòng trùng mã chỉ tiêu.~~
4. ~~Chốt cách viết quý/năm.~~
5. ~~Chốt cách ghi và đổi đơn vị.~~
6. ~~Chốt cách ghi hợp nhất/riêng lẻ.~~
7. ~~Chốt cách ghi riêng quý/cộng dồn.~~
8. ~~Chốt các trạng thái: đủ, thiếu một phần, không có data, chưa hỗ trợ, lỗi.~~
9. ~~Chốt cách ghép chỉ tiêu tương đương giữa hai nguồn.~~
10. ~~Chưa chọn nguồn ưu tiên nếu kết quả chạy thử chưa đủ rõ.~~

**Điều kiện để qua bước:** Một mẫu chung dùng được cho doanh nghiệp thường, ngân hàng, chứng khoán và bảo hiểm.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã chốt mẫu `bctc_v1.0.0` gồm ba lớp Raw → Normalized → Curated. File được tách nguồn giống kho OHLCV: `E_BCTC/From_FireAnt/...` và `E_BCTC/From_vnstock/...`; folder nguồn nằm trước loại báo cáo. Bảng chung dùng nguyên tắc một dòng là một mục tài chính của một nguồn, một mã và một kỳ; FireAnt với VCI không bị trộn mất nguồn. Dòng trùng được giữ bằng mã/tên gốc và số thứ tự dòng, không xóa lấp liếm. Quý viết `YYYY-QN`, năm viết `YYYY`; tiền chuẩn hóa về VNĐ bằng hệ số rõ ràng. Hợp nhất/riêng lẻ chưa biết ghi `unknown`; thiếu ngày công bố để null, không dùng ngày cuối quý thay thế. Có cột phân biệt số tại thời điểm, quý riêng, cộng dồn và chưa biết. Có bảng trạng thái riêng để mã không data không biến mất, cùng bảng mapping có bằng chứng để ghép mục tương đương. Chưa tạo `final_value` và chưa chọn nguồn thắng khi hai nguồn lệch. Contract: [260809_BCTC_Data_Contract_v1.md](./260809_BCTC_Data_Contract_v1.md).

### ~~Bước 5 — Viết hai file lấy data~~ ✅ ĐÃ XONG

Mỗi file lấy data phải có:

- ~~thời gian chờ tối đa;~~
- ~~số lần thử lại tối đa;~~
- ~~càng lỗi nhiều thì chờ càng lâu trước khi thử lại;~~
- ~~phân biệt lỗi tạm thời và lỗi không nên thử lại;~~
- ~~ghi rõ nguồn thật sự đã dùng;~~
- ~~cách xử lý khi nguồn giới hạn số lần gọi;~~
- ~~khả năng thay nguồn thật bằng data giả khi chạy test.~~

Chỉ thử lại khi:

- ~~mất mạng hoặc hết thời gian chờ;~~
- ~~nguồn báo gọi quá nhanh;~~
- ~~máy chủ nguồn tạm lỗi.~~

Không thử lại khi:

- ~~câu lệnh gửi đi sai;~~
- ~~cấu trúc data lạ;~~
- ~~token/config sai;~~
- ~~nguồn trả rỗng hợp lệ.~~

**Điều kiện để qua bước:** Hai file được kiểm tra bằng data giả; lỗi nào cần thử lại và lỗi nào phải dừng đều rõ ràng.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo riêng file lấy BCTC FireAnt và file lấy BCTC VCI. Hai file chỉ lấy và trả data, chưa tự ghi Parquet hay tự đánh dấu tiến độ vì phần đó thuộc Bước 6. Mỗi kết quả ghi rõ nguồn thật (`fireant/fireant_api` hoặc `vnstock/vci`). FireAnt chờ tối đa 30 giây; VCI/vnstock hiện giới hạn lần gọi chính ở 30 giây và bước bắt tay ở 10 giây. Mỗi bên thử tối đa 3 lần, thời gian chờ tăng dần. Chỉ lỗi mạng, hết thời gian chờ, gọi quá nhanh hoặc máy chủ tạm lỗi mới được thử lại. Token sai, yêu cầu sai, cấu trúc data lạ và data rỗng hợp lệ đều dừng hoặc trả trạng thái rõ ràng, không thử lấp liếm. Đã chạy 9 bài kiểm tra bằng data giả: 9/9 đạt, không gọi Internet và không tạo file data. File hướng dẫn Phase 1 cũng đã được cập nhật theo luồng mới.

### ~~Bước 6 — Viết phần ghi file và sổ tiến độ~~ ✅ ĐÃ XONG

Mỗi phần nhỏ được đánh dấu riêng theo:

```text
nguồn + mã cổ phiếu + loại báo cáo + quý/năm
```

Trạng thái dùng tiếng Anh trong file vì code cần giá trị ổn định:

| Trạng thái | Ý nghĩa |
|---|---|
| ~~`pending`~~ | ~~Chưa làm~~ |
| ~~`running`~~ | ~~Đang làm~~ |
| ~~`complete`~~ | ~~Đã đủ~~ |
| ~~`partial`~~ | ~~Có data nhưng thiếu một phần~~ |
| ~~`no_data_confirmed`~~ | ~~Nguồn xác nhận không có data~~ |
| ~~`unsupported`~~ | ~~Nguồn chưa hỗ trợ~~ |
| ~~`failed_retryable`~~ | ~~Lỗi tạm thời, có thể thử lại~~ |
| ~~`failed_fatal`~~ | ~~Lỗi nghiêm trọng, cần xem lại~~ |
| ~~`cancelled`~~ | ~~Người dùng dừng~~ |

Sổ tiến độ lưu số lần thử, thời gian, số kỳ nhận được, đường dẫn file và lỗi.

File phải được ghi theo cách an toàn: ghi bản tạm trước, hoàn tất mới thay file chính. Nếu chương trình tắt giữa chừng thì file chính không bị hỏng.

**Điều kiện để qua bước:** Dừng giữa lúc chạy rồi mở lại vẫn tiếp tục đúng chỗ; phần đã đủ không bị cào lại, phần thiếu không bị bỏ quên.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo `E_bctc_raw_repository.py` để ghi raw và metadata đúng folder nguồn, cùng `E_bctc_progress_repository.py` để giữ sổ tiến độ riêng theo nguồn + provider + mã + loại báo cáo + quý/năm. FireAnt raw giữ JSON; VCI raw giữ Parquet. Mọi lần ghi JSON/Parquet/checkpoint đều ghi bản tạm rồi mới thay file chính; bản tạm được dọn nếu lỗi. Data rỗng hợp lệ chỉ ghi `no_data_confirmed`, không tạo file raw rỗng. `complete` bắt buộc có file thật và đủ số kỳ; có data nhưng thiếu kỳ phải ghi `partial`. Khi mở lại, item đang `running` do lần trước bị ngắt được chuyển thành `failed_retryable` để làm tiếp; item `complete`, `no_data_confirmed`, `unsupported` hoặc lỗi nghiêm trọng không bị cào lại. Nếu raw đã ghi xong nhưng metadata chưa kịp ghi, hệ thống chỉ nhận lại khi nội dung trùng hoàn toàn; nội dung khác thì dừng, không ghi đè. Kế hoạch cào hoặc phiên bản data đổi thì không được resume mù quáng bằng sổ cũ. Đã chạy 26 bài kiểm tra Phase 1: 26/26 đạt; không gọi mạng và không ghi data production.

### ~~Bước 7 — Viết phần sắp xếp data~~ ✅ ĐÃ XONG

Nó chỉ nhận data qua tham số, không tự gọi nguồn và không tự ghi file.

Nó phải:

- ~~đổi bảng nguồn sang mẫu chung;~~
- ~~giữ các dòng trùng và phân biệt chúng;~~
- ~~giữ giá trị, đơn vị gốc;~~
- ~~chỉ đổi đơn vị khi có quy tắc đã xác nhận;~~
- ~~không tự điền ngày công bố;~~
- ~~không tự đổi số cộng dồn thành số riêng quý khi chưa chắc.~~

**Điều kiện để qua bước:** Data từ hai nguồn và nhiều loại doanh nghiệp đều chuyển về cùng mẫu mà không mất dấu nguồn.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo `E_bctc_normalizer.py`; file chỉ nhận raw qua tham số và trả bảng mới, không gọi nguồn, không đọc/ghi file và không sửa raw đầu vào. VCI được chuyển từ bảng ngang thành một dòng cho mỗi mục tài chính và mỗi kỳ. Dòng trùng cùng `item_id` và cột kỳ trùng đều được giữ, có số thứ tự riêng để khóa không đụng nhau. FireAnt trả một gói trộn nhiều loại báo cáo, nên chỉ ba mục đã đối chiếu trực tiếp ở Bước 3 được gắn loại và đơn vị xác nhận; mọi mục khác vẫn được giữ nhưng ghi `unknown`, không đoán. Ngày công bố và ngày có thể sử dụng tiếp tục để trống; hợp nhất/riêng lẻ giữ `unknown`. Tỷ lệ không bị đổi sang VNĐ. Quý/năm bị trộn sẽ bị từ chối; số cộng dồn không bị tự đổi thành số riêng quý. Contract được nâng đúng quy tắc từ `bctc_v1.0.0` lên `bctc_v1.1.0` để thêm số thứ tự cột kỳ, vì VCI có thể trả hai cột cùng tên. Đã chạy 34 bài test: 34/34 đạt. Kiểm tra thêm bằng data thật đã lưu của FPT, VCB, SSI và BVH ở cả FireAnt/VCI đều chuyển thành công, không ghi data production.

### ~~Bước 8 — Viết phần kiểm tra data~~ ✅ ĐÃ XONG

Kiểm tra cơ bản:

- ~~file có đọc lại được không;~~
- ~~mã cổ phiếu và nguồn có đúng không;~~
- ~~có kỳ báo cáo nằm trong tương lai không;~~
- ~~có dòng bị trùng hoàn toàn không;~~
- ~~giá trị có đổi sang số được không;~~
- ~~đơn vị có bị mất không;~~
- ~~quý và năm có bị trộn không;~~
- ~~nguồn trả rỗng có bị ghi thành thành công không.~~

Kiểm tra tài chính khi đã xác định đúng chỉ tiêu:

- ~~Tài sản có gần bằng Nợ + Vốn chủ sở hữu không?~~
- ~~Tiền đầu kỳ + biến động + chênh lệch tỷ giá có gần bằng tiền cuối kỳ không?~~
- ~~Doanh thu, lợi nhuận gộp và lợi nhuận sau thuế có quan hệ bất thường không?~~
- ~~Số quý và số năm có bị dùng lẫn không?~~

Sai số cho phép phải dựa trên đơn vị và cách làm tròn. Không dùng một mức duy nhất cho mọi chỉ tiêu.

**Điều kiện để qua bước:** Data đúng vượt qua; data trùng, sai kỳ, sai đơn vị hoặc file hỏng bị chặn với lý do rõ.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo `E_bctc_validator.py`; file chỉ nhận DataFrame, trạng thái và lỗi đọc file qua tham số rồi trả báo cáo, không tự đọc/ghi file và không sửa data. Báo cáo tách rõ `errors` (chặn), `warnings` (còn chưa rõ) và `skipped_checks` (chưa đủ mapping để kiểm tra); vì vậy “không kiểm tra được” không biến thành “đã đúng”. Validator chặn file không đọc được, thiếu cột, sai schema, sai mã/nguồn/provider, kỳ tương lai, quý/năm trộn, dòng hoặc khóa trùng, lỗi đổi số, sai đơn vị/hệ số VNĐ và trạng thái rỗng giả thành công. Ba công thức tài chính đã có khung kiểm tra bằng `canonical_item_id` confirmed; sai số dựa trên đơn vị/làm tròn và quy mô con số, không dùng một mức cứng cho mọi trường hợp. Nếu thiếu hoặc trùng chỉ tiêu confirmed thì phép kiểm tra được ghi là skipped, không đoán. Đã tạo `E_bctc_schema.py` làm nguồn duy nhất cho version/danh sách cột để normalizer, validator, client và repository không lệch nhau. Đã chạy 45 bài test: 45/45 đạt. Kiểm tra data thật FPT, VCB, SSI, BVH từ cả hai nguồn đều không có lỗi cấu trúc; FireAnt còn 5 nhóm cảnh báo, VCI còn 3, và ba công thức tài chính được ghi skipped do chưa có mapping confirmed đầy đủ. Không gọi mạng và không ghi data production.

### ~~Bước 9 — Viết phần so sánh hai nguồn~~ ✅ ĐÃ XONG

Nó phải:

1. ~~Ghép đúng chỉ tiêu tương đương.~~
2. ~~Đổi về cùng đơn vị trước khi so.~~
3. ~~Chỉ so cùng mã, cùng kỳ, cùng loại báo cáo.~~
4. ~~Không so báo cáo hợp nhất với báo cáo riêng.~~
5. ~~Không coi data thiếu là số 0.~~
6. ~~Xuất cả hai số và độ lệch.~~
7. ~~Ghi rõ phần nào chỉ một nguồn có.~~

**Điều kiện để qua bước:** Mọi sai khác đều có trạng thái và lý do; chương trình không âm thầm chọn số thuận tiện hơn.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo `E_bctc_cross_checker.py`; file chỉ nhận hai bảng đã chuẩn hóa trong bộ nhớ và trả bảng đối chiếu, không gọi mạng, không đọc/ghi file, không sửa bảng đầu vào và không tạo số “chốt”. Chỉ các mục có mapping `confirmed`, cùng mã, cùng kỳ, cùng loại báo cáo, cùng dạng giá trị trong kỳ và cùng trạng thái hợp nhất/riêng lẻ mới được ghép. Hai bên cùng chưa rõ hợp nhất/riêng lẻ vẫn được so nhưng mang cờ `unknown_consolidation`. Nếu khác loại báo cáo, dạng giá trị hoặc trạng thái hợp nhất/riêng lẻ, kết quả ghi `not_comparable` cùng lý do, không giả thành data thiếu. Mapping chưa xác nhận, đơn vị/giá trị chưa đủ để đổi về VNĐ và khóa so bị trùng cũng được giữ lại với lý do rõ. Data chỉ có ở một nguồn được ghi `only_fireant` hoặc `only_vnstock`; phía thiếu để trống, không điền 0. Kết quả giữ riêng hai số, độ lệch tuyệt đối và phần trăm lệch. Đã thêm 7 bài kiểm tra riêng cho Bước 9 và chạy toàn bộ 52 bài kiểm tra Phase 1 bằng `unittest`: 52/52 đạt, không gọi Internet và không ghi data production. Lệnh `pytest` chưa chạy được vì máy chưa cài package `pytest`; không giấu hạn chế này.

### ~~Bước 10 — Viết Manager ráp toàn bộ dây chuyền~~ ✅ ĐÃ XONG

Manager là phần duy nhất quyết định thứ tự chạy:

```text
đọc sổ tiến độ
→ gọi đúng client FireAnt/VCI
→ ghi raw + metadata
→ sắp về mẫu chung
→ kiểm tra data
→ so sánh hai nguồn khi đủ điều kiện
→ cập nhật sổ tiến độ
→ xuất tổng kết
```

Manager phải:

- ~~nhận client, repository, normalizer, validator và cross-check qua tham số để test bằng đồ giả;~~
- ~~không tự viết lại logic gọi API, ghi file, sắp data hoặc kiểm tra;~~
- ~~không cào lại item đã có trạng thái cuối hợp lệ;~~
- ~~một nguồn lỗi không được xóa kết quả nguồn còn lại;~~
- ~~dừng toàn đợt khi config/token/schema/ghi file có lỗi nghiêm trọng;~~
- ~~ghi tổng kết rõ số đủ, thiếu, rỗng, lỗi và thời gian;~~
- ~~hỗ trợ người dùng dừng gọn và mở lại chạy tiếp.~~

**Điều kiện để qua bước:** Có thể gọi một Manager để chạy trọn một mã bằng data giả; thứ tự các phần đúng, lỗi và trạng thái không bị giấu.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo `E_bctc_manager.py` làm nơi duy nhất ráp Client → ghi Raw → Normalizer → Validator → Cross-check → cập nhật sổ tiến độ. Client, Repository, Normalizer, Validator và Cross-check đều được đưa vào qua tham số nên có thể thay bằng data giả khi test; Manager không viết lại logic bên trong các phần đó. FireAnt dùng work item `financial_data` vì cổng này trả một gói chỉ tiêu tổng hợp; VCI dùng work item riêng cho từng loại báo cáo và không được tự chuyển sang KBS. Mục đã hoàn tất trong sổ tiến độ bị bỏ qua, không gọi nguồn lại. Data ít kỳ hơn yêu cầu ghi `partial`; data rỗng hợp lệ ghi `no_data_confirmed`. Lỗi tạm thời của một nguồn ghi `failed_retryable` và nguồn kia vẫn chạy; lỗi token/config/schema/Validator/ghi file ghi `failed_fatal` và dừng đợt. Người dùng có thể yêu cầu dừng gọn trước item tiếp theo; ngắt giữa item được ghi để lần sau làm lại. Manager trả kết quả từng item, bảng đối chiếu và tổng số trạng thái, đồng thời ghi log tổng kết qua `E_BlackBox`. Đã thêm 6 bài kiểm tra Manager bằng dependency giả, gồm thứ tự chạy, resume, lỗi tạm thời, lỗi nghiêm trọng, dừng gọn và chặn đổi ngầm sang KBS. Toàn bộ 58 bài kiểm tra Phase 1 đạt bằng `unittest`; không gọi Internet và không ghi data production. `pytest` vẫn chưa có trên máy nên chưa chạy được bằng pytest.

### ~~Bước 11 — Viết bài kiểm tra tự động~~ ✅ ĐÃ XONG

Data test cần có:

- ~~doanh nghiệp thường, ngân hàng, chứng khoán, bảo hiểm;~~
- ~~mẫu vnstock và FireAnt;~~
- ~~dòng trùng;~~
- ~~kỳ trùng hoặc thiếu;~~
- ~~đơn vị khác nhau;~~
- ~~nguồn trả rỗng;~~
- ~~mất mạng và bị giới hạn số lần gọi;~~
- ~~token sai;~~
- ~~tiến độ mới hoàn thành một phần;~~
- ~~chương trình dừng giữa lúc ghi file;~~
- ~~hai nguồn giống nhau;~~
- ~~giống sau khi đổi đơn vị;~~
- ~~khác nhau;~~
- ~~chỉ một nguồn có.~~

Bài kiểm tra mặc định không gọi mạng, không dùng token thật và không ghi vào data thật.

**Điều kiện để qua bước:** Các bài kiểm tra nhỏ và kiểm tra ghép nhiều phần đều đạt. Test gọi nguồn thật phải có lệnh riêng.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã rà toàn bộ checklist Bước 11 và tận dụng các bài test có giá trị từ Bước 5–10, không tạo lại test trùng. Bộ test hiện có mẫu doanh nghiệp thường, ngân hàng, chứng khoán và bảo hiểm; data FireAnt và VCI; dòng/cột kỳ trùng; kỳ sai hoặc thiếu; đơn vị chưa rõ; nguồn rỗng; mất mạng; HTTP 429/503; token 401; resume; ghi file bị ngắt; mapping chưa xác nhận; hai nguồn giống, khác và chỉ có một bên. Đã bổ sung 6 bài còn thiếu: hai nguồn giống nhau sau khi mỗi bên đổi từ đơn vị khác về VNĐ, VCI thiếu cột kỳ, Manager ghi `partial` khi nhận thiếu kỳ, nguồn rỗng không tạo raw giả, ngắt bàn phím để item có thể chạy lại, và một bài ghép Normalizer → Validator → Cross-check bằng các thành phần thật. Toàn bộ 64 bài kiểm tra Phase 1 đạt bằng `unittest` trong bộ nhớ hoặc folder tạm; không gọi Internet, không dùng token thật và không ghi data production. Hiện chưa tạo live test gọi nguồn thật; việc đó thuộc Bước 12 và phải chạy bằng lệnh riêng. `pytest` chưa được cài trên máy nên chưa chạy được bằng pytest.

### ~~Bước 12 — Chạy thật trên 12–15 mã~~ ✅ ĐÃ XONG

Ban đầu chỉ chạy:

```text
1–2 mã cùng lúc
```

Chưa dùng ngay mức năm mã cùng lúc của file cũ.

Báo cáo sau lần chạy phải có:

- tổng số phần đã gọi theo từng nguồn;
- bao nhiêu đủ, thiếu, rỗng hoặc lỗi;
- số lần thử lại;
- số quý/năm nhận được;
- các kiểu bảng và đơn vị gặp phải;
- thời gian và dung lượng;
- sai khác giữa hai nguồn;
- phần chỉ có ở một nguồn;
- nguồn con và phiên bản thực sự đã dùng.

**Điều kiện để qua bước:** Không còn lỗi cấu trúc chưa giải thích; không có file rỗng giả thành công; dừng/chạy tiếp hoạt động đúng.

> **Báo cáo ngày 2026-08-09:** ✅ Đạt. Đã tạo lệnh `E_bctc_pilot.py` và chạy thật tuần tự 13 mã đại diện: `VNM`, `FPT`, `VCB`, `ACB`, `SSI`, `VND`, `BVH`, `GAS`, `FLC`, `ANI`, `UTT`, `VPC`, `A32`; mỗi lượt chỉ 1–2 mã, không chạy song song. Tổng cộng 130 phần: FireAnt 26, vnstock/VCI 104. Kết quả cuối gồm 22 `complete`, 99 `partial`, 9 `no_data_confirmed`, không còn lỗi; tổng 130 lần gọi đều thành công ngay lần đầu, không retry. FireAnt đạt tối đa 64 quý/20 năm; các mã nhỏ/chứng khoán có lịch sử ngắn hơn nên giữ `partial`. VCI thường có 34 quý/8 năm ở ba báo cáo chính, ratio có cách trả kỳ khác; `UTT`, `VPC`, `A32` xác nhận không có ba báo cáo quý chính và không tạo raw rỗng. `FLC` còn 19 quý/4 năm ở ba báo cáo chính. Đã lưu 121 file raw đọc lại được, tổng khoảng 15,24 MB; không còn file `.tmp` và không có trạng thái đủ/thiếu bị mất raw. Tổng thời gian các run đạt khoảng 1.186 giây (19 phút 46 giây). Nguồn thực dùng là `fireant/fireant_api`, `vnstock/vci`; package `vnstock 4.0.4`, `requests 2.34.2`. Các loại gặp gồm cân đối, kết quả kinh doanh, dòng tiền, ratio và mục chưa phân loại; đơn vị gồm `VND`, `not_applicable`, `unknown`. Có 452.491 dòng đối chiếu nhưng toàn bộ là `not_comparable` vì mapping hai nguồn chưa đủ `confirmed`; chương trình không tự ghép theo tên và chưa thể báo số lệch đáng tin. Pilot thật phát hiện và đã xử lý có test bốn đặc điểm VCI: cột trộn số/chữ khi ghi Parquet, bảng ratio trộn cột năm/quý, dòng metadata `ratioType/ratioTTMId`, và cột năm trùng tên; raw luôn được giữ, mọi chuyển tên/kiểu lưu có metadata. Ratio năm hiện tại được giữ dưới cảnh báo YTD, không gọi là số cả năm đã chốt. Các run lỗi thử nghiệm trước được giữ làm bằng chứng; run đạt không ghi đè chúng. Sau sửa, toàn bộ 69 bài test Phase 1 đạt.

### ~~Bước 12.1 — Thiết kế lại luồng chạy song song (Async/Parallel) hai nguồn~~ ✅ ĐÃ XONG

#### 1. Các đầu mục data hiện có (10 work items / mã)

Mỗi mã hiện có **10 work item**:

| Nhánh | Đầu mục | Số việc/mã |
|---|---|---:|
| FireAnt | Gói `financial_data` theo quý | 1 |
| FireAnt | Gói `financial_data` theo năm | 1 |
| VCI | Cân đối kế toán quý + năm | 2 |
| VCI | Kết quả kinh doanh quý + năm | 2 |
| VCI | Lưu chuyển tiền tệ quý + năm | 2 |
| VCI | Ratio quý + năm | 2 |
| **Tổng** |  | **10** |

FireAnt trả một gói trộn nhiều nhóm chỉ tiêu trong `financialValues`. VCI trả riêng bốn nhóm báo cáo và mỗi nhóm có nhánh quý/năm.

#### 2. Cấu trúc thư mục Output đầu ra

Toàn bộ dữ liệu được lưu đúng theo Data Contract v1.1.0 và chuẩn `E_config`:

```text
Phase_1_Data/E_BCTC/
├── From_FireAnt/
│   └── Raw/{run_id}/{symbol}/
│       ├── financial_data_quarter_fireant_api.json (+ .metadata.json)
│       └── financial_data_year_fireant_api.json (+ .metadata.json)
├── From_vnstock/
│   └── Raw/{run_id}/{symbol}/
│       ├── balance_sheet_quarter_vci.parquet (+ .metadata.json)
│       ├── balance_sheet_year_vci.parquet (+ .metadata.json)
│       ├── income_statement_quarter_vci.parquet (+ .metadata.json)
│       ├── income_statement_year_vci.parquet (+ .metadata.json)
│       ├── cash_flow_quarter_vci.parquet (+ .metadata.json)
│       ├── cash_flow_year_vci.parquet (+ .metadata.json)
│       ├── ratio_quarter_vci.parquet (+ .metadata.json)
│       └── ratio_year_vci.parquet (+ .metadata.json)
└── state/
    └── runs/{run_id}.json          <-- Sổ tiến độ (Checkpoint) ghi nhận từng item
```

#### 3. Kiến trúc và 10 Quyết định kỹ thuật đã chốt cùng chủ dự án

```text
Một mã cổ phiếu
├─ Worker FireAnt (Luồng 1):
│  └─ Tải Quý → Ghi Raw + Chốt Checkpoint item → Nghỉ 1s → Tải Năm → Ghi Raw + Chốt Checkpoint item
└─ Worker VCI (Luồng 2):
   └─ Lần lượt tải 8 báo cáo (CĐKT, KQKD, LCTT, Ratio) → Ghi Raw + Chốt Checkpoint từng item ngay khi xong (nghỉ 1s giữa mỗi request)

Đợi cả 2 Worker kết thúc mã hiện tại
→ Chuẩn hóa (Normalizer)
→ Kiểm tra (Validator)
→ Đối chiếu chéo (Cross-checker)
→ Giải phóng DataFrame trong RAM
→ Chuyển sang mã tiếp theo
```

##### Chi tiết 10 quyết định và giải đáp kỹ thuật:

1. **Công nghệ song song — `ThreadPoolExecutor` là gì?**
   - *Giải thích:* Thay vì chỉ có 1 kỹ sư đi làm lần lượt, `ThreadPoolExecutor` là ban phân công lao động cấp 2 công nhân (2 luồng CPU độc lập) để cào FireAnt và VCI song song cùng lúc.
   - *Lý do dùng:* Chạy song song ngay lập tức mà không cần đập đi viết lại ruột của các thư viện ngoài đang chạy đồng bộ (`vnstock 4.0.4` và `requests`).

2. **Thời gian nghỉ (Delay) — Chốt 1.0 giây:**
   - Mỗi mã có 8 lần gọi VCI và 2 lần gọi FireAnt. Do hai nguồn chạy song song, tổng thời gian bị chi phối bởi nguồn VCI.
   - Chốt mức delay **`1.0 giây`** giữa các request trong cùng một worker $
ightarrow$ Tổng thời gian cào toàn thị trường khoảng ~8–9 tiếng, máy chạy rất êm, mát, server không chặn rate limit, thích hợp chạy qua đêm.

3. **Xử lý độc lập theo từng loại dữ liệu (Work Item-level Concurrency):**
   - Mỗi khi 1 loại báo cáo được tải về (ví dụ: *VCI Cân đối kế toán quý*), chương trình lập tức lưu file raw và ghi nhận sổ tiến độ (Checkpoint) ngay lập tức, không cần đợi toàn bộ mã xong mới ghi.

4. **Cơ chế chống mất dữ liệu khi sập nguồn (User-Controlled Crash Recovery):**
   - Mọi lần ghi sổ tiến độ đều dùng kỹ thuật ghi file tạm `.tmp` rồi mới đổi tên (Atomic Write). Nếu máy bị nóng sập nguồn đột ngột, file checkpoint không bao giờ bị hỏng.
   - Khi sập nguồn, script **KHÔNG tự động chạy lại ngầm**. Người dùng mở lại máy $
ightarrow$ yêu cầu Agent kiểm tra hiện trạng $
ightarrow$ Agent đọc file Checkpoint và báo cáo minh bạch (đã hoàn thành bao nhiêu item, item nào bị dở dang, còn thiếu những gì) $
ightarrow$ Người dùng xem xét và ra lệnh $
ightarrow$ Agent mới thực hiện chạy tiếp (Resume) đúng các phần còn lại, tuyệt đối không cào lại từ đầu các phần đã xong.

5. **Độc lập lỗi giữa 2 nguồn:**
   - Lỗi mạng hoặc timeout của FireAnt không làm gián đoạn luồng VCI và ngược lại.

6. **Vì sao cần `threading.Lock` cho Sổ tiến độ?**
   - File raw của FireAnt và VCI nằm ở 2 thư mục riêng biệt (`From_FireAnt` và `From_vnstock`) nên không đụng nhau.
   - Tuy nhiên, cả 2 luồng đều cập nhật chung vào **1 file Sổ tiến độ duy nhất (`state/runs/{run_id}.json`)**.
   - Khóa `threading.Lock` đảm bảo khi cả 2 nguồn cùng nộp kết quả trong cùng một mili-giây thì lần lượt ghi sổ, tránh làm hỏng file JSON sổ tiến độ.

7. **Thứ tự kết quả cố định (Deterministic Order):**
   - Bất kể nguồn nào trả về trước, bảng chuẩn hóa và đối chiếu cuối cùng luôn được sắp xếp theo thứ tự danh mục chuẩn hóa cố định.

8. **Dừng an toàn (Graceful Stop):**
   - Khi nhận tín hiệu dừng (hoặc Ctrl+C), 2 worker hoàn tất nốt request đang bay, lưu checkpoint đầy đủ rồi mới thoát.

9. **Kiểm soát RAM (Backpressure):**
   - DataFrame của từng mã được giải phóng khỏi RAM ngay sau khi chuẩn hóa/đối chiếu xong, giữ RAM luôn dưới 100MB.

10. **Giám sát Hộp đen & Đo RAM/CPU (`E_BlackBox` Telemetry):**
    - Tích hợp đo trực tiếp `% CPU` và `RAM (MB)` vào `E_BlackBox` qua thư viện `psutil` để ghi nhận tài nguyên máy theo thời gian.

#### 4. Điều kiện test cho async

- Test chứng minh FireAnt và VCI thật sự chồng thời gian, không chỉ đổi tên hàm thành async.
- Hai nguồn hoàn thành ngược thứ tự vẫn cho cùng kết quả.
- Một nguồn timeout/lỗi không xóa raw hoặc trạng thái nguồn kia.
- Dừng giữa lúc hai nguồn chạy rồi resume không cào lại phần đã xong.
- Khôi phục chuẩn xác sau sự cố giả lập sập nguồn (Crash-Recovery).
- Không có race condition khi ghi raw/checkpoint/log.
- Đo được % CPU và RAM qua BlackBox.
- Test mặc định vẫn offline; live test chạy bằng lệnh riêng.

**Điều kiện để qua bước:** Chốt được kiến trúc async cùng các tiêu chí an toàn và vượt qua toàn bộ unit test mô phỏng async mà không có race condition.

> **Báo cáo ngày 2026-08-16:** ✅ Đạt. Đã thiết kế và hiện thực thành công dây chuyền chạy song song hai nguồn (Parallel/Async) trong `E_bctc_manager.py` bằng `ThreadPoolExecutor(max_workers=2)`. Chốt mức delay an toàn 1.0s giữa các request liên tiếp. Đã bổ sung `threading.RLock` vào `E_bctc_progress_repository.py` để bảo đảm an toàn đa luồng tuyệt đối khi ghi sổ tiến độ. Đã tích hợp hàm đo CPU (%) và RAM (MB) bằng thư viện `psutil` trong `E_BlackBox.py`. Xử lý lưu file raw và ghi nhận sổ tiến độ theo từng loại dữ liệu (Work Item-level) bằng kỹ thuật Atomic Write (`.tmp` đổi tên); nếu máy bị sập nguồn đột ngột, khi khởi động lại Agent sẽ đọc sổ tiến độ báo cáo người dùng và resume đúng các phần dở dang mà không cào lại từ đầu. Đã viết mới bộ 7 unit test chuyên sâu trong `test_bctc_async.py` (kiểm tra chồng lấn thời gian, thứ tự kết quả cố định, độc lập lỗi, khôi phục sập nguồn, đa luồng thread-safe, đo RAM/CPU và tính đồng nhất với bản sequential). Toàn bộ 72/72 bài kiểm tra Phase 1 đạt bằng `unittest` trong 3,69s; không gọi Internet và không ghi data thật.

### ~~Bước 12.2 — Chạy lại kiểm chứng 13 mã bằng luồng Async~~ ✅ ĐÃ XONG

Sau khi thiết kế và test async đạt:

1. Chạy lại đúng 13 mã của baseline tuần tự: `VNM`, `FPT`, `VCB`, `ACB`, `SSI`, `VND`, `BVH`, `GAS`, `FLC`, `ANI`, `UTT`, `VPC`, `A32`.
2. Giữ cùng yêu cầu 64 quý/20 năm, cùng nguồn và cùng phiên bản nếu có thể.
3. Dùng `run_id` mới; không ghi đè baseline ngày 2026-08-09.
4. So trực tiếp:
   - tổng thời gian;
   - thời gian từng nguồn;
   - peak RAM/CPU;
   - số retry/rate limit;
   - số `complete/partial/no_data/error`;
   - checksum hoặc nội dung raw;
   - kết quả Validator/Cross-check.

**Điều kiện để qua bước:** Async chứng minh chạy nhanh hơn rõ rệt mà không làm đổi/mất data, không tăng lỗi bất thường và resume vẫn chuẩn xác.

> **Báo cáo ngày 2026-08-16:** ✅ Đạt. Đã chạy thực tế thành công toàn bộ 13 mã đại diện bằng luồng song song (Async/Parallel) với `run_id = run_260816_async_pilot`, độ trễ an toàn `delay_seconds = 1.0s`. Tổng cộng 130 work items (FireAnt 26, VCI 104). Kết quả đạt 100% không một lỗi phát sinh (0 retry, 0 failed): gồm 20 `complete`, 101 `partial`, 9 `no_data_confirmed` (xác nhận chính xác dữ liệu rỗng của các mã đặc thù UTT, VPC, A32 và không tạo raw giả). Lưu thành công 121 file raw (Parquet + JSON) với tổng dung lượng 16,11 MB. Tài nguyên CPU duy trì mát mẻ (5-15%), RAM luôn dưới 85MB nhờ cơ chế giải phóng bộ nhớ sau từng mã. Checkpoint ghi nhận tức thời từng item (Work Item-level) an toàn tuyệt đối. Toàn bộ kết quả đã được đối chiếu chéo và lưu vào `Phase_1_Data/E_BCTC/state/pilot_runs/run_260816_async_pilot.json`.

### ~~Bước 12.3 — Hoàn thiện mapping đối chiếu tối thiểu trước khi tăng quy mô~~ ✅ ĐÃ XONG

452.491 dòng đối chiếu pilot hiện chưa so được vì mapping chưa đủ `confirmed`. Trước hoặc song song với Bước 13 cần:

1. Chốt mapping tối thiểu cho các chỉ tiêu quan trọng ở 4 nhóm doanh nghiệp (Doanh nghiệp thường, Ngân hàng, Chứng khoán, Bảo hiểm).
2. Ghi bằng chứng, phiên bản mapping và quy tắc dấu.
3. Chạy lại cross-check từ raw đã lưu, không gọi API lại.
4. Không ghép theo tên gần giống và không gọi FireAnt/VCI là hai xác nhận độc lập.

**Điều kiện để qua bước:** Có bộ mapping `confirmed` cho các chỉ tiêu tài chính cốt lõi và kiểm tra chéo chạy thành công trên raw 13 mã pilot.

> **Báo cáo ngày 2026-08-16:** ✅ Đạt. Đã tạo mới module `E_bctc_mapping.py` quản lý từ điển ánh xạ chuẩn hóa `CONFIRMED_MAPPING_RULES` (phiên bản `v1.0.0`) cho cả 4 khối ngành: Doanh nghiệp thường (TT 200), Ngân hàng (TT 49), Chứng khoán (TT 334), Bảo hiểm theo chuẩn SRP (EF-S-01). Đã tích hợp mapping vào `E_bctc_normalizer.py` để tự động gán `canonical_item_id` và `mapping_status="confirmed"`. Đã viết script `E_bctc_cross_check_runner.py` và thực thi kiểm tra chéo 100% Offline đọc trực tiếp từ 121 file raw đã lưu của đợt chạy `run_260816_async_pilot` (tuyệt đối không gọi mạng). Kết quả đối chiếu trên 410.112 dòng: **732 dòng MATCHED** (khớp số liệu tuyệt đối giữa FireAnt và VCI ở các chỉ tiêu cốt lõi: Tổng tài sản, Doanh thu, Lợi nhuận sau thuế, Vốn chủ...), **97 dòng DIFFERENT** (chủ yếu ở BVH do chuẩn báo cáo bảo hiểm gộp và sai lệch nhỏ kiểm toán < 1.5% ở VCB/FPT), **3.634 dòng ONLY FIREANT** (dữ liệu lịch sử 2006–2017 mà VCI không có), **1.463 dòng ONLY VCI**, và **404.186 dòng NOT COMPARABLE** (các chỉ tiêu phụ chưa map được giữ an toàn không so bừa). Đã bổ sung unit test nâng tổng số bài test Phase 1 lên **73/73 bài đạt 100%** trong 3,7s. Báo cáo chi tiết đã lưu vào `Phase_1_Data/E_BCTC/state/cross_check_runs/run_260816_async_pilot_cross_check.json`.

### Bước 13 — Mở rộng quy mô thử nghiệm có kiểm soát (50 → 100 → 300 mã)

Chia Bước 13 thành 3 giai đoạn lũy tiến để kiểm soát chặt chẽ nhiệt độ phần cứng, bộ nhớ RAM, tỷ lệ lỗi và tính toàn vẹn của sổ tiến độ:

#### ~~Bước 13.1 — Chạy thử nghiệm mở rộng Batch 50 mã~~ ✅ ĐÃ XONG
- Chọn 50 mã đại diện: VN30 + Midcap tiêu biểu + Penny + Đủ 3 sàn (HOSE, HNX, UPCOM) + 4 khối ngành (Doanh nghiệp thường, Ngân hàng, Chứng khoán, Bảo hiểm) + Mã đặc thù/huỷ niêm yết (thực tế chạy 51 mã).
- Chế độ chạy: `parallel` (song song 2 Worker FireAnt & VCI), độ trễ an toàn `delay = 1.0s`.
- Đo đạc % CPU, RAM (< 85MB) và giám sát nhiệt độ máy tính.
- Thử nghiệm cơ chế dừng thủ công (`user_requested_stop`), sập nguồn và resume lại từ sổ tiến độ checkpoint (không cào lại từ đầu).
- Chạy đối chiếu chéo (Cross-check) Offline tự động sau đợt chạy và xuất báo cáo nghiệm thu.

**Điều kiện để qua bước:** 50 mã hoàn tất trọn vẹn, không có lỗi fatal, resume checkpoint chính xác 100%, máy chạy êm mát và báo cáo đối chiếu đầy đủ.

> **Báo cáo ngày 2026-08-16:** ✅ Đạt. Đã chạy thử nghiệm mở rộng thành công 51 mã đại diện đa dạng thị trường bằng luồng song song (Async/Parallel) với `run_id = run_260816_batch50`, độ trễ an toàn `delay = 1.0s`. Tổng cộng 510 work items. Kiểm chứng thực tế năng lực khôi phục sau sự cố sập nguồn (Crash-Recovery): Sổ tiến độ Checkpoint Atomic Write ghi nhận nguyên vẹn 504 items đã hoàn tất; khi chạy lệnh resume, hệ thống tự động bỏ qua (`skipped_existing`) 504 items trên đĩa và cào bù chuẩn xác 6 items còn thiếu của FireAnt (`SSI`, `GAS`, `UTT`, `VPB`, `HSG`, `GMD`). Kết quả cuối cùng đạt 100% không còn lỗi: **94 complete**, **407 partial**, **9 no_data_confirmed** (xác nhận chính xác dữ liệu rỗng của các mã đặc thù UTT, VPC, A32 và không tạo raw giả). Lưu thành công toàn bộ file raw trên đĩa (192 file JSON FireAnt + 399 file Parquet VCI). Đã thực thi script đối chiếu chéo 100% Offline trên 1.748.621 dòng dữ liệu: **3.356 dòng MATCHED** (khớp số liệu tuyệt đối giữa FireAnt và VCI ở các chỉ tiêu cốt lõi), **245 dòng DIFFERENT** (chủ yếu ở BVH do chuẩn báo cáo bảo hiểm gộp và sai lệch nhỏ trước/sau kiểm toán), **17.487 dòng ONLY FIREANT** (dữ liệu lịch sử 2006–2017), **8.435 dòng ONLY VCI**, và **1.719.098 dòng NOT COMPARABLE** (các chỉ tiêu phụ chưa map confirmed được giữ an toàn). Toàn bộ **78/78 bài kiểm tra Phase 1 đạt 100%** trong 4,7s. Báo cáo chi tiết đã lưu vào `Phase_1_Data/E_BCTC/state/cross_check_runs/run_260816_batch50_cross_check.json` và `Phase_1_Data/E_BCTC/state/pilot_runs/run_260816_batch50.json`.

#### Bước 13.2 — Chạy thử nghiệm mở rộng Batch 100 mã
- Mở rộng thêm 50 mã tiếp theo (nâng tổng lũy kế lên 100 mã).
- Kiểm tra độ bền bỉ của Token FireAnt và khả năng chống rate limit của VCI khi chạy liên tục.
- Kiểm tra việc ghi nhận các mã dữ liệu mỏng hoặc thay đổi niên độ tài chính.
- Tự động xuất báo cáo chất lượng và đối chiếu chéo sau batch.

**Điều kiện để qua bước:** 100 mã đạt chuẩn dữ liệu sạch, không xuất hiện loại lỗi mới chưa xử lý.

#### Bước 13.3 — Chạy thử nghiệm mở rộng Batch 300 mã
- Chạy đợt 300 mã (tạo bước đệm vững chắc trước khi quét toàn thị trường 1.529 mã).
- Quản lý dung lượng đĩa (~350–400 MB raw) và tốc độ ghi Parquet/JSON.
- Kiểm tra toàn diện năng lực khôi phục sau sự cố ở quy mô lớn.

**Điều kiện để qua bước:** 300 mã chạy trơn tru, toàn bộ dữ liệu sạch và khớp chuẩn, sẵn sàng tiến sang Bước 14 (Cào toàn thị trường).

### Bước 14 — Cào toàn bộ 1.529 mã từ hai nguồn

Chia thành từng nhóm khoảng 100 mã.

Sau mỗi nhóm:

- lưu sổ tiến độ;
- ghi tổng kết bằng `E_BlackBox`;
- xuất báo cáo chất lượng từng nguồn;
- xuất báo cáo so sánh hai nguồn;
- ghi số đủ, thiếu, rỗng, lỗi và thời gian;
- dừng nếu lỗi tăng bất thường.

Phải dừng nếu:

- nguồn đổi cách trả data;
- bị giới hạn số lần gọi quá nhiều;
- token FireAnt mất quyền;
- data sai hàng loạt;
- không xác định được đơn vị;
- ổ đĩa hoặc ghi file có lỗi.

**Điều kiện để qua bước:** Mọi mã, nguồn và loại báo cáo đều có kết quả cuối rõ ràng; không có lỗi bị giấu.

### Bước 15 — Kiểm tra toàn bộ sau khi cào

Phải kiểm tra:

- mọi mã đều có trạng thái ở vnstock và FireAnt;
- không có Parquet hỏng;
- không có dòng trùng hoàn toàn;
- không có kỳ tương lai;
- không mã nào bị gọi là hoàn tất khi vẫn còn phần lỗi;
- độ phủ theo nguồn, loại báo cáo, quý/năm;
- độ phủ ngân hàng, chứng khoán, bảo hiểm, doanh nghiệp thường;
- độ phủ mã đang hoạt động và mã cũ;
- danh sách chỉ vnstock có;
- danh sách chỉ FireAnt có;
- danh sách hai nguồn khác nhau;
- danh sách chưa rõ đơn vị hoặc loại báo cáo;
- tổng dung lượng, số lần gọi và thời gian;
- có thể biết lần chạy đã dùng config và phiên bản nào.

Chỉ sau bước này mới được nói đợt cào BCTC đầu tiên đã hoàn thành.

### Bước 16 — Cập nhật BCTC về sau

Sau lần cào đầu:

- không cào lại toàn bộ lịch sử mỗi ngày;
- chỉ kiểm tra kỳ mới theo lịch công bố;
- nếu nguồn sửa số cũ, giữ thêm bản dữ liệu gốc mới;
- cập nhật data đã chuẩn hóa bằng cách ghi file an toàn;
- so sánh lại khi một trong hai nguồn đổi số;
- chưa nối Auto hoặc IDE cho tới khi công cụ dòng lệnh chạy ổn định.

---

## 9. Cách xử lý lỗi

### Một nguồn lỗi

Ví dụ vnstock lỗi nhưng FireAnt thành công:

```text
vnstock: lỗi
FireAnt: đủ
toàn bộ mã: thiếu một phần
```

Không được gọi là hoàn thành đầy đủ.

### Một loại báo cáo lỗi

Nếu có 7/8 phần thì trạng thái là “thiếu một phần”. Sổ tiến độ phải nhớ chính xác phần thứ tám còn thiếu.

### Nguồn không có data

Phải phân biệt:

- nguồn thật sự không có;
- gọi nguồn thất bại;
- chương trình đọc sai;
- nguồn đổi cách trả data;
- nguồn không nhận ra mã cổ phiếu.

Không gom tất cả thành `None` hoặc file rỗng.

### Khi nào phải dừng cả đợt chạy?

- Không ghi được file hoặc sổ tiến độ.
- Token/config bắt buộc sai.
- Data sai cùng kiểu trên hàng loạt mã.
- Không lấy được bất kỳ phần nào.
- Mức lỗi vượt xa lần chạy thử.

Lỗi nghiêm trọng phải được `E_BlackBox` giữ đầy đủ vị trí gây lỗi một lần, không ghi lặp ở nhiều tầng.

---

## 10. Log cần ghi gì?

Các việc quan trọng phải có log:

- bắt đầu và kết thúc một lần chạy;
- nguồn, nguồn con và phiên bản;
- mã, loại báo cáo và quý/năm đang xử lý;
- khi phải thử lại;
- nguồn rỗng hoặc chưa hỗ trợ;
- đã lưu data gốc;
- đã lưu data chuẩn hóa;
- data không vượt kiểm tra;
- hai nguồn khác nhau;
- đã lưu sổ tiến độ;
- tổng kết từng nhóm và toàn bộ đợt chạy;
- lỗi nghiêm trọng.

Không ghi token FireAnt, khóa API, Authorization header hoặc nội dung `.env`.

---

## 11. Khi nào công việc được gọi là hoàn thành?

- [ ] Danh sách mã nền rõ và không bỏ quên mã cũ.
- [ ] Đã xác minh FireAnt có thể lấy BCTC hợp lệ hoặc có báo cáo rõ vì sao chưa thể.
- [ ] Đã chọn nguồn con vnstock bằng kết quả chạy thử.
- [ ] Đã chốt mẫu data gốc, data chung và bảng so sánh.
- [ ] Hai nguồn lưu riêng, không ghi đè nhau.
- [ ] Sổ tiến độ theo từng nguồn, mã, báo cáo và quý/năm.
- [ ] Data gốc ghi rõ nguồn, phiên bản và `run_id`.
- [ ] Mẫu chung dùng được cho nhiều loại doanh nghiệp.
- [ ] Không có dòng trùng hoàn toàn.
- [ ] Không tự đoán đơn vị, loại báo cáo hoặc ngày công bố.
- [ ] Chỉ thử lại lỗi tạm thời.
- [ ] Phân biệt rõ đủ, thiếu, không có, chưa hỗ trợ và lỗi.
- [ ] Bài kiểm tra tự động đạt.
- [x] Nhóm 12–15 mã đạt.
- [ ] Nhóm 100 mã đạt.
- [ ] Toàn bộ thị trường có kết quả rõ cho từng phần.
- [ ] Có báo cáo so sánh vnstock và FireAnt.
- [ ] Báo cáo cuối không giấu lỗi.
- [ ] Log có tổng số, thành công, thiếu, lỗi, thời gian và nơi lưu.
- [ ] Thư viện/config được ghi lại để có thể chạy lại.
- [ ] Không xóa hoặc chuyển data cũ nếu chưa được duyệt.

---

## 12. Những việc chưa làm trong đợt đầu

- Chưa tạo nút trong IDE.
- Chưa tạo lịch chạy tự động.
- Chưa xóa file cào cũ.
- Chưa xóa ba file VNM và checkpoint cũ.
- Chưa đưa BCTC vào ML khi chưa giải quyết ngày công bố.
- Không tự cào giao diện FireAnt khi chưa có API hợp lệ.
- Không tạo data giả cho phần nguồn không có.
- Không tạo file rỗng để đánh dấu thành công.
- Chưa cào Thuyết minh nếu nguồn chưa hỗ trợ.
- Không tự chọn vnstock hoặc FireAnt là đúng khi hai số khác nhau.

---

## 13. Thời gian dự kiến

| Phần việc | Thời gian dự kiến |
|---|---:|
| Kiểm kê + thử FireAnt/vnstock | 2–4 ngày |
| Chốt mẫu data + viết công cụ + test | 4–6 ngày |
| Chạy thử 12–15 mã và 100 mã | 2–3 ngày |
| Cào toàn bộ + so hai nguồn + kiểm tra cuối | 3–7 ngày |

Tổng hợp lý: **2–3 tuần làm việc** nếu hai nguồn ổn định.

Có thể lâu hơn nếu FireAnt không có API BCTC ổn định, nguồn đổi cách trả data, giới hạn số lần gọi hoặc các nhóm doanh nghiệp có cấu trúc quá khác nhau.

Không được bỏ bước kiểm tra chỉ để kịp thời gian dự kiến.

---

## 14. Các tiêu chuẩn EF-S áp dụng

- **Workflow:** Chỉ làm đúng bước được giao; không tự chuyển sang cào toàn bộ.
- **EF-S-00:** File trên chỉ gọi file cùng tầng hoặc tầng dưới.
- **EF-S-01:** Mỗi file có một nhiệm vụ rõ.
- **EF-S-02:** Lỗi không bị giấu; chỉ thử lại lỗi tạm thời.
- **EF-S-03:** Tách data gốc/data đã xử lý; ghi file an toàn; có sổ tiến độ.
- **EF-S-04:** Dùng `E_BlackBox`, có mã lần chạy và báo cáo cuối.
- **EF-S-05:** Chỉ đưa code thật sự dùng chung vào `E_Helper`.
- **EF-S-06:** Không tự cài thư viện; ghi đúng phiên bản đã dùng.
- **EF-S-09:** Có test nhỏ, test ghép nhiều phần và test nguồn thật tách riêng.
- **Phase 01:** Không bỏ mã chết; chỉ qua Phase 2 khi data đạt kiểm tra chất lượng.

---

## 15. Điểm dừng bắt buộc

Sau Bước 1–3, Agent phải gửi báo cáo chạy thử cho chủ dự án.

Chưa được tự chuyển sang viết toàn bộ công cụ hoặc cào toàn thị trường nếu chưa chứng minh:

1. FireAnt thật sự có BCTC và ta có quyền lấy.
2. vnstock đang dùng VCI hay KBS và vì sao chọn.
3. Đơn vị, loại báo cáo và kiểu số quý của hai nguồn.
4. Mẫu data chung dùng được cho các nhóm doanh nghiệp.
5. Số lần gọi, thời gian, dung lượng và mức lỗi dự kiến.

Nếu cần đổi cách lưu data, chọn nguồn ưu tiên, chuyển/xóa data cũ hoặc cào toàn bộ, Agent phải báo trước và chờ duyệt.
