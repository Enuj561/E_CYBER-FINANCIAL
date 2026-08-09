"""
Module:  E_foreign_boundary_validator
Logic:   Check if foreign buy/sell stays within totalVolume and room limits
Detail:  Kiểm tra khối ngoại mua/bán không vượt tổng KL sàn hoặc room còn lại.
"""


def check_foreign_boundary(df, symbol):
    """
    Kiểm tra:
    - buyForeignQuantity <= totalVolume (ngoại mua không thể > tổng KL giao dịch)
    - sellForeignQuantity <= totalVolume
    - buyForeignQuantity <= currentForeignRoom (ngoại mua không thể > room còn lại)
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
