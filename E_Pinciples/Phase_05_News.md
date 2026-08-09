# Chương 14 — Phase 5: News và Sentiment

> **Trạng thái:** PARTIALLY IMPLEMENTED — daily RSS collection, Gemini client, Manager, JSON save và PyQt display đã có; sentiment/anchor/ML integration chưa được coi là hoàn thành.
>
> **Agent phải đọc file này khi:** sửa News scraper/Manager/Gemini/renderer, daily JSON/backfill, làm sentiment, nối News với BCTC/Phase 3 hoặc chạy A/B backtest có/không News.
>
> **Roadmap gốc:** [19-MONTH_PLANNING.md](../19-MONTH_PLANNING.md) — thu thập News càng sớm càng tốt và xuyên suốt; chấm sentiment; neo dữ liệu ngày với BCTC quý/năm; chạy lại Phase 4 để so có News và không News.
>
> **Timeline:** Thu thập chạy xuyên suốt tháng 1–19. Khối sentiment/anchor/integration 3 tháng được hiểu là trọng tâm tháng 17–19, trừ khi roadmap được cập nhật.

## 14.1. Mục tiêu Phase

Phase 5 tạo một chuỗi dữ liệu News có provenance và thời gian đúng để nghiên cứu ảnh hưởng tới model/strategy:

1. Thu thập bài theo ngày từ nhiều nguồn.
2. Giữ source URL/title/published time/raw summary để kiểm chứng.
3. Dedupe và chuẩn hóa mà không xóa dấu vết nguồn.
4. Tạo summary/sentiment như **derived data**, có model/prompt/version.
5. Căn News theo trading calendar và BCTC availability date.
6. Đưa feature News vào Phase 3 qua data contract.
7. Chạy Phase 4 A/B công bằng: cùng model setup/period, khác đúng nhóm feature News.

AI summary/sentiment không phải “sự thật gốc”. Raw source và provenance mới là căn cứ kiểm tra.

## 14.2. Hiện trạng và phần còn thiếu

### Đã có trong repo

```text
Main Scripts/News/
├── E_news_scraper.py
├── E_news_manager.py
├── E_ai_client.py              Dùng google-genai
├── E_news_renderer.py
└── __init__.py

Main Scripts/Auto/E_auto_news.py
Main Scripts/IDE_UI/E_center_workspace.py
Phase_5_Data/
```

### Chưa được mặc định coi là hoàn thành

- Sentiment schema/scorer được kiểm chứng.
- Source-quality/bias/confidence model.
- Anchor News ngày ↔ BCTC quý/năm theo available date.
- Feature contract cho Phase 3.
- A/B backtest có News vs không News.
- UI hiện tại còn có đường gọi trực tiếp module con thay vì chỉ qua Manager theo EF-S-07.
- Log/Auto failure status chưa mặc định đạt chuẩn mới nếu chưa refactor/test.

Các dòng trên là snapshot; Agent vẫn phải kiểm tra repo thật trước task.

## 14.3. Hai chặng roadmap

### Chặng A — Thu thập xuyên suốt tháng 1–19

- Daily scheduled collection.
- Backfill có giới hạn và provenance.
- Source coverage/failure report.
- Raw/normalized articles + dedupe.
- Tích lũy dữ liệu đủ dài trước ML.

### Chặng B — Sentiment/Anchor/Integration, trọng tâm 3 tháng

| Tháng suy ra | Trọng tâm | Kết quả phải có |
|---|---|---|
| 17 | Sentiment/quality scoring có evaluation | Versioned sentiment dataset |
| 18 | Point-in-time aggregation + BCTC anchor | Feature contract cho Phase 3 |
| 19 | Retrain và A/B backtest | Báo cáo có News vs không News |

Nếu collection bắt đầu muộn hoặc coverage kém, Agent phải báo limitation; không bù bằng News do AI tự tạo.

## 14.4. Kiến trúc mục tiêu

```text
Auto/UI
  ↓
News Manager / Application Service
  ├─ RSS Scraper/Client
  ├─ Normalizer + Deduplicator
  ├─ News Repository (raw/normalized)
  ├─ Gemini Summary Adapter (derived)
  ├─ Sentiment/Quality Scorer (derived)
  └─ News Feature/Anchor Builder
                    ↓
        Versioned Phase 5 contracts
             ↓              ↓
          Phase 3         Phase 4 A/B
```

- UI/Worker chỉ gọi Manager/facade.
- Scraper không gọi AI/Renderer/Manager ngược.
- AI Client nhận input và trả structured result; không tự ghi data/UI.
- Repository ghi atomic và phân biệt raw/derived.
- Feature Builder không train model.
- Phase 3/4 đọc contract; không import chéo pipeline News.

Tham chiếu: [EF-S-00 §0.2–0.7](./EF-S-00_Dependency_Direction.md), [EF-S-07 §7.1–7.9](./EF-S-07_UI_Backend.md).

## 14.5. Daily collection contract

Mỗi article tối thiểu cần:

- stable/generated `article_id`;
- source/source feed;
- title;
- link/canonical URL;
- published timestamp + timezone hoặc độ tin cậy timestamp;
- collected timestamp;
- raw/clean summary text;
- category/language;
- content hash/dedupe group;
- parser/schema version.

Timezone chuẩn phải được chốt, ưu tiên `Asia/Ho_Chi_Minh` cho reporting, nhưng vẫn giữ offset/source timestamp khi có.

Không suy diễn published time từ “ngày file” nếu feed thiếu; đánh dấu missing/estimated rõ.

## 14.6. Raw, normalized và derived data

| Lớp | Chứa gì | Quy tắc |
|---|---|---|
| Raw/source | Article fields/provenance gần nguồn nhất | Không bị AI summary ghi đè |
| Normalized | Text/time/category/dedupe đã chuẩn hóa | Có normalizer/schema version |
| Derived summary | Gemini/algorithm summary | Có model, prompt, generated_at, validation status |
| Derived sentiment | Score/label/confidence | Có scorer/model/version và evaluation |
| Aggregated features | Daily/window/source/sector metrics | Có cutoff và feature version |

Roadmap muốn sentiment “cùng file JSON”. Điều này được phép dưới một envelope có các section rõ, nhưng derived fields không được thay raw fields:

```json
{
  "schema_version": "news_daily_v2",
  "date": "2026-08-09",
  "run_status": "partial",
  "raw_articles": [],
  "derived": {
    "summary": {},
    "sentiment": {}
  },
  "source_status": []
}
```

## 14.7. Tên file và migration

Code hiện tại dùng dạng legacy:

```text
Phase_5_Data/News_{DD}_{MM}_{YY}.json
```

Format mới nên ưu tiên ngày ISO dễ sort:

```text
Phase_5_Data/news_YYYY-MM-DD.json
```

Đổi tên/schema là migration có ảnh hưởng Manager/UI/Auto/data cũ. Agent không được tự đổi chỉ vì format mới đẹp hơn; phải có plan, backward compatibility/migration và test.

## 14.8. Dedupe, source bias và chất lượng

Một sự kiện có thể xuất hiện ở nhiều báo; không được coi mọi bài là tín hiệu độc lập.

Dedupe có thể dùng:

- canonical URL;
- normalized title/content hash;
- similarity + time window;
- entity/event grouping.

Phải giữ danh sách nguồn trong group để đánh giá coverage/corroboration.

Roadmap cảnh báo News Việt Nam có thể bị thao túng. Viết lại thành rule có thể kiểm chứng:

- nguồn có bias, lỗi hoặc agenda khác nhau;
- không coi một nguồn/bài đơn lẻ là ground truth;
- lưu provenance và source coverage;
- sentiment score cần confidence/quality flag;
- nghiên cứu sensitivity khi bỏ từng nguồn/nhóm nguồn;
- không tự dán nhãn “báo thao túng” nếu chưa có tiêu chí/bằng chứng.

## 14.9. Gemini summary và chống hallucination

- Prompt phải chứa article content thật; validate không còn placeholder như `{content}`.
- Output dùng structured schema và parser validation.
- Summary không được thêm company/event/number không có trong input nếu contract yêu cầu extractive/factual.
- Giữ article IDs/source links để trace từng ý.
- Lưu model ID, prompt version, generated_at và error/finish status.
- Response parse fail không được thay bằng AI-generated example.
- Không gửi dữ liệu/secret ngoài phạm vi đã duyệt.

AI output cần sample human review/evaluation trước khi dùng làm ML feature.

## 14.10. Sentiment contract

Trước khi triển khai scorer phải chốt:

- unit: article, event, symbol, sector hay market-day;
- label/scale, ví dụ negative/neutral/positive hoặc `[-1, 1]`;
- entity/symbol mapping;
- horizon/context;
- confidence/quality;
- treatment của duplicate/source weight;
- scorer/model/prompt version;
- labeled evaluation set và metric.

Không dùng một sentiment score chung cho toàn bài nếu bài chứa nhiều công ty với tác động trái chiều mà không ghi limitation.

## 14.11. News ↔ BCTC anchor và point-in-time

Roadmap muốn “điểm neo” vì News theo ngày còn BCTC theo quý/năm.

Anchor không phải chỉ forward-fill BCTC theo quarter end. Nó phải dựa trên thời điểm thông tin có thể biết:

- BCTC: public/available date;
- News: published/received timestamp;
- Market data: trading calendar/cutoff;
- Prediction: signal/execution timestamp.

Feature examples cần được duyệt:

- rolling sentiment 1/3/7/30 trading days;
- event/source counts;
- confidence-weighted score;
- change since latest publicly available BCTC;
- days since BCTC/news event.

Không gán BCTC quý cho các ngày trước khi báo cáo được công bố.

## 14.12. Error handling và daily run status

Một RSS feed lỗi có thể không làm cả batch crash, nhưng kết quả phải nói thật:

- `complete`: mọi source bắt buộc xử lý thành công theo contract;
- `partial`: có usable articles nhưng thiếu source/step;
- `empty_valid`: mọi source xử lý thành công và thật sự không có article hợp lệ;
- `failed`: không thể tạo output usable hoặc lỗi fatal.

Không tạo file rỗng rồi coi là “đã xử lý” nếu toàn bộ source đều lỗi. `empty_valid` và `failed` phải khác nhau.

- Retry lỗi tạm thời có giới hạn/backoff.
- Mỗi source có status/error/count.
- Fatal schema/repository/secret error đi lên boundary.
- Auto fatal phải log traceback và exit khác 0.

Tham chiếu: [EF-S-02 §2.5–2.8](./EF-S-02_Error_Handling.md), [EF-S-04 §4.2–4.11](./EF-S-04_Logging_Debug.md).

## 14.13. Phase 3/4 integration và A/B test

Phase 3 tạo hai experiment family trên cùng base dataset/split:

- A: không có News features;
- B: có News features đã versioned.

Phase 4 so trên cùng model-selection policy, period, cost, benchmark và execution assumptions. Không chỉ báo win rate; xem thêm return, drawdown, turnover, precision/stability và significance/uncertainty phù hợp.

Không tune nhóm B nhiều hơn nhóm A rồi gọi comparison công bằng. Mọi khác biệt ngoài News feature phải được kiểm soát/ghi rõ.

## 14.14. Testing gate

- RSS parser bằng saved fixtures: valid, stale, timezone thiếu, malformed.
- Dedupe URL/title/similarity và multi-source grouping.
- Không bài trong window vs mọi source lỗi cho status khác nhau.
- Gemini placeholder/schema/hallucination guard theo sample.
- Sentiment range/entity/confidence/version contract.
- Point-in-time test: future News/BCTC không đổi feature quá khứ.
- Atomic daily write/backfill idempotency.
- UI worker success/error signal; UI không import module con.
- Auto fatal exit khác 0.
- A/B dataset khác đúng News feature group.

Live RSS/Gemini test phải opt-in, có timeout và không chạy mặc định.

## 14.15. Definition of Done cho Phase 5

- [ ] Daily raw/normalized collection có provenance/source status.
- [ ] `complete/partial/empty_valid/failed` phân biệt đúng.
- [ ] AI summary không ghi đè raw và có model/prompt/version.
- [ ] Dedupe giữ source group và không đếm trùng như tín hiệu độc lập.
- [ ] Sentiment có schema, confidence và evaluation set.
- [ ] News/BCTC anchor dùng available/published time, không nhìn tương lai.
- [ ] Feature contract cho Phase 3 có cutoff/version rõ.
- [ ] Phase 4 A/B công bằng và không chỉ dựa vào win rate.
- [ ] UI chỉ gọi Manager/facade; Auto/log/error đúng EF-S.
- [ ] Legacy filename/schema nếu đổi có migration và backward-compatibility plan.
