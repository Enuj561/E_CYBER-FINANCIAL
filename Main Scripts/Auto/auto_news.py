"""
Auto News Collector - Chạy lúc 21:00 hàng ngày qua Task Scheduler.
Logic:
    1. Kiểm tra folder News_JSON xem đã có file News_dd_mm_yy.json của ngày hôm đó chưa.
    2. Nếu chưa → tự động cào tất cả tin tức (tất cả nguồn, tất cả lĩnh vực) 
       bằng fetch_news rồi lưu thành file JSON.
    3. Ghi log vào news_log.txt để tiện theo dõi.
"""

import os
import sys
import json
import datetime

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


def get_today_filename():
    """Tạo tên file theo format: News_dd_mm_yy.json"""
    now = datetime.datetime.now()
    return f"News_{now.strftime('%d_%m_%y')}.json"


def file_already_exists(filename):
    """Kiểm tra file đã tồn tại trong folder News_JSON chưa."""
    return os.path.exists(os.path.join(NEWS_JSON_DIR, filename))


def collect_all_news():
    """
    Cào toàn bộ tin tức từ tất cả nguồn báo, tất cả lĩnh vực.
    Giống như user chọn 'Tổng hợp' cho từng lĩnh vực rồi gộp lại.
    """
    all_news = {}
    all_debug = []
    total_articles = 0

    for category in ALL_CATEGORIES:
        news_items, debug_logs = fetch_news("Tổng hợp", category)
        
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


def main():
    now = datetime.datetime.now()
    log_msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Auto News Collector khởi chạy.\n"
    
    filename = get_today_filename()
    
    # Bước 1: Kiểm tra file đã tồn tại chưa
    if file_already_exists(filename):
        log_msg += f"✅ File '{filename}' đã tồn tại. Bỏ qua.\n"
        write_log(log_msg)
        return
    
    # Bước 2: Chưa có → tiến hành cào tin
    log_msg += f"📰 Chưa có file '{filename}'. Bắt đầu cào tin tức...\n"
    
    try:
        all_news, debug_logs, total_articles = collect_all_news()
        
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
