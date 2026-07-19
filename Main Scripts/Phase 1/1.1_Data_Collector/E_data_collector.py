"""
Module:  E_data_collector
Logic:   Collect historical stock data from vnstock and FireAnt
Detail:  Thu thập dữ liệu giá lịch sử cổ phiếu từ 2 nguồn (vnstock API + FireAnt API).
         Hỗ trợ Resume mode: bỏ qua mã đã cào đủ.
"""
import os
import io
import sys
import time
import random
import logging
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Setup encoding cho Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import API của vnstock
from vnstock.api.quote import Quote

# Import centralized paths
from E_Helper.E_config import (
    PROJECT_DIR, PHASE_1_DATA_DIR, VNSTOCK_DIR, FIREANT_DIR, LOG_DIR, ENV_PATH, ensure_dirs
)
# Import ghi file an toàn
from E_Helper.E_io_utils import safe_write_parquet

# ═══════════════════════════════════════════════════════════════
# CONSTANTS — Khai báo tất cả hằng số ở đầu file
# ═══════════════════════════════════════════════════════════════

# Ngày bắt đầu lấy dữ liệu lịch sử (từ năm 2012)
DEFAULT_START_DATE = "2012-01-01"

# Ngày kết thúc lấy dữ liệu FireAnt (đặt xa tương lai để luôn lấy đến hiện tại)
FIREANT_END_DATE = "2030-01-01"

# Giới hạn số bản ghi mỗi request FireAnt
FIREANT_RECORD_LIMIT = 10000

# Request timeout cho FireAnt API (giây)
FIREANT_TIMEOUT_SECONDS = 15

# Delay ngẫu nhiên giữa các mã trong cùng 1 batch (giây) — tránh bị server chặn
INTRA_BATCH_DELAY_MIN = 1
INTRA_BATCH_DELAY_MAX = 2

# Delay ngẫu nhiên giữa các batch (giây) — nghỉ dài hơn để "lừa" server
INTER_BATCH_DELAY_MIN = 10
INTER_BATCH_DELAY_MAX = 15

# Kích thước batch: mỗi đợt cào random 3-5 mã
BATCH_SIZE_MIN = 3
BATCH_SIZE_MAX = 5

# ═══════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════

# Đảm bảo thư mục tồn tại
ensure_dirs()

# Log riêng cho Phase 1
PHASE1_LOG_DIR = os.path.join(LOG_DIR, "Phase 1")
os.makedirs(PHASE1_LOG_DIR, exist_ok=True)

log_file = os.path.join(PHASE1_LOG_DIR, "data_collector.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Load token từ .env
load_dotenv(dotenv_path=ENV_PATH)
FIREANT_TOKEN = os.environ.get("FIREANT_BEARER_TOKEN", "")

# ═══════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def fetch_vnstock(symbol, start_date=DEFAULT_START_DATE):
    try:
        logging.info(f"[{symbol}] Kéo giá từ vnstock...")
        q = Quote(symbol=symbol, source='VCI')
        df = q.history(start=start_date, end=None, interval='1D')
        
        if df is not None and not df.empty:
            if 'time' in df.columns:
                df['Date'] = pd.to_datetime(df['time']).dt.normalize()
            out_path = os.path.join(VNSTOCK_DIR, f"{symbol}_historical_vnstock.parquet")
            safe_write_parquet(out_path, df)
            logging.info(f"[{symbol}] Đã lưu -> {out_path}")
            return True
    except Exception as e:
        logging.error(f"[{symbol}] Vnstock lỗi: {e}")
    return False

def fetch_fireant(symbol, start_date=DEFAULT_START_DATE):
    try:
        logging.info(f"[{symbol}] Kéo Khối ngoại từ FireAnt...")
        url = (
            f"https://restv2.fireant.vn/symbols/{symbol}/historical-quotes"
            f"?startDate={start_date}&endDate={FIREANT_END_DATE}&limit={FIREANT_RECORD_LIMIT}"
        )
        headers = {
            "Authorization": FIREANT_TOKEN,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, timeout=FIREANT_TIMEOUT_SECONDS)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                if 'date' in df.columns:
                    df['Date'] = pd.to_datetime(df['date']).dt.normalize()
                    
                # Hốt trọn bộ 27 cột! Chỉ bỏ cột 'date' gốc (đã chuyển sang 'Date') và 'symbol' (thừa)
                df = df.drop(columns=['date', 'symbol'], errors='ignore')
                
                out_path = os.path.join(FIREANT_DIR, f"{symbol}_historical_fireant.parquet")
                safe_write_parquet(out_path, df)
                logging.info(f"[{symbol}] Đã lưu -> {out_path}")
                return True
        else:
            logging.error(f"[{symbol}] FireAnt API lỗi {res.status_code}")
    except Exception as e:
        logging.error(f"[{symbol}] FireAnt Exception: {e}")
    return False

def collect_data(symbol):
    path_vnstock = os.path.join(VNSTOCK_DIR, f"{symbol}_historical_vnstock.parquet")
    path_fireant = os.path.join(FIREANT_DIR, f"{symbol}_historical_fireant.parquet")
    
    # Resume Check
    if os.path.exists(path_vnstock) and os.path.exists(path_fireant):
        logging.info(f"[{symbol}] Đã cào đủ 2 nguồn, bỏ qua (Resume mode).")
        return
        
    if not os.path.exists(path_vnstock):
        fetch_vnstock(symbol)
        
    if not os.path.exists(path_fireant):
        fetch_fireant(symbol)

def run_all(symbols):
    logging.info(f"Bắt đầu thu thập cho {len(symbols)} mã...")
    
    total_symbols = len(symbols)
    idx = 0
    
    while idx < total_symbols:
        batch_size = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        batch_symbols = symbols[idx:idx+batch_size]
        
        logging.info(f"--- Đợt cào mới: Quét {len(batch_symbols)} mã ({', '.join(batch_symbols)}) ---")
        
        for sym in batch_symbols:
            logging.info(f"Tiến độ: {idx+1}/{total_symbols} - Đang xử lý: {sym}")
            collect_data(sym)
            idx += 1
            
            time.sleep(random.uniform(INTRA_BATCH_DELAY_MIN, INTRA_BATCH_DELAY_MAX))
            
        if idx < total_symbols:
            long_delay = random.uniform(INTER_BATCH_DELAY_MIN, INTER_BATCH_DELAY_MAX)
            logging.info(f"[*] Hoàn thành đợt cào. Nghỉ ngơi giải lao {long_delay:.2f} giây để lừa Server...")
            time.sleep(long_delay)

if __name__ == "__main__":
    from vnstock import Listing
    
    logging.info("=== Đang tải danh sách toàn bộ mã chứng khoán từ vnstock... ===")
    ls = Listing()
    all_df = ls.all_symbols()
    all_symbols = all_df['symbol'].tolist()
    logging.info(f"=== Tổng cộng {len(all_symbols)} mã. THÁO THẮNG - HẾT GA - HẾT SỐ! ===")
    
    run_all(all_symbols)
    
    logging.info("=== HOÀN THÀNH THU HOẠCH TOÀN BỘ THỊ TRƯỜNG! ===")
