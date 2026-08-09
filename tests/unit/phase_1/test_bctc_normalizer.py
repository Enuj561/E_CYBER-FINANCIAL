"""Kiểm tra sắp BCTC về mẫu chung; không gọi mạng và không ghi file."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
sys.path.insert(0, str(BCTC_DIR))

from E_bctc_normalizer import BCTCNormalizer, OUTPUT_COLUMNS  # noqa: E402


COLLECTED_AT = "2026-08-09T22:00:00+07:00"


class VCINormalizerTests(unittest.TestCase):
    def test_duplicate_rows_and_period_columns_are_all_preserved(self):
        frame = pd.DataFrame(
            [
                ["Tổng tài sản", "Total assets", "total_assets", 100, 101],
                ["Tổng tài sản lặp", "Total assets duplicate", "total_assets", 200, 201],
            ],
            columns=["item", "item_en", "item_id", "2026-Q1", "2026-Q1"],
        )
        original = frame.copy(deep=True)

        result = BCTCNormalizer().normalize_vci(
            frame,
            run_id="run-test",
            symbol="fpt",
            company_type="General",
            report_type="balance_sheet",
            period_type="quarter",
            collected_at=COLLECTED_AT,
            raw_file="raw/vci.parquet",
        )

        self.assertEqual(len(result), 4)
        self.assertEqual(set(result["source_period_column_number"]), {1, 2})
        self.assertEqual(result["source_item_key"].nunique(), 4)
        self.assertEqual(set(result["source_row_number"]), {1, 2})
        self.assertEqual(result["value_vnd"].tolist(), [100.0, 101.0, 200.0, 201.0])
        self.assertTrue((result["period_value_mode"] == "point_in_time").all())
        pd.testing.assert_frame_equal(frame, original)

    def test_year_cash_flow_is_cumulative_and_missing_dates_stay_empty(self):
        frame = pd.DataFrame(
            {"item": ["Dòng tiền"], "item_id": ["cash"], "2025": [50]}
        )
        result = BCTCNormalizer().normalize_vci(
            frame,
            run_id="run-test",
            symbol="VCB",
            company_type="Bank",
            report_type="cash_flow",
            period_type="year",
            collected_at=COLLECTED_AT,
            raw_file="raw/vci.parquet",
        )
        row = result.iloc[0]
        self.assertEqual(row["company_type"], "bank")
        self.assertEqual(row["period_value_mode"], "cumulative")
        self.assertEqual(row["cash_flow_method"], "unknown")
        self.assertIsNone(row["publication_date"])
        self.assertIsNone(row["availability_date"])
        self.assertEqual(row["consolidation_status"], "unknown")

    def test_ratio_is_not_converted_to_vnd(self):
        frame = pd.DataFrame({"item_id": ["roe"], "2025": [0.25]})
        result = BCTCNormalizer().normalize_vci(
            frame,
            run_id="run-test",
            symbol="SSI",
            company_type="Securities",
            report_type="ratio",
            period_type="year",
            collected_at=COLLECTED_AT,
            raw_file="raw/vci.parquet",
        )
        row = result.iloc[0]
        self.assertEqual(row["value_type"], "ratio")
        self.assertEqual(row["currency"], "not_applicable")
        self.assertIsNone(row["value_vnd"])

    def test_ratio_control_rows_stay_in_raw_but_not_financial_records(self):
        frame = pd.DataFrame({
            "item_id": ["year", "quarter", "ratioTTMId", "ratioType", "pe_ratio"],
            "2025-Q1": [2025, 1, 123, "RATIO_TTM", 12.5],
        })
        result = BCTCNormalizer().normalize_vci(
            frame, run_id="run-test", symbol="FPT", company_type="general",
            report_type="ratio", period_type="quarter", collected_at=COLLECTED_AT,
            raw_file="raw/vci.parquet",
        )
        self.assertEqual(result["source_item_id"].tolist(), ["pe_ratio"])

    def test_mixed_period_columns_keep_requested_kind_and_raise_quality_flag(self):
        frame = pd.DataFrame({"item_id": ["asset"], "2026-Q1": [10], "2025": [9]})
        result = BCTCNormalizer().normalize_vci(
            frame, run_id="run-test", symbol="FPT", company_type="general",
            report_type="balance_sheet", period_type="year",
            collected_at=COLLECTED_AT, raw_file="raw/vci.parquet",
        )
        self.assertEqual(result["period_key"].tolist(), ["2025"])
        self.assertIn("source_mixed_period_columns", result.iloc[0]["quality_flags"])

    def test_nonempty_vci_without_requested_period_is_rejected(self):
        frame = pd.DataFrame({"item_id": ["asset"], "note": ["không có cột kỳ"]})
        with self.assertRaisesRegex(ValueError, "không có cột kỳ"):
            BCTCNormalizer().normalize_vci(
                frame, run_id="run-test", symbol="FPT", company_type="general",
                report_type="balance_sheet", period_type="year",
                collected_at=COLLECTED_AT, raw_file="raw/vci.parquet",
            )


class FireAntNormalizerTests(unittest.TestCase):
    def test_confirmed_and_unknown_items_are_both_preserved(self):
        payload = [
            {
                "symbol": "FPT",
                "year": 2026,
                "quarter": 2,
                "companyType": "General",
                "financialValues": {
                    "Quarter": 2,
                    "Year": 2026,
                    "CompanyType": "General",
                    "TotalAsset": 1000,
                    "MysteryMetric": "chưa rõ",
                    "MissingMetric": None,
                },
            }
        ]
        original = deepcopy(payload)
        result = BCTCNormalizer().normalize_fireant(
            payload,
            run_id="run-test",
            symbol="fpt",
            period_type="quarter",
            collected_at=COLLECTED_AT,
            raw_file="raw/fireant.json",
        )

        self.assertEqual(len(result), 3)
        assets = result[result["source_item_id"] == "TotalAsset"].iloc[0]
        mystery = result[result["source_item_id"] == "MysteryMetric"].iloc[0]
        missing = result[result["source_item_id"] == "MissingMetric"].iloc[0]
        self.assertEqual(assets["report_type"], "balance_sheet")
        self.assertEqual(assets["value_vnd"], 1000.0)
        self.assertEqual(assets["record_status"], "valid")
        self.assertEqual(mystery["report_type"], "unknown")
        self.assertIn("unclassified_report_type", mystery["quality_flags"])
        self.assertEqual(mystery["value_text"], "chưa rõ")
        self.assertEqual(missing["record_status"], "source_null")
        self.assertEqual(payload, original)

    def test_all_supported_company_types_keep_their_identity(self):
        normalizer = BCTCNormalizer()
        expected = {
            "General": "general",
            "Bank": "bank",
            "Securities": "securities",
            "Insurance": "insurance",
        }
        for source_value, normalized_value in expected.items():
            with self.subTest(company_type=source_value):
                result = normalizer.normalize_fireant(
                    [
                        {
                            "year": 2025,
                            "quarter": 0,
                            "companyType": source_value,
                            "financialValues": {"TotalAsset": 1},
                        }
                    ],
                    run_id="run-test",
                    symbol="TEST",
                    period_type="year",
                    collected_at=COLLECTED_AT,
                    raw_file="raw/fireant.json",
                )
                self.assertEqual(result.iloc[0]["company_type"], normalized_value)

    def test_fireant_quarter_inside_year_data_is_rejected(self):
        with self.assertRaises(ValueError):
            BCTCNormalizer().normalize_fireant(
                [{"year": 2025, "quarter": 4, "financialValues": {"TotalAsset": 1}}],
                run_id="run-test",
                symbol="FPT",
                period_type="year",
                collected_at=COLLECTED_AT,
                raw_file="raw/fireant.json",
            )

    def test_empty_input_returns_contract_columns(self):
        result = BCTCNormalizer().normalize_fireant(
            [],
            run_id="run-test",
            symbol="FPT",
            period_type="year",
            collected_at=COLLECTED_AT,
            raw_file="raw/fireant.json",
        )
        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), OUTPUT_COLUMNS)


if __name__ == "__main__":
    unittest.main()
