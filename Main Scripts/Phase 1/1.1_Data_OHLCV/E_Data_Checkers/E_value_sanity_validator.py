"""
Module:  E_value_sanity_validator
Logic:   Check if totalValue ≈ dealVolume × priceAverage × unit
Detail:  Kiểm tra giá trị giao dịch có khớp với volume × giá trung bình × đơn vị hay không.
"""
import numpy as np

# Sai số cho phép khi so sánh value (do làm tròn giá)
VALUE_TOLERANCE_PCT = 5.0   # 5% sai lệch chấp nhận được

# Các cột cần thiết
COLS_VALUE = ['totalValue', 'putthroughValue', 'dealVolume', 'priceAverage', 'unit']


def check_value_sanity(df, symbol):
    """
    Kiểm tra: totalValue gần bằng dealVolume × priceAverage × unit
    Nếu chênh > 5% → data đáng ngờ.
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
