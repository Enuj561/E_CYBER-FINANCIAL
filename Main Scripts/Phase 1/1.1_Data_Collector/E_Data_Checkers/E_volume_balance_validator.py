"""
Module:  E_volume_balance_validator
Logic:   Check if totalVolume == dealVolume + putthroughVolume
Detail:  Kiểm tra cân bằng khối lượng giao dịch. Tự sửa (auto-fix) nếu phát hiện lệch.
"""

# Sai số volume balance cho phép (do làm tròn)
VOLUME_TOLERANCE = 1

# Các cột cần thiết
COLS_VOLUME_BALANCE = ['totalVolume', 'dealVolume', 'putthroughVolume']


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

        # AUTO-FIX: Ép totalVolume = dealVolume + putthroughVolume
        df['totalVolume'] = df['dealVolume'].fillna(0) + df['putthroughVolume'].fillna(0)

        return {
            'status': 'FIXED',
            'total': total_rows,
            'fails': fail_count,
            'fixed': fail_count,
            'pct_fail': fail_count / total_rows * 100,
            'examples': examples
        }
