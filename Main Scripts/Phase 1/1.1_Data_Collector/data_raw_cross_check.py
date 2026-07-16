"""
data_raw_cross_check.py - Kiểm tra tính toàn vẹn dữ liệu raw từ FireAnt
Quét file .parquet trong Phase_1_Data/From_FireAnt, thực hiện 4 phép check chéo:
  1. Volume Balance:  dealVolume + putthroughVolume == totalVolume?
  2. Foreign Boundary: Ngoại mua/bán có vượt tổng KL sàn hoặc room?
  3. OHLC Integrity:   High >= Low, Close nằm trong [Low, High]?
  4. Value Sanity:     totalValue có khớp dealVolume × priceAverage × unit?
Log kết quả vào Log_Debug/Phase 1/Data_Raw_Cross_Check.log

Cách dùng:
  python data_raw_cross_check.py                   # Quét toàn bộ
  python data_raw_cross_check.py VCB FPT SSI       # Chỉ quét 3 mã
  python data_raw_cross_check.py --limit 10        # Quét 10 mã đầu tiên
"""
import os
import sys
import io
import logging
import glob
import pandas as pd
import numpy as np
from datetime import datetime

# Setup encoding cho Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ═══════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════
BASE_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"
FIREANT_DIR = os.path.join(BASE_DIR, "Phase_1_Data", "From_FireAnt")
LOG_DIR = os.path.join(BASE_DIR, "Log_Debug", "Phase 1")
os.makedirs(LOG_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════
log_file = os.path.join(LOG_DIR, "Data_Raw_Cross_Check.log")

# Xóa log cũ mỗi lần chạy
if os.path.exists(log_file):
    os.remove(log_file)

logger = logging.getLogger("DataRawCrossCheck")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

fh = logging.FileHandler(log_file, encoding='utf-8')
fh.setFormatter(formatter)
logger.addHandler(fh)

sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
# Sai số cho phép khi so sánh value (do làm tròn giá)
VALUE_TOLERANCE_PCT = 5.0   # 5% sai lệch chấp nhận được
# Sai số volume balance
VOLUME_TOLERANCE = 1        # Chênh lệch tuyệt đối cho phép (do làm tròn)

# Các cột cần thiết cho từng check
COLS_VOLUME_BALANCE = ['totalVolume', 'dealVolume', 'putthroughVolume']
COLS_FOREIGN = ['buyForeignQuantity', 'sellForeignQuantity', 'dealVolume', 'currentForeignRoom']
COLS_OHLC = ['priceHigh', 'priceLow', 'priceOpen', 'priceClose']
COLS_VALUE = ['totalValue', 'putthroughValue', 'dealVolume', 'priceAverage', 'unit']


def extract_symbol(filepath):
    """Trích mã CK từ tên file (VCB_historical_fireant.parquet -> VCB)."""
    return os.path.basename(filepath).split('_')[0].upper()


# ═══════════════════════════════════════════════════════════════
# CHECK 1: VOLUME BALANCE
# totalVolume == dealVolume + putthroughVolume?
# ═══════════════════════════════════════════════════════════════
def check_volume_balance(df, symbol):
    """
    Kiểm tra: totalVolume = dealVolume + putthroughVolume
    Nếu 1+1 != 2 → tự sửa lại totalVolume = dealVolume + putthroughVolume.
    """
    missing = [c for c in COLS_VOLUME_BALANCE if c not in df.columns]
    if missing:
        return {'status': 'SKIP', 'reason': f'Thiếu cột: {missing}', 'fixed': 0}

    computed = df['dealVolume'].fillna(0) + df['putthroughVolume'].fillna(0)
    actual = df['totalVolume'].fillna(0)
    diff = (actual - computed).abs()

    violations = df[diff > VOLUME_TOLERANCE].copy()
    violations['vol_diff'] = diff[diff > VOLUME_TOLERANCE]
    total_rows = len(df)
    fail_count = len(violations)

    if fail_count == 0:
        return {
            'status': 'PASS',
            'total': total_rows,
            'fails': 0,
            'fixed': 0,
            'detail': 'dealVolume + putthroughVolume == totalVolume cho mọi phiên'
        }
    else:
        # Lấy 3 phiên sai lệch tệ nhất (để log trước khi sửa)
        worst = violations.nlargest(3, 'vol_diff')
        examples = []
        for _, r in worst.iterrows():
            examples.append(
                f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                f"total={r['totalVolume']:,.0f} vs deal+PT={r['dealVolume']:,.0f}+{r['putthroughVolume']:,.0f}"
                f"={r['dealVolume']+r['putthroughVolume']:,.0f} (lệch {r['vol_diff']:,.0f})"
            )

        # ═══ AUTO-FIX: Ép totalVolume = dealVolume + putthroughVolume ═══
        df['totalVolume'] = df['dealVolume'].fillna(0) + df['putthroughVolume'].fillna(0)

        return {
            'status': 'FIXED',
            'total': total_rows,
            'fails': fail_count,
            'fixed': fail_count,
            'pct_fail': fail_count / total_rows * 100,
            'examples': examples
        }


# ═══════════════════════════════════════════════════════════════
# CHECK 2: FOREIGN BOUNDARY
# Khối ngoại mua/bán có vượt tổng KL sàn hoặc room?
# ═══════════════════════════════════════════════════════════════
def check_foreign_boundary(df, symbol):
    """
    Kiểm tra:
    - buyForeignQuantity <= totalVolume (ngoại mua không thể > tổng KL giao dịch)
    - sellForeignQuantity <= totalVolume
    - buyForeignQuantity <= currentForeignRoom (ngoại mua không thể > room còn lại)
    
    Dùng totalVolume (= dealVolume + putthroughVolume) vì khối ngoại có thể
    giao dịch qua cả khớp lệnh lẫn thỏa thuận.
    """
    needed = ['buyForeignQuantity', 'sellForeignQuantity', 'totalVolume']
    missing = [c for c in needed if c not in df.columns]
    if missing:
        return {'status': 'SKIP', 'reason': f'Thiếu cột: {missing}'}

    buy_f = df['buyForeignQuantity'].fillna(0)
    sell_f = df['sellForeignQuantity'].fillna(0)
    total_v = df['totalVolume'].fillna(0)

    violations = []
    fail_indices = set()

    # Check: Ngoại mua > tổng KL giao dịch?
    mask_buy = buy_f > total_v
    if mask_buy.any():
        bad = df[mask_buy]
        for _, r in bad.head(3).iterrows():
            violations.append(
                f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                f"Foreign_Buy={r['buyForeignQuantity']:,.0f} > totalVolume={r['totalVolume']:,.0f}"
            )
        fail_indices.update(bad.index.tolist())

    # Check: Ngoại bán > tổng KL giao dịch?
    mask_sell = sell_f > total_v
    if mask_sell.any():
        bad = df[mask_sell]
        for _, r in bad.head(3).iterrows():
            violations.append(
                f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                f"Foreign_Sell={r['sellForeignQuantity']:,.0f} > totalVolume={r['totalVolume']:,.0f}"
            )
        fail_indices.update(bad.index.tolist())

    # Check: Ngoại mua > room? (nếu có cột currentForeignRoom)
    room_violations = 0
    if 'currentForeignRoom' in df.columns:
        room = df['currentForeignRoom'].fillna(float('inf'))
        # Chỉ check khi room > 0 (có data)
        valid_room = room > 0
        mask_room = (buy_f > room) & valid_room
        room_violations = mask_room.sum()
        if mask_room.any():
            bad = df[mask_room]
            for _, r in bad.head(3).iterrows():
                violations.append(
                    f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                    f"Foreign_Buy={r['buyForeignQuantity']:,.0f} > Room={r['currentForeignRoom']:,.0f}"
                )
            fail_indices.update(bad.index.tolist())

    fail_count = len(fail_indices)
    total_rows = len(df)

    if fail_count == 0:
        return {
            'status': 'PASS',
            'total': total_rows,
            'fails': 0,
            'detail': 'Foreign buy/sell nằm trong giới hạn totalVolume & room'
        }
    else:
        return {
            'status': 'FAIL',
            'total': total_rows,
            'fails': fail_count,
            'pct_fail': fail_count / total_rows * 100,
            'buy_over_total': int(mask_buy.sum()),
            'sell_over_total': int(mask_sell.sum()),
            'buy_over_room': room_violations,
            'examples': violations[:5]
        }


# ═══════════════════════════════════════════════════════════════
# CHECK 3: OHLC PRICE INTEGRITY
# Giá cao >= giá thấp, giá đóng/mở nằm trong range?
# ═══════════════════════════════════════════════════════════════
def check_ohlc_integrity(df, symbol):
    """
    Kiểm tra:
    - priceHigh >= priceLow
    - priceHigh >= priceOpen  &  priceHigh >= priceClose
    - priceLow  <= priceOpen  &  priceLow  <= priceClose
    """
    missing = [c for c in COLS_OHLC if c not in df.columns]
    if missing:
        return {'status': 'SKIP', 'reason': f'Thiếu cột: {missing}'}

    h = df['priceHigh']
    l = df['priceLow']
    o = df['priceOpen']
    c = df['priceClose']

    violations = []
    fail_indices = set()

    # High < Low (vô lý hoàn toàn)
    mask_hl = h < l
    if mask_hl.any():
        bad = df[mask_hl]
        for _, r in bad.head(3).iterrows():
            violations.append(
                f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                f"High={r['priceHigh']:.1f} < Low={r['priceLow']:.1f} ← VÔ LÝ!"
            )
        fail_indices.update(bad.index.tolist())

    # High < Open hoặc High < Close
    mask_ho = h < o
    mask_hc = h < c
    mask_h = mask_ho | mask_hc
    if mask_h.any():
        bad = df[mask_h]
        for _, r in bad.head(3).iterrows():
            violations.append(
                f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                f"High={r['priceHigh']:.1f} nhưng Open={r['priceOpen']:.1f}, Close={r['priceClose']:.1f}"
            )
        fail_indices.update(bad.index.tolist())

    # Low > Open hoặc Low > Close
    mask_lo = l > o
    mask_lc = l > c
    mask_l = mask_lo | mask_lc
    if mask_l.any():
        bad = df[mask_l]
        for _, r in bad.head(3).iterrows():
            violations.append(
                f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                f"Low={r['priceLow']:.1f} nhưng Open={r['priceOpen']:.1f}, Close={r['priceClose']:.1f}"
            )
        fail_indices.update(bad.index.tolist())

    fail_count = len(fail_indices)
    total_rows = len(df)

    if fail_count == 0:
        return {
            'status': 'PASS',
            'total': total_rows,
            'fails': 0,
            'detail': 'OHLC logic đúng: High >= Open/Close >= Low cho mọi phiên'
        }
    else:
        return {
            'status': 'FAIL',
            'total': total_rows,
            'fails': fail_count,
            'pct_fail': fail_count / total_rows * 100,
            'high_lt_low': int(mask_hl.sum()),
            'high_lt_oc': int(mask_h.sum()),
            'low_gt_oc': int(mask_l.sum()),
            'examples': violations[:5]
        }


# ═══════════════════════════════════════════════════════════════
# CHECK 4: VALUE CROSS-VALIDATION
# totalValue ≈ dealVolume × priceAverage × unit?
# ═══════════════════════════════════════════════════════════════
def check_value_sanity(df, symbol):
    """
    Kiểm tra: totalValue gần bằng dealVolume × priceAverage × unit
    Nếu chênh > 5% → data đáng ngờ (giá trị giao dịch không khớp volume × giá).
    
    Lưu ý: totalValue = dealValue + putthroughValue, nên chỉ check khi
    putthroughVolume == 0 hoặc ta trừ đi putthroughValue.
    """
    missing = [c for c in COLS_VALUE if c not in df.columns]
    if missing:
        return {'status': 'SKIP', 'reason': f'Thiếu cột: {missing}'}

    # Chỉ check những phiên có volume > 0 và giá > 0
    valid = (df['dealVolume'] > 0) & (df['priceAverage'] > 0) & (df['unit'] > 0)
    df_check = df[valid].copy()

    if len(df_check) == 0:
        return {'status': 'SKIP', 'reason': 'Không có phiên nào có volume > 0'}

    # Tính deal value (trừ đi putthrough nếu có)
    deal_value_actual = df_check['totalValue'].fillna(0) - df_check['putthroughValue'].fillna(0)
    deal_value_computed = df_check['dealVolume'] * df_check['priceAverage'] * df_check['unit']

    # Tính % sai lệch
    with np.errstate(divide='ignore', invalid='ignore'):
        pct_diff = np.where(
            deal_value_computed != 0,
            np.abs(deal_value_actual - deal_value_computed) / np.abs(deal_value_computed) * 100,
            0
        )

    df_check = df_check.copy()
    df_check['value_pct_diff'] = pct_diff
    df_check['value_computed'] = deal_value_computed
    df_check['value_actual'] = deal_value_actual

    violations = df_check[df_check['value_pct_diff'] > VALUE_TOLERANCE_PCT]
    fail_count = len(violations)
    total_checked = len(df_check)

    if fail_count == 0:
        avg_diff = np.mean(pct_diff)
        return {
            'status': 'PASS',
            'total': total_checked,
            'fails': 0,
            'avg_diff_pct': avg_diff,
            'detail': f'totalValue khớp dealVol×priceAvg×unit (sai lệch TB: {avg_diff:.2f}%)'
        }
    else:
        worst = violations.nlargest(3, 'value_pct_diff')
        examples = []
        for _, r in worst.iterrows():
            examples.append(
                f"{r['Date'].date() if hasattr(r['Date'], 'date') else r['Date']}: "
                f"actual={r['value_actual']:,.0f} vs computed={r['value_computed']:,.0f} "
                f"(lệch {r['value_pct_diff']:.1f}%)"
            )
        return {
            'status': 'FAIL',
            'total': total_checked,
            'fails': fail_count,
            'pct_fail': fail_count / total_checked * 100,
            'examples': examples
        }


# ═══════════════════════════════════════════════════════════════
# MAIN: Chạy tất cả 4 check cho 1 file
# ═══════════════════════════════════════════════════════════════
def cross_check_single(filepath):
    """Chạy 4 phép kiểm tra cho 1 file .parquet. Return dict kết quả."""
    symbol = extract_symbol(filepath)

    try:
        df = pd.read_parquet(filepath)
    except Exception as e:
        logger.error(f"  [{symbol}] Không đọc được file: {e}")
        return None

    # Chuẩn hóa cột Date
    if 'Date' not in df.columns:
        if 'date' in df.columns:
            df['Date'] = pd.to_datetime(df['date'])
        else:
            logger.warning(f"  [{symbol}] Không tìm thấy cột Date → BỎ QUA.")
            return None
    else:
        df['Date'] = pd.to_datetime(df['Date'])

    df = df.sort_values('Date').reset_index(drop=True)
    total_rows = len(df)

    # Chạy 4 checks (Volume_Balance chạy TRƯỚC vì nó có thể auto-fix totalVolume,
    # ảnh hưởng đến Foreign_Boundary check sau đó)
    checks = {
        'Volume_Balance': check_volume_balance(df, symbol),
        'Foreign_Boundary': check_foreign_boundary(df, symbol),
        'OHLC_Integrity': check_ohlc_integrity(df, symbol),
        'Value_Sanity': check_value_sanity(df, symbol),
    }

    # Đếm kết quả
    pass_count = sum(1 for v in checks.values() if v['status'] == 'PASS')
    fail_count = sum(1 for v in checks.values() if v['status'] == 'FAIL')
    skip_count = sum(1 for v in checks.values() if v['status'] == 'SKIP')
    fixed_count = sum(1 for v in checks.values() if v['status'] == 'FIXED')
    total_fixed_rows = sum(v.get('fixed', 0) for v in checks.values())

    # Phán quyết tổng thể (FIXED không tính là FAIL vì đã sửa)
    if fail_count == 0 and skip_count == 0:
        verdict = "SẠCH" if fixed_count == 0 else "SẠCH (đã auto-fix)"
    elif fail_count == 0:
        verdict = "SẠCH (có check bị skip)"
    elif fail_count <= 1:
        verdict = "ĐÁNG NGỜ"
    else:
        verdict = "DATA CÓ VẤN ĐỀ"

    # Log chi tiết
    logger.info(f"  [{symbol}] {total_rows} phiên | Verdict: {verdict} "
                f"(PASS={pass_count}, FAIL={fail_count}, FIXED={fixed_count}, SKIP={skip_count})")

    for check_name, result in checks.items():
        status = result['status']
        if status == 'PASS':
            logger.info(f"    ✅ {check_name}: PASS — {result.get('detail', '')}")
        elif status == 'SKIP':
            logger.info(f"    ⏭️  {check_name}: SKIP — {result.get('reason', '')}")
        elif status == 'FIXED':
            # Auto-fixed
            fails = result.get('fails', 0)
            total = result.get('total', 0)
            pct = result.get('pct_fail', 0)
            logger.warning(f"    🔧 {check_name}: FIXED — {fails} phiên bị lệch → đã tự sửa totalVolume")
            for ex in result.get('examples', []):
                logger.warning(f"       → {ex}")
        else:
            # FAIL
            fails = result.get('fails', 0)
            total = result.get('total', 0)
            pct = result.get('pct_fail', 0)
            logger.warning(f"    ❌ {check_name}: FAIL — {fails}/{total} phiên lỗi ({pct:.1f}%)")

            # Log thêm detail cho Foreign
            if check_name == 'Foreign_Boundary':
                if result.get('buy_over_total', 0) > 0:
                    logger.warning(f"       Buy > TotalVol: {result['buy_over_total']} phiên")
                if result.get('sell_over_total', 0) > 0:
                    logger.warning(f"       Sell > TotalVol: {result['sell_over_total']} phiên")
                if result.get('buy_over_room', 0) > 0:
                    logger.warning(f"       Buy > Room: {result['buy_over_room']} phiên")

            # Log thêm detail cho OHLC
            if check_name == 'OHLC_Integrity':
                if result.get('high_lt_low', 0) > 0:
                    logger.warning(f"       High < Low: {result['high_lt_low']} phiên")

            # Log examples
            for ex in result.get('examples', []):
                logger.warning(f"       → {ex}")

    # Lưu file lại nếu có auto-fix
    if total_fixed_rows > 0:
        try:
            df.to_parquet(filepath, index=False)
            logger.info(f"    💾 Đã lưu file đã sửa: {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"    ❌ Không lưu được file: {e}")

    return {
        'symbol': symbol,
        'total_rows': total_rows,
        'verdict': verdict,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'fixed_count': fixed_count,
        'skip_count': skip_count,
        'checks': checks,
    }


def run_cross_check(symbols=None, limit=None):
    """
    Quét file .parquet trong From_FireAnt và chạy cross-check data integrity.

    Args:
        symbols: list mã cụ thể (VD: ['VCB', 'FPT']). None = quét tất cả.
        limit: giới hạn số file xử lý. None = không giới hạn.
    """
    logger.info("=" * 70)
    logger.info(f"DATA RAW CROSS-CHECK (Data Integrity)")
    logger.info(f"Bắt đầu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Thư mục: {FIREANT_DIR}")
    logger.info("=" * 70)
    logger.info("4 phép kiểm tra:")
    logger.info("  1. Volume Balance:   dealVol + putthroughVol == totalVol?")
    logger.info("  2. Foreign Boundary: Ngoại mua/bán <= totalVol & <= room?")
    logger.info("  3. OHLC Integrity:   High >= Open/Close >= Low?")
    logger.info("  4. Value Sanity:     totalValue ≈ dealVol × avgPrice × unit?")
    logger.info("-" * 70)

    # Tìm file .parquet
    if symbols:
        parquet_files = []
        for sym in symbols:
            matched = glob.glob(os.path.join(FIREANT_DIR, f"{sym.upper()}_*.parquet"))
            if matched:
                parquet_files.extend(matched)
            else:
                logger.warning(f"Không tìm thấy file cho mã: {sym}")
        parquet_files = sorted(parquet_files)
        logger.info(f"Chế độ: Quét {len(parquet_files)} mã chỉ định → "
                     f"{[extract_symbol(f) for f in parquet_files]}")
    else:
        parquet_files = sorted(glob.glob(os.path.join(FIREANT_DIR, "*.parquet")))

    if not parquet_files:
        logger.error("Không tìm thấy file .parquet nào!")
        return

    if limit and limit < len(parquet_files):
        parquet_files = parquet_files[:limit]
        logger.info(f"Chế độ: Giới hạn {limit} file đầu tiên")

    total_files = len(parquet_files)
    logger.info(f"Sẽ xử lý {total_files} file")
    logger.info("-" * 70)

    results = []
    clean_symbols = []
    suspect_symbols = []
    dirty_symbols = []

    for i, fpath in enumerate(parquet_files, 1):
        symbol = extract_symbol(fpath)
        logger.info(f"[{i}/{total_files}] {symbol}")

        result = cross_check_single(fpath)
        if result:
            results.append(result)
            if 'SẠCH' in result['verdict']:
                clean_symbols.append(symbol)
            elif result['verdict'] == 'ĐÁNG NGỜ':
                suspect_symbols.append(symbol)
            else:
                dirty_symbols.append(symbol)

        logger.info("-" * 40)

    # ═══════════════════════════════════════════════════════════════
    # TỔNG KẾT
    # ═══════════════════════════════════════════════════════════════
    logger.info("=" * 70)
    logger.info("TỔNG KẾT DATA INTEGRITY CHECK")
    logger.info("=" * 70)
    logger.info(f"Tổng file quét:  {total_files}")
    logger.info(f"✅ SẠCH:         {len(clean_symbols)}")
    logger.info(f"⚠️  ĐÁNG NGỜ:     {len(suspect_symbols)}")
    logger.info(f"❌ CÓ VẤN ĐỀ:    {len(dirty_symbols)}")

    # Thống kê theo từng check
    if results:
        logger.info("")
        logger.info("CHI TIẾT THEO TỪNG PHÉP KIỂM TRA:")
        for check_name in ['Volume_Balance', 'Foreign_Boundary', 'OHLC_Integrity', 'Value_Sanity']:
            pass_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'PASS')
            fail_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'FAIL')
            fixed_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'FIXED')
            skip_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'SKIP')
            logger.info(f"  {check_name:<20} → PASS={pass_c} | FAIL={fail_c} | FIXED={fixed_c} | SKIP={skip_c}")

    # List các mã có vấn đề
    if suspect_symbols:
        logger.warning("")
        logger.warning(f"⚠️  CÁC MÃ ĐÁNG NGỜ ({len(suspect_symbols)}):")
        for sym in suspect_symbols:
            r = next(x for x in results if x['symbol'] == sym)
            fails = [k for k, v in r['checks'].items() if v['status'] == 'FAIL']
            logger.warning(f"  {sym}: fail ở {fails}")

    if dirty_symbols:
        logger.warning("")
        logger.warning(f"❌ CÁC MÃ CÓ VẤN ĐỀ ({len(dirty_symbols)}):")
        for sym in dirty_symbols:
            r = next(x for x in results if x['symbol'] == sym)
            fails = [k for k, v in r['checks'].items() if v['status'] == 'FAIL']
            logger.warning(f"  {sym}: fail ở {fails}")

    logger.info("")
    logger.info(f"Hoàn thành: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Cross-check data integrity từ FireAnt')
    parser.add_argument('symbols', nargs='*',
                        help='Mã CK cần quét (VD: VCB FPT). Bỏ trống = quét tất cả.')
    parser.add_argument('--limit', type=int, default=None,
                        help='Giới hạn số file (VD: --limit 10)')
    args = parser.parse_args()

    run_cross_check(
        symbols=args.symbols if args.symbols else None,
        limit=args.limit
    )
