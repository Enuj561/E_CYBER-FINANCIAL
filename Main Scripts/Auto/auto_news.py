"""
Auto News Collector - Chạy lúc 21:00 hàng ngày qua Task Scheduler.
Logic:
    1. Scan folder News_JSON, tìm file gần nhất → so sánh với ngày hiện tại.
    2. Nếu phát hiện ngày bị thiếu (do máy tắt) → backfill tin tức cho các ngày đó trước.
    3. Kiểm tra file hôm nay đã có chưa → nếu chưa thì cào tin hôm nay.
    4. Ghi log vào news_log.txt để tiện theo dõi.
"""

import os
import sys
import json
import datetime
import re

# Fix encoding cho Task Scheduler chạy ngầm
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Thêm project root vào sys.path để import được news_scraper
PROJECT_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"
sys.path.insert(0, os.path.join(PROJECT_DIR, "Main Scripts"))

from News.news_scraper import fetch_news, RSS_FEEDS

NEWS_JSON_DIR = os.path.join(PROJECT_DIR, "News_JSON")
LOG_FILE = os.path.join(PROJECT_DIR, "Main Scripts", "Auto", "news_log.txt")

# Tất cả lĩnh vực cần cào
ALL_CATEGORIES = ["Vĩ mô & Tiền tệ", "Thị trường & Đầu tư", "Công nghệ"]


def get_filename_for_date(target_date):
    """Tạo tên file theo format: News_dd_mm_yy.json cho một ngày bất kỳ."""
    return f"News_{target_date.strftime('%d_%m_%y')}.json"


def get_today_filename():
    """Tạo tên file theo format: News_dd_mm_yy.json cho ngày hôm nay."""
    return get_filename_for_date(datetime.date.today())


def file_already_exists(filename):
    """Kiểm tra file đã tồn tại trong folder News_JSON chưa."""
    return os.path.exists(os.path.join(NEWS_JSON_DIR, filename))


def find_missing_dates():
    """
    Scan folder News_JSON, tìm file có ngày gần nhất.
    So sánh với ngày hôm nay → trả về danh sách ngày bị thiếu.
    
    Returns:
        list[datetime.date]: Danh sách các ngày bị thiếu (đã sắp xếp tăng dần).
                             Rỗng nếu không thiếu ngày nào.
    """
    os.makedirs(NEWS_JSON_DIR, exist_ok=True)
    
    # Parse tên file → lấy danh sách ngày đã có
    pattern = re.compile(r"^News_(\d{2})_(\d{2})_(\d{2})\.json$")
    existing_dates = []
    
    for filename in os.listdir(NEWS_JSON_DIR):
        match = pattern.match(filename)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                file_date = datetime.date(2000 + year, month, day)
                existing_dates.append(file_date)
            except ValueError:
                continue  # Bỏ qua file có tên không hợp lệ
    
    if not existing_dates:
        return []  # Không có file nào → không biết bắt đầu từ đâu, bỏ qua
    
    # Scan TẤT CẢ ngày từ file sớm nhất → hôm nay để tìm gap
    # (bao gồm cả gap ở giữa, không chỉ gap ở cuối)
    existing_dates_set = set(existing_dates)
    earliest_date = min(existing_dates)
    today = datetime.date.today()
    
    missing = []
    current = earliest_date + datetime.timedelta(days=1)
    while current < today:
        if current not in existing_dates_set:
            filename = get_filename_for_date(current)
            if not file_already_exists(filename):
                missing.append(current)
        current += datetime.timedelta(days=1)
    
    return missing


def collect_all_news(target_date=None):
    """
    Cào toàn bộ tin tức từ tất cả nguồn báo, tất cả lĩnh vực.
    Giống như user chọn 'Tổng hợp' cho từng lĩnh vực rồi gộp lại.
    
    Args:
        target_date: (Optional) datetime.date - Ngày cần lấy tin.
                     Nếu None → dùng logic realtime (datetime.now()).
    """
    all_news = {}
    all_debug = []
    total_articles = 0

    for category in ALL_CATEGORIES:
        news_items, debug_logs = fetch_news("Tổng hợp", category, target_date=target_date)
        
        # Loại bỏ bài trùng lặp dựa trên link
        seen_links = set()
        unique_items = []
        for item in news_items:
            if item["link"] not in seen_links:
                seen_links.add(item["link"])
                unique_items.append(item)
        
        all_news[category] = unique_items
        all_debug.extend(debug_logs)
        total_articles += len(unique_items)

    return all_news, all_debug, total_articles


def save_to_json(data, filename):
    """Lưu data vào file JSON trong folder News_JSON."""
    os.makedirs(NEWS_JSON_DIR, exist_ok=True)
    filepath = os.path.join(NEWS_JSON_DIR, filename)
    
    # Thêm metadata vào file JSON
    output = {
        "metadata": {
            "collected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_articles": sum(len(articles) for articles in data.values()),
            "categories": list(data.keys()),
            "sources": list(RSS_FEEDS.keys())
        },
        "news": data
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return filepath


def write_log(message):
    """Ghi log ra console và file."""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n" + "-" * 50 + "\n")


def backfill_missing_days(missing_dates):
    """
    Backfill tin tức cho các ngày bị thiếu.
    
    Args:
        missing_dates: list[datetime.date] - Danh sách ngày cần backfill.
    
    Returns:
        str: Log message tổng hợp.
    """
    log_msg = f"🔄 Phát hiện {len(missing_dates)} ngày bị thiếu: " \
              f"{', '.join(d.strftime('%d/%m/%Y') for d in missing_dates)}\n"
    
    for target_date in missing_dates:
        filename = get_filename_for_date(target_date)
        date_str = target_date.strftime('%d/%m/%Y')
        
        try:
            all_news, debug_logs, total_articles = collect_all_news(target_date=target_date)
            
            if total_articles == 0:
                # Vẫn tạo file rỗng để lần sau không backfill lại
                log_msg += f"   ⚠️ [{date_str}] Không có bài viết nào (RSS có thể đã hết hạn). " \
                           f"Tạo file rỗng để đánh dấu.\n"
                save_to_json(all_news, filename)
            else:
                filepath = save_to_json(all_news, filename)
                log_msg += f"   ✅ [{date_str}] Backfill thành công {total_articles} bài → {filename}\n"
                for category, items in all_news.items():
                    if len(items) > 0:
                        log_msg += f"      📂 {category}: {len(items)} bài\n"
                        
        except Exception as e:
            log_msg += f"   ❌ [{date_str}] Lỗi khi backfill: {str(e)}\n"
    
    return log_msg


def main():
    now = datetime.datetime.now()
    log_msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Auto News Collector khởi chạy.\n"
    
    # ===== Bước 0: Kiểm tra và backfill các ngày bị thiếu =====
    missing_dates = find_missing_dates()
    
    if missing_dates:
        log_msg += backfill_missing_days(missing_dates)
        log_msg += "\n"
    
    # ===== Bước 1: Xử lý tin tức ngày hôm nay (logic cũ) =====
    filename = get_today_filename()
    
    if file_already_exists(filename):
        log_msg += f"✅ File '{filename}' đã tồn tại. Bỏ qua.\n"
        write_log(log_msg)
        return
    
    # Bước 2: Chưa có → tiến hành cào tin
    log_msg += f"📰 Chưa có file '{filename}'. Bắt đầu cào tin tức...\n"
    
    try:
        all_news, debug_logs, total_articles = collect_all_news(target_date=datetime.date.today())
        
        if total_articles == 0:
            log_msg += "⚠️ Không cào được bài viết nào. Có thể do RSS feed lỗi hoặc ngoài khung giờ.\n"
            # Ghi debug log để debug
            for d in debug_logs:
                log_msg += f"   {d}\n"
            write_log(log_msg)
            return
        
        # Bước 3: Lưu file JSON
        filepath = save_to_json(all_news, filename)
        
        log_msg += f"✅ Đã lưu {total_articles} bài viết vào: {filepath}\n"
        for category, items in all_news.items():
            log_msg += f"   📂 {category}: {len(items)} bài\n"
            
    except Exception as e:
        log_msg += f"❌ Lỗi khi cào tin: {str(e)}\n"
    
    write_log(log_msg)


if __name__ == "__main__":
    main()
