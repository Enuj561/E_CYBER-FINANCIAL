"""
Module:  E_news_manager
Logic:   Orchestrate the full news collection pipeline
Detail:  Tổng chỉ huy pipeline tin tức: cào → lọc trùng → lưu JSON → backfill ngày thiếu.
         Các file khác chỉ cần gọi run_full_pipeline() — không cần biết chi tiết bên trong.
"""
import os
import datetime
import re

# Import centralized paths
from E_Helper.E_config import PROJECT_DIR, PHASE_5_DATA_DIR
# Import ghi file an toàn
from E_Helper.E_io_utils import safe_write_json
# Import scraper
from News.E_news_scraper import fetch_news, RSS_FEEDS

# Tất cả lĩnh vực cần cào
ALL_CATEGORIES = ["Vĩ mô & Tiền tệ", "Thị trường & Đầu tư", "Công nghệ"]

class NewsManager:
    @staticmethod
    def get_filename_for_date(target_date):
        """Tạo tên file theo format: News_dd_mm_yy.json cho một ngày bất kỳ."""
        return f"News_{target_date.strftime('%d_%m_%y')}.json"

    @staticmethod
    def get_today_filename():
        """Tạo tên file theo format: News_dd_mm_yy.json cho ngày hôm nay."""
        return NewsManager.get_filename_for_date(datetime.date.today())

    @staticmethod
    def file_already_exists(filename):
        """Kiểm tra file đã tồn tại trong folder Phase_5_Data chưa."""
        return os.path.exists(os.path.join(PHASE_5_DATA_DIR, filename))

    @staticmethod
    def find_missing_dates():
        """
        Scan folder Phase_5_Data, tìm file có ngày gần nhất.
        So sánh với ngày hôm nay → trả về danh sách ngày bị thiếu.
        """
        os.makedirs(PHASE_5_DATA_DIR, exist_ok=True)
        
        # Parse tên file → lấy danh sách ngày đã có
        pattern = re.compile(r"^News_(\d{2})_(\d{2})_(\d{2})\.json$")
        existing_dates = []
        
        for filename in os.listdir(PHASE_5_DATA_DIR):
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
        existing_dates_set = set(existing_dates)
        earliest_date = min(existing_dates)
        today = datetime.date.today()
        
        missing = []
        current = earliest_date + datetime.timedelta(days=1)
        while current < today:
            if current not in existing_dates_set:
                filename = NewsManager.get_filename_for_date(current)
                if not NewsManager.file_already_exists(filename):
                    missing.append(current)
            current += datetime.timedelta(days=1)
        
        return missing

    @staticmethod
    def collect_all_news(target_date=None, log_callback=None):
        """
        Cào toàn bộ tin tức từ tất cả nguồn báo, tất cả lĩnh vực.
        """
        all_news = {}
        all_debug = []
        total_articles = 0

        for category in ALL_CATEGORIES:
            if log_callback:
                log_callback(f"📂 Đang cào lĩnh vực: {category}...")
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

    @staticmethod
    def save_to_json(data, filename):
        """Lưu data vào file JSON trong folder Phase_5_Data (ghi an toàn)."""
        os.makedirs(PHASE_5_DATA_DIR, exist_ok=True)
        filepath = os.path.join(PHASE_5_DATA_DIR, filename)
        
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
        
        safe_write_json(filepath, output)
        
        return filepath

    @staticmethod
    def backfill_missing_days(missing_dates, log_callback=None):
        """
        Backfill tin tức cho các ngày bị thiếu.
        """
        log_msg = f"🔄 Phát hiện {len(missing_dates)} ngày bị thiếu: " \
                  f"{', '.join(d.strftime('%d/%m/%Y') for d in missing_dates)}\n"
        if log_callback:
            log_callback(log_msg)
            
        full_log = log_msg
        
        for target_date in missing_dates:
            filename = NewsManager.get_filename_for_date(target_date)
            date_str = target_date.strftime('%d/%m/%Y')
            
            try:
                all_news, debug_logs, total_articles = NewsManager.collect_all_news(target_date=target_date, log_callback=log_callback)
                
                if total_articles == 0:
                    msg = f"   ⚠️ [{date_str}] Không có bài viết nào (RSS có thể đã hết hạn). Tạo file rỗng để đánh dấu.\n"
                    if log_callback:
                        log_callback(msg)
                    full_log += msg
                    NewsManager.save_to_json(all_news, filename)
                else:
                    filepath = NewsManager.save_to_json(all_news, filename)
                    msg = f"   ✅ [{date_str}] Backfill thành công {total_articles} bài → {filename}\n"
                    for category, items in all_news.items():
                        if len(items) > 0:
                            msg += f"      📂 {category}: {len(items)} bài\n"
                    if log_callback:
                        log_callback(msg)
                    full_log += msg
                            
            except Exception as e:
                msg = f"   ❌ [{date_str}] Lỗi khi backfill: {str(e)}\n"
                if log_callback:
                    log_callback(msg)
                full_log += msg
        
        return full_log

    @staticmethod
    def run_full_pipeline(log_callback=None):
        """
        Gộp toàn bộ flow: backfill → cào hôm nay → lưu JSON.
        Trả về kết quả (thông báo hoàn tất) dạng string.
        """
        now = datetime.datetime.now()
        log_msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Auto News Collector khởi chạy.\n"
        if log_callback:
            log_callback("Bắt đầu kiểm tra dữ liệu...")
        
        # Bước 0: Kiểm tra và backfill các ngày bị thiếu
        missing_dates = NewsManager.find_missing_dates()
        
        if missing_dates:
            log_msg += NewsManager.backfill_missing_days(missing_dates, log_callback=log_callback)
            log_msg += "\n"
        
        # Bước 1: Xử lý tin tức ngày hôm nay
        filename = NewsManager.get_today_filename()
        
        if NewsManager.file_already_exists(filename):
            msg = f"✅ File '{filename}' đã tồn tại. Bỏ qua.\n"
            if log_callback:
                log_callback(msg)
            log_msg += msg
            return log_msg
        
        # Bước 2: Chưa có → tiến hành cào tin
        msg = f"📰 Chưa có file '{filename}'. Bắt đầu cào tin tức hôm nay...\n"
        if log_callback:
            log_callback(msg)
        log_msg += msg
        
        try:
            all_news, debug_logs, total_articles = NewsManager.collect_all_news(target_date=datetime.date.today(), log_callback=log_callback)
            
            if total_articles == 0:
                msg = "⚠️ Không cào được bài viết nào. Có thể do RSS feed lỗi hoặc ngoài khung giờ.\n"
                if log_callback:
                    log_callback(msg)
                log_msg += msg
                # Ghi debug log để debug
                for d in debug_logs:
                    log_msg += f"   {d}\n"
                return log_msg
            
            # Bước 3: Lưu file JSON
            filepath = NewsManager.save_to_json(all_news, filename)
            
            msg = f"✅ Đã lưu {total_articles} bài viết vào: {filename}\n"
            for category, items in all_news.items():
                msg += f"   📂 {category}: {len(items)} bài\n"
                
            if log_callback:
                log_callback(msg)
            log_msg += msg
                
        except Exception as e:
            msg = f"❌ Lỗi khi cào tin: {str(e)}\n"
            if log_callback:
                log_callback(msg)
            log_msg += msg
        
        return log_msg
