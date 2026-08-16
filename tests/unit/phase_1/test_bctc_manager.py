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


class DelayedClient:
    def __init__(self, source: str, delay_seconds: float = 0.05, error: Exception | None = None):
        self.source = source
        self.delay_seconds = delay_seconds
        self.error = error
        self.call_log: list[dict[str, float]] = []

    def fetch(self, symbol: str, **kwargs):
        import time
        start_time = time.monotonic()
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
        end_time = time.monotonic()
        self.call_log.append({"start": start_time, "end": end_time})
        if self.error:
            raise self.error
        count = kwargs.get("count", 1)
        common = dict(
            source=self.source,
            provider="fireant_api" if self.source == "fireant" else "vci",
            symbol=symbol,
            period_type=kwargs.get("period_type", "quarter"),
            requested_count=count,
            received_count=count,
            collection_status="complete",
            collected_at="2026-08-16T15:00:00+07:00",
            attempts=1,
        )
        if self.source == "fireant":
            payload = [{"year": 2025, "quarter": 1, "financialValues": {"TotalAsset": 500}}]
            return SimpleNamespace(**common, payload=payload)
        frame_data = pd.DataFrame({"item_id": ["assets"], "2025-Q1": [500]})
        return SimpleNamespace(**common, report_type=kwargs.get("report_type", "balance_sheet"), frame=frame_data)


class BCTCManagerParallelTests(unittest.TestCase):
    """Kiểm tra chuyên sâu luồng song song (Parallel) và an toàn dữ liệu."""

    def test_01_fireant_and_vci_run_concurrently(self):
        import time
        fireant_client = DelayedClient("fireant", delay_seconds=0.1)
        vci_client = DelayedClient("vnstock", delay_seconds=0.1)
        events = []
        manager = BCTCManager(
            run_id="test_run_01",
            fireant_client=fireant_client,
            vci_client=vci_client,
            raw_repository=Raw(events),
            progress_repository=Progress(events),
            normalizer=Normalizer(events),
            validator=Validator(events),
            cross_checker=Cross(events),
            mode="parallel",
            delay_seconds=0.0,
            sleeper=lambda _: None,
            logger=Logger(),
        )
        work_items = [
            BCTCWorkItem("fireant", "fireant_api", "financial_data", "quarter", 4),
            BCTCWorkItem("vnstock", "vci", "balance_sheet", "quarter", 4),
        ]
        started = time.monotonic()
        result = manager.run_symbol("VNM", work_items)
        elapsed = time.monotonic() - started
        self.assertEqual(len(result.outcomes), 2)
        self.assertLess(elapsed, 0.8)
        fa_start, fa_end = fireant_client.call_log[0]["start"], fireant_client.call_log[0]["end"]
        vci_start, vci_end = vci_client.call_log[0]["start"], vci_client.call_log[0]["end"]
        overlap = max(0.0, min(fa_end, vci_end) - max(fa_start, vci_start))
        self.assertGreater(overlap, 0.04)

    def test_02_deterministic_ordering_regardless_of_finishing_order(self):
        events = []
        manager = BCTCManager(
            run_id="test_run_02",
            fireant_client=DelayedClient("fireant", delay_seconds=0.08),
            vci_client=DelayedClient("vnstock", delay_seconds=0.01),
            raw_repository=Raw(events),
            progress_repository=Progress(events),
            normalizer=Normalizer(events),
            validator=Validator(events),
            cross_checker=Cross(events),
            mode="parallel",
            delay_seconds=0.0,
            sleeper=lambda _: None,
            logger=Logger(),
        )
        work_items = [
            BCTCWorkItem("fireant", "fireant_api", "financial_data", "quarter", 4),
            BCTCWorkItem("vnstock", "vci", "balance_sheet", "quarter", 4),
            BCTCWorkItem("vnstock", "vci", "income_statement", "quarter", 4),
        ]
        result = manager.run_symbol("FPT", work_items)
        self.assertEqual(result.outcomes[0].source, "fireant")
        self.assertEqual(result.outcomes[1].report_type, "balance_sheet")
        self.assertEqual(result.outcomes[2].report_type, "income_statement")

    def test_03_isolated_failures_between_sources(self):
        events = []
        manager = BCTCManager(
            run_id="test_run_03",
            fireant_client=DelayedClient("fireant", delay_seconds=0.01, error=RuntimeError("FireAnt Timeout")),
            vci_client=DelayedClient("vnstock", delay_seconds=0.01),
            raw_repository=Raw(events),
            progress_repository=Progress(events),
            normalizer=Normalizer(events),
            validator=Validator(events),
            cross_checker=Cross(events),
            mode="parallel",
            delay_seconds=0.0,
            sleeper=lambda _: None,
            logger=Logger(),
        )
        work_items = [
            BCTCWorkItem("fireant", "fireant_api", "financial_data", "quarter", 4),
            BCTCWorkItem("vnstock", "vci", "balance_sheet", "quarter", 4),
        ]
        result = manager.run_symbol("VCB", work_items)
        self.assertEqual(result.outcomes[0].status, "failed_fatal")
        self.assertEqual(result.outcomes[1].status, "complete")
        self.assertIsNotNone(result.outcomes[1].normalized)

    def test_04_crash_recovery_resumes_without_re_scraping_completed_items(self):
        events = []
        progress = Progress(events)
        k1 = progress.ensure_item(source="fireant", provider="fireant_api", symbol="ACB", report_type="financial_data", period_type="quarter", requested_count=4)
        progress.mark_running(k1)
        progress.mark_finished(k1, status="complete", received_count=4, raw_file="acb_fa.json")
        k2 = progress.ensure_item(source="vnstock", provider="vci", symbol="ACB", report_type="balance_sheet", period_type="quarter", requested_count=4)
        progress.mark_running(k2)

        for item in progress.items.values():
            if item["status"] == "running":
                item["status"] = "failed_retryable"

        self.assertFalse(progress.should_process(k1))
        self.assertTrue(progress.should_process(k2))

    def test_05_blackbox_telemetry_captures_cpu_and_ram(self):
        from E_Helper.E_BlackBox import get_system_telemetry
        telemetry = get_system_telemetry()
        self.assertIn("cpu_percent", telemetry)
        self.assertIn("memory_mb", telemetry)
        self.assertIsInstance(telemetry["cpu_percent"], float)
        self.assertIsInstance(telemetry["memory_mb"], float)
        self.assertGreaterEqual(telemetry["cpu_percent"], 0.0)
        self.assertGreater(telemetry["memory_mb"], 1.0)

    def test_06_parallel_and_sequential_produce_identical_results(self):
        work_items = [
            BCTCWorkItem("fireant", "fireant_api", "financial_data", "quarter", 4),
            BCTCWorkItem("vnstock", "vci", "balance_sheet", "quarter", 4),
            BCTCWorkItem("vnstock", "vci", "income_statement", "quarter", 4),
        ]
        def _make(mode: str) -> BCTCManager:
            events = []
            return BCTCManager(
                run_id=f"test_{mode}",
                fireant_client=DelayedClient("fireant", delay_seconds=0.01),
                vci_client=DelayedClient("vnstock", delay_seconds=0.01),
                raw_repository=Raw(events),
                progress_repository=Progress(events),
                normalizer=Normalizer(events),
                validator=Validator(events),
                cross_checker=Cross(events),
                mode=mode,
                delay_seconds=0.0,
                sleeper=lambda _: None,
                logger=Logger(),
            )
        res_seq = _make("sequential").run_symbol("SSI", work_items)
        res_par = _make("parallel").run_symbol("SSI", work_items)
        self.assertEqual(len(res_seq.outcomes), len(res_par.outcomes))
        for o_seq, o_par in zip(res_seq.outcomes, res_par.outcomes):
            self.assertEqual(o_seq.key, o_par.key)
            self.assertEqual(o_seq.status, o_par.status)
            self.assertEqual(o_seq.received_count, o_par.received_count)


if __name__ == "__main__":
    unittest.main()

