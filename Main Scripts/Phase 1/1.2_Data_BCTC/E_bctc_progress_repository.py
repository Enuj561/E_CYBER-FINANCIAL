"""
Module:  E_bctc_progress_repository
Logic:   Persist BCTC item progress for safe resume
Detail:  Giữ trạng thái riêng theo nguồn, mã, loại báo cáo và quý/năm.
         Không gọi API, không ghi raw data và không tự điều phối batch.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from threading import RLock
from typing import Any, Callable

from E_Helper.E_BlackBox import BlackBox, get_black_box
from E_Helper.E_config import BCTC_STATE_DIR
from E_Helper.E_io_utils import safe_write_json
from E_bctc_schema import SCHEMA_VERSION


PIPELINE_NAME = "phase1_bctc"
TERMINAL_SKIP_STATUSES = frozenset(
    {"complete", "partial", "no_data_confirmed", "unsupported", "failed_fatal", "cancelled"}
)
RETRY_STATUSES = frozenset({"pending", "failed_retryable"})
ALL_STATUSES = TERMINAL_SKIP_STATUSES | RETRY_STATUSES | {"running"}

_SECRET_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;]+"),
)


class BCTCProgressError(RuntimeError):
    """Lỗi sổ tiến độ BCTC cần caller xử lý rõ."""


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _fingerprint(plan: dict[str, Any]) -> str:
    encoded = json.dumps(plan, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_error_message(message: str | None) -> str | None:
    if message is None:
        return None
    safe = str(message)
    for pattern in _SECRET_PATTERNS:
        safe = pattern.sub(r"\1***", safe)
    return safe[:2000]


def item_key(
    *, source: str, provider: str, symbol: str, report_type: str, period_type: str
) -> str:
    """Tạo khóa ổn định; không dùng dấu này trong các giá trị đầu vào."""
    values = (source, provider, symbol.upper(), report_type, period_type)
    if any(not str(value).strip() or "|" in str(value) for value in values):
        raise ValueError("Thông tin item rỗng hoặc chứa ký tự '|' không hợp lệ")
    return "|".join(str(value).strip() for value in values)


class BCTCProgressRepository:
    """Sổ tiến độ atomically; mở lại sẽ nhận ra item đang chạy bị ngắt."""

    def __init__(
        self,
        *,
        run_id: str,
        collection_plan: dict[str, Any],
        state_dir: str | Path = BCTC_STATE_DIR,
        write_json: Callable[[str | Path, Any], None] = safe_write_json,
        clock: Callable[[], str] = _now,
        logger: BlackBox | Any | None = None,
    ) -> None:
        if not run_id.strip() or any(char in run_id for char in '<>:"/\\|?*'):
            raise ValueError("run_id không hợp lệ cho tên file")
        self._lock = RLock()
        self.run_id = run_id.strip()
        self._plan = collection_plan
        self._plan_fingerprint = _fingerprint(collection_plan)
        self._path = Path(state_dir) / "runs" / f"{self.run_id}.json"
        self._write_json = write_json
        self._clock = clock
        self._logger = logger or get_black_box(__file__).bind()
        with self._lock:
            self._state = self._load_or_create()
            self._recover_interrupted_items()


    @property
    def path(self) -> Path:
        return self._path

    def _load_or_create(self) -> dict[str, Any]:
        if not self._path.exists():
            now = self._clock()
            state = {
                "schema_version": SCHEMA_VERSION,
                "pipeline": PIPELINE_NAME,
                "run_id": self.run_id,
                "plan_fingerprint": self._plan_fingerprint,
                "collection_plan": self._plan,
                "status": "in_progress",
                "created_at": now,
                "updated_at": now,
                "items": {},
            }
            self._write_json(self._path, state)
            return state

        try:
            with self._path.open("r", encoding="utf-8") as stream:
                state = json.load(stream)
        except (OSError, json.JSONDecodeError) as error:
            raise BCTCProgressError(f"Không đọc được sổ tiến độ: {self._path}") from error

        if state.get("schema_version") != SCHEMA_VERSION:
            raise BCTCProgressError("Sổ tiến độ khác phiên bản data; không resume mù quáng")
        if state.get("run_id") != self.run_id:
            raise BCTCProgressError("run_id trong sổ tiến độ không khớp")
        if state.get("plan_fingerprint") != self._plan_fingerprint:
            raise BCTCProgressError("Kế hoạch cào đã đổi; không resume bằng sổ cũ")
        if not isinstance(state.get("items"), dict):
            raise BCTCProgressError("Danh sách item trong sổ tiến độ bị hỏng")
        return state

    def _save(self) -> None:
        with self._lock:
            self._state["updated_at"] = self._clock()
            self._write_json(self._path, self._state)

    def _recover_interrupted_items(self) -> None:
        with self._lock:
            recovered = 0
            for item in self._state["items"].values():
                if item.get("status") == "running":
                    item.update(
                        {
                            "status": "failed_retryable",
                            "finished_at": self._clock(),
                            "error_type": "InterruptedRun",
                            "error_message": "Lần chạy trước dừng giữa chừng; item cần làm lại",
                        }
                    )
                    recovered += 1
            if recovered:
                self._save()
                self._logger.warning(
                    "Đã khôi phục item BCTC bị ngắt",
                    run_id=self.run_id,
                    recovered_items=recovered,
                )

    def ensure_item(
        self,
        *,
        source: str,
        provider: str,
        symbol: str,
        report_type: str,
        period_type: str,
        requested_count: int,
    ) -> str:
        if requested_count < 1:
            raise ValueError("requested_count phải ít nhất là 1")
        key = item_key(
            source=source,
            provider=provider,
            symbol=symbol,
            report_type=report_type,
            period_type=period_type,
        )
        with self._lock:
            existing = self._state["items"].get(key)
            if existing:
                if int(existing["requested_count"]) != int(requested_count):
                    raise BCTCProgressError("Số kỳ yêu cầu của item đã đổi trong cùng run")
                return key

            now = self._clock()
            self._state["items"][key] = {
                "source": source,
                "provider": provider,
                "symbol": symbol.upper(),
                "report_type": report_type,
                "period_type": period_type,
                "status": "pending",
                "attempt_count": 0,
                "requested_count": int(requested_count),
                "received_count": 0,
                "started_at": None,
                "finished_at": None,
                "updated_at": now,
                "raw_file": None,
                "error_type": None,
                "error_message": None,
            }
            self._save()
            return key

    def should_process(self, key: str, *, include_cancelled: bool = False) -> bool:
        with self._lock:
            item = self._state["items"].get(key)
            if item is None:
                raise KeyError(f"Item chưa có trong sổ tiến độ: {key}")
            status = item.get("status")
            if status not in ALL_STATUSES:
                raise BCTCProgressError(f"Trạng thái item không hợp lệ: {status}")
            if status == "cancelled":
                return include_cancelled
            return status not in TERMINAL_SKIP_STATUSES

    def mark_running(self, key: str) -> None:
        with self._lock:
            item = self._state["items"].get(key)
            if item is None:
                raise KeyError(f"Item chưa có trong sổ tiến độ: {key}")
            if not self.should_process(key):
                raise BCTCProgressError(f"Không được chạy lại item có trạng thái {item['status']}")
            now = self._clock()
            item.update(
                {
                    "status": "running",
                    "attempt_count": int(item["attempt_count"]) + 1,
                    "started_at": now,
                    "finished_at": None,
                    "updated_at": now,
                    "error_type": None,
                    "error_message": None,
                }
            )
            self._save()

    def mark_finished(
        self,
        key: str,
        *,
        status: str,
        received_count: int,
        raw_file: str | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        if status not in ALL_STATUSES - {"pending", "running"}:
            raise ValueError(f"Trạng thái kết thúc không hợp lệ: {status}")
        with self._lock:
            item = self._state["items"].get(key)
            if item is None:
                raise KeyError(f"Item chưa có trong sổ tiến độ: {key}")
            if item.get("status") != "running":
                raise BCTCProgressError("Chỉ item đang running mới được đánh dấu kết thúc")
            if received_count < 0:
                raise ValueError("received_count không được âm")
            if status == "complete" and (not raw_file or not Path(raw_file).is_file()):
                raise BCTCProgressError("Không được đánh dấu complete khi chưa có file raw")
            if status == "complete" and received_count < int(item["requested_count"]):
                raise BCTCProgressError("Nhận thiếu kỳ thì phải ghi partial, không được ghi complete")
            if status == "partial" and (
                received_count < 1 or not raw_file or not Path(raw_file).is_file()
            ):
                raise BCTCProgressError("partial phải có data và file raw đọc được")
            if status in {"no_data_confirmed", "unsupported"} and (
                raw_file or received_count != 0
            ):
                raise BCTCProgressError(f"{status} không được gắn data/file raw giả")
            if status.startswith("failed_") and not error_type:
                raise BCTCProgressError("Trạng thái lỗi phải có error_type")

            now = self._clock()
            item.update(
                {
                    "status": status,
                    "received_count": int(received_count),
                    "finished_at": now,
                    "updated_at": now,
                    "raw_file": raw_file,
                    "error_type": error_type,
                    "error_message": _safe_error_message(error_message),
                }
            )
            self._save()

    def item(self, key: str) -> dict[str, Any]:
        with self._lock:
            if key not in self._state["items"]:
                raise KeyError(f"Item chưa có trong sổ tiến độ: {key}")
            return dict(self._state["items"][key])

    def summary(self) -> dict[str, int]:
        with self._lock:
            counts = {status: 0 for status in ALL_STATUSES}
            for item in self._state["items"].values():
                counts[item["status"]] += 1
            return {status: count for status, count in counts.items() if count}

