"""
compare_data.py - So sánh OHLCV giữa Vnstock và FireAnt (Sau khi điều chỉnh giá)
"""
import os
import sys
import io
import json
import logging
import requests
import pandas as pd
import numpy as np

# Setup encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"
DATA_DIR = os.path.join(BASE_DIR, "Phase_1_Data")
VNSTOCK_DIR = os.path.join(DATA_DIR, "From_vnstock")
FIREANT_DIR = os.path.join(DATA_DIR, "From_FireAnt")
LOG_DIR = os.path.join(BASE_DIR, "Log_Debug", "Phase 1")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "Compare_Data.log")

if os.path.exists(log_file):
    os.remove(log_file)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()])

config_path = os.path.join(BASE_DIR, "Main Scripts", "Phase 1", "1.1_Data_Collector", "config.json")
try:
    with open(config_path, "r") as f:
        FIREANT_TOKEN = json.load(f).get("FIREANT_BEARER_TOKEN", "")
except:
    FIREANT_TOKEN = ""

def fetch_fireant_ohlcv(symbol):
    url = f"https://restv2.fireant.vn/symbols/{symbol}/historical-quotes?startDate=2010-01-01&endDate=2030-01-01&limit=10000"
    headers = {"Authorization": FIREANT_TOKEN, "User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code == 200:
        data = res.json()
        if data:
            df = pd.DataFrame(data)
            df['Date'] = pd.to_datetime(df['date']).dt.normalize()
            return df
    return pd.DataFrame()

def compare_adjusted_data(symbol):
    logging.info("=" * 60)
    logging.info(f"[{symbol}] BẮT ĐẦU SO SÁNH GIÁ ĐÃ ĐIỀU CHỈNH")
    logging.info("=" * 60)
    
    vnstock_path = os.path.join(VNSTOCK_DIR, f"{symbol}_historical_vnstock.parquet")
    if not os.path.exists(vnstock_path):
        logging.error(f" File vnstock không tồn tại.")
        return

    df_vn = pd.read_parquet(vnstock_path)
    if 'time' in df_vn.columns: df_vn['Date'] = pd.to_datetime(df_vn['time']).dt.normalize()
    df_vn = df_vn.sort_values('Date').reset_index(drop=True)

    df_fa = fetch_fireant_ohlcv(symbol)
    if df_fa.empty:
        logging.error(" Không lấy được dữ liệu FireAnt từ API.")
        return
    df_fa = df_fa.sort_values('Date').reset_index(drop=True)

    common_dates = set(df_vn['Date']).intersection(set(df_fa['Date']))
    df_vn = df_vn[df_vn['Date'].isin(common_dates)].set_index('Date').sort_index()
    df_fa = df_fa[df_fa['Date'].isin(common_dates)].set_index('Date').sort_index()
    
    total_days = len(common_dates)
    if total_days == 0:
        logging.error(" Không có ngày chung để so sánh.")
        return

    logging.info(f" Tong so ngay giao dich doi chieu: {total_days}")
    logging.info("---")

    adj_ratio = df_fa['adjRatio'].replace(0, 1)
    
    fa_adj = pd.DataFrame(index=df_fa.index)
    fa_adj['open'] = df_fa['priceOpen'] / adj_ratio
    fa_adj['high'] = df_fa['priceHigh'] / adj_ratio
    fa_adj['low'] = df_fa['priceLow'] / adj_ratio
    fa_adj['close'] = df_fa['priceClose'] / adj_ratio
    fa_adj['volume_deal'] = df_fa['dealVolume']
    fa_adj['volume_total'] = df_fa['totalVolume']

    for col in ['open', 'high', 'low', 'close']:
        vn_vals, fa_vals = df_vn[col], fa_adj[col]
        with np.errstate(divide='ignore', invalid='ignore'):
            pct_diff = np.where(fa_vals != 0, np.abs(vn_vals - fa_vals) / np.abs(fa_vals) * 100, 0)
        
        diff_mask = pct_diff > 1.5
        num_diff = diff_mask.sum()
        pct_match = (total_days - num_diff) / total_days * 100
        
        if num_diff == 0:
            logging.info(f" [OK] {col.upper():>6} : Khop {pct_match:.1f}% (Tuyet doi)")
        else:
            logging.warning(f" [WARN] {col.upper():>6} : Khop {pct_match:.1f}% - Sai khac {num_diff}/{total_days} ngay")
            extreme_indices = np.argsort(pct_diff)[::-1]
            count = 0
            for idx in extreme_indices:
                if pct_diff[idx] <= 1.5: break
                d = df_vn.index[idx]
                logging.warning(f"       + {d.date()}: Vnstock = {vn_vals.iloc[idx]:.2f}, FireAnt_Adj = {fa_vals.iloc[idx]:.2f} (Lech {pct_diff[idx]:.1f}%)")
                count += 1
                if count >= 3: break
    
    logging.info("---")
    vn_vol = df_vn['volume']
    for vol_col in ['volume_deal', 'volume_total']:
        fa_vol = fa_adj[vol_col]
        with np.errstate(divide='ignore', invalid='ignore'):
            pct_diff_vol = np.where(fa_vol != 0, np.abs(vn_vol - fa_vol) / np.abs(fa_vol) * 100, 0)
        
        diff_mask_vol = pct_diff_vol > 5.0
        num_diff_vol = diff_mask_vol.sum()
        pct_match_vol = (total_days - num_diff_vol) / total_days * 100
        
        if num_diff_vol == 0:
            logging.info(f" [OK] {vol_col.upper():>12} : Khop {pct_match_vol:.1f}%")
        else:
            logging.warning(f" [WARN] {vol_col.upper():>12} : Khop {pct_match_vol:.1f}% - Sai khac {num_diff_vol}/{total_days} ngay")
            extreme_indices = np.argsort(pct_diff_vol)[::-1]
            count = 0
            for idx in extreme_indices:
                if pct_diff_vol[idx] <= 5.0: break
                d = df_vn.index[idx]
                logging.warning(f"       + {d.date()}: Vnstock = {vn_vol.iloc[idx]:,.0f}, FireAnt_{vol_col} = {fa_vol.iloc[idx]:,.0f} (Lech {pct_diff_vol[idx]:.1f}%)")
                count += 1
                if count >= 3: break

if __name__ == '__main__':
    compare_adjusted_data('VCB')
    logging.info("=" * 60)
    logging.info("HOAN THANH SO SANH")
    logging.info("=" * 60)
