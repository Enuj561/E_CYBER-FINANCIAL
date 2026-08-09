"""Kiểm tra ghi raw và resume BCTC; dùng folder tạm, không chạm data thật."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys
import tempfile
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BCTC_DIR))

from E_Helper.E_io_utils import safe_write_json, safe_write_parquet  # noqa: E402
from E_bctc_progress_repository import (  # noqa: E402
    BCTCProgressError,
    BCTCProgressRepository,
)
from E_bctc_raw_repository import BCTCRawRepository  # noqa: E402
from E_fireant_bctc_client import FireAntBCTCResult  # noqa: E402
from E_vci_bctc_client import VCIBCTCResult  # noqa: E402


class FakeLogger:
    def info(self, _message, **_context):
        return None

    def warning(self, _message, **_context):
        return None


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class AtomicWriteTests(unittest.TestCase):
    def test_json_failure_keeps_old_file_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "state.json"
            target.write_text('{"old": true}', encoding="utf-8")

            with self.assertRaises(TypeError):
                safe_write_json(target, {"cannot_encode": {1, 2}})

            self.assertEqual(target.read_text(encoding="utf-8"), '{"old": true}')
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_parquet_failure_keeps_old_file_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "raw.parquet"
            target.write_bytes(b"old-complete-file")
            frame = pd.DataFrame({"value": [1]})
            original = frame.to_parquet

            def fail_after_partial(path, **_kwargs):
                Path(path).write_bytes(b"partial")
                raise OSError("simulated interruption")

            frame.to_parquet = fail_after_partial
            try:
                with self.assertRaises(OSError):
                    safe_write_parquet(target, frame)
            finally:
                frame.to_parquet = original

            self.assertEqual(target.read_bytes(), b"old-complete-file")
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])


class RawRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repository = BCTCRawRepository(root_dir=self.root, logger=FakeLogger())

    def tearDown(self):
        self.temp.cleanup()

    def test_fireant_raw_is_json_under_fireant_source(self):
        result = FireAntBCTCResult(
            schema_version="bctc_v1.1.0",
            source="fireant",
            provider="fireant_api",
            symbol="FPT",
            period_type="quarter",
            requested_count=4,
            received_count=1,
            collection_status="complete",
            attempts=1,
            collected_at=timestamp(),
            endpoint_name="symbols/{symbol}/financial-data",
            payload=[{"year": 2026, "quarter": 2, "value": 10}],
        )
        raw_file = self.repository.save_fireant(
            result, run_id="run-test", report_type="balance_sheet"
        )
        raw_path = Path(raw_file)
        self.assertIn("From_FireAnt", raw_path.parts)
        self.assertEqual(json.loads(raw_path.read_text(encoding="utf-8")), result.payload)
        metadata = json.loads(
            raw_path.with_suffix(".json.metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["provider"], "fireant_api")
        self.assertEqual(len(metadata["content_sha256"]), 64)

    def test_fireant_combined_financial_data_work_item_can_be_saved(self):
        result = FireAntBCTCResult(
            schema_version="bctc_v1.1.0", source="fireant", provider="fireant_api",
            symbol="FPT", period_type="year", requested_count=1, received_count=1,
            collection_status="complete", attempts=1, collected_at=timestamp(),
            endpoint_name="symbols/{symbol}/financial-data",
            payload=[{"year": 2025, "quarter": 0, "financialValues": {"TotalAsset": 10}}],
        )
        raw_file = self.repository.save_fireant(
            result, run_id="run-manager", report_type="financial_data"
        )
        self.assertIn("financial_data_year_fireant_api.json", raw_file)

    def test_vci_raw_is_parquet_under_vnstock_source(self):
        frame = pd.DataFrame({"item_id": [1], "2025": [100]})
        result = VCIBCTCResult(
            schema_version="bctc_v1.1.0",
            source="vnstock",
            provider="vci",
            symbol="FPT",
            report_type="income_statement",
            period_type="year",
            requested_count=4,
            received_count=1,
            collection_status="complete",
            attempts=1,
            collected_at=timestamp(),
            frame=frame,
        )
        raw_file = self.repository.save_vci(result, run_id="run-test")
        raw_path = Path(raw_file)
        self.assertIn("From_vnstock", raw_path.parts)
        pd.testing.assert_frame_equal(pd.read_parquet(raw_path), frame)

    def test_vci_mixed_type_period_column_is_stored_as_text_with_metadata(self):
        frame = pd.DataFrame({"item_id": ["roe", "note"], "2025-Q1": [10, "N/A"]})
        result = VCIBCTCResult(
            schema_version="bctc_v1.1.0", source="vnstock", provider="vci",
            symbol="FPT", report_type="ratio", period_type="quarter",
            requested_count=1, received_count=1, collection_status="complete",
            attempts=1, collected_at=timestamp(), frame=frame,
        )
        raw_file = self.repository.save_vci(result, run_id="mixed-type")
        stored = pd.read_parquet(raw_file)
        self.assertEqual(stored["2025-Q1"].tolist(), ["10", "N/A"])
        metadata = json.loads(Path(raw_file + ".metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["storage_coercions"][0]["column_name"], "2025-Q1")

    def test_vci_duplicate_period_names_are_kept_by_position_in_metadata(self):
        frame = pd.DataFrame(
            [["asset", 10, 11]], columns=["item_id", "2025", "2025"]
        )
        result = VCIBCTCResult(
            schema_version="bctc_v1.1.0", source="vnstock", provider="vci",
            symbol="FPT", report_type="ratio", period_type="year",
            requested_count=2, received_count=2, collection_status="complete",
            attempts=1, collected_at=timestamp(), frame=frame,
        )
        raw_file = self.repository.save_vci(result, run_id="duplicate-columns")
        stored = pd.read_parquet(raw_file)
        self.assertEqual(stored.iloc[0].tolist(), ["asset", 10, 11])
        self.assertEqual(len(set(stored.columns)), 3)
        metadata = json.loads(Path(raw_file + ".metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["storage_column_renames"][0]["original_name"], "2025")

    def test_no_data_does_not_create_fake_raw_file(self):
        result = FireAntBCTCResult(
            schema_version="bctc_v1.1.0",
            source="fireant",
            provider="fireant_api",
            symbol="EMPTY",
            period_type="year",
            requested_count=4,
            received_count=0,
            collection_status="no_data_confirmed",
            attempts=1,
            collected_at=timestamp(),
            endpoint_name="symbols/{symbol}/financial-data",
            payload=[],
        )
        raw_file = self.repository.save_fireant(
            result, run_id="run-test", report_type="ratio"
        )
        self.assertIsNone(raw_file)
        self.assertEqual(list(self.root.rglob("*.json")), [])

    def test_same_complete_raw_is_reused_without_overwrite(self):
        result = FireAntBCTCResult(
            schema_version="bctc_v1.1.0",
            source="fireant",
            provider="fireant_api",
            symbol="FPT",
            period_type="year",
            requested_count=4,
            received_count=1,
            collection_status="complete",
            attempts=1,
            collected_at=timestamp(),
            endpoint_name="symbols/{symbol}/financial-data",
            payload=[{"value": 10}],
        )
        first = self.repository.save_fireant(
            result, run_id="run-test", report_type="ratio"
        )
        second = self.repository.save_fireant(
            result, run_id="run-test", report_type="ratio"
        )
        self.assertEqual(first, second)

    def test_orphan_raw_is_recovered_when_content_matches(self):
        result = FireAntBCTCResult(
            schema_version="bctc_v1.1.0",
            source="fireant",
            provider="fireant_api",
            symbol="FPT",
            period_type="year",
            requested_count=4,
            received_count=1,
            collection_status="complete",
            attempts=1,
            collected_at=timestamp(),
            endpoint_name="symbols/{symbol}/financial-data",
            payload=[{"value": 10}],
        )
        raw_path, metadata_path = self.repository._paths(
            run_id="run-test",
            provider="fireant_api",
            symbol="FPT",
            report_type="ratio",
            period_type="year",
            extension="json",
        )
        safe_write_json(raw_path, result.payload)
        self.assertFalse(metadata_path.exists())

        recovered = self.repository.save_fireant(
            result, run_id="run-test", report_type="ratio"
        )
        self.assertEqual(recovered, str(raw_path))
        self.assertTrue(metadata_path.is_file())

    def test_existing_different_raw_is_not_overwritten(self):
        result = FireAntBCTCResult(
            schema_version="bctc_v1.1.0",
            source="fireant",
            provider="fireant_api",
            symbol="FPT",
            period_type="year",
            requested_count=4,
            received_count=1,
            collection_status="complete",
            attempts=1,
            collected_at=timestamp(),
            endpoint_name="symbols/{symbol}/financial-data",
            payload=[{"value": 10}],
        )
        raw_path, _ = self.repository._paths(
            run_id="run-test",
            provider="fireant_api",
            symbol="FPT",
            report_type="ratio",
            period_type="year",
            extension="json",
        )
        safe_write_json(raw_path, [{"value": 999}])
        with self.assertRaises(RuntimeError):
            self.repository.save_fireant(
                result, run_id="run-test", report_type="ratio"
            )


class ProgressRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp.name)
        self.plan = {"symbols": ["FPT"], "requested_count": 4}

    def tearDown(self):
        self.temp.cleanup()

    def make_repository(self):
        return BCTCProgressRepository(
            run_id="run-test",
            collection_plan=self.plan,
            state_dir=self.state_dir,
            logger=FakeLogger(),
        )

    def ensure_fireant_item(self, repository):
        return repository.ensure_item(
            source="fireant",
            provider="fireant_api",
            symbol="FPT",
            report_type="balance_sheet",
            period_type="quarter",
            requested_count=4,
        )

    def test_complete_item_is_skipped_on_resume(self):
        repository = self.make_repository()
        key = self.ensure_fireant_item(repository)
        repository.mark_running(key)
        raw_file = self.state_dir / "complete.json"
        raw_file.write_text("[]", encoding="utf-8")
        repository.mark_finished(
            key, status="complete", received_count=4, raw_file=str(raw_file)
        )

        resumed = self.make_repository()
        self.assertFalse(resumed.should_process(key))
        self.assertEqual(resumed.item(key)["attempt_count"], 1)

    def test_interrupted_running_item_is_retried_on_resume(self):
        repository = self.make_repository()
        key = self.ensure_fireant_item(repository)
        repository.mark_running(key)

        resumed = self.make_repository()
        item = resumed.item(key)
        self.assertEqual(item["status"], "failed_retryable")
        self.assertTrue(resumed.should_process(key))
        self.assertEqual(item["error_type"], "InterruptedRun")

    def test_no_data_is_skipped_without_raw_file(self):
        repository = self.make_repository()
        key = self.ensure_fireant_item(repository)
        repository.mark_running(key)
        repository.mark_finished(key, status="no_data_confirmed", received_count=0)
        self.assertFalse(repository.should_process(key))
        self.assertIsNone(repository.item(key)["raw_file"])

    def test_fatal_error_is_not_retried_and_secret_is_hidden(self):
        repository = self.make_repository()
        key = self.ensure_fireant_item(repository)
        repository.mark_running(key)
        repository.mark_finished(
            key,
            status="failed_fatal",
            received_count=0,
            error_type="AuthError",
            error_message="Authorization: Bearer very-secret-token",
        )
        item = repository.item(key)
        self.assertFalse(repository.should_process(key))
        self.assertNotIn("very-secret-token", item["error_message"])

    def test_changed_plan_cannot_resume_old_checkpoint(self):
        self.make_repository()
        with self.assertRaises(BCTCProgressError):
            BCTCProgressRepository(
                run_id="run-test",
                collection_plan={"symbols": ["VCB"], "requested_count": 4},
                state_dir=self.state_dir,
                logger=FakeLogger(),
            )


if __name__ == "__main__":
    unittest.main()
