"""
Module:  E_auto_news
Logic:   Scheduled news collection via Windows Task Scheduler (21:00 daily)
Detail:  Script chạy tự động hàng ngày, gọi NewsManager.run_full_pipeline().
         Có try/except toàn cục để không bao giờ crash im lặng.
"""
import os
import sys
import datetime

# Fix encoding cho Task Scheduler chạy ngầm
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Import centralized paths
from E_Helper.E_config import PROJECT_DIR, MAIN_SCRIPTS_DIR

# Đảm bảo Main Scripts trong sys.path
if MAIN_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, MAIN_SCRIPTS_DIR)

from News.E_news_manager import NewsManager

LOG_FILE = os.path.join(MAIN_SCRIPTS_DIR, "Auto", "news_log.txt")

def write_log(message):
    """Ghi log ra file."""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def main():
    try:
        full_log = NewsManager.run_full_pipeline(log_callback=print)
        
        # Ghi lại toàn bộ log vào file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full_log + "\n" + "-" * 50 + "\n")
    except Exception as e:
        # Bảo vệ toàn cục — ghi lỗi vào file log thay vì crash im lặng
        error_msg = f"[{datetime.datetime.now()}] ❌ FATAL ERROR: {str(e)}\n"
        print(error_msg)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(error_msg + "-" * 50 + "\n")

if __name__ == "__main__":
    main()
