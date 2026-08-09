"""Manager điều phối dây chuyền BCTC; không chứa lại logic của các thành phần."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
from typing import Any, Callable, Iterable

import pandas as pd

from E_Helper.E_BlackBox import get_black_box
from E_bctc_schema import RECORD_COLUMNS


class BCTCValidationError(ValueError):
    """Lỗi Validator giữ mã lỗi/context để checkpoint không chỉ còn một con số."""

    def __init__(self, report: Any) -> None:
        details = [
            {"code": issue.code, "context": issue.context}
            for issue in report.errors[:20]
        ]
        message = json.dumps(
            {"summary": report.summary(), "first_errors": details},
            ensure_ascii=False,
            default=str,
        )
        super().__init__(f"Validator chặn data: {message}")
        self.report = report


@dataclass(frozen=True)
class BCTCWorkItem:
    source: str
    provider: str
    report_type: str
    period_type: str
    requested_count: int
    company_type: str = "unknown"

    def __post_init__(self) -> None:
        valid_pairs = {("fireant", "fireant_api"), ("vnstock", "vci")}
        if (self.source, self.provider) not in valid_pairs:
            raise ValueError("Manager chỉ nhận fireant/fireant_api hoặc vnstock/vci")
        if self.period_type not in {"quarter", "year"}:
            raise ValueError("period_type chỉ nhận quarter hoặc year")
        if self.requested_count < 1:
            raise ValueError("requested_count phải ít nhất là 1")
        if self.source == "fireant" and self.report_type != "financial_data":
            raise ValueError("FireAnt trả gói chung nên report_type của work item phải là financial_data")
        if self.source == "vnstock" and self.report_type not in {
            "balance_sheet", "income_statement", "cash_flow", "ratio"
        }:
            raise ValueError("report_type VCI không hợp lệ")


@dataclass
class BCTCItemOutcome:
    key: str
    source: str
    report_type: str
    period_type: str
    status: str
    raw_file: str | None = None
    normalized: pd.DataFrame | None = None
    validation: Any | None = None
    error_type: str | None = None
    error_message: str | None = None
    received_count: int = 0
    attempts: int = 0


@dataclass
class BCTCRunResult:
    symbol: str
    outcomes: list[BCTCItemOutcome] = field(default_factory=list)
    cross_check: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame()
    )
    stopped: bool = False
    stop_reason: str | None = None
    duration_seconds: float = 0.0

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.status] = counts.get(outcome.status, 0) + 1
        return {
            "symbol": self.symbol,
            "items": len(self.outcomes),
            "statuses": counts,
            "cross_check_rows": len(self.cross_check),
            "duration_seconds": round(self.duration_seconds, 3),
            "stopped": self.stopped,
            "stop_reason": self.stop_reason,
        }


class BCTCManager:
    """Điều phối một mã; mọi dependency đều được đưa vào để test bằng đồ giả."""

    def __init__(
        self,
        *,
        run_id: str,
        fireant_client: Any,
        vci_client: Any,
        raw_repository: Any,
        progress_repository: Any,
        normalizer: Any,
        validator: Any,
        cross_checker: Any,
        stop_requested: Callable[[], bool] = lambda: False,
        clock: Callable[[], float] = time.monotonic,
        logger: Any | None = None,
    ) -> None:
        self.run_id = run_id
        self.fireant_client = fireant_client
        self.vci_client = vci_client
        self.raw_repository = raw_repository
        self.progress_repository = progress_repository
        self.normalizer = normalizer
        self.validator = validator
        self.cross_checker = cross_checker
        self.stop_requested = stop_requested
        self.clock = clock
        self.logger = logger or get_black_box(__file__, run_id=run_id)

    def run_symbol(self, symbol: str, work_items: Iterable[BCTCWorkItem]) -> BCTCRunResult:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol không được rỗng")
        result = BCTCRunResult(symbol=normalized_symbol)
        started_at = self.clock()
        self.logger.info("Bắt đầu dây chuyền BCTC", symbol=normalized_symbol)

        for work in work_items:
            if self.stop_requested():
                result.stopped = True
                result.stop_reason = "user_requested_stop"
                break
            outcome = self._run_item(normalized_symbol, work)
            result.outcomes.append(outcome)
            if outcome.status == "interrupted":
                result.stopped = True
                result.stop_reason = "keyboard_interrupt"
                break
            if outcome.status == "failed_fatal":
                result.stopped = True
                result.stop_reason = outcome.error_type or "fatal_error"
                break

        result.cross_check = self._cross_check_valid_results(result.outcomes)
        result.duration_seconds = max(0.0, self.clock() - started_at)
        self.logger.info("Kết thúc dây chuyền BCTC", **result.summary())
        return result

    def _run_item(self, symbol: str, work: BCTCWorkItem) -> BCTCItemOutcome:
        key = self.progress_repository.ensure_item(
            source=work.source,
            provider=work.provider,
            symbol=symbol,
            report_type=work.report_type,
            period_type=work.period_type,
            requested_count=work.requested_count,
        )
        if not self.progress_repository.should_process(key):
            saved = self.progress_repository.item(key)
            return BCTCItemOutcome(
                key=key, source=work.source, report_type=work.report_type,
                period_type=work.period_type, status="skipped_existing",
                raw_file=saved.get("raw_file"), received_count=int(saved.get("received_count", 0)),
                attempts=int(saved.get("attempt_count", 0)),
            )

        self.progress_repository.mark_running(key)
        try:
            fetched = self._fetch(symbol, work)
            raw_file = self._save_raw(fetched, work)
            final_status = self._collection_status(fetched)
            normalized = self._normalize(fetched, work, raw_file)
            validation = self.validator.validate(
                normalized,
                collection_status=final_status,
                expected_symbol=symbol,
                expected_source=work.source,
            )
            if not validation.is_valid:
                raise BCTCValidationError(validation)
            self.progress_repository.mark_finished(
                key,
                status=final_status,
                received_count=fetched.received_count,
                raw_file=raw_file,
            )
            return BCTCItemOutcome(
                key=key, source=work.source, report_type=work.report_type,
                period_type=work.period_type, status=final_status, raw_file=raw_file,
                normalized=normalized, validation=validation,
                received_count=int(fetched.received_count), attempts=int(fetched.attempts),
            )
        except KeyboardInterrupt as error:
            self._mark_error(key, "failed_retryable", error)
            return BCTCItemOutcome(
                key=key, source=work.source, report_type=work.report_type,
                period_type=work.period_type, status="interrupted",
                error_type=type(error).__name__, error_message=str(error),
            )
        except Exception as error:
            status = "failed_retryable" if bool(getattr(error, "retryable", False)) else "failed_fatal"
            self._mark_error(key, status, error)
            self.logger.error(
                "Item BCTC thất bại", source=work.source, symbol=symbol,
                report_type=work.report_type, period_type=work.period_type,
                status=status, error_type=type(error).__name__, error_message=str(error),
            )
            return BCTCItemOutcome(
                key=key, source=work.source, report_type=work.report_type,
                period_type=work.period_type, status=status,
                error_type=type(error).__name__, error_message=str(error),
                attempts=int(getattr(error, "attempts", 0)),
            )

    def _fetch(self, symbol: str, work: BCTCWorkItem) -> Any:
        if work.source == "fireant":
            return self.fireant_client.fetch(
                symbol, period_type=work.period_type, count=work.requested_count
            )
        return self.vci_client.fetch(
            symbol, report_type=work.report_type, period_type=work.period_type,
            count=work.requested_count,
        )

    def _save_raw(self, fetched: Any, work: BCTCWorkItem) -> str | None:
        if work.source == "fireant":
            return self.raw_repository.save_fireant(
                fetched, run_id=self.run_id, report_type=work.report_type
            )
        return self.raw_repository.save_vci(fetched, run_id=self.run_id)

    def _normalize(self, fetched: Any, work: BCTCWorkItem, raw_file: str | None) -> pd.DataFrame:
        if fetched.collection_status == "no_data_confirmed":
            return pd.DataFrame(columns=RECORD_COLUMNS)
        if not raw_file:
            raise RuntimeError("Có data nhưng không có đường dẫn raw")
        if work.source == "fireant":
            return self.normalizer.normalize_fireant(
                fetched.payload, run_id=self.run_id, symbol=fetched.symbol,
                period_type=work.period_type, collected_at=fetched.collected_at,
                raw_file=raw_file,
            )
        return self.normalizer.normalize_vci(
            fetched.frame, run_id=self.run_id, symbol=fetched.symbol,
            company_type=work.company_type, report_type=work.report_type,
            period_type=work.period_type, collected_at=fetched.collected_at,
            raw_file=raw_file,
        )

    @staticmethod
    def _collection_status(fetched: Any) -> str:
        if fetched.collection_status == "no_data_confirmed":
            return "no_data_confirmed"
        return "complete" if fetched.received_count >= fetched.requested_count else "partial"

    def _mark_error(self, key: str, status: str, error: BaseException) -> None:
        self.progress_repository.mark_finished(
            key, status=status, received_count=0,
            error_type=type(error).__name__, error_message=str(error),
        )

    def _cross_check_valid_results(self, outcomes: list[BCTCItemOutcome]) -> pd.DataFrame:
        frames: dict[str, list[pd.DataFrame]] = {"fireant": [], "vnstock": []}
        for outcome in outcomes:
            if outcome.normalized is not None and outcome.validation is not None and outcome.validation.is_valid:
                frames[outcome.source].append(outcome.normalized)
        combined = {
            source: pd.concat(source_frames, ignore_index=True) if source_frames else pd.DataFrame(columns=RECORD_COLUMNS)
            for source, source_frames in frames.items()
        }
        return self.cross_checker.compare(combined["fireant"], combined["vnstock"])
