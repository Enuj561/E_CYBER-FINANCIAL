|   Phase | Task          | To Do                                          | Note                                                     | Deadline   | Check Date   |
|--------:|:--------------|:-----------------------------------------------|:---------------------------------------------------------|:-----------|:-------------|
|       1 | CHUẨN BỊ DATA | Dùng thư viện vnstock để cào data.             | * *Lưu ý:                                                | 1 month    | -            |
|         |               |                                                | -Đối với giá cổ phiếu, BẮT BUỘC dùng giá điều chỉnh.     |            |              |
|         |               |                                                | -Không bỏ qua các mã đã chết.                            |            |              |
|     nan | nan           | Làm sạch data bằng Scikit-Learn                | nan                                                      | nan        | -            |
|       2 | THUẬT TOÁN    | Học về ý nghĩa và thuật toán tài chính.        | -Tham khảo sử dụng thư viện TA-lib, pandas-ta.           | 3 months   | -            |
|     nan | nan           | Viết các thuật toán và kiểm tra độ chính xác.  | nan                                                      | nan        | -            |
|       3 | ML TRAINING   | PyCaret: dùng để training 3 thằng ở dưới.      | PyCaret tổ chức 1 sàn đấu để cho 3 thằng dưới            | 6 months   | -            |
|         |               |                                                | tàn sát nhau. Cuối cùng chọn ra thằng mạnh nhất.         |            |              |
|         |               |                                                | **Lưu ý:                                                 |            |              |
|         |               |                                                | -BẮT BUỘC dùng Time Series Split (Walk-foward            |            |              |
|         |               |                                                | validation).                                             |            |              |
|         |               |                                                | -Xem xét thời gian và RAM tiêu thụ khi training.         |            |              |
|         |               |                                                | -Xem xét việc dùng blend_models để tránh sai số.         |            |              |
|         |               |                                                | -Nếu thay đổi context từ dài hạn sang trung hạn          |            |              |
|         |               |                                                | hoặc lướt sóng, cần train lại model bằng PyCaret.        |            |              |
|     nan | nan           | Gradient Boosting Decision Tree:               | GBDT: thuật toán cây quyết định.                         | nan        | -            |
|         |               | -XGBoost: cần data lớn, RAM khỏe nhưng bù      | Bắt đầu tạo ra 1 quyết định, tiếp theo                   |            |              |
|         |               | lại train chậm nhất.                           | tạo ra các quyết định trổ xuống (giống                   |            |              |
|         |               | -LightGBM: là model train nhanh nhất nhưng     | cây gia phả) để bắt lỗi các quyết định                   |            |              |
|         |               | bắt buộc data lớn. Nếu data ít thì model dễ    | trước và đưa ra quyết định chính xác                     |            |              |
|         |               | học vẹt.                                       | hơn.                                                     |            |              |
|         |               | -CatBoost: không cần số hóa data, train nhanh  |                                                          |            |              |
|         |               | sau LightGBM.                                  |                                                          |            |              |
|       4 | CHIẾN TRƯỜNG  | Tiến hành mô phỏng quá trình đầu tư dựa trên   | **Lưu ý:                                                 | 6 months   | -            |
|         | GIẢ LẬP       | các ML vừa build được.                         | -Trừ chi phí giao dịch.                                  |            |              |
|         |               |                                                | -Tính trượt giá.                                         |            |              |
|         |               |                                                | -Stress Test model bằng năm 2022.                        |            |              |
|         |               |                                                | -So sánh lợi nhuận với chiến lược Buy and Hold VN-Index. |            |              |
|       5 | TÍCH HỢP NEWS | Tiến hành cập chạy tool cập nhật tin tức hàng  | **Lưu ý:                                                 | Through    | -            |
|         |               | ngày, lưu lại file dưới dạng JSON.             | -Làm càng sớm càng tốt để tích lũy data cho việc         |            |              |
|         |               |                                                | training.                                                |            |              |
|     nan | nan           | Tích hợp chấm điểm Sentiment Score cùng file   | **Lưu ý:                                                 | Through    | -            |
|         |               | JSON.                                          | -Tin tức ở VN luôn bị thao túng, be careful.             |            |              |
|     nan | nan           | Kết hợp data news vào bộ xương của BCTC.       | **Lưu ý:                                                 | 3 months   | -            |
|         |               |                                                | -Data news là mỗi ngày còn BCTC tính theo quý/năm.       |            |              |
|         |               |                                                | -> Tạo điểm neo để ML không phụ thuộc vào sự biến        |            |              |
|         |               |                                                | động.                                                    |            |              |
|     nan | nan           | Dựng lại Phase 4 kết hợp với data news sau đó  | **Lưu ý:                                                 | nan        | -            |
|         |               | chấm điểm win rate dựa trên cả 2 kết quả.      | -Sử dụng NLP.                                            |            |              |
|         |               |                                                | -So sánh win rate của 2 kết quả giữa việc có news và     |            |              |
|         |               |                                                | không có news.                                           |            |              |