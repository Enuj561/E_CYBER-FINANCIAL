"""Lệnh chạy pilot BCTC thật theo từng mã, mặc định chạy tuần tự và có resume."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import importlib.metadata
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from E_Helper.E_config import BCTC_DIR, BCTC_STATE_DIR
from E_Helper.E_io_utils import safe_write_json
from E_bctc_cross_checker import BCTCCrossChecker
from E_bctc_manager import BCTCManager, BCTCWorkItem
from E_bctc_normalizer import BCTCNormalizer
from E_bctc_progress_repository import BCTCProgressRepository
from E_bctc_raw_repository import BCTCRawRepository
from E_bctc_validator import BCTCValidator
from E_fireant_bctc_client import FireAntBCTCClient
from E_vci_bctc_client import VCIBCTCClient


PILOT_COMPANY_TYPES = {
    "VCB": "bank", "ACB": "bank", "SSI": "securities", "VND": "securities",
    "BVH": "insurance",
}
VCI_REPORT_TYPES = ("balance_sheet", "income_statement", "cash_flow", "ratio")


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def build_work_items(symbol: str, quarter_count: int, year_count: int) -> list[BCTCWorkItem]:
    company_type = PILOT_COMPANY_TYPES.get(symbol, "general")
    items = [
        BCTCWorkItem("fireant", "fireant_api", "financial_data", "quarter", quarter_count, company_type),
        BCTCWorkItem("fireant", "fireant_api", "financial_data", "year", year_count, company_type),
    ]
    for report_type in VCI_REPORT_TYPES:
        items.extend(
            BCTCWorkItem("vnstock", "vci", report_type, period_type, count, company_type)
            for period_type, count in (("quarter", quarter_count), ("year", year_count))
        )
    return items


def run_pilot(symbols: list[str], *, run_id: str, quarter_count: int, year_count: int) -> dict[str, Any]:
    plan = {
        "symbols": symbols, "sources": ["fireant/fireant_api", "vnstock/vci"],
        "quarter_count": quarter_count, "year_count": year_count,
        "mode": "sequential_pilot",
    }
    progress = BCTCProgressRepository(run_id=run_id, collection_plan=plan)
    manager = BCTCManager(
        run_id=run_id, fireant_client=FireAntBCTCClient(), vci_client=VCIBCTCClient(),
        raw_repository=BCTCRawRepository(), progress_repository=progress,
        normalizer=BCTCNormalizer(), validator=BCTCValidator(),
        cross_checker=BCTCCrossChecker(),
    )
    started = datetime.now().astimezone()
    symbol_results = []
    for symbol in symbols:
        result = manager.run_symbol(symbol, build_work_items(symbol, quarter_count, year_count))
        units, report_types = set(), set()
        raw_bytes = 0
        for outcome in result.outcomes:
            if outcome.raw_file and Path(outcome.raw_file).is_file():
                raw_bytes += Path(outcome.raw_file).stat().st_size
            if outcome.normalized is not None and not outcome.normalized.empty:
                units.update(str(v) for v in outcome.normalized["source_unit"].dropna().unique())
                report_types.update(str(v) for v in outcome.normalized["report_type"].dropna().unique())
        cross_counts = Counter(result.cross_check.get("comparison_status", []))
        symbol_results.append({
            **result.summary(),
            "calls_by_source": dict(Counter(o.source for o in result.outcomes if o.status != "skipped_existing")),
            "received_periods": {o.key: o.received_count for o in result.outcomes},
            "attempts": {o.key: o.attempts for o in result.outcomes},
            "report_types": sorted(report_types), "source_units": sorted(units),
            "raw_bytes": raw_bytes, "cross_check_statuses": dict(cross_counts),
        })
        if result.stopped:
            break
    finished = datetime.now().astimezone()
    summary = {
        "run_id": run_id, "mode": "sequential_pilot", "symbols_requested": symbols,
        "symbols_finished": [item["symbol"] for item in symbol_results],
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "duration_seconds": round((finished - started).total_seconds(), 3),
        "providers": {"fireant": "fireant_api", "vnstock": "vci"},
        "package_versions": {"vnstock": _package_version("vnstock"), "requests": _package_version("requests")},
        "results": symbol_results,
    }
    output = Path(BCTC_STATE_DIR) / "pilot_runs" / f"{run_id}.json"
    safe_write_json(output, summary)
    summary["summary_file"] = str(output)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Chạy pilot BCTC thật, tuần tự từng mã")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--quarter-count", type=int, default=64)
    parser.add_argument("--year-count", type=int, default=20)
    args = parser.parse_args()
    symbols = [symbol.strip().upper() for symbol in args.symbols]
    if not all(symbols) or len(set(symbols)) != len(symbols):
        parser.error("Danh sách mã rỗng hoặc bị trùng")
    summary = run_pilot(
        symbols, run_id=args.run_id, quarter_count=args.quarter_count,
        year_count=args.year_count,
    )
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    print()
    stopped = any(item.get("stopped") for item in summary["results"])
    return 0 if len(summary["symbols_finished"]) == len(symbols) and not stopped else 2


if __name__ == "__main__":
    raise SystemExit(main())
