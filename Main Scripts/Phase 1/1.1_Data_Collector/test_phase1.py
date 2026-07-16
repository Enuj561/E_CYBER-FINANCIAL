import pandas as pd
import os

file_path = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL\Phase_1_Data\From_FireAnt\VCB_historical_fireant.parquet"
if not os.path.exists(file_path):
    print("File không tồn tại!")
    exit()

df = pd.read_parquet(file_path)
df['Date'] = pd.to_datetime(df['Date'])
day_data = df[df['Date'] == '2022-04-29']

if day_data.empty:
    print("Không tìm thấy dữ liệu ngày 2022-04-29!")
    exit()

row = day_data.iloc[0]

total_vol = row['totalVolume']
deal_vol = row['dealVolume']
pt_vol = row['putthroughVolume']

fgn_buy_qty = row.get('buyForeignQuantity', 0)
fgn_sell_qty = row.get('sellForeignQuantity', 0)
fgn_total_qty = fgn_buy_qty + fgn_sell_qty

prop_net_val = row.get('propTradingNetValue', 0)
prop_net_deal = row.get('propTradingNetDealValue', 0)
prop_net_pt = row.get('propTradingNetPTValue', 0)

print("=" * 60)
print(f"KIỂM TRA DỮ LIỆU VCB NGÀY {row['Date'].date()}")
print("=" * 60)
print(f"1. Tổng khối lượng (Total Volume)     : {total_vol:,.0f}")
print(f"2. KL Khớp lệnh (Deal Volume)         : {deal_vol:,.0f}")
print(f"3. KL Thỏa thuận (Put-through Volume) : {pt_vol:,.0f}")
print(f"-> Phép trừ (Total - Deal)            : {total_vol - deal_vol:,.0f}")
print("-" * 60)
print(f"4. Khối ngoại MUA (Foreign Buy Qty)   : {fgn_buy_qty:,.0f}")
print(f"5. Khối ngoại BÁN (Foreign Sell Qty)  : {fgn_sell_qty:,.0f}")
print(f"-> Tổng KL Khối ngoại Giao dịch (4+5) : {fgn_total_qty:,.0f}")
print("-" * 60)
print(f"6. Tự doanh Mua ròng (Net Value)      : {prop_net_val:,.0f} VND")
print(f"   - Khớp lệnh (Deal Net Value)       : {prop_net_deal:,.0f} VND")
print(f"   - Thỏa thuận (PT Net Value)        : {prop_net_pt:,.0f} VND")
print("=" * 60)
print("KẾT LUẬN VỀ CÂU HỎI:")
print("- KL Thỏa Thuận (Put-through) KHÔNG BẰNG Tổng KL Khối Ngoại + Tự Doanh.")
print("- LÝ DO:")
print("  + Khối ngoại và Tự doanh tham gia vào CẢ Khớp lệnh LẪN Thỏa thuận.")
print("  + Các quỹ nội, tổ chức, hoặc cá mập cá nhân (không phải Tây, không phải Tự doanh)")
print("    hoàn toàn có thể thực hiện giao dịch Thỏa thuận.")
print("  => Thỏa thuận là 1 phương thức giao dịch chung cho toàn bộ thị trường,")
print("     chứ không phải là số đo riêng biệt đại diện cho Tây hay Tự doanh!")
