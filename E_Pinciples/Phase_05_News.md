# Chương 14 — Phase 5: Tích hợp News

> **Mô hình: Pipeline xuyên suốt (Scrape → Score → Integrate)**
> **Thời lượng:** Xuyên suốt (Through) | **Tech stack:** feedparser, Gemini AI, NLP

---

## 13.1. Dependency Flow

```
Scraper (cào RSS) → Manager (điều phối) → AI Client (Gemini) → Renderer (HTML output)
                         ↓
                    Phase_5_Data/ (lưu trữ)
                         ↓
                 Sentiment Scorer ← [CHỜ TRIỂN KHAI]
                         ↓
                 Anchor Builder (tạo điểm neo cho BCTC) ← [CHỜ TRIỂN KHAI]
                         ↓
                 Feed vào Phase 3 (feature_builder.py đọc sentiment)
```

Quy tắc:
- ✅ `Manager` ĐƯỢC gọi `Scraper`, `AI Client`, `Renderer`
- ✅ `Sentiment Scorer` ĐƯỢC đọc `Phase_5_Data/`
- ✅ Phase 3 `feature_builder.py` ĐƯỢC đọc sentiment output
- ❌ `Scraper` KHÔNG ĐƯỢC gọi ngược `Manager`
- ❌ `AI Client` KHÔNG ĐƯỢC import `IDE_UI` hoặc `Renderer`
- ❌ `Sentiment Scorer` KHÔNG ĐƯỢC modify News JSON gốc

---

## 13.2. Cấu trúc thư mục

```
Main Scripts/News/
├── news_scraper.py           ← Cào RSS từ 4 nguồn báo
├── news_manager.py           ← Điều phối pipeline (backfill + cào + lưu)
├── ai_client.py              ← Gọi Gemini API, trả về JSON thuần ← [CẦN TÁCH TỪ gemini_ai.py]
├── news_renderer.py          ← Render HTML output ← [CẦN TÁCH TỪ gemini_ai.py]
├── sentiment_scorer.py       ← Chấm điểm sentiment ← [CHỜ TRIỂN KHAI]
└── anchor_builder.py         ← Tạo điểm neo news vs BCTC ← [CHỜ TRIỂN KHAI]
```

---

## 13.3. Kiểu module đặc thù

Ngoài các hậu tố chung ở [§3.2 — EF-S-01](./EF-S-01_Data_Structure.md), Phase 5 bổ sung:

| Hậu tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `_scorer` | Chấm điểm (sentiment, quality) | `sentiment_scorer.py` |
| `_builder` | Xây dựng cấu trúc data (điểm neo) | `anchor_builder.py` |

---

## 13.4. Error Handling

**Chiến lược: Resilient — 1 nguồn lỗi không crash toàn bộ** (Xem thêm [EF-S-02](./EF-S-02_Error_Handling.md))

Cào tin tức từ 4+ nguồn báo, 1 nguồn die là chuyện bình thường. Code PHẢI:
- Catch exception cho TỪNG nguồn, log rồi tiếp tục nguồn tiếp theo
- KHÔNG crash toàn bộ batch vì 1 RSS feed lỗi
- Tạo file rỗng nếu không cào được bài nào (đánh dấu "đã xử lý")

```python
# ✅ ĐÚNG — Resilient, skip bad source
for url in urls_to_fetch:
    try:
        feed = feedparser.parse(url)
        # ... xử lý ...
    except Exception as e:
        logging.error(f"[news_scraper] {url}: {e}", exc_info=True)
        debug_logs.append(f"❌ [{url}] Lỗi: {e}")
        continue  # Skip, không crash
```

---

## 13.5. Output Contract

| Thuộc tính | Giá trị |
|---|---|
| **Format** | `.json` (News JSON) + HTML (summary) |
| **Vị trí** | `Phase_5_Data/` |
| **Tên file** | `News_{dd}_{mm}_{yy}.json` |
| **Ai đọc?** | Phase 3 `feature_builder.py` (sentiment data), IDE_UI (hiển thị), Phase 4 (so sánh win rate) |

> [!IMPORTANT]
> **Constraints từ Planning:**
> - Làm **càng sớm càng tốt** để tích lũy data cho training
> - Tin tức ở VN **luôn bị thao túng** — be careful
> - Data news theo **ngày** nhưng BCTC theo **quý/năm** → cần tạo **điểm neo** (anchor)
> - Sử dụng **NLP** cho sentiment scoring
> - Phase 4 sẽ chạy lại kèm news data → so sánh win rate **có news vs không news**

---

## 13.6. Ví dụ thực tế

### Hiện trạng tốt: news_scraper.py + news_manager.py ✅
```
news_scraper.py       ← Thu thập RSS (1 concern) ✅
news_manager.py       ← Điều phối pipeline (1 concern) ✅
```

### Cần refactor: gemini_ai.py ❌
```
Hiện tại: 1 file trộn API call + HTML rendering

Đề xuất tách:
├── ai_client.py          ← Chỉ gọi Gemini API, trả về JSON thuần
└── news_renderer.py      ← Chỉ nhận JSON, render HTML output
```

---

> **Ghi nhớ cuối cùng:** Nếu bạn phải giải thích "module này làm gì" bằng từ **"và"** (ví dụ: "module này cào tin **và** gọi AI **và** render HTML"), thì module đó đang vi phạm SRP và cần được tách ra.
