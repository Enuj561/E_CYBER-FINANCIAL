"""
Auto News Collector - Chạy lúc 21:00 hàng ngày qua Task Scheduler.
"""

import os
import sys
import datetime

# Fix encoding cho Task Scheduler chạy ngầm
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Thêm project root vào sys.path để import được News
PROJECT_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from News.news_manager import NewsManager

LOG_FILE = os.path.join(PROJECT_DIR, "Main Scripts", "Auto", "news_log.txt")

def write_log(message):
    """Ghi log ra file."""
    # Xoá bớt các ký tự định dạng html/icons nếu cần thiết, hoặc để nguyên
    # Ở đây in thẳng ra console và ghi file
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def main():
    # Gọi hàm xử lý cốt lõi từ NewsManager
    # Cung cấp log_callback = None vì run_full_pipeline đã trả về full log message 
    # Nhưng ta cũng có thể truyền write_log để in dần dần ra console
    full_log = NewsManager.run_full_pipeline(log_callback=print)
    
    # Ghi lại toàn bộ log vào file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_log + "\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    main()
