"""Kiểm tra hai client BCTC bằng data giả; tuyệt đối không gọi Internet."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BCTC_DIR))

from E_fireant_bctc_client import FireAntBCTCClient, FireAntBCTCError  # noqa: E402
from E_vci_bctc_client import VCIBCTCClient, VCIBCTCError  # noqa: E402


class FakeLogger:
    def warning(self, _message, **_context):
        return None


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, BaseException):
            raise self._payload
        return self._payload


class FireAntClientTests(unittest.TestCase):
    def make_client(self, outcomes, sleeps=None):
        queue = list(outcomes)

        def fake_get(*_args, **kwargs):
            self.last_request = kwargs
            outcome = queue.pop(0)
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

        return FireAntBCTCClient(
            token="Bearer fake-token",
            request_get=fake_get,
            sleep=(sleeps if sleeps is not None else []).append,
            logger=FakeLogger(),
        )

    def test_success_records_real_source_and_timeout(self):
        client = self.make_client([FakeResponse(payload=[{"year": 2025}])])
        result = client.fetch("fpt", period_type="year", count=4)
        self.assertEqual((result.source, result.provider), ("fireant", "fireant_api"))
        self.assertEqual(result.collection_status, "complete")
        self.assertEqual(self.last_request["timeout"], 30.0)
        self.assertEqual(self.last_request["headers"]["Authorization"], "Bearer fake-token")

    def test_timeout_is_retried_then_succeeds(self):
        sleeps = []
        client = self.make_client(
            [requests.Timeout("slow"), FakeResponse(payload=[])], sleeps
        )
        result = client.fetch("FPT", period_type="quarter", count=2)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.collection_status, "no_data_confirmed")
        self.assertEqual(sleeps, [1.0])

    def test_rate_limit_respects_retry_after(self):
        sleeps = []
        client = self.make_client(
            [
                FakeResponse(429, headers={"Retry-After": "3"}),
                FakeResponse(payload=[{"quarter": 1}]),
            ],
            sleeps,
        )
        result = client.fetch("FPT", period_type="quarter", count=2)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(sleeps, [3.0])

    def test_bad_token_response_stops_without_retry(self):
        sleeps = []
        client = self.make_client([FakeResponse(401, payload={})], sleeps)
        with self.assertRaises(FireAntBCTCError) as raised:
            client.fetch("FPT", period_type="year", count=2)
        self.assertFalse(raised.exception.retryable)
        self.assertEqual(raised.exception.attempts, 1)
        self.assertEqual(sleeps, [])

    def test_strange_data_stops_without_retry(self):
        client = self.make_client([FakeResponse(payload={"unexpected": True})])
        with self.assertRaises(FireAntBCTCError) as raised:
            client.fetch("FPT", period_type="year", count=2)
        self.assertFalse(raised.exception.retryable)


class FakeProvider:
    def __init__(self, outcomes):
        self.outcomes = outcomes

    def _get_financial_report(self, *_args, **_kwargs):
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeFinance:
    def __init__(self, provider):
        self.provider = provider


class VCIClientTests(unittest.TestCase):
    def make_client(self, outcomes, sleeps=None):
        provider = FakeProvider(list(outcomes))

        def factory(_symbol, _period):
            return FakeFinance(provider)

        return VCIBCTCClient(
            finance_factory=factory,
            sleep=(sleeps if sleeps is not None else []).append,
            logger=FakeLogger(),
        )

    def test_success_records_vnstock_vci_and_period_count(self):
        frame = pd.DataFrame({"item_id": [1], "2026-Q2": [10], "2026-Q1": [9]})
        client = self.make_client([frame])
        result = client.fetch(
            "fpt", report_type="balance_sheet", period_type="quarter", count=8
        )
        self.assertEqual((result.source, result.provider), ("vnstock", "vci"))
        self.assertEqual(result.received_count, 2)
        self.assertEqual(client.timeout_seconds, 30.0)

    def test_connection_error_is_retried_then_succeeds(self):
        sleeps = []
        client = self.make_client(
            [requests.ConnectionError("offline"), pd.DataFrame()], sleeps
        )
        result = client.fetch(
            "FPT", report_type="cash_flow", period_type="year", count=4
        )
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.collection_status, "no_data_confirmed")
        self.assertEqual(sleeps, [1.0])

    def test_temporary_server_error_is_retried(self):
        response = requests.Response()
        response.status_code = 503
        error = requests.HTTPError("temporary", response=response)
        frame = pd.DataFrame({"item_id": [1], "2025": [10]})
        client = self.make_client([error, frame])
        result = client.fetch(
            "FPT", report_type="income_statement", period_type="year", count=2
        )
        self.assertEqual(result.attempts, 2)

    def test_strange_data_stops_without_retry(self):
        sleeps = []
        client = self.make_client([{"not": "a dataframe"}], sleeps)
        with self.assertRaises(VCIBCTCError) as raised:
            client.fetch("FPT", report_type="ratio", period_type="year", count=2)
        self.assertFalse(raised.exception.retryable)
        self.assertEqual(raised.exception.attempts, 1)
        self.assertEqual(sleeps, [])


if __name__ == "__main__":
    unittest.main()
