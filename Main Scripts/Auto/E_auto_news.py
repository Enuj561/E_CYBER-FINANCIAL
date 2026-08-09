"""
Module:  E_auto_news
Logic:   Scheduled news collection via Windows Task Scheduler (21:00 daily)
Detail:  Script chạy tự động hàng ngày, gọi NewsManager.run_full_pipeline().
         Có try/except toàn cục để không bao giờ crash im lặng.
"""
import sys

# Fix encoding cho Task Scheduler chạy ngầm
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Import centralized paths
from E_Helper.E_config import MAIN_SCRIPTS_DIR
from E_Helper.E_BlackBox import get_black_box

# Đảm bảo Main Scripts trong sys.path
if MAIN_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, MAIN_SCRIPTS_DIR)

from News.E_news_manager import NewsManager

black_box = get_black_box(__file__, console=True)

def main():
    run_log = black_box.bind()
    try:
        run_log.info("Auto News bắt đầu")
        full_log = NewsManager.run_full_pipeline(
            log_callback=lambda message: run_log.info(str(message).strip())
        )
        run_log.info("Auto News hoàn thành", summary=full_log.strip())
        return 0
    except Exception:
        run_log.exception("Auto News thất bại")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
