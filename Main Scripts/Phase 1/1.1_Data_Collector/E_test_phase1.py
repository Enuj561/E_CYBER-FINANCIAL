"""
Module:  E_test_phase1
Logic:   Unit tests for Phase 1 data collection and integrity
Detail:  Test tự động cho các chức năng Phase 1. Dùng pytest + mock data.
         Chạy: pytest E_test_phase1.py -v
"""
import pytest
import pandas as pd
import numpy as np


class TestVolumeBalance:
    """Test check volume balance: totalVolume == dealVolume + putthroughVolume."""

    def test_pass_when_balanced(self):
        """Khi deal + putthrough == total → PASS."""
        from E_Data_Checkers import check_volume_balance
        df = pd.DataFrame({
            'Date': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'totalVolume': [1000, 2000],
            'dealVolume': [800, 1500],
            'putthroughVolume': [200, 500],
        })
        result = check_volume_balance(df, 'TEST')
        assert result['status'] == 'PASS'

    def test_fixed_when_unbalanced(self):
        """Khi deal + putthrough != total → FIXED (auto-fix)."""
        from E_Data_Checkers import check_volume_balance
        df = pd.DataFrame({
            'Date': pd.to_datetime(['2024-01-01']),
            'totalVolume': [9999],
            'dealVolume': [800],
            'putthroughVolume': [200],
        })
        result = check_volume_balance(df, 'TEST')
        assert result['status'] == 'FIXED'
        assert df['totalVolume'].iloc[0] == 1000  # đã sửa


class TestOHLCIntegrity:
    """Test check OHLC: High >= Low, Close trong range."""

    def test_pass_valid_ohlc(self):
        """OHLC hợp lệ → PASS."""
        from E_Data_Checkers import check_ohlc_integrity
        df = pd.DataFrame({
            'Date': pd.to_datetime(['2024-01-01']),
            'priceHigh': [100.0],
            'priceLow': [90.0],
            'priceOpen': [95.0],
            'priceClose': [98.0],
        })
        result = check_ohlc_integrity(df, 'TEST')
        assert result['status'] == 'PASS'

    def test_fail_high_lt_low(self):
        """High < Low → FAIL."""
        from E_Data_Checkers import check_ohlc_integrity
        df = pd.DataFrame({
            'Date': pd.to_datetime(['2024-01-01']),
            'priceHigh': [80.0],
            'priceLow': [90.0],
            'priceOpen': [85.0],
            'priceClose': [85.0],
        })
        result = check_ohlc_integrity(df, 'TEST')
        assert result['status'] == 'FAIL'
