"""
Module:  E_ohlc_integrity_validator
Logic:   Check if OHLC prices are logically consistent
Detail:  Kiểm tra giá High >= Low, Close/Open nằm trong range [Low, High].
"""

# Các cột cần thiết
COLS_OHLC = ['priceHigh', 'priceLow', 'priceOpen', 'priceClose']


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
