# Báo cáo Cross-check: SRP Principles vs Codebase thực tế

> Đối chiếu [srp_principles.md](file:///c:/Users/HP/Documents/E_CYBER-FINANCIAL/srp_principles.md) với kiến trúc thực tế của dự án E_CYBER-FINANCIAL và lộ trình [19-MONTH_PLANNING.md](file:///c:/Users/HP/Documents/E_CYBER-FINANCIAL/19-MONTH_PLANNING.md) để tìm ra "lỗ hổng" và đề xuất cải thiện.

---

## Tổng quan

Bộ tiêu chuẩn SRP (đã adapt cho Python/Financial) đã **chắc** ở 3 trục chính:
- ✅ **Tách module** — Quy tắc "1 File = 1 Module/Concern" rõ ràng, có ví dụ đúng/sai.
- ✅ **Tổ chức thư mục** — Phase-first phù hợp với lộ trình 19 tháng.
- ✅ **Hành vi bị cấm** — Danh sách blacklist cụ thể (God File, hardcode path, UI chứa logic).

Tuy nhiên, khi cross-check với **code thực tế** và **planning**, có **6 lỗ hổng** cần bổ sung:

---

## 🔴 Ưu tiên CAO (Ảnh hưởng trực tiếp đến chất lượng code)

### Đề xuất 1: Quy tắc hướng phụ thuộc cho ML Pipeline (Phase 3)

**Vấn đề:** Bộ tiêu chuẩn đã có Dependency Flow cho module News, nhưng Phase 3 (ML Training) sẽ phức tạp hơn nhiều. Planning yêu cầu chạy 3 model (XGBoost, LightGBM, CatBoost) qua "sàn đấu" PyCaret. Nếu không quy định rõ, code ML sẽ nhanh chóng thành mớ spaghetti.

**Lý do:** Phase 3 chiếm **6 tháng** — dài nhất trong planning. Mỗi model có hyperparameters, training config, và evaluation riêng. Cần SRP rõ ràng từ đầu.

**Đề xuất bổ sung:**

```
Dependency Flow cho ML Pipeline:

data_loader → feature_engineer → model_trainer → model_evaluator → model_selector
                                       ↓
                                  model_config (JSON/YAML)

Quy tắc:
✅ model_trainer ĐƯỢC gọi data_loader, feature_engineer
✅ model_evaluator ĐƯỢC gọi model_trainer để lấy kết quả
✅ model_selector (PyCaret arena) ĐƯỢC gọi model_evaluator
❌ model_trainer KHÔNG ĐƯỢC chứa logic đánh giá (evaluation)
❌ model_config KHÔNG ĐƯỢC import bất kỳ module nào (nó là config thuần)
❌ feature_engineer KHÔNG ĐƯỢC gọi ngược data_loader
```

---

### Đề xuất 2: Anatomy cho Scheduled Tasks (bổ sung §4)

**Vấn đề:** Dự án đã có 2 scheduled tasks (`auto_news.py`, `auto_sync.py`) chạy bằng Windows Task Scheduler. Nhưng theo planning, Phase 5 sẽ thêm nhiều task nữa (cào tin hàng ngày, chấm sentiment score, v.v.). Bộ tiêu chuẩn chỉ nói "scheduled script delegate sang Manager" nhưng chưa có hướng dẫn chi tiết.

**Lý do:** Scheduled tasks chạy ngầm, không có user nhìn thấy output. Nếu crash mà không log, bug sẽ "im lặng" rất khó debug.

**Đề xuất bổ sung:**

```
### Quy tắc cho Scheduled Tasks (Auto/)

Mọi script trong Auto/ PHẢI tuân thủ:

1. PHẢI có error handling bao quanh toàn bộ main():
   try:
       main()
   except Exception as e:
       write_log(f"FATAL: {e}")

2. PHẢI ghi log ra file (không chỉ print ra console).
   Console output sẽ mất khi Task Scheduler chạy ngầm.

3. PHẢI delegate logic sang Manager. File Auto/ chỉ chứa:
   - Import
   - Log setup
   - Gọi Manager.run_pipeline()
   - Ghi log kết quả
   
4. KHÔNG ĐƯỢC vượt quá ~50 dòng.
   Nếu dài hơn, logic đang bị rò rỉ vào script trigger.
   
5. Tên file BẮT BUỘC bắt đầu bằng `auto_` để phân biệt.
```

---

### Đề xuất 3: Quy tắc cho Entry Point (`Warden.py`)

**Vấn đề:** `Warden.py` hiện chỉ 29 dòng — rất tốt. Nhưng khi Phase 2-4 hoàn thành, sẽ có thêm nhiều tab/panel mới trong IDE. Nếu không kiểm soát, `Warden.py` hoặc `main_window.py` sẽ phình to.

**Lý do:** Tương tự vấn đề `Extension.cs` trong Revit — entry point là "thần giữ cổng" cần được kiểm soát nghiêm ngặt.

**Đề xuất bổ sung:**

```
### Quy tắc cho Warden.py (Entry Point)

Warden.py chỉ được phép:
  ✅ Import và khởi tạo QApplication
  ✅ Gọi MainWindow()
  ✅ Setup sys.path (nếu cần)

Warden.py KHÔNG ĐƯỢC:
  ❌ Chứa business logic
  ❌ Import trực tiếp các module Phase (phải qua IDE_UI/)
  ❌ Vượt quá ~50 dòng

Khi IDE phình to, logic khởi tạo panel/tab phải nằm trong IDE_UI/,
KHÔNG đẩy vào Warden.py.
```

---

## 🟡 Ưu tiên TRUNG BÌNH (Nên có, nhưng chưa gấp)

### Đề xuất 4: Quy ước xử lý lỗi (Error Handling Strategy)

**Vấn đề:** Hiện tại, error handling không nhất quán:
- `data_collector.py`: Dùng `logging.error()` ✅
- `news_scraper.py`: Dùng bare `except Exception: continue` (nuốt lỗi) ❌
- `gemini_ai.py`: Retry 3 lần rồi return HTML error ⚠️

**Đề xuất:**

```
Quy ước xử lý lỗi:

1. Module thu thập (Collector/Scraper): ĐƯỢC PHÉP try/catch từng item
   nhưng PHẢI log chi tiết lỗi (không nuốt im lặng).

2. Module điều phối (Manager): PHẢI có try/catch bao ngoài toàn bộ pipeline.
   Khi catch, PHẢI log + thông báo user (qua callback hoặc return message).

3. Module tính toán (Analyzer/ML): KHÔNG try/catch bên trong.
   Để exception tự nhiên bay lên Manager xử lý.
   
4. TUYỆT ĐỐI KHÔNG:
   ❌ except Exception: continue   (nuốt lỗi không log)
   ❌ except Exception: pass       (im lặng hoàn toàn)
   
   PHẢI:
   ✅ except Exception as e: logging.error(f"[{context}] {e}")
```

---

### Đề xuất 5: Quy tắc quản lý Data Files

**Vấn đề:** Planning yêu cầu nhiều loại data:
- Phase 1: Giá cổ phiếu (Parquet) — **BẮT BUỘC giá điều chỉnh**
- Phase 2: Feature indicators (DataFrame mới)
- Phase 3: Model artifacts (.pkl, .joblib)
- Phase 5: News JSON + Sentiment scores

Hiện chưa có quy tắc data nào trong SRP.

**Đề xuất:**

```
Quy tắc quản lý Data Files:

1. Data thô (raw) → Data_Main/ (chỉ ghi 1 lần, KHÔNG sửa)
2. Data đã xử lý (processed) → Data_Processed/ (output của Phase 1-2)
3. Model artifacts → Models/ (output của Phase 3)
4. News JSON → News_JSON/ (đã có)

Nguyên tắc:
- Data thô là IMMUTABLE — không bao giờ sửa trực tiếp.
- Nếu cần sửa, tạo pipeline transform và lưu sang folder khác.
- File data KHÔNG ĐƯỢC nằm cùng thư mục với code.
- Tên file data PHẢI chứa nguồn gốc: {symbol}_historical_{source}.parquet
```

---

### Đề xuất 6: Giới hạn kích thước file

**Vấn đề:** §5.3 đặt soft limit ~80 dòng cho hàm, nhưng không có guideline cho **file/module**. `data_raw_cross_check.py` 26KB mà không vi phạm bất kỳ quy tắc cụ thể nào, dù rõ ràng là God File.

**Đề xuất:**

```
Giới hạn kích thước (soft limit):

| Đơn vị     | Soft limit | Khi vượt, cần review                                      |
|------------|-----------|-------------------------------------------------------------|
| Hàm        | ~80 dòng  | Tách thành sub-function hoặc module mới                    |
| File/Module | ~300 dòng | Kiểm tra xem module có đang làm > 1 việc không            |
| Phase Folder | ~10 file | Kiểm tra xem phase có cần tách sub-step không             |

Tham chiếu thực tế:
- ✅ auto_news.py: 44 dòng (trigger thuần — mẫu mực)
- ✅ news_scraper.py: 168 dòng (1 concern duy nhất)
- ⚠️ news_manager.py: 234 dòng (gần limit, nhưng vẫn 1 concern)
- ❌ data_raw_cross_check.py: ~700+ dòng (God File, cần tách ngay)
```

---

## Tóm tắt

| # | Đề xuất | Ưu tiên | Lý do |
|---|---|---|---|
| 1 | ML Pipeline Dependency Flow | 🔴 Cao | Phase 3 (6 tháng) cần SRP rõ từ đầu |
| 2 | Anatomy cho Scheduled Tasks | 🔴 Cao | Đã có `auto_news.py`, `auto_sync.py` — cần chuẩn hóa |
| 3 | Quy tắc cho `Warden.py` | 🔴 Cao | Entry point cần kiểm soát trước khi IDE mở rộng |
| 4 | Error Handling Strategy | 🟡 Trung bình | Hiện không nhất quán giữa các module |
| 5 | Data Files Management | 🟡 Trung bình | Phase 1-3 tạo nhiều loại data, cần quy tắc rõ |
| 6 | File Size Guideline | 🟡 Trung bình | `data_raw_cross_check.py` 26KB là ví dụ sống |

> [!NOTE]
> Báo cáo này chỉ mang tính **đề xuất**. Mọi thay đổi vào codebase sẽ chỉ được thực hiện khi bạn duyệt và xác nhận.
