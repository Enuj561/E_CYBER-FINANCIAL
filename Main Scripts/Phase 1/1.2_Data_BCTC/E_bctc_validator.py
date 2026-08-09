"""
Module:  E_bctc_validator
Logic:   Validate normalized BCTC records without mutating them
Detail:  Nhận DataFrame/status qua tham số và trả báo cáo lỗi, cảnh báo, kiểm tra
         bị bỏ qua. Không đọc/ghi file, không sửa data và không tự chọn nguồn đúng.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import json
import math
from typing import Any, Iterable

import pandas as pd

from E_bctc_schema import (
    RECORD_COLUMNS,
    SCHEMA_VERSION,
    SOURCE_PROVIDER_PAIRS,
    VALID_PERIOD_TYPES,
    VALID_REPORT_TYPES,
    VALID_SOURCE_UNITS,
)


ROUNDING_IN_VND = {
    "VND": 1.0,
    "thousand_VND": 1_000.0,
    "million_VND": 1_000_000.0,
}
RELATIVE_EQUATION_TOLERANCE = 1e-8
EMPTY_STATUSES = frozenset({"no_data_confirmed", "unsupported"})
SUCCESS_WITH_DATA_STATUSES = frozenset({"complete", "partial"})


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FinancialEquation:
    name: str
    report_type: str
    left_item: str
    right_items: tuple[tuple[str, float], ...]


DEFAULT_FINANCIAL_EQUATIONS = (
    FinancialEquation(
        name="assets_equal_liabilities_plus_equity",
        report_type="balance_sheet",
        left_item="total_assets",
        right_items=(("total_liabilities", 1.0), ("total_equity", 1.0)),
    ),
    FinancialEquation(
        name="ending_cash_reconciliation",
        report_type="cash_flow",
        left_item="cash_and_equivalents_end",
        right_items=(
            ("cash_and_equivalents_begin", 1.0),
            ("net_change_in_cash", 1.0),
            ("fx_effect_on_cash", 1.0),
        ),
    ),
    FinancialEquation(
        name="gross_profit_reconciliation",
        report_type="income_statement",
        left_item="gross_profit",
        right_items=(("revenue", 1.0), ("cost_of_goods_sold", -1.0)),
    ),
)


@dataclass
class BCTCValidationReport:
    checked_rows: int
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    skipped_checks: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def summary(self) -> dict[str, int | bool]:
        return {
            "is_valid": self.is_valid,
            "checked_rows": self.checked_rows,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "skipped_checks": len(self.skipped_checks),
        }


def _issue(code: str, message: str, **context: Any) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, context=context)


def _is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
        return bool(result) if not isinstance(result, (list, tuple, pd.Series)) else False
    except (TypeError, ValueError):
        return False


def _period_end(year: int, quarter: int | None) -> date:
    if quarter is None:
        return date(year, 12, 31)
    month_day = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    month, day = month_day[quarter]
    return date(year, month, day)


def _serialized_row(row: pd.Series) -> str:
    return json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True, default=str)


class BCTCValidator:
    """Validator thuần; lỗi làm báo cáo fail nhưng không đụng vào DataFrame."""

    def __init__(
        self,
        *,
        equations: Iterable[FinancialEquation] = DEFAULT_FINANCIAL_EQUATIONS,
    ) -> None:
        self._equations = tuple(equations)

    def validate(
        self,
        records: pd.DataFrame | None,
        *,
        collection_status: str | None = None,
        expected_symbol: str | None = None,
        expected_source: str | None = None,
        as_of_date: date | None = None,
        load_error: BaseException | None = None,
    ) -> BCTCValidationReport:
        report = BCTCValidationReport(checked_rows=0 if records is None else len(records))
        if load_error is not None or records is None:
            report.errors.append(
                _issue(
                    "file_unreadable",
                    "Không đọc được file data",
                    error_type=type(load_error).__name__ if load_error else "UnknownLoadError",
                    error_message=str(load_error)[:500] if load_error else None,
                )
            )
            return report

        missing_columns = [column for column in RECORD_COLUMNS if column not in records.columns]
        if missing_columns:
            report.errors.append(
                _issue("missing_columns", "Thiếu cột bắt buộc", columns=missing_columns)
            )
            return report

        if records.empty:
            if collection_status in SUCCESS_WITH_DATA_STATUSES:
                report.errors.append(
                    _issue(
                        "empty_marked_success",
                        "Data rỗng nhưng trạng thái lại nói có data",
                        collection_status=collection_status,
                    )
                )
            elif collection_status not in EMPTY_STATUSES:
                report.warnings.append(
                    _issue(
                        "empty_without_clear_status",
                        "Data rỗng nhưng chưa có trạng thái xác nhận rõ",
                        collection_status=collection_status,
                    )
                )
            return report

        if collection_status in EMPTY_STATUSES:
            report.errors.append(
                _issue(
                    "data_present_marked_empty",
                    "Có data nhưng trạng thái lại nói nguồn rỗng/chưa hỗ trợ",
                    collection_status=collection_status,
                )
            )

        self._validate_identity(records, report, expected_symbol, expected_source)
        self._validate_schema_and_periods(records, report, as_of_date or date.today())
        self._validate_duplicates(records, report)
        self._validate_values_and_units(records, report)
        self._validate_financial_equations(records, report)
        return report

    @staticmethod
    def _validate_identity(
        records: pd.DataFrame,
        report: BCTCValidationReport,
        expected_symbol: str | None,
        expected_source: str | None,
    ) -> None:
        symbols = {str(value) for value in records["symbol"].dropna().unique()}
        sources = {str(value) for value in records["source"].dropna().unique()}
        if len(symbols) != 1:
            report.errors.append(
                _issue("mixed_symbols", "Một bảng chứa nhiều mã cổ phiếu", symbols=sorted(symbols))
            )
        if len(sources) != 1:
            report.errors.append(
                _issue("mixed_sources", "Một bảng chứa nhiều nguồn", sources=sorted(sources))
            )
        if expected_symbol and symbols != {expected_symbol.strip().upper()}:
            report.errors.append(
                _issue(
                    "wrong_symbol",
                    "Mã trong data không khớp mã yêu cầu",
                    expected=expected_symbol.strip().upper(),
                    actual=sorted(symbols),
                )
            )
        if expected_source and sources != {expected_source}:
            report.errors.append(
                _issue(
                    "wrong_source",
                    "Nguồn trong data không khớp nguồn yêu cầu",
                    expected=expected_source,
                    actual=sorted(sources),
                )
            )

        pairs = set(zip(records["source"].astype(str), records["provider"].astype(str)))
        invalid_pairs = sorted(pairs - SOURCE_PROVIDER_PAIRS)
        if invalid_pairs:
            report.errors.append(
                _issue(
                    "invalid_source_provider",
                    "Source và provider không đi cùng nhau",
                    pairs=invalid_pairs,
                )
            )

    @staticmethod
    def _validate_schema_and_periods(
        records: pd.DataFrame,
        report: BCTCValidationReport,
        as_of_date: date,
    ) -> None:
        wrong_versions = sorted(
            {str(value) for value in records["schema_version"].dropna().unique()}
            - {SCHEMA_VERSION}
        )
        if wrong_versions:
            report.errors.append(
                _issue(
                    "wrong_schema_version",
                    "Data không đúng phiên bản contract hiện hành",
                    versions=wrong_versions,
                )
            )

        current_year_ratio_rows = 0
        for index, row in records.iterrows():
            period_type = row["period_type"]
            report_type = row["report_type"]
            if period_type not in VALID_PERIOD_TYPES:
                report.errors.append(
                    _issue("invalid_period_type", "Loại kỳ không hợp lệ", row=str(index))
                )
                continue
            if report_type not in VALID_REPORT_TYPES:
                report.errors.append(
                    _issue("invalid_report_type", "Loại báo cáo không hợp lệ", row=str(index))
                )
            try:
                year = int(row["fiscal_year"])
                quarter = None if _is_null(row["fiscal_quarter"]) else int(row["fiscal_quarter"])
            except (TypeError, ValueError):
                report.errors.append(
                    _issue("invalid_period_value", "Năm/quý không đổi được thành số", row=str(index))
                )
                continue
            expected_key = str(year)
            if period_type == "quarter":
                if quarter not in {1, 2, 3, 4}:
                    report.errors.append(
                        _issue("invalid_quarter", "Quý phải từ 1 đến 4", row=str(index))
                    )
                    continue
                expected_key = f"{year}-Q{quarter}"
            elif quarter is not None:
                report.errors.append(
                    _issue("year_has_quarter", "Báo cáo năm không được mang số quý", row=str(index))
                )
            if str(row["period_key"]) != expected_key:
                report.errors.append(
                    _issue(
                        "period_key_mismatch",
                        "Tên kỳ không khớp năm/quý",
                        row=str(index),
                        expected=expected_key,
                        actual=str(row["period_key"]),
                    )
                )
            is_current_year_ratio = (
                report_type == "ratio"
                and period_type == "year"
                and year == as_of_date.year
            )
            if is_current_year_ratio:
                current_year_ratio_rows += 1
            elif _period_end(year, quarter) > as_of_date:
                report.errors.append(
                    _issue(
                        "future_period",
                        "Kỳ báo cáo nằm trong tương lai",
                        row=str(index),
                        period_key=expected_key,
                    )
                )

            collected_at = pd.to_datetime(row["collected_at"], errors="coerce")
            if pd.isna(collected_at) or collected_at.tzinfo is None:
                report.errors.append(
                    _issue(
                        "collected_at_without_timezone",
                        "Thời gian lấy data thiếu hoặc không có múi giờ",
                        row=str(index),
                    )
                )
        if current_year_ratio_rows:
            report.warnings.append(
                _issue(
                    "current_year_ratio_incomplete",
                    "Tỷ lệ của năm hiện tại có thể là YTD, chưa phải số cả năm đã chốt",
                    rows=current_year_ratio_rows,
                    fiscal_year=as_of_date.year,
                )
            )

    @staticmethod
    def _validate_duplicates(records: pd.DataFrame, report: BCTCValidationReport) -> None:
        serialized = records.apply(_serialized_row, axis=1)
        duplicated = serialized.duplicated(keep=False)
        if duplicated.any():
            report.errors.append(
                _issue(
                    "exact_duplicate_rows",
                    "Có dòng trùng hoàn toàn",
                    count=int(duplicated.sum()),
                    row_indices=[str(index) for index in records.index[duplicated].tolist()[:20]],
                )
            )

        keys = ["run_id", "provider", "symbol", "report_type", "period_key", "source_item_key"]
        duplicated_keys = records.duplicated(keys, keep=False)
        if duplicated_keys.any():
            report.errors.append(
                _issue(
                    "duplicate_record_keys",
                    "Khóa record bị trùng; dòng/cột nguồn chưa được phân biệt đủ",
                    count=int(duplicated_keys.sum()),
                )
            )

    @staticmethod
    def _validate_values_and_units(
        records: pd.DataFrame, report: BCTCValidationReport
    ) -> None:
        warning_specs = (
            (records["report_type"] == "unknown", "unclassified_report_type", "Có mục chưa xác định loại báo cáo"),
            (records["source_unit"] == "unknown", "unknown_unit", "Có mục chưa xác định đơn vị"),
            (records["mapping_status"] != "confirmed", "unconfirmed_mapping", "Có mục chưa có mapping confirmed"),
            (records["publication_date"].isna(), "missing_publication_date", "Có mục chưa có ngày công bố"),
            (records["consolidation_status"] == "unknown", "unknown_consolidation", "Có mục chưa rõ hợp nhất hay riêng lẻ"),
        )
        for mask, code, message in warning_specs:
            count = int(mask.sum())
            if count:
                report.warnings.append(_issue(code, message, count=count))

        for index, row in records.iterrows():
            value_type = row["value_type"]
            source_unit = row["source_unit"]
            numeric = row["value_numeric"]
            value_vnd = row["value_vnd"]
            if row["record_status"] == "parse_error":
                report.errors.append(
                    _issue("value_parse_error", "Giá trị nguồn không đổi được đúng kiểu", row=str(index))
                )
            if source_unit not in VALID_SOURCE_UNITS:
                report.errors.append(
                    _issue("invalid_source_unit", "Đơn vị nguồn không hợp lệ", row=str(index))
                )
                continue
            if value_type == "money":
                if source_unit in {"unknown", "not_applicable"}:
                    report.errors.append(
                        _issue("money_without_unit", "Giá trị tiền bị thiếu đơn vị", row=str(index))
                    )
                multiplier = row["unit_multiplier_to_vnd"]
                if not _is_null(numeric) and not _is_null(multiplier):
                    expected_vnd = float(numeric) * float(multiplier)
                    if _is_null(value_vnd) or not math.isclose(
                        float(value_vnd), expected_vnd, rel_tol=0.0, abs_tol=1e-9
                    ):
                        report.errors.append(
                            _issue(
                                "wrong_vnd_conversion",
                                "Giá trị VNĐ không khớp giá trị gốc × hệ số",
                                row=str(index),
                            )
                        )
            elif source_unit == "unknown" and not _is_null(value_vnd):
                report.errors.append(
                    _issue(
                        "unknown_unit_has_vnd",
                        "Đơn vị chưa rõ nhưng lại có giá trị VNĐ",
                        row=str(index),
                    )
                )
            if value_type == "ratio" and not _is_null(value_vnd):
                report.errors.append(
                    _issue("ratio_has_vnd", "Tỷ lệ không được đổi thành VNĐ", row=str(index))
                )

    def _validate_financial_equations(
        self, records: pd.DataFrame, report: BCTCValidationReport
    ) -> None:
        group_columns = [
            "source",
            "provider",
            "symbol",
            "company_type",
            "report_type",
            "period_key",
            "consolidation_status",
        ]
        confirmed = records[
            (records["mapping_status"] == "confirmed")
            & records["canonical_item_id"].notna()
            & records["value_vnd"].notna()
        ]
        for equation in self._equations:
            equation_rows = confirmed[confirmed["report_type"] == equation.report_type]
            if equation_rows.empty:
                report.skipped_checks.append(
                    _issue(
                        "financial_check_skipped",
                        "Chưa có mapping confirmed để kiểm tra công thức tài chính",
                        equation=equation.name,
                    )
                )
                continue
            for group_key, group in equation_rows.groupby(group_columns, dropna=False):
                needed = {equation.left_item, *(item for item, _ in equation.right_items)}
                by_item: dict[str, pd.DataFrame] = {
                    item: group[group["canonical_item_id"] == item] for item in needed
                }
                missing = sorted(item for item, rows in by_item.items() if rows.empty)
                ambiguous = sorted(item for item, rows in by_item.items() if len(rows) > 1)
                context = dict(zip(group_columns, group_key))
                if missing or ambiguous:
                    report.skipped_checks.append(
                        _issue(
                            "financial_check_skipped",
                            "Thiếu hoặc trùng chỉ tiêu confirmed nên không đoán để kiểm tra",
                            equation=equation.name,
                            missing=missing,
                            ambiguous=ambiguous,
                            **context,
                        )
                    )
                    continue

                left_row = by_item[equation.left_item].iloc[0]
                left_value = float(left_row["value_vnd"])
                right_value = sum(
                    float(by_item[item].iloc[0]["value_vnd"]) * sign
                    for item, sign in equation.right_items
                )
                rows_used = [left_row, *(by_item[item].iloc[0] for item, _ in equation.right_items)]
                rounding = max(
                    ROUNDING_IN_VND.get(str(row["source_unit"]), 0.0) for row in rows_used
                )
                scale = max(abs(left_value), abs(right_value), 1.0)
                allowed_difference = max(
                    rounding * len(rows_used), scale * RELATIVE_EQUATION_TOLERANCE
                )
                actual_difference = abs(left_value - right_value)
                if actual_difference > allowed_difference:
                    report.errors.append(
                        _issue(
                            "financial_equation_failed",
                            "Quan hệ tài chính không cân bằng trong sai số cho phép",
                            equation=equation.name,
                            left_value=left_value,
                            right_value=right_value,
                            difference=actual_difference,
                            allowed_difference=allowed_difference,
                            **context,
                        )
                    )
