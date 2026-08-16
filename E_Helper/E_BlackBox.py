"""
Module:  E_BlackBox
Logic:   Central structured logging for every project feature
Detail:  Tạo logger dùng chung, ghi JSON Lines cạnh script chính của tính năng và phát
         sự kiện cho UI. Module không chứa nghiệp vụ của Phase, News hoặc IDE.
"""

from __future__ import annotations

import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
import sys
from threading import RLock
from typing import Any, Callable
from uuid import uuid4
from datetime import datetime


MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3
DEFAULT_LEVEL = logging.INFO
_SECRET_KEY = re.compile(r"(api[_-]?key|token|authorization|password|secret)", re.IGNORECASE)
_BEARER_VALUE = re.compile(r"(?i)(bearer\s+)[^\s,;]+")
_SUBSCRIBERS: set[Callable[[dict[str, Any]], None]] = set()
_SUBSCRIBER_LOCK = RLock()


def new_run_id() -> str:
    """Tạo mã ngắn để nối các log thuộc cùng một lần chạy."""
    return uuid4().hex[:12]


def get_system_telemetry() -> dict[str, float]:
    """Lấy thông số tải CPU (%) và RAM tiêu thụ (MB) của process hiện tại."""
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        cpu_pct = process.cpu_percent(interval=None)
        return {
            "cpu_percent": round(float(cpu_pct), 2),
            "memory_mb": round(float(mem_info.rss) / (1024 * 1024), 2),
        }
    except Exception:
        return {"cpu_percent": 0.0, "memory_mb": 0.0}



def _safe_value(value: Any, key: str = "") -> Any:
    """Che secret và đổi object lạ thành dữ liệu có thể ghi JSON."""
    if _SECRET_KEY.search(key):
        return "***REDACTED***"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _BEARER_VALUE.sub(r"\1***REDACTED***", value)
    if isinstance(value, dict):
        return {str(k): _safe_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(item) for item in value]
    return str(value)


def _event_from_record(record: logging.LogRecord) -> dict[str, Any]:
    timestamp = datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="seconds")
    event: dict[str, Any] = {
        "timestamp": timestamp,
        "level": record.levelname,
        "feature": getattr(record, "feature", record.name),
        "run_id": getattr(record, "run_id", None),
        "message": _safe_value(record.getMessage()),
    }
    context = getattr(record, "blackbox_context", {})
    if context:
        event["context"] = _safe_value(context)
    if record.exc_info:
        event["exception"] = _safe_value(logging.Formatter().formatException(record.exc_info))
    return event


class _JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(_event_from_record(record), ensure_ascii=False, separators=(",", ":"))


class _SubscriberHandler(logging.Handler):
    """Phát log trong process cho UI; không import PyQt để giữ đúng chiều phụ thuộc."""

    def emit(self, record: logging.LogRecord) -> None:
        event = _event_from_record(record)
        with _SUBSCRIBER_LOCK:
            callbacks = tuple(_SUBSCRIBERS)
        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                # Subscriber hỏng không được làm hỏng tính năng đang ghi log.
                continue


class BlackBox:
    """Cổng ghi log nhỏ, thống nhất cho mọi tính năng."""

    def __init__(self, logger: logging.Logger, feature: str, run_id: str | None = None):
        self._logger = logger
        self.feature = feature
        self.run_id = run_id

    @property
    def log_path(self) -> Path:
        for handler in self._logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                return Path(handler.baseFilename)
        raise RuntimeError("E_BlackBox chưa có file handler")

    def bind(self, run_id: str | None = None) -> "BlackBox":
        """Tạo view cùng feature nhưng gắn run_id mới."""
        return BlackBox(self._logger, self.feature, run_id or new_run_id())

    def close(self) -> None:
        """Đóng handler khi test hoặc khi toàn process kết thúc có kiểm soát."""
        for handler in tuple(self._logger.handlers):
            handler.close()
            self._logger.removeHandler(handler)

    def _write(self, level: int, message: str, *, exc_info: Any = None, **context: Any) -> None:
        self._logger.log(
            level,
            message,
            exc_info=exc_info,
            extra={
                "feature": self.feature,
                "run_id": self.run_id,
                "blackbox_context": context,
            },
        )

    def debug(self, message: str, **context: Any) -> None:
        self._write(logging.DEBUG, message, **context)

    def info(self, message: str, **context: Any) -> None:
        self._write(logging.INFO, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self._write(logging.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> None:
        self._write(logging.ERROR, message, **context)

    def critical(self, message: str, **context: Any) -> None:
        self._write(logging.CRITICAL, message, **context)

    def exception(self, message: str, **context: Any) -> None:
        self._write(logging.ERROR, message, exc_info=True, **context)


def get_black_box(
    script_path: str | Path,
    *,
    feature: str | None = None,
    run_id: str | None = None,
    level: int = DEFAULT_LEVEL,
    console: bool = False,
) -> BlackBox:
    """Tạo/lấy logger của một script; file log luôn nằm cạnh script đó."""
    script = Path(script_path).resolve()
    if script.suffix.lower() != ".py":
        raise ValueError("script_path phải trỏ tới file Python của tính năng")

    feature_name = feature or script.stem
    digest = hashlib.sha1(str(script).encode("utf-8")).hexdigest()[:10]
    logger = logging.getLogger(f"E.BlackBox.{script.stem}.{digest}")
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        log_path = script.with_suffix(".log")
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(_JsonLineFormatter())
        logger.addHandler(file_handler)
        logger.addHandler(_SubscriberHandler())

        if console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(_JsonLineFormatter())
            logger.addHandler(console_handler)

    return BlackBox(logger, feature_name, run_id)


def subscribe(callback: Callable[[dict[str, Any]], None]) -> None:
    """Đăng ký nơi nhận log trong process, ví dụ panel bên phải của IDE."""
    with _SUBSCRIBER_LOCK:
        _SUBSCRIBERS.add(callback)


def unsubscribe(callback: Callable[[dict[str, Any]], None]) -> None:
    """Gỡ nơi nhận log khi UI đóng."""
    with _SUBSCRIBER_LOCK:
        _SUBSCRIBERS.discard(callback)
