# Chương 6 — EF-S-06: Library Catalog (Thư viện được phép dùng)

> **Trạng thái:** ACTIVE — phải cập nhật cùng dependency manifest.
>
> **Agent phải đọc file này khi:** muốn `pip install`, thêm một import bên thứ ba, chọn thư viện cho indicator/ML/API/UI hoặc nâng version dependency.
>
> **Mục tiêu:** Biết thư viện nào đang dùng thật, thư viện nào chỉ đang cân nhắc và không tự ý đưa dependency lạ vào dự án.

## 6.1. Ba trạng thái thư viện

| Trạng thái | Ý nghĩa | Agent được làm gì? |
|---|---|---|
| **CURRENT** | Code hiện tại đang import/dùng | Được dùng đúng phạm vi; thêm use case mới vẫn phải kiểm tra compatibility |
| **APPROVED** | Đã được chủ dự án chọn nhưng có thể chưa dùng | Được triển khai trong Phase/use case đã duyệt |
| **CANDIDATE** | Mới là phương án để so sánh | Không được tự cài/chốt; phải đề xuất và xin duyệt |

Không gọi một package là “đang dùng” chỉ vì nó từng được nhắc trong kế hoạch hoặc đang có sẵn trên máy.

## 6.2. Thư viện CURRENT của code hiện tại

Snapshot kiểm tra ngày **2026-08-09**. Version chính xác phải lấy từ dependency manifest/lock file sau khi được tạo, không lấy bảng này làm lock file.

| Package/import | Dùng cho | Phạm vi hiện tại | Ghi chú |
|---|---|---|---|
| `pandas` | DataFrame, Parquet | Phase 1, News/helper | Thư viện dữ liệu chính |
| `numpy` | Kiểm tra/tính số | Validator và test | Không tự viết lại phép vector hóa đã có |
| `requests` | HTTP đồng bộ | FireAnt | Luôn có timeout và error handling |
| `vnstock` | Dữ liệu chứng khoán VN | Phase 1 | Giấy phép tùy chỉnh cho cá nhân/nghiên cứu, phi thương mại; cần attribution và re-audit nếu dự án thương mại |
| `feedparser` | Parse RSS/Atom | News | Không parse RSS bằng regex |
| `beautifulsoup4` (`bs4`) | Làm sạch HTML từ RSS | News | Chỉ dùng cho HTML parsing/sanitizing phù hợp |
| `google-genai` (`from google import genai`) | Gemini API | News AI client | Đây là SDK hiện hành; không dùng package cũ `google-generativeai` cho code mới |
| `python-dotenv` | Đọc `.env` | API clients | Secret nằm trong `System/.env`, không commit/log |
| `PyQt6` | Desktop UI | `IDE_UI/` | Có GPLv3 hoặc commercial license; phải xem lại license trước khi phân phối sản phẩm đóng nguồn |
| `pyarrow` hoặc `fastparquet` | Parquet engine cho pandas | Data I/O | Chọn/pin engine rõ trong manifest để kết quả cài đặt tái hiện được |

Thư viện chuẩn Python như `logging`, `json`, `pathlib`, `unittest.mock` không cài bằng pip.

## 6.3. Development dependency

| Package | Trạng thái | Dùng cho |
|---|---|---|
| `pytest` | **APPROVED nhưng chưa có trong môi trường audit** | Chạy unit/integration test |

Agent phải thêm dependency dev vào manifest trước khi coi test suite là có thể chạy. Không ghi “test đã pass” nếu pytest chưa cài hoặc test chưa thực sự chạy.

## 6.4. Thư viện cho Phase tương lai

Các package dưới đây là **CANDIDATE**, chưa được xem là dependency của dự án:

| Bài toán | Candidate | Điều phải quyết định trước khi dùng |
|---|---|---|
| Technical indicators | `pandas-ta`, `pandas-ta-classic`, `TA-Lib` | Độ chính xác, license, version Python, tốc độ và cách cài trên Windows |
| ML cơ bản | `scikit-learn` | Split/time-series validation, leakage, reproducibility |
| Gradient boosting | `xgboost`, `lightgbm`, `catboost` | Chỉ cài model thật sự cần; kiểm tra tương thích Python/CPU/GPU |
| AutoML | `pycaret` | So sánh với pipeline scikit-learn trực tiếp; pin major version vì API có thể thay đổi lớn |
| Async HTTP | `aiohttp` hoặc `httpx` async | Chỉ dùng khi API/rate limit và pipeline thật sự hưởng lợi từ async |

Agent không được biến danh sách candidate thành một lệnh cài hàng loạt.

## 6.5. Quy tắc chọn thư viện

Trước khi tự code một tính năng phổ biến, Agent kiểm tra theo thứ tự:

1. Python standard library đã làm được chưa?
2. Dự án đã có helper/module phù hợp chưa?
3. Một package CURRENT đã làm được chưa?
4. Nếu cần package mới, lợi ích có lớn hơn chi phí dependency không?

“Đừng phát minh lại bánh xe” không có nghĩa luôn chọn thư viện. Một hàm 10 dòng ổn định có thể tốt hơn thêm package lớn; ngược lại, parser, cryptography, ML algorithm hoặc chuẩn file phức tạp nên ưu tiên thư viện đã được kiểm chứng.

## 6.6. PyCaret và state

Không có luật kỹ thuật rằng “nhiều file import PyCaret chắc chắn conflict”. PyCaret có Experiment object/API để quản lý state.

Tuy vậy, nếu dự án chọn PyCaret, nên có một entry/facade ML rõ như `E_arena_manager.py` để:

- tập trung config và random seed;
- tránh mỗi file tự setup experiment khác nhau;
- lưu model/metric/metadata nhất quán;
- dễ thay PyCaret bằng giải pháp khác.

Đây là quyết định kiến trúc để đơn giản hóa, không phải vì import ở file thứ hai tự động làm hỏng state.

## 6.7. Dependency manifest là nguồn sự thật

Trước khi thêm/nâng package, Agent phải cập nhật một nguồn version chính thức:

- giai đoạn hiện tại: `requirements.txt` + `requirements-dev.txt`; hoặc
- khi chuẩn hóa package: `pyproject.toml` + lock file phù hợp.

Không ghi version ví dụ cũ trong tài liệu rồi coi đó là version dự án. Manifest phải pin version đã test; lock file/hashes được khuyến nghị khi workflow cài đặt đã ổn định.

Mỗi lần nâng major version phải đọc migration guide và chạy test liên quan.

## 6.8. Security và license audit trước khi cài

Checklist bắt buộc:

- [ ] Đúng tên package chính thức trên PyPI/repo, tránh package giả gần giống tên?
- [ ] Maintainer/repo/release history có hợp lý?
- [ ] License có phù hợp dự án cá nhân và kế hoạch phân phối?
- [ ] Version hỗ trợ Python đang dùng?
- [ ] Package có network, telemetry, subprocess hoặc ghi file ngoài project không?
- [ ] Nó yêu cầu API key để làm gì và secret được lưu ở đâu?
- [ ] Dependency kéo theo có quá lớn hoặc có xung đột không?
- [ ] Đã kiểm tra advisory/vulnerability bằng công cụ phù hợp khi có thể?
- [ ] Đã chạy test/smoke test sau khi cài?
- [ ] Đã cập nhật manifest và tài liệu CURRENT/APPROVED/CANDIDATE?

Số GitHub stars chỉ là tín hiệu phụ, không phải bằng chứng an toàn.

## 6.9. Những hành vi bị cấm

- Tự ý `pip install` package chưa được duyệt trong lúc sửa một lỗi không liên quan.
- Dùng `google-generativeai` cho code mới thay vì `google-genai`.
- Ghi `vnstock` là MIT hoặc dùng cho thương mại mà chưa kiểm tra giấy phép hiện hành.
- Thêm tất cả model ML “để dành”.
- Dùng version `latest` không pin trong môi trường production/scheduled task.
- Ghi package là CURRENT chỉ vì nó có trên máy nhưng code không sử dụng.
- Tự viết thuật toán tài chính rồi khẳng định đúng mà không có dữ liệu chuẩn/cross-check/test.

## 6.10. Checklist cho Agent

- [ ] Package đang là CURRENT, APPROVED hay CANDIDATE?
- [ ] Có thể giải quyết bằng standard library/module sẵn có không?
- [ ] Chủ dự án đã duyệt dependency mới chưa?
- [ ] Đã kiểm tra license, Python version và hành vi network/file/telemetry?
- [ ] Import/package name là SDK hiện hành?
- [ ] Đã cập nhật manifest/lock file?
- [ ] Đã chạy test phù hợp sau khi cài/nâng version?
- [ ] Đã cập nhật bảng này nếu trạng thái package thay đổi?
