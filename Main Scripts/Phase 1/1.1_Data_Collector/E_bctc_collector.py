"""
Module:  E_bctc_collector
Logic:   Async collector for financial statements (BCTC) via vnstock Fundamental API
Detail:  Thu thập BCTC đầy đủ (BCDKT, KQKD, LCTT, Thuyết minh, Chỉ số) cho toàn bộ mã CK.
         Sử dụng asyncio + Semaphore để cào bất đồng bộ. Checkpoint.json để resume.
"""
import os
import io
import sys
import time
import json
import asyncio
import logging
import pandas as pd
from datetime import datetime

# Setup encoding cho Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import centralized paths
from E_Helper.E_config import (
    BCTC_BALANCE_SHEET_DIR, BCTC_INCOME_STMT_DIR, BCTC_CASH_FLOW_DIR,
    BCTC_RATIO_DIR, LOG_DIR, ensure_dirs
)
# Import ghi file an toàn
from E_Helper.E_io_utils import safe_write_parquet, safe_write_json

# ═══════════════════════════════════════════════════════════════
# CONSTANTS — Khai báo tất cả hằng số ở đầu file
# ═══════════════════════════════════════════════════════════════

# Số request đồng thời tối đa (Semaphore)
MAX_CONCURRENT_REQUESTS = 5

# Số lần retry tối đa khi API lỗi
RETRY_MAX = 3

# Delay giữa các lần retry (giây)
RETRY_DELAY_SECONDS = 5

# Delay nhẹ giữa mỗi mã sau khi cào xong (giây) — lịch sự với server
POLITENESS_DELAY = 1.0

# Tên file checkpoint
CHECKPOINT_FILE = "checkpoint_bctc.json"

# Định nghĩa 7 loại báo cáo cần cào
# Format: (report_type, period, output_dir, filename_suffix)
# NOTE: "note" (thuyết minh BCTC) bị loại vì vnstock API hiện tại không hỗ trợ.
#       Thư mục E_BCTC/Note/ vẫn giữ lại cho tương lai.
REPORT_TYPES = [
    ("balance_sheet",     "quarter", BCTC_BALANCE_SHEET_DIR, "balance_sheet_quarter"),
    ("balance_sheet",     "year",    BCTC_BALANCE_SHEET_DIR, "balance_sheet_year"),
    ("income_statement",  "quarter", BCTC_INCOME_STMT_DIR,   "income_statement_quarter"),
    ("income_statement",  "year",    BCTC_INCOME_STMT_DIR,   "income_statement_year"),
    ("cash_flow",         "quarter", BCTC_CASH_FLOW_DIR,     "cash_flow_quarter"),
    ("cash_flow",         "year",    BCTC_CASH_FLOW_DIR,     "cash_flow_year"),
    ("ratio",             None,      BCTC_RATIO_DIR,         "ratio"),
]

# ═══════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════

# Đảm bảo thư mục tồn tại
ensure_dirs()

# Log riêng cho BCTC
PHASE1_LOG_DIR = os.path.join(LOG_DIR, "Phase 1")
os.makedirs(PHASE1_LOG_DIR, exist_ok=True)

log_file = os.path.join(PHASE1_LOG_DIR, "bctc_collector.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Semaphore toàn cục — giới hạn concurrency
SEM = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def build_output_path(symbol, suffix, out_dir):
    """Tạo đường dẫn output file cho 1 báo cáo."""
    return os.path.join(out_dir, f"{symbol}_{suffix}.parquet")


def get_checkpoint_path():
    """Trả về đường dẫn checkpoint file trong thư mục log."""
    return os.path.join(PHASE1_LOG_DIR, CHECKPOINT_FILE)


def load_checkpoint():
    """Đọc checkpoint từ file JSON. Trả về dict rỗng nếu chưa có."""
    cp_path = get_checkpoint_path()
    if os.path.exists(cp_path):
        with open(cp_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "module": "E_bctc_collector",
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "total_symbols": 0,
        "completed": [],
        "failed": {},
        "status": "not_started"
    }


def save_checkpoint(checkpoint):
    """Ghi checkpoint an toàn bằng atomic write."""
    cp_path = get_checkpoint_path()
    safe_write_json(cp_path, checkpoint)


# ═══════════════════════════════════════════════════════════════
# CORE FUNCTIONS — Sync & Async
# ═══════════════════════════════════════════════════════════════

def _call_vnstock_api(eq, report_type, period, orient):
    """
    Gọi đúng method vnstock theo report_type.
    Tách riêng để dễ retry với orient khác nhau.
    """
    if report_type == "balance_sheet":
        return eq.balance_sheet(period=period, orient=orient)
    elif report_type == "income_statement":
        return eq.income_statement(period=period, orient=orient)
    elif report_type == "cash_flow":
        return eq.cash_flow(period=period, orient=orient)
    elif report_type == "ratio":
        return eq.ratio()
    else:
        return None


def fetch_report_sync(symbol, report_type, period=None):
    """
    Gọi vnstock Fundamental API (blocking).
    Retry tối đa RETRY_MAX lần.
    Ưu tiên orient='time_series', fallback sang 'report' nếu lỗi duplicate columns.

    Returns:
        pd.DataFrame nếu thành công, None nếu thất bại.
    """
    from vnstock import Fundamental

    for attempt in range(1, RETRY_MAX + 1):
        try:
            fa = Fundamental()
            eq = fa.equity(symbol)

            # ratio không có orient → gọi thẳng
            if report_type == "ratio":
                df = _call_vnstock_api(eq, report_type, period, orient=None)
            else:
                # Thử orient='time_series' trước
                try:
                    df = _call_vnstock_api(eq, report_type, period, orient='time_series')
                except Exception as orient_err:
                    # Fallback sang orient='report' nếu time_series lỗi (duplicate columns)
                    logging.warning(
                        f"[{symbol}] {report_type} orient='time_series' lỗi, "
                        f"fallback sang 'report': {orient_err}"
                    )
                    df = _call_vnstock_api(eq, report_type, period, orient='report')

            if df is not None and not df.empty:
                return df
            else:
                logging.warning(f"[{symbol}] {report_type} (period={period}): Không có dữ liệu.")
                return None

        except Exception as e:
            logging.warning(
                f"[{symbol}] {report_type} (period={period}) — "
                f"Lần thử {attempt}/{RETRY_MAX} lỗi: {e}"
            )
            if attempt < RETRY_MAX:
                time.sleep(RETRY_DELAY_SECONDS)

    logging.error(f"[{symbol}] {report_type} (period={period}): Thất bại sau {RETRY_MAX} lần thử.")
    return None


async def fetch_and_save_async(symbol, report_type, period, out_dir, suffix):
    """
    Wrapper async: chạy fetch_report_sync trong thread pool.
    Không dùng Semaphore ở đây — Semaphore kiểm soát ở cấp symbol.

    Returns:
        (suffix, True/False, error_message_or_None)
    """
    out_path = build_output_path(symbol, suffix, out_dir)

    # Skip nếu file đã tồn tại (Resume mode)
    if os.path.exists(out_path):
        return (suffix, True, None)

    try:
        df = await asyncio.to_thread(fetch_report_sync, symbol, report_type, period)

        if df is not None and not df.empty:
            safe_write_parquet(out_path, df)
            logging.info(f"[{symbol}] ✅ {suffix} -> {out_path}")
            return (suffix, True, None)
        else:
            return (suffix, False, "No data returned")

    except Exception as e:
        logging.error(f"[{symbol}] ❌ {suffix} — Exception: {e}")
        return (suffix, False, str(e))


async def collect_bctc_async(symbol):
    """
    Cào 7 loại BCTC cho 1 mã — TUẦN TỰ (không song song).
    vnstock không thread-safe: chạy song song gây lỗi duplicate columns.

    Returns:
        (success_count, fail_count, fail_reasons)
    """
    success_count = 0
    fail_count = 0
    fail_reasons = []

    for report_type, period, out_dir, suffix in REPORT_TYPES:
        result = await fetch_and_save_async(symbol, report_type, period, out_dir, suffix)

        if isinstance(result, Exception):
            fail_count += 1
            fail_reasons.append(str(result))
        else:
            s, ok, err = result
            if ok:
                success_count += 1
            else:
                fail_count += 1
                if err:
                    fail_reasons.append(f"{s}: {err}")

    return success_count, fail_count, fail_reasons


async def run_all_async(symbols):
    """
    Entry point — Chạy toàn bộ danh sách mã.
    Nhiều mã chạy đồng thời (Semaphore kiểm soát), reports per mã chạy tuần tự.
    Checkpoint cập nhật an toàn qua asyncio.Lock().
    """
    checkpoint = load_checkpoint()
    completed_set = set(checkpoint.get("completed", []))
    remaining = [s for s in symbols if s not in completed_set]

    checkpoint["total_symbols"] = len(symbols)
    checkpoint["status"] = "in_progress"
    save_checkpoint(checkpoint)

    total = len(symbols)
    done_count = len(completed_set)

    logging.info(f"=== BCTC Collector — Tổng: {total} mã | Đã xong: {done_count} | Còn lại: {len(remaining)} ===")

    # Lock để bảo vệ checkpoint khi nhiều symbol chạy đồng thời
    lock = asyncio.Lock()
    progress = {"value": done_count}

    async def process_one_symbol(symbol):
        """Cào + cập nhật checkpoint cho 1 mã, Semaphore kiểm soát concurrency."""
        async with SEM:
            progress["value"] += 1
            current = progress["value"]
            logging.info(f"--- [{current}/{total}] Đang cào BCTC cho: {symbol} ---")

            success, fail, reasons = await collect_bctc_async(symbol)
            logging.info(f"[{symbol}] Kết quả: {success} thành công, {fail} thất bại.")

            # Cập nhật checkpoint — dùng lock tránh race condition
            async with lock:
                checkpoint["completed"].append(symbol)
                checkpoint["updated_at"] = datetime.now().isoformat()
                if fail > 0 and reasons:
                    checkpoint["failed"][symbol] = "; ".join(reasons)
                save_checkpoint(checkpoint)

            # Politeness delay — nghỉ ngắn giữa các mã
            await asyncio.sleep(POLITENESS_DELAY)

    # Tạo task cho tất cả mã còn lại — Semaphore giới hạn chỉ chạy tối đa 5 mã cùng lúc
    tasks = [process_one_symbol(s) for s in remaining]
    await asyncio.gather(*tasks, return_exceptions=True)

    checkpoint["status"] = "completed"
    checkpoint["updated_at"] = datetime.now().isoformat()
    save_checkpoint(checkpoint)

    total_failed = len(checkpoint.get("failed", {}))
    logging.info(f"=== HOÀN THÀNH — {total} mã | Thất bại: {total_failed} ===")


# ═══════════════════════════════════════════════════════════════
# MAIN — Entry point khi chạy trực tiếp
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from vnstock import Listing

    logging.info("=== Đang tải danh sách toàn bộ mã chứng khoán từ vnstock... ===")
    ls = Listing()
    all_df = ls.all_symbols()
    all_symbols = all_df['symbol'].tolist()
    logging.info(f"=== Tổng cộng {len(all_symbols)} mã. Bắt đầu cào BCTC! ===")

    asyncio.run(run_all_async(all_symbols))

