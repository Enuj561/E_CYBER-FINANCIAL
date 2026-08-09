"""
Module: E_vci_bctc_client
Logic:  Gọi BCTC qua vnstock với provider VCI và trả DataFrame có trạng thái rõ.
Detail: Không ghi file, không quản lý checkpoint, không tự chuyển sang KBS.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import time
from typing import Any, Callable

import pandas as pd
import requests

from E_Helper.E_BlackBox import BlackBox, get_black_box
from E_bctc_schema import SCHEMA_VERSION


SOURCE = "vnstock"
PROVIDER = "vci"

# vnstock/VCI hiện giới hạn mỗi lần gọi chính ở 30 giây (bắt tay: 10 giây).
# Finance API chưa cho truyền con số này từ bên ngoài, nên không giả vờ rằng client
# có thể đổi nó. Nếu vnstock thay đổi cách gọi, bài kiểm tra tương thích phải báo lại.
VCI_REQUEST_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_BASE_SECONDS = 1.0
DEFAULT_BACKOFF_MAX_SECONDS = 8.0
RETRYABLE_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})
VALID_PERIOD_TYPES = frozenset({"quarter", "year"})
VALID_REPORT_TYPES = frozenset(
    {"balance_sheet", "income_statement", "cash_flow", "ratio"}
)


class VCIBCTCError(RuntimeError):
    """Lỗi VCI có ghi rõ có được thử lại hay không."""

    def __init__(
        self,
        message: str,
        *,
        symbol: str,
        retryable: bool,
        status_code: int | None = None,
        attempts: int = 1,
    ) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.retryable = retryable
        self.status_code = status_code
        self.attempts = attempts


@dataclass(frozen=True)
class VCIBCTCResult:
    """Kết quả lấy VCI; phần ghi file ở Bước 6 sẽ sử dụng object này."""

    schema_version: str
    source: str
    provider: str
    symbol: str
    report_type: str
    period_type: str
    requested_count: int
    received_count: int
    collection_status: str
    attempts: int
    collected_at: str
    frame: pd.DataFrame


def _normalize_symbol(symbol: str) -> str:
    normalized = str(symbol).strip().upper()
    if not normalized or len(normalized) > 20:
        raise ValueError("symbol phải là mã cổ phiếu hợp lệ, dài tối đa 20 ký tự")
    return normalized


def _default_finance_factory(symbol: str, period_type: str) -> Any:
    from vnstock import Finance

    return Finance(
        source="VCI",
        symbol=symbol,
        period=period_type,
        get_all=True,
        show_log=False,
    )


class VCIBCTCClient:
    """Client VCI có retry giới hạn và factory giả cho unit test offline."""

    def __init__(
        self,
        *,
        finance_factory: Callable[[str, str], Any] = _default_finance_factory,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
        backoff_max_seconds: float = DEFAULT_BACKOFF_MAX_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        logger: BlackBox | Any | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts phải ít nhất là 1")
        if backoff_base_seconds < 0 or backoff_max_seconds < 0:
            raise ValueError("thời gian chờ retry không được âm")

        self._finance_factory = finance_factory
        self._max_attempts = int(max_attempts)
        self._backoff_base_seconds = float(backoff_base_seconds)
        self._backoff_max_seconds = float(backoff_max_seconds)
        self._sleep = sleep
        self._logger = logger or get_black_box(__file__).bind()

    @property
    def timeout_seconds(self) -> float:
        """Giới hạn chờ của mỗi request do vnstock/VCI đang áp dụng."""
        return VCI_REQUEST_TIMEOUT_SECONDS

    def _backoff_seconds(self, attempt: int) -> float:
        return min(
            self._backoff_base_seconds * (2 ** max(attempt - 1, 0)),
            self._backoff_max_seconds,
        )

    @staticmethod
    def _http_status(error: BaseException) -> int | None:
        response = getattr(error, "response", None)
        status_code = getattr(response, "status_code", None)
        return int(status_code) if status_code is not None else None

    @classmethod
    def _is_retryable(cls, error: BaseException) -> bool:
        if isinstance(
            error,
            (requests.Timeout, requests.ConnectionError, TimeoutError, ConnectionError),
        ):
            return True
        status_code = cls._http_status(error)
        return status_code in RETRYABLE_HTTP_STATUS

    def _warn_retry(self, *, symbol: str, report_type: str, attempt: int, error: BaseException, delay: float) -> None:
        self._logger.warning(
            "VCI tạm lỗi, sẽ thử lại",
            source=SOURCE,
            provider=PROVIDER,
            symbol=symbol,
            report_type=report_type,
            attempt=attempt,
            max_attempts=self._max_attempts,
            wait_seconds=delay,
            reason=type(error).__name__,
        )

    def _request_once(
        self,
        *,
        symbol: str,
        report_type: str,
        period_type: str,
        count: int,
    ) -> pd.DataFrame:
        finance = self._finance_factory(symbol, period_type)
        provider = getattr(finance, "provider", finance)
        method = getattr(provider, "_get_financial_report", None)
        if not callable(method):
            raise TypeError(
                "vnstock/VCI hiện tại không có cổng lấy số kỳ theo contract; cần kiểm tra phiên bản"
            )
        frame = method(
            report_type,
            period=period_type,
            lang="en",
            get_all=True,
            dropna=False,
            show_log=False,
            limit=count,
        )
        if not isinstance(frame, pd.DataFrame):
            raise TypeError("VCI trả kết quả không phải pandas DataFrame")
        return frame

    def fetch(
        self,
        symbol: str,
        *,
        report_type: str,
        period_type: str,
        count: int,
    ) -> VCIBCTCResult:
        """Lấy một loại BCTC VCI theo quý hoặc năm; không ghi file."""
        normalized_symbol = _normalize_symbol(symbol)
        if report_type not in VALID_REPORT_TYPES:
            raise ValueError(
                "report_type chỉ nhận balance_sheet, income_statement, cash_flow hoặc ratio"
            )
        if period_type not in VALID_PERIOD_TYPES:
            raise ValueError("period_type chỉ nhận 'quarter' hoặc 'year'")
        if count < 1:
            raise ValueError("count phải ít nhất là 1")

        for attempt in range(1, self._max_attempts + 1):
            try:
                frame = self._request_once(
                    symbol=normalized_symbol,
                    report_type=report_type,
                    period_type=period_type,
                    count=int(count),
                )
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as error:
                retryable = self._is_retryable(error)
                status_code = self._http_status(error)
                if not retryable:
                    raise VCIBCTCError(
                        f"VCI lỗi không nên thử lại cho {normalized_symbol}: {error}",
                        symbol=normalized_symbol,
                        retryable=False,
                        status_code=status_code,
                        attempts=attempt,
                    ) from error
                if attempt >= self._max_attempts:
                    raise VCIBCTCError(
                        f"VCI vẫn lỗi tạm thời cho {normalized_symbol} sau {attempt} lần",
                        symbol=normalized_symbol,
                        retryable=True,
                        status_code=status_code,
                        attempts=attempt,
                    ) from error
                delay = self._backoff_seconds(attempt)
                self._warn_retry(
                    symbol=normalized_symbol,
                    report_type=report_type,
                    attempt=attempt,
                    error=error,
                    delay=delay,
                )
                self._sleep(delay)
                continue

            period_columns = [
                column
                for column in frame.columns
                if isinstance(column, str)
                and (
                    (period_type == "quarter" and "-Q" in column)
                    or (period_type == "year" and column.isdigit() and len(column) == 4)
                )
            ]
            collection_status = "complete" if not frame.empty else "no_data_confirmed"
            return VCIBCTCResult(
                schema_version=SCHEMA_VERSION,
                source=SOURCE,
                provider=PROVIDER,
                symbol=normalized_symbol,
                report_type=report_type,
                period_type=period_type,
                requested_count=int(count),
                received_count=len(period_columns),
                collection_status=collection_status,
                attempts=attempt,
                collected_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                frame=frame,
            )

        raise AssertionError("Luồng retry VCI kết thúc ngoài dự kiến")
