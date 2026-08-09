# E_CYBER-FINANCIAL — User & AI Agent Operating Workflow

> **Trạng thái:** ACTIVE — luật vận hành cấp cao của AI Agent trong repo này.
>
> **Workflow version:** 2026-08-09.3
>
> **Agent phải đọc file này trước khi:** review, chẩn đoán, lập plan, sửa code, sửa tài liệu, xử lý data hoặc thay đổi cấu hình dự án.
>
> **Mục tiêu:** Agent làm đúng việc được giao, dựa trên bằng chứng, tuân thủ đúng nhánh EF-S, không tự chế yêu cầu, không sửa lan man, không giấu lỗi và không tuyên bố hoàn thành khi chưa kiểm chứng.

## 0. Luật vàng

> **Không được nói “đã xong”, “đã sửa” hoặc “đã test” nếu chưa có bằng chứng tương ứng.**

Dự án dùng hai lớp tài liệu:

```text
E_User_Agent_Workflow.md   → Agent phải làm việc theo quy trình nào
EF-S-00 đến EF-S-09        → Khi code một vấn đề cụ thể thì phải thiết kế thế nào
```

Workflow này không thay thế EF-S. Nó chỉ định lúc nào Agent phải mở nhánh EF-S phù hợp.

### 0.1. Không đọc lặp lại vô ích

- Agent mới hoặc conversation mới: đọc Workflow hiện hành một lần để hiểu quyền hạn và quy trình.
- Trong cùng conversation, nếu đã đọc đúng `Workflow version` ở trên: không đọc lại toàn file ở mỗi turn; chỉ quay lại mục liên quan.
- Khi version thay đổi: đọc lại phần diff hoặc các mục đã đổi; nếu không xác định được phần đổi thì đọc lại toàn file.
- Khi bàn giao: quay lại §11 `Definition of Done`; không cần tải lại mọi phần phía trên.

---

## 1. Hiểu đúng về người dùng

- Người dùng là **BIM Engineer**, không phải Software Engineer.
- Mức hiểu code tự đánh giá khoảng **10/100**: hiểu ý chính nhưng không thể tự kiểm tra mọi chi tiết kỹ thuật.
- Người dùng cung cấp ý tưởng, mục tiêu, logic nghiệp vụ, trải nghiệm mong muốn và định hướng kiến trúc.
- Agent chịu trách nhiệm phân tích kỹ thuật, cảnh báo rủi ro, đề xuất phương án dễ hiểu, viết code và chứng minh kết quả.

### Cách giao tiếp bắt buộc

- Nói kết quả/ảnh hưởng trước, kỹ thuật sau.
- Dùng tiếng Việt đời thường; nếu buộc dùng thuật ngữ thì giải thích ngay bằng một câu đơn giản.
- Có thể dùng ví dụ BIM: module giống bộ môn, interface giống điểm giao, data contract giống quy ước trao đổi model.
- Không đẩy trách nhiệm kiểm tra code ngược cho người dùng bằng câu kiểu “bạn tự xem code có đúng không”.
- Chỉ hỏi khi câu trả lời làm thay đổi đáng kể kết quả, kiến trúc, dữ liệu, chi phí hoặc phạm vi.
- Không hỏi lại thông tin đã có thể tìm thấy trong repo hoặc tài liệu.

Agent phải tôn trọng ý tưởng của người dùng nhưng **không được mù quáng triển khai một thiết kế kỹ thuật có lỗi**. Nếu thấy rủi ro, Agent phải giải thích dễ hiểu, đưa bằng chứng và đề xuất lựa chọn an toàn hơn để người dùng quyết định.

---

## 2. Bối cảnh dự án

- Đây là dự án cá nhân về phân tích/tự động hóa dữ liệu tài chính và chứng khoán Việt Nam.
- Dự án đi theo 5 Phase: data → thuật toán → ML → backtest → news/sentiment.
- Backend hiện tại chủ yếu là Python; UI hiện tại là PyQt6.
- C# frontend vẫn là hướng tương lai và chưa được tự động kích hoạt.
- Dữ liệu tài chính và công thức phải được xử lý cẩn thận: kết quả “chạy được” chưa chắc đã “đúng”.

Thông tin trạng thái Phase, package và file thay đổi theo thời gian. Agent phải kiểm tra repo thật; không được coi mô tả lịch sử trong tài liệu là bằng chứng rằng một feature đang tồn tại hoặc đã hoàn thành.

---

## 3. Thứ tự ưu tiên khi có nhiều nguồn hướng dẫn

Trong phạm vi repo, Agent xử lý theo thứ tự:

1. Quy tắc an toàn/hệ thống của môi trường đang chạy.
2. Yêu cầu và phạm vi người dùng vừa giao trong task hiện tại.
3. Workflow này.
4. Các file EF-S liên quan.
5. Tài liệu Phase/feature liên quan.
6. Code, test, config và dependency manifest đang tồn tại.
7. `agent/lessonlearn.md` và changelog lịch sử.

`lessonlearn.md` là bài học lịch sử, **không phải tiêu chuẩn bắt buộc**. Một lesson cũ có thể đã lỗi thời. Nếu lesson mâu thuẫn Workflow/EF-S mới, Workflow/EF-S mới được ưu tiên.

### Khi tài liệu và code không khớp

Agent không được âm thầm chọn bên thuận tiện hơn.

- Muốn biết code **đang chạy thế nào** → đọc code/test/log.
- Muốn biết code **phải được thiết kế thế nào** → đọc Workflow + EF-S + yêu cầu hiện tại.
- Nếu khác nhau → báo rõ “chuẩn yêu cầu A, code hiện tại đang làm B”, rồi chỉ sửa khi task cho phép.

---

## 4. Phân quyền giữa người dùng và Agent

| Quyết định | Người dùng | Agent |
|---|---:|---:|
| Mục tiêu sản phẩm, ưu tiên, nghiệp vụ | Quyết định | Làm rõ và cảnh báo rủi ro |
| Kiến trúc lớn, đổi framework, đổi data contract | Duyệt | Phân tích và đề xuất |
| Thêm dependency, dịch vụ hoặc chi phí mới | Duyệt | Audit và đề xuất |
| Cách triển khai kỹ thuật nhỏ trong phạm vi đã duyệt | Không cần chọn từng dòng | Chủ động quyết định theo EF-S |
| Test, kiểm tra diff và báo cáo | Nhận kết quả dễ hiểu | Chịu trách nhiệm thực hiện |
| Phát hiện yêu cầu/kiến trúc có vấn đề | Quyết định sau khi được giải thích | Bắt buộc phải nói thật, không làm theo mù quáng |

Kế hoạch đã duyệt là **hợp đồng về mục tiêu, phạm vi và kết quả**, không phải mệnh lệnh phải bám từng chữ kể cả khi bằng chứng mới cho thấy plan sai. Nếu plan không còn đúng, Agent phải dừng phần bị ảnh hưởng, báo lý do và xin cập nhật plan.

---

## 5. Xác định loại task trước khi hành động

| Người dùng yêu cầu | Agent được phép làm |
|---|---|
| “Giải thích”, “review”, “kiểm tra”, “đánh giá” | Đọc và báo cáo; **không tự sửa** |
| “Chẩn đoán”, “tìm nguyên nhân” | Tìm root cause; **không tự implement fix** nếu chưa được yêu cầu |
| “Lập kế hoạch” | Tạo plan; **không sửa file** |
| “Sửa”, “triển khai”, “refactor”, “xây dựng” | Được sửa trong đúng phạm vi và phải kiểm chứng |
| “Chờ”, “theo dõi”, “monitor” | Theo dõi trạng thái; không tự mở rộng thành sửa hệ thống |

Nếu câu yêu cầu có cả “kiểm tra và sửa”, Agent được thực hiện cả hai. Nếu chỉ có “kiểm tra”, việc phát hiện lỗi không tự động cấp quyền sửa.

---

## 6. Bảng phân nhánh EF-S

Agent đọc theo **Progressive Disclosure — mở dần theo nhu cầu**, không mặc định đọc toàn bộ file.

### 6.1. Ba mức đọc để tiết kiệm token

| Mức | Khi dùng | Phải đọc |
|---|---|---|
| **A — Đúng mục** | Một câu hỏi/thay đổi nhỏ, ranh giới rõ | Phần header đầu file + đúng mục `§x.y` + checklist cuối file |
| **B — Nhiều mục liên quan** | Task chạm vài quy tắc trong cùng EF-S | Header + các mục liên quan + checklist |
| **C — Toàn file** | Module/kiến trúc mới, refactor lớn, audit toàn chuẩn, nội dung mâu thuẫn hoặc đọc mục nhỏ chưa đủ hiểu | Toàn bộ file |

Quy trình tìm đúng mục:

1. Dùng search lấy danh sách heading, ví dụ `rg -n "^## " EF-S-02_Error_Handling.md`.
2. Chọn mục theo bảng §6.3.
3. Đọc từ heading đó đến ngay trước heading cùng cấp tiếp theo.
4. Đọc checklist cuối file để không bỏ sót điều kiện bàn giao.
5. Nếu mục đang đọc dẫn sang mục/EF-S khác hoặc chưa đủ ngữ cảnh, mở rộng lên mức B/C.

Số dòng như `L35–50` chỉ là **tọa độ tạm thời tại thời điểm đọc**. Không hardcode line number vào workflow vì thêm một đoạn phía trên sẽ làm toàn bộ số dòng đổi. Routing phải dùng số mục ổn định như `EF-S-02 §2.6`.

Agent nên ghi ngắn trong plan/update:

```text
EF-S đã đọc: EF-S-02 §2.5–2.6 + §2.9 checklist; EF-S-04 §4.7.
```

Nhờ đó người dùng biết Agent đã dựa vào đúng phần nào, không cần Agent kể lại toàn bộ tài liệu.

### 6.2. Chọn file EF-S

| Khi task có nội dung này | Phải mở |
|---|---|
| Thêm/sửa import, module mới, circular import, nối Phase/UI/backend | [EF-S-00](./EF-S-00_Dependency_Direction.md) |
| Tạo/đổi/tách file, SRP, tên module, chọn folder/package | [EF-S-01](./EF-S-01_Data_Structure.md) |
| `try/except`, retry, batch failure, UI/Auto báo lỗi | [EF-S-02](./EF-S-02_Error_Handling.md) |
| Đọc/ghi JSON/Parquet, schema, checkpoint, snapshot, async, model artifact | [EF-S-03](./EF-S-03_Data_Pipeline.md) |
| Log, timing, batch summary, Auto chạy ngầm | [EF-S-04](./EF-S-04_Logging_Debug.md) |
| Helper, utility, duplication, shared code | [EF-S-05](./EF-S-05_Shared_Code.md) |
| `pip install`, dependency/version/license, chọn thư viện | [EF-S-06](./EF-S-06_Library_Catalog.md) |
| PyQt6 widget/thread/signal/UI flow | [EF-S-07](./EF-S-07_UI_Backend.md) |
| C# frontend — chỉ khi người dùng yêu cầu rõ | [EF-S-08](./EF-S-08_UI_Frontend.md) |
| Sửa logic, bug, formula, parser, validator hoặc thêm test | [EF-S-09](./EF-S-09_Testing_Strategy.md) |

Một task có thể cần nhiều nhánh. Ví dụ “thêm nút PyQt để chạy một pipeline mới và lưu JSON” cần ít nhất EF-S-00, 02, 03, 04, 07 và 09.

Không mở EF-S-08 chỉ vì task có chữ “frontend” nếu code đang là PyQt6.

### 6.3. Bản đồ mục nhỏ trong từng EF-S

| Cần biết | Đọc đúng mục |
|---|---|
| Tầng/module nào được gọi nhau | EF-S-00 §0.2–0.4 |
| Nối các Phase; Data/config; callback đi ngược | EF-S-00 §0.5–0.7 |
| Cấu trúc repo và chọn folder | EF-S-01 §1.2–1.3 |
| Đặt tên/header/chia vai trò/tách file | EF-S-01 §1.4–1.7 |
| Constant/import/package/hành vi cấm | EF-S-01 §1.8–1.10 |
| Phân loại lỗi và tầng nào bắt lỗi | EF-S-02 §2.1–2.3 |
| Batch/retry/chiến lược Phase/UI/Auto | EF-S-02 §2.5–2.8 |
| Ai ghi data và atomic write | EF-S-03 §3.2–3.4 |
| Output/data contract | EF-S-03 §3.5–3.6 |
| Checkpoint/async/retrain/retention | EF-S-03 §3.7–3.10 |
| Nơi lưu, format và level log | EF-S-04 §4.2–4.6 |
| Log lỗi/timing/bảo mật/rotation | EF-S-04 §4.7–4.11 |
| Có nên tạo shared code không | EF-S-05 §5.1–5.4 |
| Di chuyển/sửa shared code | EF-S-05 §5.5–5.7 |
| Package đang dùng hay chỉ dự kiến | EF-S-06 §6.1–6.4 |
| Chọn/cài/nâng/audit dependency | EF-S-06 §6.5–6.9 |
| UI được làm gì và chỉ gọi Manager | EF-S-07 §7.1–7.4 |
| PyQt thread/nút/lỗi/HTML/test | EF-S-07 §7.5–7.9 |
| C# hiện có được triển khai chưa | EF-S-08 §8.1 và §8.6 |
| Thiết kế C#/IPC/MVVM | EF-S-08 §8.2–8.5 |
| Tên/vị trí/loại test và logic cần test | EF-S-09 §9.1–9.4 |
| Missing data/mock/fixture/deterministic | EF-S-09 §9.5–9.9 |
| Quy trình bug fix và lệnh test | EF-S-09 §9.10–9.11 |

Checklist của mỗi file luôn là mục cuối (`§0.8`, `§1.11`, `§2.9`...); đọc checklist chỉ tốn ít dòng nhưng giúp tránh bỏ quên bước quan trọng.

### 6.4. Chọn tài liệu Phase theo phần việc

| Khi task thuộc phần này | Phải mở |
|---|---|
| Thu thập/làm sạch dữ liệu, danh sách mã, giá điều chỉnh, BCTC | [Phase 01 — Data Prep](./Phase_01_Data_Prep.md) |
| Chỉ báo kỹ thuật, công thức tài chính, feature đầu vào | [Phase 02 — Algorithms](./Phase_02_Algorithms.md) |
| Huấn luyện/chọn/đánh giá model ML | [Phase 03 — ML Training](./Phase_03_ML_Training.md) |
| Backtest, phí giao dịch, trượt giá, benchmark, stress test | [Phase 04 — Backtesting](./Phase_04_Backtesting.md) |
| Thu thập News, sentiment, nối News với BCTC | [Phase 05 — News](./Phase_05_News.md) |

- Tài liệu Phase cho biết **mục tiêu nghiệp vụ, đầu vào/đầu ra và cổng nghiệm thu** của phần việc; EF-S cho biết **code phải được thiết kế thế nào**. Task triển khai thường cần cả hai lớp.
- Dùng lại cách đọc tiết kiệm token ở §6.1: đọc header + đúng mục Phase liên quan + `Definition of Done`; chỉ đọc toàn file khi task rộng hoặc thông tin chưa đủ.
- [19-MONTH_PLANNING](../19-MONTH_PLANNING.md) là nguồn xác định mục tiêu và thời lượng roadmap. Tài liệu Phase diễn giải roadmap thành yêu cầu triển khai; code/test/config là bằng chứng về trạng thái thực tế.
- Nếu roadmap, Phase, EF-S và code không khớp, Agent phải nêu rõ từng bên đang nói gì; không được âm thầm chọn bản thuận tiện hơn.

---

## 7. Workflow bắt buộc từ lúc nhận task đến lúc bàn giao

### Bước 0 — Hiểu task và chốt “xong nghĩa là gì”

Agent phải xác định:

- Mục tiêu cuối cùng người dùng muốn đạt.
- Loại task theo §5.
- File/module/data nào nằm trong phạm vi.
- Kết quả nào được xem là đạt (điều kiện hoàn thành).
- Điều gì **không** nằm trong phạm vi.
- Có quyết định lớn nào cần người dùng duyệt trước không.

Task nhỏ không cần một bản plan dài. Task nhiều file, rủi ro dữ liệu, đổi kiến trúc hoặc thêm dependency cần plan rõ.

### Bước 1 — Kiểm tra hiện trạng trước khi sửa

Agent phải:

1. Kiểm tra instruction của repo nếu có.
2. Xem `git status` hoặc trạng thái file để biết thay đổi nào đã tồn tại.
3. Không ghi đè thay đổi của người dùng hoặc thay đổi không thuộc task.
4. Xác định file liên quan bằng search/tree.
5. Kiểm tra test, config, danh sách dependency và nơi gọi/nơi được gọi liên quan.

Nếu worktree đang có thay đổi, không được tự coi chúng là rác và xóa/reset.

### Bước 2 — Mở đúng EF-S và tài liệu Phase

Dùng §6.2 để chọn file, sau đó dùng §6.3 để chọn đúng mục. Mặc định bắt đầu ở mức A; chỉ nâng lên B/C theo điều kiện §6.1.

Nếu task thuộc một Phase cụ thể, dùng §6.4 để mở đúng tài liệu Phase và chỉ đọc phần liên quan theo cùng nguyên tắc tiết kiệm token.

Không được chỉ đọc tên mục rồi tự suy diễn. Phải đọc nội dung của mục đã chọn và checklist trước khi sửa.

### Bước 3 — Quét rồi đọc đủ ngữ cảnh

Quy trình:

```text
TÌM → ĐỌC → VẼ LUỒNG → XÁC NHẬN NGUYÊN NHÂN → MỚI SỬA
```

- Search để tìm file, function, import và caller.
- Đọc trọn function/class liên quan; đọc caller/callee, test và config nếu ảnh hưởng.
- “20–50 dòng” chỉ là điểm bắt đầu, không phải giới hạn. Nếu cần hiểu cả file nhỏ thì đọc cả file.
- Không sửa dựa trên một dòng tìm được mà chưa hiểu input → xử lý → output.
- Không dựa vào tên function để đoán nó đang làm gì.

### Bước 4 — Chứng minh nguyên nhân trước khi vá

Với bug, Agent phải mô tả được bốn ý:

1. **Hiện tượng:** cái gì đang sai.
2. **Kỳ vọng:** đúng ra phải xảy ra gì.
3. **Nguyên nhân gốc:** dòng/luồng nào tạo ra sai lệch.
4. **Ảnh hưởng:** còn module/data/test nào liên quan.

Nếu chưa xác định được nguyên nhân, tiếp tục đọc/chạy kiểm tra hoặc nói rõ đang thiếu bằng chứng. Không được “thử sửa đại xem sao” rồi gọi đó là root cause.

### Bước 5 — Chọn giải pháp đúng mức

Giải pháp phải là **thay đổi nhỏ nhất nhưng hoàn chỉnh**:

- Nhỏ nhất: không sửa phần không liên quan.
- Hoàn chỉnh: xử lý nguyên nhân, nhánh xảy ra lỗi và test liên quan; không chỉ làm thông báo lỗi biến mất.

Trước khi implement, kiểm tra:

- Có phá data contract/import direction không?
- Có tạo helper/dependency mới không?
- Có thay đổi hành vi UI/output không?
- Có migration/xóa/ghi đè dữ liệu không?
- Test nào sẽ chứng minh fix?

### Bước 6 — Plan và quyền phê duyệt

Agent có thể triển khai ngay khi người dùng đã yêu cầu sửa và thay đổi:

- nhỏ, cục bộ, dễ hoàn tác;
- không đổi kiến trúc/data contract/dependency;
- không có tác động ngoài repo.

Agent phải trình plan và xin duyệt trước nếu có:

- đổi kiến trúc hoặc ranh giới module lớn;
- package/service mới;
- thay schema/format/path dữ liệu;
- migration, xóa hoặc ghi đè dữ liệu quan trọng;
- thay UI behavior đáng kể ngoài yêu cầu;
- nhiều phương án có trade-off lớn;
- chi phí API/cloud hoặc hành động bên ngoài repo.

Nếu đang làm mà phát hiện plan sai, không âm thầm đổi plan. Báo: “Đã phát hiện X, vì vậy bước Y không còn an toàn; đề xuất đổi thành Z”.

### Bước 7 — Implement có kiểm soát

Trong lúc sửa:

- Mỗi edit phải giải thích được nó phục vụ mục tiêu nào.
- Không refactor/rename/reformat phần không liên quan “tiện tay”.
- Không thêm notification, text UI, dependency, log hoặc feature ngoài phạm vi nếu chúng không cần cho kết quả đúng.
- Giữ style hiện tại trừ khi style đó vi phạm EF-S trực tiếp trong phần đang sửa.
- Không copy-paste một bản logic mới nếu có nguồn sự thật phù hợp.
- Không dùng hardcode/path tuyệt đối/giá trị giả để ép code chạy.
- Cập nhật test và tài liệu khi contract/hành vi thật sự đổi.
- Không chỉnh test để test chấp nhận một kết quả sai.

### Bước 8 — Kiểm chứng theo rủi ro

Agent phải chạy mức kiểm tra phù hợp:

1. Test nhỏ đúng phần vừa sửa.
2. Test module/Phase liên quan.
3. Import/compile/lint/type check nếu dự án có.
4. Kiểm tra output/schema/log/UI flow nếu liên quan.
5. Xem toàn bộ diff cuối cùng.

Với công thức tài chính/ML/data:

- test “không crash” là chưa đủ;
- phải kiểm tra invariant, sample chuẩn hoặc cross-check với nguồn/thư viện tin cậy;
- kiểm tra NaN, timezone, duplicate, dữ liệu thiếu và giá trị biên khi liên quan.

Nếu không thể chạy test:

- ghi rõ test nào **chưa chạy**;
- lý do cụ thể;
- phần nào mới chỉ được kiểm tra bằng đọc code;
- cách cần làm để xác minh tiếp.

Không được đổi “không chạy được” thành “khả năng cao là ổn”.

### Bước 9 — Tự review toàn bộ phần đã thay đổi như một người khác

Trước khi bàn giao, Agent phải kiểm tra:

- Danh sách thay đổi (`diff`) chỉ chứa file trong phạm vi?
- Có vô tình xóa/đổi code của người dùng?
- Có debug print, temp file hoặc comment thử nghiệm?
- Có secret/token/path máy cá nhân?
- Error có bị nuốt hoặc biến thành success?
- Test có bị nới lỏng để qua?
- Import, data, log, UI và test có đúng EF-S đã mở?
- Tài liệu nói đúng code mới?

### Bước 10 — Báo cáo minh bạch

Báo cáo cuối phải có:

1. **Kết quả:** người dùng nhận được gì.
2. **Đã thay đổi:** file/luồng chính, nói bằng ngôn ngữ dễ hiểu.
3. **Đã kiểm chứng:** lệnh/test/check cụ thể và kết quả.
4. **Chưa kiểm chứng:** phần nào chưa test được và lý do.
5. **Vấn đề còn lại:** bug/rủi ro ngoài phạm vi chưa sửa.
6. **Sai khác với plan:** nếu có, phải nói rõ và lý do.

Không cần kể toàn bộ quá trình dùng tool. Chỉ báo bằng chứng giúp người dùng hiểu kết quả đáng tin tới đâu.

---

## 8. Các hành vi bị cấm

### 8.1. Tự chế yêu cầu hoặc dữ liệu

Agent không được:

- tự thêm feature, màn hình, field, schema, API hoặc business rule chưa được yêu cầu/duyệt;
- bịa response API, số liệu tài chính, test result hoặc trạng thái package;
- biến placeholder/mock thành dữ liệu production mà không ghi rõ;
- đoán file/module tồn tại mà chưa kiểm tra repo;
- ghi kiến trúc tương lai như thể đã triển khai.

### 8.2. “Xào nấu” code

Agent không được:

- viết lại cả file chỉ vì thích style khác nếu task chỉ sửa một bug nhỏ;
- đổi tên hàng loạt, format cả repo hoặc di chuyển module ngoài plan;
- trộn một refactor lớn vào commit/fix nhỏ;
- thay giải pháp đã duyệt bằng một pattern khác mà không báo;
- tạo nhiều abstraction/class/helper không có nhu cầu thật.

### 8.3. Giấu lỗi

Các mẫu sau bị cấm nếu dùng để làm lỗi biến mất:

```python
except Exception:
    pass
```

```python
except Exception:
    return {}       # Caller tưởng có kết quả rỗng hợp lệ
```

```python
await asyncio.gather(*tasks, return_exceptions=True)
# Sau đó không kiểm tra exception
```

Cũng bị cấm:

- log lỗi rồi vẫn trả trạng thái success;
- gửi lỗi qua signal `finished/succeeded`;
- bỏ item lỗi mà không đưa vào failure summary;
- làm mất traceback tại nơi cuối cùng chịu trách nhiệm ghi lỗi fatal;
- Task Scheduler nhận exit code 0 khi tác vụ thực sự fail.

### 8.4. Sửa lấp liếm để test/chương trình “xanh”

Agent không được:

- hardcode output đúng cho một sample;
- giảm ngưỡng/validation chỉ để test pass;
- xóa, skip hoặc sửa test đang bắt đúng bug;
- catch exception rồi trả default để UI hết báo lỗi;
- comment out feature gây lỗi thay vì sửa nguyên nhân;
- thêm delay/retry vô hạn để che race condition;
- sửa data đầu vào production để né bug của code;
- nói “fix” khi chỉ đổi message/log.

Workaround tạm thời chỉ được dùng khi:

- người dùng đồng ý;
- được gắn nhãn rõ là temporary;
- ghi giới hạn/rủi ro;
- có bước xử lý dứt điểm tiếp theo.

### 8.5. Thiếu minh bạch

Agent không được:

- nói test pass khi chưa chạy;
- nói “đã kiểm tra toàn bộ” khi chỉ đọc một phần;
- giấu file đã sửa hoặc thay đổi ngoài plan;
- trình bày suy đoán như sự thật;
- giấu test fail/pre-existing issue;
- tự nhận lỗi là “do môi trường” khi chưa có bằng chứng;
- báo hoàn thành khi còn vướng mắc trực tiếp làm điều kiện hoàn thành chưa đạt.

### 8.6. Hành động ngoài phạm vi hoặc khó hoàn tác

Không tự làm nếu người dùng chưa yêu cầu/duyệt:

- xóa/migrate/ghi đè data quan trọng;
- cài/nâng package;
- đổi Task Scheduler/system setting;
- commit, push, tạo PR hoặc publish;
- gọi API có chi phí/tác dụng ngoài để “test thử”;
- gửi message/email hoặc thay đổi dịch vụ bên ngoài;
- reset/checkout làm mất thay đổi trong worktree.

---

## 9. Xử lý phát hiện ngoài phạm vi

| Phát hiện | Cách xử lý |
|---|---|
| Nhỏ, trực tiếp cần để hoàn thành task, dễ hoàn tác | Được sửa cùng task và báo rõ |
| Có liên quan nhưng không chặn kết quả | Không sửa; ghi vào “vấn đề còn lại” |
| Cần đổi kiến trúc/dependency/schema/data | Dừng phần đó, trình bày và xin duyệt |
| Có nguy cơ mất data, lộ secret hoặc kết quả tài chính sai nghiêm trọng | Dừng, cảnh báo ngay, không tiếp tục mù quáng |
| Test cũ fail không liên quan | Xác minh mức có thể; không sửa tiện tay và không giấu |

Không dùng câu “tiện thể em sửa luôn” để mở rộng phạm vi.

---

## 10. Giả định và câu hỏi

Agent được tự đưa ra giả định khi nó:

- nhỏ và dễ hoàn tác;
- không thay đổi output/business behavior đáng kể;
- phù hợp code/EF-S hiện tại;
- được nêu rõ trong báo cáo nếu quan trọng.

Agent phải hỏi trước khi giả định liên quan tới:

- công thức/logic tài chính;
- xóa/ghi đè/migrate data;
- framework, dependency hoặc service mới;
- UI behavior người dùng sẽ thấy;
- format/schema mà Phase khác phụ thuộc;
- chi phí hoặc hệ thống bên ngoài;
- hai cách hiểu dẫn tới hai kết quả khác nhau đáng kể.

Không hỏi cho có nếu có thể tự tìm câu trả lời chắc chắn trong repo.

---

## 11. Definition of Done — Khi nào được gọi là “xong”?

Một task sửa/triển khai chỉ được gọi là hoàn thành khi:

- [ ] Mục tiêu và điều kiện hoàn thành đã đạt.
- [ ] Không có thay đổi ngoài phạm vi chưa được giải thích.
- [ ] Root cause đã được xử lý nếu task là bug fix.
- [ ] EF-S liên quan đã được tuân thủ.
- [ ] Test/check phù hợp đã chạy và có kết quả thật.
- [ ] Diff cuối đã được tự review.
- [ ] Không giấu exception, không fake success, không hardcode lấp liếm.
- [ ] Không để secret/debug/temp artifact.
- [ ] Tài liệu/test đã cập nhật nếu contract thay đổi.
- [ ] Phần chưa kiểm chứng và rủi ro còn lại đã báo rõ.

Nếu một mục bắt buộc chưa đạt, trạng thái phải là **chưa hoàn thành**, **blocked** hoặc **cần xác minh thêm** — không được gọi là xong.

---

## 12. Mẫu báo cáo ngắn cho Agent

### Khi bắt đầu task có sửa file

```text
Mục tiêu: ...
Phạm vi: ...
EF-S sẽ dùng: ...
Kiểm tra dự kiến: ...
```

### Khi phát hiện plan không còn đúng

```text
Đã phát hiện: ...
Vì sao ảnh hưởng plan: ...
Nếu tiếp tục plan cũ, rủi ro là: ...
Đề xuất: ...
Cần người dùng duyệt: ...
```

### Khi bàn giao

```text
Kết quả: ...
Đã thay đổi: ...
Đã kiểm chứng: ...
Chưa kiểm chứng: ...
Vấn đề còn lại/rủi ro: ...
```

---

> **Nhắc cuối cho Agent:** Người dùng không cần một câu trả lời nghe tự tin. Người dùng cần kết quả đúng, bằng chứng thật và lời báo cáo trung thực về những gì còn chưa chắc chắn.
