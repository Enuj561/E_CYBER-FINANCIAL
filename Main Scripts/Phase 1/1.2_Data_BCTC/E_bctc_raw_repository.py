"""
Module:  E_bctc_raw_repository
Logic:   Persist immutable raw BCTC results and source metadata
Detail:  Ghi raw FireAnt/VCI atomically vào đúng folder nguồn. Không gọi API,
         không sắp xếp data về mẫu chung và không quản lý sổ tiến độ.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from E_Helper.E_BlackBox import BlackBox, get_black_box
from E_Helper.E_config import BCTC_DIR
from E_Helper.E_io_utils import safe_write_json, safe_write_parquet
from E_bctc_schema import SCHEMA_VERSION


SOURCE_FOLDERS = {
    "fireant_api": "From_FireAnt",
    "vci": "From_vnstock",
}
VALID_REPORT_TYPES = frozenset(
    {"balance_sheet", "income_statement", "cash_flow", "ratio", "financial_data"}
)
VALID_PERIOD_TYPES = frozenset({"quarter", "year"})
NO_FILE_STATUSES = frozenset({"no_data_confirmed", "unsupported"})


class BCTCRawRepositoryError(RuntimeError):
    """Lỗi ghi raw BCTC có đường dẫn và nguyên nhân rõ ràng."""


def _clean_name(value: str, *, field: str) -> str:
    cleaned = str(value).strip()
    if not cleaned or any(char in cleaned for char in '<>:"/\\|?*'):
        raise ValueError(f"{field} chứa ký tự không hợp lệ cho tên file")
    return cleaned


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parquet_safe_frame(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    """Giữ giá trị raw nhưng đổi cột object trộn kiểu thành text để Parquet ghi được."""
    safe = frame.copy(deep=True)
    coercions: list[dict[str, Any]] = []
    renames: list[dict[str, Any]] = []
    for position in range(len(safe.columns)):
        series = safe.iloc[:, position]
        if series.dtype != object:
            continue
        python_types = sorted({type(value).__name__ for value in series if not pd.isna(value)})
        if len(python_types) <= 1:
            continue
        safe.iloc[:, position] = series.map(lambda value: None if pd.isna(value) else str(value))
        coercions.append(
            {"column_number": position + 1, "column_name": str(safe.columns[position]),
             "original_python_types": python_types, "stored_as": "string"}
        )
    seen: dict[str, int] = {}
    stored_names: list[str] = []
    occupied: set[str] = set()
    for position, original in enumerate(map(str, safe.columns), start=1):
        occurrence = seen.get(original, 0) + 1
        seen[original] = occurrence
        stored = original
        if occurrence > 1 or stored in occupied:
            stored = f"{original}__source_column_{position}"
            while stored in occupied:
                stored += "_"
            renames.append(
                {"column_number": position, "original_name": original, "stored_name": stored}
            )
        stored_names.append(stored)
        occupied.add(stored)
    safe.columns = stored_names
    return safe, coercions, renames


class BCTCRawRepository:
    """Repository ghi raw theo run; file raw đã có thì không ghi đè âm thầm."""

    def __init__(
        self,
        *,
        root_dir: str | Path = BCTC_DIR,
        write_json: Callable[[str | Path, Any], None] = safe_write_json,
        write_parquet: Callable[[str | Path, pd.DataFrame], None] = safe_write_parquet,
        logger: BlackBox | Any | None = None,
    ) -> None:
        self._root_dir = Path(root_dir)
        self._write_json = write_json
        self._write_parquet = write_parquet
        self._logger = logger or get_black_box(__file__).bind()

    def _paths(
        self,
        *,
        run_id: str,
        provider: str,
        symbol: str,
        report_type: str,
        period_type: str,
        extension: str,
    ) -> tuple[Path, Path]:
        if provider not in SOURCE_FOLDERS:
            raise ValueError(f"provider chưa được hỗ trợ: {provider}")
        if report_type not in VALID_REPORT_TYPES:
            raise ValueError(f"report_type không hợp lệ: {report_type}")
        if period_type not in VALID_PERIOD_TYPES:
            raise ValueError(f"period_type không hợp lệ: {period_type}")

        safe_run_id = _clean_name(run_id, field="run_id")
        safe_symbol = _clean_name(symbol.upper(), field="symbol")
        filename = f"{report_type}_{period_type}_{provider}.{extension}"
        raw_path = (
            self._root_dir
            / SOURCE_FOLDERS[provider]
            / "Raw"
            / safe_run_id
            / safe_symbol
            / filename
        )
        metadata_path = raw_path.with_suffix(raw_path.suffix + ".metadata.json")
        return raw_path, metadata_path

    @staticmethod
    def _base_metadata(result: Any, *, run_id: str, report_type: str) -> dict[str, Any]:
        metadata = asdict(result) if is_dataclass(result) else dict(vars(result))
        metadata.pop("payload", None)
        metadata.pop("frame", None)
        metadata.update(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "requested_report_type": report_type,
                "requested_period_type": result.period_type,
                "request_parameters": {
                    "count": int(result.requested_count),
                    "period_type": result.period_type,
                    "report_type": report_type,
                },
                "http_status": None,
                "library_version": None,
                "error_type": None,
                "error_message": None,
            }
        )
        return metadata

    @staticmethod
    def _library_version(provider: str) -> str | None:
        package = "vnstock" if provider == "vci" else "requests"
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None

    @staticmethod
    def _validate_existing_metadata(metadata_path: Path, raw_path: Path) -> None:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BCTCRawRepositoryError(
                f"Metadata raw đã có nhưng không đọc được: {metadata_path}"
            ) from error
        if metadata.get("content_sha256") != _sha256(raw_path):
            raise BCTCRawRepositoryError(
                f"Raw và metadata không còn khớp nhau: {raw_path}"
            )

    def _existing_raw_is_reusable(
        self,
        *,
        raw_path: Path,
        metadata_path: Path,
        content_matches: Callable[[], bool],
    ) -> bool:
        if metadata_path.exists() and not raw_path.exists():
            raise BCTCRawRepositoryError(
                f"Có metadata nhưng mất file raw: {metadata_path}"
            )
        if not raw_path.exists():
            return False
        try:
            matches = content_matches()
        except Exception as error:
            raise BCTCRawRepositoryError(
                f"Không kiểm tra được raw đang có: {raw_path}"
            ) from error
        if not matches:
            raise BCTCRawRepositoryError(
                f"Raw cùng run đã có nội dung khác; không ghi đè: {raw_path}"
            )
        if metadata_path.exists():
            self._validate_existing_metadata(metadata_path, raw_path)
            return True
        return False

    def _finish_metadata(
        self,
        *,
        raw_path: Path,
        metadata_path: Path,
        metadata: dict[str, Any],
    ) -> str:
        metadata["content_sha256"] = _sha256(raw_path)
        metadata["raw_file"] = str(raw_path)
        metadata["library_version"] = self._library_version(metadata["provider"])
        self._write_json(metadata_path, metadata)
        self._logger.info(
            "Đã lưu raw BCTC",
            source=metadata["source"],
            provider=metadata["provider"],
            symbol=metadata["symbol"],
            report_type=metadata["requested_report_type"],
            period_type=metadata["requested_period_type"],
            run_id=metadata["run_id"],
            output=str(raw_path),
        )
        return str(raw_path)

    def save_fireant(self, result: Any, *, run_id: str, report_type: str) -> str | None:
        """Ghi nguyên payload JSON FireAnt; data rỗng hợp lệ không tạo file raw."""
        if result.provider != "fireant_api" or result.source != "fireant":
            raise ValueError("Kết quả không thuộc nguồn FireAnt")
        if result.collection_status in NO_FILE_STATUSES:
            return None
        if result.collection_status != "complete" or not result.payload:
            raise BCTCRawRepositoryError("FireAnt chưa có data complete để ghi raw")

        raw_path, metadata_path = self._paths(
            run_id=run_id,
            provider=result.provider,
            symbol=result.symbol,
            report_type=report_type,
            period_type=result.period_type,
            extension="json",
        )
        metadata = self._base_metadata(result, run_id=run_id, report_type=report_type)
        metadata["endpoint_name"] = result.endpoint_name
        raw_exists = raw_path.exists()
        reusable = self._existing_raw_is_reusable(
            raw_path=raw_path,
            metadata_path=metadata_path,
            content_matches=lambda: json.loads(raw_path.read_text(encoding="utf-8"))
            == result.payload,
        )
        if reusable:
            return str(raw_path)
        if not raw_exists:
            self._write_json(raw_path, result.payload)
        try:
            return self._finish_metadata(
                raw_path=raw_path, metadata_path=metadata_path, metadata=metadata
            )
        except Exception:
            raw_path.unlink(missing_ok=True)
            raise

    def save_vci(self, result: Any, *, run_id: str) -> str | None:
        """Ghi nguyên DataFrame VCI; data rỗng hợp lệ không tạo file raw."""
        if result.provider != "vci" or result.source != "vnstock":
            raise ValueError("Kết quả không thuộc nguồn vnstock/VCI")
        if result.collection_status in NO_FILE_STATUSES:
            return None
        if result.collection_status != "complete" or result.frame.empty:
            raise BCTCRawRepositoryError("VCI chưa có data complete để ghi raw")

        raw_path, metadata_path = self._paths(
            run_id=run_id,
            provider=result.provider,
            symbol=result.symbol,
            report_type=result.report_type,
            period_type=result.period_type,
            extension="parquet",
        )
        metadata = self._base_metadata(
            result, run_id=run_id, report_type=result.report_type
        )
        metadata["endpoint_name"] = "vnstock.Finance.provider._get_financial_report"
        stored_frame, storage_coercions, storage_column_renames = _parquet_safe_frame(result.frame)
        metadata["storage_coercions"] = storage_coercions
        metadata["storage_column_renames"] = storage_column_renames
        raw_exists = raw_path.exists()

        def existing_frame_matches() -> bool:
            try:
                existing = pd.read_parquet(raw_path)
                pd.testing.assert_frame_equal(
                    existing,
                    stored_frame,
                    check_dtype=False,
                    check_index_type=False,
                    check_column_type=False,
                    check_frame_type=False,
                    check_exact=False,
                )
                return True
            except (AssertionError, ValueError):
                return False

        reusable = self._existing_raw_is_reusable(
            raw_path=raw_path,
            metadata_path=metadata_path,
            content_matches=existing_frame_matches,
        )
        if reusable:
            return str(raw_path)
        if not raw_exists:
            self._write_parquet(raw_path, stored_frame)
        try:
            return self._finish_metadata(
                raw_path=raw_path, metadata_path=metadata_path, metadata=metadata
            )
        except Exception:
            raw_path.unlink(missing_ok=True)
            raise
