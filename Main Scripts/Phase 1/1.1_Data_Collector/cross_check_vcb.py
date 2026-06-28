import os
import json
import requests
import pandas as pd
from vnstock.api.quote import Quote
from datetime import datetime, timedelta

# Tải cấu hình Token
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)
FIREANT_TOKEN = config.get("FIREANT_BEARER_TOKEN", "")

def get_vnstock_data(symbol, start_date, end_date):
    print(f"[*] Đang kéo dữ liệu OHLCV từ Vnstock (Nguồn: TCBS) cho mã {symbol}...")
    try:
        # Sử dụng vnstock v4 (API Quote)
        q = Quote(symbol=symbol, source='VCI')
        df = q.history(start=start_date, end=end_date, interval='1D')
        if df is None or df.empty:
            q = Quote(symbol=symbol, source='FMP')
            df = q.history(start=start_date, end=end_date, interval='1D')
        
        if df is not None and not df.empty:
            # Vnstock trả về cột thời gian tên là 'time'
            df['Date'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
            # Lấy các cột quan trọng
            df = df[['Date', 'open', 'high', 'low', 'close', 'volume']]
            df.columns = ['Date', 'Open_Vnstock', 'High_Vnstock', 'Low_Vnstock', 'Close_Vnstock', 'Volume_Vnstock']
            return df.sort_values('Date').reset_index(drop=True)
    except Exception as e:
        print(f"[!] Lỗi khi lấy Vnstock: {e}")
    return pd.DataFrame()

def get_fireant_data(symbol, start_date, end_date):
    print(f"[*] Đang kéo dữ liệu OHLCV + Khối ngoại từ FireAnt cho mã {symbol}...")
    headers = {
        "Authorization": FIREANT_TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    # Fireant yêu cầu định dạng YYYY-MM-DD
    url = f"https://restv2.fireant.vn/symbols/{symbol}/historical-quotes?startDate={start_date}&endDate={end_date}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        # Parse ngày giờ
        df['Date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # Chọn lọc và đổi tên các cột
        df = df[['Date', 'priceOpen', 'priceHigh', 'priceLow', 'priceClose', 'dealVolume', 'buyForeignQuantity', 'sellForeignQuantity']]
        df.columns = ['Date', 'Open_FireAnt', 'High_FireAnt', 'Low_FireAnt', 'Close_FireAnt', 'Volume_FireAnt', 'Buy_Foreign', 'Sell_Foreign']
        
        return df.sort_values('Date').reset_index(drop=True)
    else:
        print(f"[!] FireAnt API lỗi: {response.status_code} - {response.text}")
        return pd.DataFrame()

def cross_check():
    symbol = "VCB"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d") # Lấy 1 năm để check cho nhanh
    
    df_vnstock = get_vnstock_data(symbol, start_date, end_date)
    df_fireant = get_fireant_data(symbol, start_date, end_date)
    
    if df_vnstock.empty or df_fireant.empty:
        print("[!] Không thể đối soát vì thiếu dữ liệu từ 1 trong 2 nguồn.")
        return

    # Gộp 2 luồng dữ liệu theo Ngày
    print("[*] Đang đối soát chéo (Cross-check) dữ liệu...")
    merged_df = pd.merge(df_vnstock, df_fireant, on='Date', how='inner')
    
    # Kiểm tra lệch giá Đóng cửa (Close Price)
    # LƯU Ý: Giá FireAnt có thể chưa nhân x1000 như Vnstock. Ta cần chuẩn hóa trước khi so sánh.
    # Thông thường Vnstock giá VCB là 90000, FireAnt là 90.0
    
    if merged_df['Close_FireAnt'].iloc[0] < 1000 and merged_df['Close_Vnstock'].iloc[0] > 1000:
        merged_df['Close_FireAnt'] = merged_df['Close_FireAnt'] * 1000
    
    merged_df['Price_Diff'] = abs(merged_df['Close_Vnstock'] - merged_df['Close_FireAnt'])
    
    # Lọc ra những ngày bị lệch giá > 100 VND (do làm tròn hoặc do chia cổ tức khác nhau)
    diff_df = merged_df[merged_df['Price_Diff'] > 100]
    
    print("\n" + "="*50)
    print(f"KẾT QUẢ ĐỐI SOÁT CHÉO MÃ {symbol} (1 Năm Qua)")
    print("="*50)
    print(f"Tổng số ngày giao dịch: {len(merged_df)}")
    if diff_df.empty:
        print("✅ DỮ LIỆU GIÁ HOÀN TOÀN KHỚP NHAU 100%! Không phát hiện sai lệch đáng kể.")
    else:
        print(f"❌ Phát hiện {len(diff_df)} ngày bị lệch giá (sai số > 100 VND):")
        print(diff_df[['Date', 'Close_Vnstock', 'Close_FireAnt', 'Price_Diff']].head(10).to_string())
        print("... (Chỉ hiển thị 10 dòng đầu)")

    print("\n--- 5 DÒNG DỮ LIỆU KHỐI NGOẠI GẦN NHẤT (FIREANT) ---")
    print(df_fireant.tail(5)[['Date', 'Close_FireAnt', 'Buy_Foreign', 'Sell_Foreign']].to_string())

if __name__ == "__main__":
    cross_check()
