"""Kiểm tra Validator BCTC; chỉ dùng DataFrame trong bộ nhớ."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
import sys
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
sys.path.insert(0, str(BCTC_DIR))

from E_bctc_normalizer import BCTCNormalizer  # noqa: E402
from E_bctc_schema import RECORD_COLUMNS  # noqa: E402
from E_bctc_validator import BCTCValidator  # noqa: E402


COLLECTED_AT = "2026-08-09T22:00:00+07:00"
AS_OF_DATE = date(2026, 8, 9)


def normalized_balance(values=(1000, 600, 400)) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "item": ["Tài sản", "Nợ", "Vốn"],
            "item_id": ["asset", "liability", "equity"],
            "2025": list(values),
        }
    )
    result = BCTCNormalizer().normalize_vci(
        frame,
        run_id="run-test",
        symbol="FPT",
        company_type="general",
        report_type="balance_sheet",
        period_type="year",
        collected_at=COLLECTED_AT,
        raw_file="raw/vci.parquet",
    )
    result["canonical_item_id"] = ["total_assets", "total_liabilities", "total_equity"]
    result["mapping_status"] = "confirmed"
    return result


def issue_codes(report) -> set[str]:
    return {issue.code for issue in report.errors}


class BCTCValidatorTests(unittest.TestCase):
    def test_valid_data_and_balance_equation_pass(self):
        records = normalized_balance()
        original = records.copy(deep=True)
        report = BCTCValidator().validate(
            records,
            collection_status="complete",
            expected_symbol="FPT",
            expected_source="vnstock",
            as_of_date=AS_OF_DATE,
        )
        self.assertTrue(report.is_valid, report.errors)
        self.assertEqual(report.checked_rows, 3)
        pd.testing.assert_frame_equal(records, original)

    def test_unreadable_file_result_is_blocked(self):
        report = BCTCValidator().validate(
            None, load_error=OSError("parquet damaged"), as_of_date=AS_OF_DATE
        )
        self.assertFalse(report.is_valid)
        self.assertIn("file_unreadable", issue_codes(report))

    def test_wrong_symbol_source_and_provider_are_blocked(self):
        records = normalized_balance()
        records.loc[0, "source"] = "fireant"
        report = BCTCValidator().validate(
            records,
            expected_symbol="VCB",
            expected_source="vnstock",
            as_of_date=AS_OF_DATE,
        )
        codes = issue_codes(report)
        self.assertIn("mixed_sources", codes)
        self.assertIn("wrong_symbol", codes)
        self.assertIn("invalid_source_provider", codes)

    def test_future_and_mismatched_period_are_blocked(self):
        records = normalized_balance()
        records.loc[0, ["fiscal_year", "period_key"]] = [2027, "2027"]
        records.loc[1, "period_key"] = "2024"
        report = BCTCValidator().validate(records, as_of_date=AS_OF_DATE)
        codes = issue_codes(report)
        self.assertIn("future_period", codes)
        self.assertIn("period_key_mismatch", codes)

    def test_current_year_ratio_is_warning_but_future_year_is_blocked(self):
        current = normalized_balance().iloc[[0]].copy()
        current["report_type"] = "ratio"
        current["period_value_mode"] = "unknown"
        current[["fiscal_year", "period_key"]] = [2026, "2026"]
        report = BCTCValidator().validate(current, as_of_date=AS_OF_DATE)
        self.assertTrue(report.is_valid)
        self.assertIn("current_year_ratio_incomplete", {x.code for x in report.warnings})

        current[["fiscal_year", "period_key"]] = [2027, "2027"]
        report = BCTCValidator().validate(current, as_of_date=AS_OF_DATE)
        self.assertIn("future_period", issue_codes(report))

    def test_exact_duplicate_and_duplicate_key_are_blocked(self):
        records = normalized_balance()
        records = pd.concat([records, records.iloc[[0]]], ignore_index=True)
        report = BCTCValidator().validate(records, as_of_date=AS_OF_DATE)
        codes = issue_codes(report)
        self.assertIn("exact_duplicate_rows", codes)
        self.assertIn("duplicate_record_keys", codes)

    def test_parse_error_missing_unit_and_wrong_vnd_are_blocked(self):
        records = normalized_balance()
        records.loc[0, "record_status"] = "parse_error"
        records.loc[1, "source_unit"] = "unknown"
        records.loc[2, "value_vnd"] = 999
        report = BCTCValidator().validate(records, as_of_date=AS_OF_DATE)
        codes = issue_codes(report)
        self.assertIn("value_parse_error", codes)
        self.assertIn("money_without_unit", codes)
        self.assertIn("wrong_vnd_conversion", codes)

    def test_empty_status_cannot_lie(self):
        empty = pd.DataFrame(columns=RECORD_COLUMNS)
        false_success = BCTCValidator().validate(
            empty, collection_status="complete", as_of_date=AS_OF_DATE
        )
        self.assertIn("empty_marked_success", issue_codes(false_success))

        records = normalized_balance()
        false_empty = BCTCValidator().validate(
            records, collection_status="no_data_confirmed", as_of_date=AS_OF_DATE
        )
        self.assertIn("data_present_marked_empty", issue_codes(false_empty))

    def test_financial_equation_failure_has_real_tolerance(self):
        records = normalized_balance(values=(1010, 600, 400))
        report = BCTCValidator().validate(records, as_of_date=AS_OF_DATE)
        failures = [issue for issue in report.errors if issue.code == "financial_equation_failed"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].context["equation"], "assets_equal_liabilities_plus_equity")
        self.assertGreater(failures[0].context["difference"], failures[0].context["allowed_difference"])

    def test_rounding_tolerance_depends_on_source_unit(self):
        records = normalized_balance(values=(1002, 600, 400))
        records["source_unit"] = "thousand_VND"
        records["unit_multiplier_to_vnd"] = 1000.0
        records["value_vnd"] = records["value_numeric"] * 1000.0
        report = BCTCValidator().validate(records, as_of_date=AS_OF_DATE)
        equation_failures = [
            issue for issue in report.errors if issue.code == "financial_equation_failed"
        ]
        self.assertEqual(equation_failures, [])

    def test_missing_confirmed_mapping_is_reported_as_skipped_not_passed(self):
        records = normalized_balance()
        records["mapping_status"] = "unmapped"
        records["canonical_item_id"] = None
        report = BCTCValidator().validate(records, as_of_date=AS_OF_DATE)
        skipped_names = {
            issue.context.get("equation") for issue in report.skipped_checks
        }
        self.assertIn("assets_equal_liabilities_plus_equity", skipped_names)
        self.assertTrue(report.is_valid)

    def test_unknown_information_is_reported_as_warning(self):
        records = BCTCNormalizer().normalize_fireant(
            [
                {
                    "year": 2025,
                    "quarter": 0,
                    "companyType": "General",
                    "financialValues": {"MysteryMetric": 10},
                }
            ],
            run_id="run-test",
            symbol="FPT",
            period_type="year",
            collected_at=COLLECTED_AT,
            raw_file="raw/fireant.json",
        )
        report = BCTCValidator().validate(records, as_of_date=AS_OF_DATE)
        warning_codes = {issue.code for issue in report.warnings}
        self.assertIn("unclassified_report_type", warning_codes)
        self.assertIn("unknown_unit", warning_codes)
        self.assertIn("missing_publication_date", warning_codes)
        self.assertTrue(report.is_valid)


if __name__ == "__main__":
    unittest.main()
