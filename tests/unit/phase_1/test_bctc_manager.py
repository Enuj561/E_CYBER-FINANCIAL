"""Kiểm tra Manager BCTC bằng dependency giả; không gọi mạng và không ghi data thật."""

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BCTC_DIR))

from E_bctc_manager import BCTCManager, BCTCWorkItem  # noqa: E402
from E_bctc_schema import RECORD_COLUMNS  # noqa: E402


class Logger:
    def info(self, *_args, **_kwargs): pass
    def error(self, *_args, **_kwargs): pass


class Progress:
    def __init__(self, events, existing=False):
        self.events, self.existing, self.items = events, existing, {}
    def ensure_item(self, **data):
        key = "|".join(str(data[k]) for k in ("source", "provider", "symbol", "report_type", "period_type"))
        self.items.setdefault(key, {**data, "status": "complete" if self.existing else "pending", "raw_file": "old.raw"})
        self.events.append("ensure")
        return key
    def should_process(self, key): return self.items[key]["status"] != "complete"
    def item(self, key): return self.items[key]
    def mark_running(self, key):
        self.events.append("running"); self.items[key]["status"] = "running"
    def mark_finished(self, key, **data):
        self.events.append(f"finished:{data['status']}"); self.items[key].update(data)


class Client:
    def __init__(self, events, source, error=None, received_count=None, no_data=False):
        self.events, self.source, self.error = events, source, error
        self.received_count, self.no_data = received_count, no_data
    def fetch(self, symbol, **kwargs):
        self.events.append(f"fetch:{self.source}")
        if self.error: raise self.error
        count = kwargs["count"]
        received = 0 if self.no_data else count if self.received_count is None else self.received_count
        common = dict(source=self.source, provider="fireant_api" if self.source == "fireant" else "vci", symbol=symbol,
                      period_type=kwargs["period_type"], requested_count=count, received_count=received,
                      collection_status="no_data_confirmed" if self.no_data else "complete",
                      collected_at="2026-08-09T00:00:00+07:00", attempts=1)
        if self.source == "fireant":
            payload = [] if self.no_data else [{"year": 2025, "quarter": 0, "financialValues": {"TotalAsset": 100}}]
            return SimpleNamespace(**common, payload=payload)
        frame_data = pd.DataFrame() if self.no_data else pd.DataFrame({"item_id": ["assets"], "2025": [100]})
        return SimpleNamespace(**common, report_type=kwargs["report_type"], frame=frame_data)


class Raw:
    def __init__(self, events): self.events = events
    def save_fireant(self, result, **_kwargs): self.events.append("raw:fireant"); return None if result.collection_status == "no_data_confirmed" else "fireant.raw"
    def save_vci(self, result, **_kwargs): self.events.append("raw:vnstock"); return None if result.collection_status == "no_data_confirmed" else "vnstock.raw"


class Normalizer:
    def __init__(self, events): self.events = events
    def normalize_fireant(self, _payload, **kwargs): self.events.append("normalize:fireant"); return frame("fireant", kwargs["symbol"])
    def normalize_vci(self, _frame, **kwargs): self.events.append("normalize:vnstock"); return frame("vnstock", kwargs["symbol"])


def frame(source, symbol):
    row = {column: None for column in RECORD_COLUMNS}
    row.update(source=source, provider="fireant_api" if source == "fireant" else "vci", symbol=symbol,
               report_type="balance_sheet", period_type="year", period_key="2025",
               period_value_mode="point_in_time", consolidation_status="unknown",
               source_item_id="assets", canonical_item_id="total_assets", mapping_status="confirmed", value_vnd=100)
    return pd.DataFrame([row])


class Validator:
    def __init__(self, events, valid=True): self.events, self.valid = events, valid
    def validate(self, _data, **_kwargs):
        self.events.append("validate")
        return SimpleNamespace(is_valid=self.valid, summary=lambda: {"is_valid": self.valid})


class Cross:
    def __init__(self, events): self.events = events
    def compare(self, left, right):
        self.events.append("cross")
        return pd.DataFrame({"left_rows": [len(left)], "right_rows": [len(right)]})


class RetryableError(RuntimeError):
    retryable = True


def item(source):
    return BCTCWorkItem(source=source, provider="fireant_api" if source == "fireant" else "vci",
                        report_type="financial_data" if source == "fireant" else "balance_sheet",
                        period_type="year", requested_count=1, company_type="general")


class BCTCManagerTests(unittest.TestCase):
    def manager(self, events, *, fireant_error=None, fireant_received=None,
                fireant_no_data=False, existing=False, stop=lambda: False):
        return BCTCManager(run_id="test", fireant_client=Client(events, "fireant", fireant_error, fireant_received, fireant_no_data),
                           vci_client=Client(events, "vnstock"), raw_repository=Raw(events),
                           progress_repository=Progress(events, existing), normalizer=Normalizer(events),
                           validator=Validator(events), cross_checker=Cross(events), stop_requested=stop, logger=Logger())

    def test_one_symbol_runs_in_required_order_and_cross_checks(self):
        events = []
        result = self.manager(events).run_symbol("fpt", [item("fireant"), item("vnstock")])
        self.assertEqual(events, ["ensure", "running", "fetch:fireant", "raw:fireant", "normalize:fireant", "validate", "finished:complete",
                                  "ensure", "running", "fetch:vnstock", "raw:vnstock", "normalize:vnstock", "validate", "finished:complete", "cross"])
        self.assertFalse(result.stopped)
        self.assertEqual(result.summary()["statuses"], {"complete": 2})
        self.assertIn("duration_seconds", result.summary())

    def test_retryable_source_error_does_not_delete_or_block_other_source(self):
        events = []
        result = self.manager(events, fireant_error=RetryableError("temporary")).run_symbol("FPT", [item("fireant"), item("vnstock")])
        self.assertEqual([o.status for o in result.outcomes], ["failed_retryable", "complete"])
        self.assertIn("fetch:vnstock", events)
        self.assertFalse(result.stopped)

    def test_fatal_error_stops_whole_run(self):
        events = []
        result = self.manager(events, fireant_error=ValueError("bad config")).run_symbol("FPT", [item("fireant"), item("vnstock")])
        self.assertTrue(result.stopped)
        self.assertEqual(len(result.outcomes), 1)
        self.assertNotIn("fetch:vnstock", events)

    def test_completed_items_are_not_fetched_again(self):
        events = []
        result = self.manager(events, existing=True).run_symbol("FPT", [item("fireant")])
        self.assertEqual(result.outcomes[0].status, "skipped_existing")
        self.assertNotIn("fetch:fireant", events)

    def test_user_stop_is_clean_and_does_not_start_item(self):
        events = []
        result = self.manager(events, stop=lambda: True).run_symbol("FPT", [item("fireant")])
        self.assertTrue(result.stopped)
        self.assertEqual(result.stop_reason, "user_requested_stop")
        self.assertEqual(events, ["cross"])

    def test_fewer_periods_than_requested_is_partial_not_complete(self):
        events = []
        result = self.manager(events, fireant_received=1).run_symbol(
            "FPT", [BCTCWorkItem(source="fireant", provider="fireant_api",
                                  report_type="financial_data", period_type="year",
                                  requested_count=4)]
        )
        self.assertEqual(result.outcomes[0].status, "partial")
        self.assertIn("finished:partial", events)

    def test_confirmed_empty_source_has_no_fake_raw_file(self):
        events = []
        result = self.manager(events, fireant_no_data=True).run_symbol("FPT", [item("fireant")])
        outcome = result.outcomes[0]
        self.assertEqual(outcome.status, "no_data_confirmed")
        self.assertIsNone(outcome.raw_file)
        self.assertIn("finished:no_data_confirmed", events)

    def test_keyboard_interrupt_marks_item_retryable_and_stops_cleanly(self):
        events = []
        result = self.manager(events, fireant_error=KeyboardInterrupt()).run_symbol(
            "FPT", [item("fireant"), item("vnstock")]
        )
        self.assertTrue(result.stopped)
        self.assertEqual(result.stop_reason, "keyboard_interrupt")
        self.assertIn("finished:failed_retryable", events)
        self.assertNotIn("fetch:vnstock", events)

    def test_work_item_rejects_hidden_provider_switch(self):
        with self.assertRaises(ValueError):
            BCTCWorkItem(source="vnstock", provider="kbs", report_type="balance_sheet", period_type="year", requested_count=1)


if __name__ == "__main__":
    unittest.main()
