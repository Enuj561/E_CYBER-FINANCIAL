"""
Module:  E_data_raw_cross_check
Logic:   Orchestrate all 4 data integrity checks on FireAnt parquet files
Detail:  Quét file .parquet trong Phase_1_Data/E_OHLCV/From_FireAnt, gọi 4 phép check từ
         package integrity_checks/, tổng hợp kết quả và ghi log.

Cách dùng:
  python E_data_raw_cross_check.py                   # Quét toàn bộ
  python E_data_raw_cross_check.py VCB FPT SSI       # Chỉ quét 3 mã
  python E_data_raw_cross_check.py --limit 10        # Quét 10 mã đầu tiên
"""
import os
import sys
import io
import logging
import glob
import pandas as pd
from datetime import datetime

# Setup encoding cho Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import centralized paths
from E_Helper.E_config import FIREANT_DIR, LOG_DIR
# Import ghi file an toàn
from E_Helper.E_io_utils import safe_write_parquet
# Import 4 checks
from E_Data_Checkers import (
    check_volume_balance,
    check_foreign_boundary,
    check_ohlc_integrity,
    check_value_sanity,
)

# ═══════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════
PHASE1_LOG_DIR = os.path.join(LOG_DIR, "Phase 1")
os.makedirs(PHASE1_LOG_DIR, exist_ok=True)
log_file = os.path.join(PHASE1_LOG_DIR, "Data_Raw_Cross_Check.log")

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
# HELPER
# ═══════════════════════════════════════════════════════════════
def extract_symbol(filepath):
    """Trích mã CK từ tên file (VCB_historical_fireant.parquet -> VCB)."""
    return os.path.basename(filepath).split('_')[0].upper()


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
            logger.warning(f"    🔧 {check_name}: FIXED — {result.get('fails', 0)} phiên bị lệch → đã tự sửa totalVolume")
            for ex in result.get('examples', []):
                logger.warning(f"       → {ex}")
        else:
            fails = result.get('fails', 0)
            total = result.get('total', 0)
            pct = result.get('pct_fail', 0)
            logger.warning(f"    ❌ {check_name}: FAIL — {fails}/{total} phiên lỗi ({pct:.1f}%)")

            if check_name == 'Foreign_Boundary':
                if result.get('buy_over_total', 0) > 0:
                    logger.warning(f"       Buy > TotalVol: {result['buy_over_total']} phiên")
                if result.get('sell_over_total', 0) > 0:
                    logger.warning(f"       Sell > TotalVol: {result['sell_over_total']} phiên")
                if result.get('buy_over_room', 0) > 0:
                    logger.warning(f"       Buy > Room: {result['buy_over_room']} phiên")

            if check_name == 'OHLC_Integrity':
                if result.get('high_lt_low', 0) > 0:
                    logger.warning(f"       High < Low: {result['high_lt_low']} phiên")

            for ex in result.get('examples', []):
                logger.warning(f"       → {ex}")

    # Lưu file lại nếu có auto-fix (ghi an toàn)
    if total_fixed_rows > 0:
        try:
            safe_write_parquet(filepath, df)
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

    # TỔNG KẾT
    logger.info("=" * 70)
    logger.info("TỔNG KẾT DATA INTEGRITY CHECK")
    logger.info("=" * 70)
    logger.info(f"Tổng file quét:  {total_files}")
    logger.info(f"✅ SẠCH:         {len(clean_symbols)}")
    logger.info(f"⚠️  ĐÁNG NGỜ:     {len(suspect_symbols)}")
    logger.info(f"❌ CÓ VẤN ĐỀ:    {len(dirty_symbols)}")

    if results:
        logger.info("")
        logger.info("CHI TIẾT THEO TỪNG PHÉP KIỂM TRA:")
        for check_name in ['Volume_Balance', 'Foreign_Boundary', 'OHLC_Integrity', 'Value_Sanity']:
            pass_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'PASS')
            fail_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'FAIL')
            fixed_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'FIXED')
            skip_c = sum(1 for r in results if r['checks'][check_name]['status'] == 'SKIP')
            logger.info(f"  {check_name:<20} → PASS={pass_c} | FAIL={fail_c} | FIXED={fixed_c} | SKIP={skip_c}")

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
