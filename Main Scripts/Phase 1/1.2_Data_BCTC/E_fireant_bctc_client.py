"""
Module: E_fireant_bctc_client
Logic:  Gọi cổng BCTC FireAnt và trả kết quả có nguồn/trạng thái rõ ràng.
Detail: Không ghi file, không quản lý checkpoint, không trộn data với VCI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import time
from typing import Any, Callable

import requests
from dotenv import load_dotenv

from E_Helper.E_BlackBox import BlackBox, get_black_box
from E_Helper.E_config import ENV_PATH
from E_bctc_schema import SCHEMA_VERSION


SOURCE = "fireant"
PROVIDER = "fireant_api"
FINANCIAL_DATA_URL = "https://api.fireant.vn/symbols/{symbol}/financial-data"

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_BASE_SECONDS = 1.0
DEFAULT_BACKOFF_MAX_SECONDS = 8.0
RETRYABLE_HTTP_STATUS = frozenset({404, 408, 429, 500, 502, 503, 504})
VALID_PERIOD_TYPES = frozenset({"quarter", "year"})


class FireAntBCTCError(RuntimeError):
    """Lỗi FireAnt có ghi rõ có được thử lại hay không."""

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
class FireAntBCTCResult:
    """Kết quả lấy data; phần ghi file ở Bước 6 sẽ sử dụng object này."""

    schema_version: str
    source: str
    provider: str
    symbol: str
    period_type: str
    requested_count: int
    received_count: int
    collection_status: str
    attempts: int
    collected_at: str
    endpoint_name: str
    payload: list[dict[str, Any]]


def _normalize_symbol(symbol: str) -> str:
    normalized = str(symbol).strip().upper()
    if not normalized or len(normalized) > 20:
        raise ValueError("symbol phải là mã cổ phiếu hợp lệ, dài tối đa 20 ký tự")
    return normalized


def _period_code(period_type: str) -> str:
    if period_type not in VALID_PERIOD_TYPES:
        raise ValueError("period_type chỉ nhận 'quarter' hoặc 'year'")
    return "Q" if period_type == "quarter" else "Y"


def _load_token() -> str:
    load_dotenv(ENV_PATH)
    token = os.getenv("FIREANT_BEARER_TOKEN", "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise FireAntBCTCError(
            "Thiếu FIREANT_BEARER_TOKEN trong System/.env",
            symbol="unknown",
            retryable=False,
            attempts=0,
        )
    return token


class FireAntBCTCClient:
    """Client BCTC FireAnt có timeout, retry giới hạn và dependency giả cho test."""

    def __init__(
        self,
        *,
        token: str | None = None,
        request_get: Callable[..., Any] = requests.get,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
        backoff_max_seconds: float = DEFAULT_BACKOFF_MAX_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        logger: BlackBox | Any | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds phải lớn hơn 0")
        if max_attempts < 1:
            raise ValueError("max_attempts phải ít nhất là 1")
        if backoff_base_seconds < 0 or backoff_max_seconds < 0:
            raise ValueError("thời gian chờ retry không được âm")

        normalized_token = token.strip() if token is not None else _load_token()
        if normalized_token.lower().startswith("bearer "):
            normalized_token = normalized_token[7:].strip()
        if not normalized_token:
            raise FireAntBCTCError(
                "Token FireAnt rỗng",
                symbol="unknown",
                retryable=False,
                attempts=0,
            )

        self._token = normalized_token
        self._request_get = request_get
        self._timeout_seconds = float(timeout_seconds)
        self._max_attempts = int(max_attempts)
        self._backoff_base_seconds = float(backoff_base_seconds)
        self._backoff_max_seconds = float(backoff_max_seconds)
        self._sleep = sleep
        self._logger = logger or get_black_box(__file__).bind()

    def _backoff_seconds(self, attempt: int, response: Any | None = None) -> float:
        delay = min(
            self._backoff_base_seconds * (2 ** max(attempt - 1, 0)),
            self._backoff_max_seconds,
        )
        if response is not None and getattr(response, "status_code", None) == 429:
            retry_after = getattr(response, "headers", {}).get("Retry-After")
            try:
                delay = max(delay, float(retry_after))
            except (TypeError, ValueError):
                pass
            delay = min(delay, self._backoff_max_seconds)
        return delay

    def _warn_retry(self, *, symbol: str, attempt: int, reason: str, delay: float) -> None:
        self._logger.warning(
            "FireAnt tạm lỗi, sẽ thử lại",
            source=SOURCE,
            provider=PROVIDER,
            symbol=symbol,
            attempt=attempt,
            max_attempts=self._max_attempts,
            wait_seconds=delay,
            reason=reason,
        )

    def fetch(
        self,
        symbol: str,
        *,
        period_type: str,
        count: int,
    ) -> FireAntBCTCResult:
        """Lấy gói data tài chính FireAnt theo quý hoặc năm; không ghi file."""
        normalized_symbol = _normalize_symbol(symbol)
        period_code = _period_code(period_type)
        if count < 1:
            raise ValueError("count phải ít nhất là 1")

        url = FINANCIAL_DATA_URL.format(symbol=normalized_symbol)
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        params = {"type": period_code, "count": int(count)}

        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._request_get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self._timeout_seconds,
                )
            except (requests.Timeout, requests.ConnectionError, TimeoutError, ConnectionError) as error:
                if attempt >= self._max_attempts:
                    raise FireAntBCTCError(
                        f"FireAnt không kết nối được cho {normalized_symbol} sau {attempt} lần",
                        symbol=normalized_symbol,
                        retryable=True,
                        attempts=attempt,
                    ) from error
                delay = self._backoff_seconds(attempt)
                self._warn_retry(
                    symbol=normalized_symbol,
                    attempt=attempt,
                    reason=type(error).__name__,
                    delay=delay,
                )
                self._sleep(delay)
                continue

            status_code = int(getattr(response, "status_code", 0))
            if status_code in RETRYABLE_HTTP_STATUS:
                if attempt >= self._max_attempts:
                    raise FireAntBCTCError(
                        f"FireAnt trả lỗi tạm thời HTTP {status_code} cho {normalized_symbol}",
                        symbol=normalized_symbol,
                        retryable=True,
                        status_code=status_code,
                        attempts=attempt,
                    )
                delay = self._backoff_seconds(attempt, response)
                self._warn_retry(
                    symbol=normalized_symbol,
                    attempt=attempt,
                    reason=f"HTTP {status_code}",
                    delay=delay,
                )
                self._sleep(delay)
                continue

            if status_code != 200:
                raise FireAntBCTCError(
                    f"FireAnt từ chối yêu cầu HTTP {status_code} cho {normalized_symbol}",
                    symbol=normalized_symbol,
                    retryable=False,
                    status_code=status_code,
                    attempts=attempt,
                )

            try:
                payload = response.json()
            except (ValueError, TypeError) as error:
                raise FireAntBCTCError(
                    f"FireAnt trả nội dung không phải JSON hợp lệ cho {normalized_symbol}",
                    symbol=normalized_symbol,
                    retryable=False,
                    status_code=status_code,
                    attempts=attempt,
                ) from error

            if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
                raise FireAntBCTCError(
                    f"Cấu trúc data FireAnt lạ cho {normalized_symbol}; cần người kiểm tra",
                    symbol=normalized_symbol,
                    retryable=False,
                    status_code=status_code,
                    attempts=attempt,
                )

            collection_status = "complete" if payload else "no_data_confirmed"
            return FireAntBCTCResult(
                schema_version=SCHEMA_VERSION,
                source=SOURCE,
                provider=PROVIDER,
                symbol=normalized_symbol,
                period_type=period_type,
                requested_count=int(count),
                received_count=len(payload),
                collection_status=collection_status,
                attempts=attempt,
                collected_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                endpoint_name="symbols/{symbol}/financial-data",
                payload=payload,
            )

        raise AssertionError("Luồng retry FireAnt kết thúc ngoài dự kiến")
