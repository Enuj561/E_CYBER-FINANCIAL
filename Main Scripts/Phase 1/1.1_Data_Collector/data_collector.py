import os
import io
import sys
import time
import json
import random
import logging
import requests
import pandas as pd
from datetime import datetime

# Setup encoding cho Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import API của vnstock
from vnstock.api.quote import Quote

# Setup paths
BASE_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"
DATA_DIR = os.path.join(BASE_DIR, "Data_Main")
VNSTOCK_DIR = os.path.join(DATA_DIR, "From_vnstock")
FIREANT_DIR = os.path.join(DATA_DIR, "From_FireAnt")
LOG_DIR = os.path.join(BASE_DIR, "Log_Debug", "Phase 1")

for d in [DATA_DIR, VNSTOCK_DIR, FIREANT_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

# Setup logging
log_file = os.path.join(LOG_DIR, "data_collector.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_fireant_token():
    config_path = os.path.join(BASE_DIR, "Main Scripts", "Phase 1", "1.1_Data_Collector", "config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f).get("FIREANT_BEARER_TOKEN", "")
    except Exception as e:
        logging.error(f"Không tìm thấy config.json hoặc token: {e}")
        return ""

FIREANT_TOKEN = get_fireant_token()

def fetch_vnstock(symbol, start_date="2012-01-01"):
    try:
        logging.info(f"[{symbol}] Kéo giá từ vnstock...")
        q = Quote(symbol=symbol, source='VCI')
        df = q.history(start=start_date, end=None, interval='1D')
        
        if df is not None and not df.empty:
            if 'time' in df.columns:
                df['Date'] = pd.to_datetime(df['time']).dt.normalize()
            # Đổi tên file theo yêu cầu: XXX_historical_vnstock.parquet
            out_path = os.path.join(VNSTOCK_DIR, f"{symbol}_historical_vnstock.parquet")
            df.to_parquet(out_path, index=False)
            logging.info(f"[{symbol}] Đã lưu -> {out_path}")
            return True
    except Exception as e:
        logging.error(f"[{symbol}] Vnstock lỗi: {e}")
    return False

def fetch_fireant(symbol, start_date="2012-01-01"):
    try:
        logging.info(f"[{symbol}] Kéo Khối ngoại từ FireAnt...")
        url = f"https://restv2.fireant.vn/symbols/{symbol}/historical-quotes?startDate={start_date}&endDate=2030-01-01&limit=10000"
        headers = {
            "Authorization": FIREANT_TOKEN,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                if 'date' in df.columns:
                    df['Date'] = pd.to_datetime(df['date']).dt.normalize()
                    
                # Hốt trọn bộ 27 cột! Chỉ bỏ cột 'date' gốc (đã chuyển sang 'Date') và 'symbol' (thừa)
                df = df.drop(columns=['date', 'symbol'], errors='ignore')
                
                # Đổi tên file theo yêu cầu: XXX_historical_fireant.parquet
                out_path = os.path.join(FIREANT_DIR, f"{symbol}_historical_fireant.parquet")
                df.to_parquet(out_path, index=False)
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
        
    # Nếu file vnstock chưa có thì cào
    if not os.path.exists(path_vnstock):
        fetch_vnstock(symbol)
        
    # Nếu file fireant chưa có thì cào
    if not os.path.exists(path_fireant):
        fetch_fireant(symbol)

def run_all(symbols):
    logging.info(f"Bắt đầu thu thập cho {len(symbols)} mã...")
    
    total_symbols = len(symbols)
    idx = 0
    
    while idx < total_symbols:
        # Lấy random số lượng mã cho mỗi "đợt" (batch) từ 3 đến 5 mã
        batch_size = random.randint(3, 5)
        batch_symbols = symbols[idx:idx+batch_size]
        
        logging.info(f"--- Đợt cào mới: Quét {len(batch_symbols)} mã ({', '.join(batch_symbols)}) ---")
        
        for sym in batch_symbols:
            logging.info(f"Tiến độ: {idx+1}/{total_symbols} - Đang xử lý: {sym}")
            collect_data(sym)
            idx += 1
            
            # Nghỉ ngắn 1-2 giây giữa các mã trong cùng 1 batch
            time.sleep(random.uniform(1, 2))
            
        if idx < total_symbols:
            # Sau khi cào xong 1 đợt (3-5 mã), nghỉ dài 10-15 giây giữa các cụm
            long_delay = random.uniform(10, 15)
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
