import pandas as pd
import numpy as np

file_path = r'C:\Users\HP\Documents\E_CYBER-FINANCIAL\Data_Main\From_FireAnt\VCB_historical_fireant.parquet'
df = pd.read_parquet(file_path)
df['Date'] = pd.to_datetime(df['Date'])

# Lấy 120 ngày gần nhất (khoảng 6 tháng)
df = df.sort_values('Date').reset_index(drop=True)
df_recent = df.tail(120).copy()

# 1. Whale Ratio
buy_count = df_recent['buyCount'].replace(0, 1)
sell_count = df_recent['sellCount'].replace(0, 1)
avg_buy_order = df_recent['buyQuantity'] / buy_count
avg_sell_order = df_recent['sellQuantity'] / sell_count
df_recent['Whale_Ratio'] = avg_buy_order / avg_sell_order.replace(0, 1)

# 2. Net Active Volume
df_recent['Net_Active_Vol'] = df_recent['buyQuantity'] - df_recent['sellQuantity']

# 3. Prop Net Vol
df_recent['Prop_Net_Vol'] = df_recent['propTradingNetValue'] / df_recent['priceAverage'].replace(0, 1)

# 4. Foreign Dominance
df_recent['Net_Foreign_Vol'] = df_recent['buyForeignQuantity'] - df_recent['sellForeignQuantity']
df_recent['Foreign_Dominance'] = (df_recent['buyForeignQuantity'] + df_recent['sellForeignQuantity']) / (df_recent['dealVolume'].replace(0, 1) * 2) * 100

md = []
md.append('# Báo Cáo Phân Tích Dấu Chân Cá Mập (Whale Footprint) - Mã VCB')
md.append('> Phân tích 120 phiên giao dịch gần nhất (Nửa đầu năm 2026)')
md.append('')

md.append('## 1. Kết Quả 4 Phương Thức Phân Tích')
md.append('')

mean_whale = df_recent['Whale_Ratio'].mean()
sum_active = df_recent['Net_Active_Vol'].sum()
sum_prop = df_recent['Prop_Net_Vol'].sum()
sum_foreign = df_recent['Net_Foreign_Vol'].sum()
mean_fgn_dom = df_recent['Foreign_Dominance'].mean()

md.append('### A. Chỉ số Dấu Chân Cá Mập (Whale Ratio)')
md.append(f'- **Trung bình:** {mean_whale:.2f}')
md.append('- **Nhận xét:** ' + ('Lệnh mua chủ động trung bình lớn hơn lệnh bán (Cá mập gom hàng).' if mean_whale > 1 else 'Lệnh bán chủ động trung bình lớn hơn lệnh mua (Cá mập xả hàng hoặc nhỏ lẻ bán tháo).'))

md.append('### B. Dòng Tiền Chủ Động (Active Flow)')
md.append(f'- **Lũy kế 6 tháng:** {sum_active:,.0f} cổ phiếu')
md.append('- **Nhận xét:** ' + ('Phe Mua Chủ Động hoàn toàn áp đảo.' if sum_active > 0 else 'Phe Bán Chủ Động áp đảo, áp lực cung lớn.'))

md.append('### C. Tự Doanh (Proprietary Trading)')
md.append(f'- **Lũy kế 6 tháng mua/bán ròng:** {sum_prop:,.0f} cổ phiếu')
md.append('- **Nhận xét:** ' + ('Tự doanh gom ròng mạnh.' if sum_prop > 0 else 'Tự doanh xả ròng hoặc bán khống.'))

md.append('### D. Khối Ngoại (Foreign Investors)')
md.append(f'- **Lũy kế 6 tháng mua/bán ròng:** {sum_foreign:,.0f} cổ phiếu')
md.append(f'- **Tỷ trọng chi phối (Dominance):** {mean_fgn_dom:.1f}%')
md.append('- **Nhận xét:** ' + ('Tây lông gom ròng.' if sum_foreign > 0 else 'Tây lông xả ròng mạnh.'))
md.append('')

md.append('## 2. Check Chéo Các Nguồn Tiền (Cross-check)')
md.append('')
# Tính Correlation
corr = df_recent[['Net_Active_Vol', 'Prop_Net_Vol', 'Net_Foreign_Vol', 'Whale_Ratio']].corr()

md.append('### Bảng Tương Quan (Correlation) Giữa Các Nhóm:')
md.append('| Chỉ báo 1 | Chỉ báo 2 | Hệ số (R) | Tình trạng |')
md.append('|---|---|---|---|')

def get_meaning(val):
    if val > 0.6: return 'Đồng pha mạnh (Đánh cùng nhau)'
    if val > 0.3: return 'Có xu hướng đồng thuận'
    if val > -0.3: return 'Độc lập (Không liên quan)'
    if val > -0.6: return 'Ngược pha (Bên bán - Bên mua)'
    return 'Đối đầu kịch liệt (Cân nhau)'

pairs = [
    ('Dòng tiền chủ động', 'Tự doanh', 'Net_Active_Vol', 'Prop_Net_Vol'),
    ('Dòng tiền chủ động', 'Khối ngoại', 'Net_Active_Vol', 'Net_Foreign_Vol'),
    ('Tự doanh', 'Khối ngoại', 'Prop_Net_Vol', 'Net_Foreign_Vol'),
    ('Dấu chân Lệnh Lớn (Whale)', 'Dòng tiền chủ động', 'Whale_Ratio', 'Net_Active_Vol'),
]

for name1, name2, col1, col2 in pairs:
    v = corr.loc[col1, col2]
    md.append(f'| {name1} | {name2} | {v:.2f} | {get_meaning(v)} |')

md.append('')
md.append('### Soi 5 Phiên "Cá Mập" Vẩy Đuôi Mạnh Nhất')
md.append('Những phiên có `Whale Ratio` cao nhất (Quy mô lệnh mua vọt lên khủng khiếp so với lệnh bán):')
md.append('')
md.append('| Ngày | Giá (Close) | Whale Ratio | Dòng tiền Chủ động | Tự Doanh (Vol) | Khối Ngoại (Vol) | Tây Chiếm (%) |')
md.append('|---|---|---|---|---|---|---|')

top_whales = df_recent.sort_values('Whale_Ratio', ascending=False).head(5)
for _, r in top_whales.iterrows():
    md.append(f'| {r["Date"].date()} | {r["priceClose"]:,.1f} | **{r["Whale_Ratio"]:.2f}** | {r["Net_Active_Vol"]:,.0f} | {r["Prop_Net_Vol"]:,.0f} | {r["Net_Foreign_Vol"]:,.0f} | {r["Foreign_Dominance"]:.1f}% |')

md.append('')
md.append('## 3. Tổng Luận Hành Vi Dòng Tiền VCB')
md.append('Từ bảng Check chéo và phân tích các phương thức, ta thấy:')

val_pf = corr.loc["Prop_Net_Vol", "Net_Foreign_Vol"]
if val_pf < -0.3:
    md.append('- **Tự Doanh và Khối Ngoại đang CHOẢNG NHAU.** Dòng tiền của 2 bên ngược pha, một bên xả thì bên kia hứng, tạo thanh khoản giả tạo.')
elif val_pf > 0.3:
    md.append('- **Tự Doanh và Khối Ngoại BẮT TAY NHAU.** Hai thế lực này đang đồng thuận đẩy giá hoặc đè giá VCB.')
else:
    md.append('- **Tự Doanh và Khối Ngoại đánh ĐỘC LẬP.** Không có dấu hiệu hiệp đồng tác chiến rõ rệt.')

val_wf = corr.loc["Whale_Ratio", "Net_Foreign_Vol"]
val_wp = corr.loc["Whale_Ratio", "Prop_Net_Vol"]

if val_wf > 0.3:
    md.append('- Dấu chân cá mập (lệnh cực lớn) **thuộc về Khối Ngoại**. Khối ngoại chính là người chi phối các lệnh quét lớn trên sàn.')
elif val_wp > 0.3:
    md.append('- Dấu chân cá mập (lệnh cực lớn) **thuộc về Tự Doanh**. Tự doanh đang ẩn mình đằng sau những lệnh Mua/Bán size khủng.')
else:
    md.append('- Dấu chân lệnh lớn **THUỘC VỀ TAY TO NỘI (Cá mập trong nước)**. Cả Tây và Tự doanh đều không phải là tác giả của những pha chẻ lệnh khổng lồ.')

md.append(f'- **Nhìn chung 6 tháng qua:** {"Dòng tiền đang âm thầm TÍCH LŨY (Gom hàng)." if sum_active > 0 else "Dòng tiền đang âm thầm PHÂN PHỐI (Xả hàng)." }')

out_path = r'C:\Users\HP\.gemini\antigravity-ide\brain\5700ed55-422a-4dec-94c2-8500778eaea2\vcb_whale_analysis.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md))

print('SUCCESS')
