# E_CYBER-FINANCIAL STANDARDS — Danh sách chờ triển khai

> **Mục đích:** Chống quên. File này liệt kê 5 bộ tiêu chuẩn dự án CÓ THỂ cần trong tương lai.
> **Cập nhật lần cuối:** 2026-07-04
> **Tiêu chuẩn đã hoàn thành:** EF-S-00 (SRP) → [srp_principles.md](file:///c:/Users/HP/Documents/E_CYBER-FINANCIAL/E_Pinciples/srp_principles.md)

---

## Quy ước mức độ ưu tiên

| Ký hiệu | Nghĩa | Khi nào làm |
|---|---|---|
| 🔴 | Nên làm sớm | Trong vòng 1-2 tuần |
| 🟡 | Nên có trước phase tiếp theo | Trước Phase 3 (tháng 5) |
| 🟢 | Chưa cần gấp | Khi dự án mở rộng |
| ✅ | Đã đủ, không cần thêm | — |

---
---

# EF-S-01: ERROR HANDLING STRATEGY
## "Quy tắc ứng phó sự cố"
### Ưu tiên: 🟡 Trung bình — Làm trước Phase 3

---

### Đang có gì rồi?

SRP đã quy định error handling **riêng cho từng phase** — đây là nền tảng tốt:

| Phase | Chiến lược | Ý nghĩa |
|---|---|---|
| Phase 1 | Retry + Resume | Lỗi → thử lại → bỏ qua mã đó → cào tiếp |
| Phase 2 | Strict — Crash ngay | Sai số → dừng ngay, không tha |
| Phase 3 | Graceful + Checkpoint | Lưu tiến trình → crash vẫn resume được |
| Phase 4 | Zero Tolerance | Giống Phase 2 — sai giao dịch = dừng |
| Phase 5 | Resilient | 1 nguồn báo chết → bỏ qua, cào nguồn khác |

### Còn thiếu gì?

**1. Format log lỗi chung** — Hiện mỗi module ghi lỗi 1 kiểu:
```python
# Module A: print("Lỗi!")
# Module B: logging.error("[2027-01-15] Lỗi: ...")
# Module C: debug_logs.append(f"❌ [{url}] Lỗi: {e}")
```
→ Cần 1 format thống nhất để khi đọc log không bị loạn.

**2. Danh sách hành vi tuyệt đối cấm:**
```python
# ❌ TUYỆT ĐỐI CẤM — bắt lỗi rồi im lặng bỏ qua ("nuốt lỗi")
except Exception:
    pass

# ❌ TUYỆT ĐỐI CẤM — bắt lỗi, bỏ qua, không log
except Exception:
    continue

# ✅ PHẢI LÀM — bắt lỗi, ghi log, rồi mới quyết định tiếp
except Exception as e:
    logging.error(f"[{module_name}] {e}")
    # rồi mới continue hoặc raise tùy strategy
```

### Khi nào làm?

- [ ] Khi gặp tình huống "code chạy sai mà không biết lỗi ở đâu"
- [ ] Hoặc trước khi bắt đầu Phase 3 (training dài hàng giờ, crash = mất trắng)

---
---

# EF-S-02: LOGGING CONVENTION
## "Quy tắc ghi nhật ký"
### Ưu tiên: 🟡 Trung bình — Làm trước Phase 3

---

### Đang có gì rồi?

- SRP §2.2: "PHẢI ghi log ra file" (cho Auto/)
- SRP §3.4: "Log chi tiết mã nào thành công/thất bại"
- Thư mục `Log_Debug/` đã tồn tại

### Còn thiếu gì?

| Câu hỏi | Đề xuất |
|---|---|
| **Log lưu ở đâu?** | `Log_Debug/{module}_{YYYY-MM-DD}.log` |
| **Format 1 dòng log?** | `[2027-01-15 08:30:22] [ERROR] [news_scraper] Timeout khi cào VNExpress` |
| **Khi nào xóa log cũ?** | Giữ 30 ngày gần nhất |
| **Dùng `print()` hay `logging`?** | `print()` khi dev/test trên IDE. `logging` khi chạy Auto/ ngầm |
| **Có cần log rotation?** | Có — khi 1 file log vượt 10MB thì tách file mới |

### Mẫu format chuẩn (nếu làm):

```
[TIMESTAMP]  [LEVEL]  [MODULE]  Message

Ví dụ:
[2027-01-15 08:30:22] [INFO]    [data_collector]  Bắt đầu cào VNM...
[2027-01-15 08:30:23] [INFO]    [data_collector]  VNM: 3248 dòng, OK
[2027-01-15 08:30:24] [WARNING] [data_collector]  HPG: Retry lần 2/3 (timeout)
[2027-01-15 08:30:25] [ERROR]   [data_collector]  HPG: Thất bại sau 3 lần retry
[2027-01-15 08:31:00] [INFO]    [data_collector]  Hoàn thành: 1795/1800 mã OK, 5 lỗi
```

### Khi nào làm?

- [ ] Trước Phase 3 (training chạy hàng giờ, cần log để biết tiến trình + debug)
- [ ] Khi auto_news.py hoặc auto_sync.py gặp lỗi mà không biết tại sao

---
---

# EF-S-03: GIT & VERSION CONTROL
## "Quy tắc sao lưu + quản lý phiên bản"
### Ưu tiên: 🔴 Sửa .gitignore ngay — Phần còn lại chưa cần

---

### Đang có gì rồi?

| Hạng mục | Trạng thái |
|---|---|
| Git repo + push GitHub | ✅ Có |
| auto_sync.py (Task Scheduler) | ✅ Chạy tự động mỗi đêm |
| .gitignore | ⚠️ Có nhưng thiếu 3 dòng |
| Commit thủ công khi xong feature | ❌ Chưa có thói quen |

### Cần sửa ngay: `.gitignore`

Thêm 3 dòng:
```
News_JSON/
Models/
*.pkl
```

**Lý do:** Git dùng cho **code** (file text nhỏ, thay đổi từng dòng). Data files (JSON, parquet, pkl) là file **binary lớn** — Git không giỏi xử lý loại này. Push lên GitHub tốn dung lượng + chậm sync.

### Data sync lên Google Drive

> **Hoàn toàn nên làm.** Drive (nhất là Google One Ultra vài TB) là nơi lý tưởng để lưu:
> - `News_JSON/` — hàng trăm file JSON mỗi ngày
> - `Data_Main/` — ~1800 file parquet
> - `Models/` — file .pkl lớn

**Cách đơn giản nhất:** Dùng Google Drive desktop app (đã cài sẵn trên Windows) → đặt folder data trong Drive hoặc dùng symlink. Hoặc viết thêm 1 script `auto_backup_data.py` trong `Auto/` để copy data quan trọng lên Drive folder.

### Commit thủ công — "Walkthrough" cho code

> **Đúng — nó giống walkthrough.** Mỗi khi hoàn thành 1 feature lớn:
> 1. Mở terminal
> 2. `git add .`
> 3. `git commit -m "feat: Hoàn thành data_cleaner module - làm sạch null values + so sánh vnstock vs FireAnt"`
> 4. `git push`
>
> Message nên theo format: `"feat: Mô tả ngắn gọn cái vừa làm xong"`
> Auto-sync vẫn chạy song song để bắt những thay đổi nhỏ.

### Khi nào làm?

- [x] Sửa `.gitignore` → **NGAY**
- [ ] Tập commit thủ công khi xong feature → Dần dần tạo thói quen
- [ ] Sửa `auto_sync.py` hardcoded path → Ngày mai khi refactor

---
---

# EF-S-04: DATA GOVERNANCE & VERSIONING
## "Quy tắc quản lý kho dữ liệu"
### Ưu tiên: 🟢 Thấp — Làm trước Phase 3

---

### Đang có gì rồi?

SRP đã có Output Contract cho mỗi phase:
- Data thô (parquet) → `Data_Main/` — immutable
- News JSON → `News_JSON/` — theo ngày
- Model .pkl → `Phase 3/Models/` — theo experiment

### Còn thiếu gì?

**1. Data versioning** — Khi cào lại data mới, data cũ xử lý thế nào?

```
Tình huống: Tháng 1 cào 1800 mã. Tháng 6 cào lại (vì vnstock update API).
Data tháng 1 → xóa? giữ? lưu ở đâu?

Đề xuất: Data_Main/v1/ (tháng 1), Data_Main/v2/ (tháng 6)
Hoặc đơn giản hơn: backup lên Drive trước khi cào lại
```

**2. Data lineage** — Model X được train từ data nào?

```
Nôm na: "Cuốn sổ ghi chép nguyên liệu"
- exp_003_blend_long_v2.pkl
  - Data: cào ngày 15/01/2027, v1
  - Features: 47 TA indicators + sentiment (tháng 12/2026)
  - Config: training_config_long_v2.yaml

→ Nếu không ghi lại, 6 tháng sau không ai nhớ model này train từ cái gì
→ experiment_registry.json trong Phase 3 đã giải quyết 1 phần vấn đề này
```

**3. Backup** — Data không nằm trên Git, vậy backup ở đâu?

```
Đề xuất: Google Drive (đã có vài TB)
Tần suất: Sau mỗi lần cào data mới hoặc train model mới
```

### Khi nào làm?

- [ ] Trước Phase 3 — khi bắt đầu train model, cần biết "model này train từ data nào"
- [ ] Khi cào lại data lần 2 — cần quyết định giữ hay xóa data cũ

---
---

# EF-S-05: SECURITY & SECRETS
## "Quy tắc bảo mật"
### Ưu tiên: ✅ ĐÃ ĐỦ — Không cần thêm

---

### Đang có gì?

| Hạng mục | Trạng thái | Chi tiết |
|---|---|---|
| API keys trong `.env` | ✅ | SRP §1.4 quy định rõ |
| `.env` excluded khỏi Git | ✅ | `.gitignore` đã có |
| Warning không để token trong config | ✅ | SRP §3.5 `[!WARNING]` |

### Cần thêm gì?

**Không cần.** Đối với dự án 1 người, `.env` + `.gitignore` là đủ.

Các cơ chế phức tạp hơn (vault, key rotation, encryption) chỉ cần khi:
- Deploy lên server public
- Có 2+ người truy cập code
- API key có quyền thanh toán/giao dịch thật

---
---

# 📦 PACK NHẮC NHỞ ĐẶC BIỆT — BCTC DATA

> [!CAUTION]
> **ĐỘ NGHIÊM: CAO.** Cần giải quyết TRƯỚC khi bắt tay vào làm việc với BCTC.
> **Dự kiến:** Ngày mai (2026-07-05) sau khi refactor xong.

### Vấn đề

Planning nói: *"Kết hợp data news vào bộ xương của BCTC"* — nhưng BCTC data **chưa có chỗ** trong kiến trúc hiện tại:

1. **Nguồn BCTC lấy từ đâu?** vnstock có API BCTC không? Hay cào từ nguồn khác?
2. **Lưu ở đâu?** `Data_Main/` hiện chỉ có `From_vnstock/` và `From_FireAnt/` — cần thêm folder cho BCTC
3. **Format?** Parquet? CSV? JSON? → Ảnh hưởng đến cách Phase 3 `data_loader.py` đọc
4. **Anchor builder thuộc phase nào?** Module này kết nối News (ngày) với BCTC (quý) — nó thuộc Phase 5 hay Phase 3?
5. **Output là gì?** File mapping (news_date → bctc_quarter)? Hay transform function mà feature_builder gọi inline?

### Checklist trước khi code BCTC

- [ ] Xác định nguồn BCTC data
- [ ] Thêm folder `Data_Main/From_BCTC/` (hoặc tên khác) vào SRP §1.4
- [ ] Quyết định `anchor_builder.py` thuộc Phase 5 hay Phase 3
- [ ] Viết output contract cho BCTC data (format, naming, immutability)
- [ ] Cập nhật SRP §7.2 (thêm BCTC vào dependency flow)
