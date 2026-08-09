"""Đối chiếu BCTC đã chuẩn hóa giữa FireAnt và vnstock/VCI."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import pandas as pd

from E_bctc_schema import RECORD_COLUMNS


COMPARISON_COLUMNS = [
    "symbol", "canonical_item_id", "report_type", "period_type", "period_key",
    "period_value_mode", "consolidation_status", "fireant_source_item_id",
    "vnstock_source_item_id", "fireant_value_vnd", "vnstock_value_vnd",
    "absolute_difference", "difference_percent", "comparison_status",
    "comparison_reason", "quality_flags",
]

MATCH_KEYS = [
    "symbol", "canonical_item_id", "report_type", "period_type", "period_key",
    "period_value_mode", "consolidation_status",
]
IDENTITY_KEYS = ["symbol", "canonical_item_id", "period_type", "period_key"]


@dataclass(frozen=True)
class CrossCheckSummary:
    total: int
    matched: int
    different: int
    only_fireant: int
    only_vnstock: int
    not_comparable: int


def _blank(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _output_row(row: pd.Series, *, side: str, status: str, reason: str) -> dict[str, Any]:
    result = {column: None for column in COMPARISON_COLUMNS}
    for column in MATCH_KEYS:
        result[column] = row.get(column)
    result[f"{side}_source_item_id"] = row.get("source_item_id")
    result[f"{side}_value_vnd"] = row.get("value_vnd")
    result["comparison_status"] = status
    result["comparison_reason"] = reason
    result["quality_flags"] = row.get("quality_flags")
    return result


class BCTCCrossChecker:
    """So hai DataFrame trong bộ nhớ; không sửa input và không chọn nguồn thắng."""

    def compare(self, fireant: pd.DataFrame, vnstock: pd.DataFrame) -> pd.DataFrame:
        self._require_normalized(fireant, "fireant")
        self._require_normalized(vnstock, "vnstock")
        left = fireant.copy(deep=True)
        right = vnstock.copy(deep=True)
        rows: list[dict[str, Any]] = []

        left_ready, left_rejected = self._split_ready(left, "fireant")
        right_ready, right_rejected = self._split_ready(right, "vnstock")
        rows.extend(left_rejected)
        rows.extend(right_rejected)

        left_ready, left_duplicates = self._remove_duplicate_keys(left_ready, "fireant")
        right_ready, right_duplicates = self._remove_duplicate_keys(right_ready, "vnstock")
        rows.extend(left_duplicates)
        rows.extend(right_duplicates)

        merged = left_ready.merge(
            right_ready,
            on=MATCH_KEYS,
            how="outer",
            suffixes=("_fireant", "_vnstock"),
            indicator=True,
            validate="one_to_one",
        )
        for _, item in merged.iterrows():
            rows.append(self._compare_merged_row(item, left_ready, right_ready))
        return pd.DataFrame(rows, columns=COMPARISON_COLUMNS)

    @staticmethod
    def summarize(result: pd.DataFrame) -> CrossCheckSummary:
        counts = result["comparison_status"].value_counts().to_dict()
        return CrossCheckSummary(
            total=len(result),
            matched=int(counts.get("matched", 0)),
            different=int(counts.get("different", 0)),
            only_fireant=int(counts.get("only_fireant", 0)),
            only_vnstock=int(counts.get("only_vnstock", 0)),
            not_comparable=int(counts.get("not_comparable", 0)),
        )

    @staticmethod
    def _require_normalized(frame: pd.DataFrame, expected_source: str) -> None:
        missing = [column for column in RECORD_COLUMNS if column not in frame.columns]
        if missing:
            raise ValueError(f"{expected_source}: thiếu cột chuẩn hóa: {missing}")
        sources = set(frame["source"].dropna().astype(str))
        if sources and sources != {expected_source}:
            raise ValueError(f"Bảng {expected_source} chứa sai nguồn: {sorted(sources)}")

    @staticmethod
    def _split_ready(frame: pd.DataFrame, side: str):
        ready: list[int] = []
        rejected: list[dict[str, Any]] = []
        for index, row in frame.iterrows():
            if row.get("mapping_status") != "confirmed" or _blank(row.get("canonical_item_id")):
                rejected.append(_output_row(row, side=side, status="not_comparable", reason="mapping_not_confirmed"))
            elif row.get("report_type") == "unknown":
                rejected.append(_output_row(row, side=side, status="not_comparable", reason="report_type_unknown"))
            elif _blank(row.get("value_vnd")):
                rejected.append(_output_row(row, side=side, status="not_comparable", reason="value_or_unit_unknown"))
            else:
                ready.append(index)
        return frame.loc[ready].copy(), rejected

    @staticmethod
    def _remove_duplicate_keys(frame: pd.DataFrame, side: str):
        duplicated = frame.duplicated(MATCH_KEYS, keep=False)
        rejected = [
            _output_row(row, side=side, status="not_comparable", reason="duplicate_comparison_key")
            for _, row in frame.loc[duplicated].iterrows()
        ]
        return frame.loc[~duplicated].copy(), rejected

    @staticmethod
    def _compare_merged_row(
        row: pd.Series, left_ready: pd.DataFrame, right_ready: pd.DataFrame
    ) -> dict[str, Any]:
        result = {column: row.get(column) for column in MATCH_KEYS}
        result.update(
            fireant_source_item_id=row.get("source_item_id_fireant"),
            vnstock_source_item_id=row.get("source_item_id_vnstock"),
            fireant_value_vnd=row.get("value_vnd_fireant"),
            vnstock_value_vnd=row.get("value_vnd_vnstock"),
            absolute_difference=None,
            difference_percent=None,
            quality_flags=None,
        )
        if row["_merge"] == "left_only":
            reason = BCTCCrossChecker._mismatch_reason(row, right_ready)
            result.update(
                comparison_status="not_comparable" if reason else "only_fireant",
                comparison_reason=reason or "missing_in_vnstock",
            )
            return result
        if row["_merge"] == "right_only":
            reason = BCTCCrossChecker._mismatch_reason(row, left_ready)
            result.update(
                comparison_status="not_comparable" if reason else "only_vnstock",
                comparison_reason=reason or "missing_in_fireant",
            )
            return result

        fireant_value = float(row["value_vnd_fireant"])
        vnstock_value = float(row["value_vnd_vnstock"])
        difference = abs(fireant_value - vnstock_value)
        denominator = max(abs(fireant_value), abs(vnstock_value))
        result["absolute_difference"] = difference
        result["difference_percent"] = 0.0 if denominator == 0 else difference / denominator * 100.0
        equal = math.isclose(fireant_value, vnstock_value, rel_tol=1e-12, abs_tol=0.5)
        result["comparison_status"] = "matched" if equal else "different"
        result["comparison_reason"] = "values_equal" if equal else "values_different"
        if row.get("consolidation_status") == "unknown":
            result["quality_flags"] = "unknown_consolidation"
        return result

    @staticmethod
    def _mismatch_reason(row: pd.Series, other: pd.DataFrame) -> str | None:
        candidates = other
        for key in IDENTITY_KEYS:
            candidates = candidates[candidates[key] == row.get(key)]
        if candidates.empty:
            return None
        if not (candidates["report_type"] == row.get("report_type")).any():
            return "report_type_mismatch"
        same_report = candidates[candidates["report_type"] == row.get("report_type")]
        if not (same_report["period_value_mode"] == row.get("period_value_mode")).any():
            return "period_value_mode_mismatch"
        same_mode = same_report[same_report["period_value_mode"] == row.get("period_value_mode")]
        if not (same_mode["consolidation_status"] == row.get("consolidation_status")).any():
            return "consolidation_mismatch"
        return None
