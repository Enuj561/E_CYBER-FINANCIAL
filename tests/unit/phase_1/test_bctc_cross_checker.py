"""Kiểm tra đối chiếu BCTC; không gọi mạng và không ghi file."""

from pathlib import Path
import sys
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
sys.path.insert(0, str(BCTC_DIR))

from E_bctc_cross_checker import BCTCCrossChecker  # noqa: E402
from E_bctc_normalizer import BCTCNormalizer  # noqa: E402
from E_bctc_schema import RECORD_COLUMNS, SCHEMA_VERSION  # noqa: E402
from E_bctc_validator import BCTCValidator  # noqa: E402


def record(source, item, value, **changes):
    row = {column: None for column in RECORD_COLUMNS}
    row.update(
        schema_version=SCHEMA_VERSION, run_id="test", source=source,
        provider="fireant_api" if source == "fireant" else "vci", symbol="FPT",
        company_type="general", report_type="balance_sheet", cash_flow_method="not_applicable",
        period_type="year", fiscal_year=2025, period_key="2025",
        period_value_mode="point_in_time", consolidation_status="unknown",
        source_item_id=f"{source}_{item}", source_row_number=1,
        source_item_key=f"{source}:{item}", canonical_item_id=item,
        mapping_version="map-1", mapping_status="confirmed", value_raw=value,
        value_numeric=value, value_type="money", currency="VND", source_unit="VND",
        unit_multiplier_to_vnd=1.0, value_vnd=value, record_status="ok", quality_flags=None,
    )
    row.update(changes)
    return row


class BCTCCrossCheckerTests(unittest.TestCase):
    def setUp(self):
        self.checker = BCTCCrossChecker()

    def test_equal_and_different_values_keep_both_sources(self):
        fireant = pd.DataFrame([record("fireant", "assets", 100), record("fireant", "equity", 60)])
        vnstock = pd.DataFrame([record("vnstock", "assets", 100), record("vnstock", "equity", 50)])
        result = self.checker.compare(fireant, vnstock).set_index("canonical_item_id")
        self.assertEqual(result.loc["assets", "comparison_status"], "matched")
        self.assertEqual(result.loc["equity", "comparison_status"], "different")
        self.assertEqual(result.loc["equity", "fireant_value_vnd"], 60)
        self.assertEqual(result.loc["equity", "vnstock_value_vnd"], 50)
        self.assertEqual(result.loc["equity", "absolute_difference"], 10)
        self.assertAlmostEqual(result.loc["equity", "difference_percent"], 100 / 6)

    def test_values_match_after_each_source_is_converted_to_vnd(self):
        fireant = pd.DataFrame([
            record("fireant", "assets", 1_000_000, value_numeric=1_000_000,
                   source_unit="VND", unit_multiplier_to_vnd=1.0)
        ])
        vnstock = pd.DataFrame([
            record("vnstock", "assets", 1_000_000, value_numeric=1,
                   value_raw="1", source_unit="million_VND",
                   unit_multiplier_to_vnd=1_000_000.0)
        ])
        result = self.checker.compare(fireant, vnstock)
        self.assertEqual(result.iloc[0]["comparison_status"], "matched")
        self.assertEqual(result.iloc[0]["absolute_difference"], 0)

    def test_missing_rows_are_not_changed_to_zero(self):
        result = self.checker.compare(
            pd.DataFrame([record("fireant", "assets", 100)]),
            pd.DataFrame([record("vnstock", "equity", 50)]),
        )
        statuses = set(result["comparison_status"])
        self.assertEqual(statuses, {"only_fireant", "only_vnstock"})
        self.assertTrue(result.loc[result["comparison_status"] == "only_fireant", "vnstock_value_vnd"].isna().all())

    def test_unconfirmed_mapping_unknown_unit_and_duplicates_are_explained(self):
        fireant = pd.DataFrame([
            record("fireant", "assets", 100, mapping_status="provisional"),
            record("fireant", "cash", 20, value_vnd=None, source_unit="unknown"),
            record("fireant", "equity", 50), record("fireant", "equity", 51, source_row_number=2),
        ])
        result = self.checker.compare(fireant, pd.DataFrame(columns=RECORD_COLUMNS))
        self.assertEqual(set(result["comparison_reason"]), {"mapping_not_confirmed", "value_or_unit_unknown", "duplicate_comparison_key"})
        self.assertTrue((result["comparison_status"] == "not_comparable").all())

    def test_report_period_mode_and_consolidation_must_match(self):
        fireant = pd.DataFrame([record("fireant", "assets", 100, consolidation_status="consolidated")])
        vnstock = pd.DataFrame([record("vnstock", "assets", 100, consolidation_status="separate")])
        result = self.checker.compare(fireant, vnstock)
        self.assertEqual(set(result["comparison_status"]), {"not_comparable"})
        self.assertEqual(set(result["comparison_reason"]), {"consolidation_mismatch"})

        vnstock.loc[0, "consolidation_status"] = "consolidated"
        vnstock.loc[0, "report_type"] = "income_statement"
        result = self.checker.compare(fireant, vnstock)
        self.assertEqual(set(result["comparison_reason"]), {"report_type_mismatch"})

    def test_unknown_consolidation_is_visible_and_inputs_are_not_mutated(self):
        fireant = pd.DataFrame([record("fireant", "assets", 100)])
        vnstock = pd.DataFrame([record("vnstock", "assets", 100)])
        original = fireant.copy(deep=True)
        result = self.checker.compare(fireant, vnstock)
        self.assertEqual(result.iloc[0]["quality_flags"], "unknown_consolidation")
        pd.testing.assert_frame_equal(fireant, original)

    def test_wrong_source_or_missing_schema_is_blocked(self):
        with self.assertRaises(ValueError):
            self.checker.compare(pd.DataFrame([record("vnstock", "assets", 100)]), pd.DataFrame(columns=RECORD_COLUMNS))
        with self.assertRaises(ValueError):
            self.checker.compare(pd.DataFrame({"symbol": ["FPT"]}), pd.DataFrame(columns=RECORD_COLUMNS))

    def test_summary_counts_every_status(self):
        result = self.checker.compare(
            pd.DataFrame([record("fireant", "assets", 100), record("fireant", "equity", 60)]),
            pd.DataFrame([record("vnstock", "assets", 100), record("vnstock", "equity", 50)]),
        )
        summary = self.checker.summarize(result)
        self.assertEqual((summary.total, summary.matched, summary.different), (2, 1, 1))

    def test_real_normalizer_validator_and_cross_checker_fit_together(self):
        normalizer = BCTCNormalizer()
        fireant = normalizer.normalize_fireant(
            [{"year": 2025, "quarter": 0, "companyType": "General",
              "financialValues": {"TotalAsset": 1_000_000}}],
            run_id="integration", symbol="FPT", period_type="year",
            collected_at="2026-08-09T00:00:00+07:00", raw_file="fireant.json",
        )
        vnstock = normalizer.normalize_vci(
            pd.DataFrame({"item_id": ["asset_total"], "2025": [1_000_000]}),
            run_id="integration", symbol="FPT", company_type="general",
            report_type="balance_sheet", period_type="year",
            collected_at="2026-08-09T00:00:00+07:00", raw_file="vci.parquet",
        )
        for data in (fireant, vnstock):
            self.assertTrue(BCTCValidator().validate(data).is_valid)
        comparison = self.checker.compare(fireant, vnstock)
        self.assertEqual(comparison.iloc[0]["comparison_status"], "matched")
        self.assertEqual(comparison.iloc[0]["canonical_item_id"], "total_assets")

    def test_bank_cross_check_automatic_matching(self):
        normalizer = BCTCNormalizer()
        fireant = normalizer.normalize_fireant(
            [{"year": 2025, "quarter": 0, "companyType": "Bank",
              "financialValues": {"CustomerLoans": 2_000_000, "ProfitAfterTax": 500_000}}],
            run_id="bank-test", symbol="VCB", period_type="year",
            collected_at="2026-08-16T00:00:00+07:00", raw_file="fireant.json",
        )
        vnstock_bs = normalizer.normalize_vci(
            pd.DataFrame({"item_id": ["loans_and_advances_to_customers"], "2025": [2_000_000]}),
            run_id="bank-test", symbol="VCB", company_type="bank",
            report_type="balance_sheet", period_type="year",
            collected_at="2026-08-16T00:00:00+07:00", raw_file="vci.parquet",
        )
        vnstock_is = normalizer.normalize_vci(
            pd.DataFrame({"item_id": ["net_profit_loss_after_tax"], "2025": [500_000]}),
            run_id="bank-test", symbol="VCB", company_type="bank",
            report_type="income_statement", period_type="year",
            collected_at="2026-08-16T00:00:00+07:00", raw_file="vci.parquet",
        )
        full_vci = pd.concat([vnstock_bs, vnstock_is], ignore_index=True)
        comparison = self.checker.compare(fireant, full_vci)
        summary = self.checker.summarize(comparison)
        self.assertEqual(summary.matched, 2)
        self.assertEqual(summary.different, 0)


if __name__ == "__main__":
    unittest.main()

