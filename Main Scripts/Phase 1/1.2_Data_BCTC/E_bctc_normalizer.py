"""
Module:  E_bctc_normalizer
Logic:   Normalize FireAnt and VCI financial data into one record shape
Detail:  Nhận raw data qua tham số và trả DataFrame theo contract chung. Không gọi
         API, không đọc/ghi file, không xóa dòng/cột trùng và không đoán thông tin thiếu.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Mapping, Sequence

import pandas as pd

from E_bctc_schema import RECORD_COLUMNS, SCHEMA_VERSION

PERIOD_COLUMN_PATTERN = re.compile(r"^(?P<year>\d{4})(?:-Q(?P<quarter>[1-4]))?$")
VALID_COMPANY_TYPES = frozenset(
    {"general", "bank", "securities", "insurance", "unknown"}
)
COMPANY_TYPE_MAP = {
    "general": "general",
    "company": "general",
    "bank": "bank",
    "securities": "securities",
    "security": "securities",
    "insurance": "insurance",
}
CONTROL_FIREANT_KEYS = frozenset({"Quarter", "Year", "CompanyType"})

OUTPUT_COLUMNS = RECORD_COLUMNS


@dataclass(frozen=True)
class FireAntItemRule:
    """Chỉ gắn thông tin đã có bằng chứng; mục chưa có rule giữ unknown."""

    report_type: str
    value_type: str
    currency: str
    source_unit: str
    unit_multiplier_to_vnd: float | None
    period_value_mode_quarter: str
    period_value_mode_year: str


MONEY_POINT_IN_TIME = FireAntItemRule(
    report_type="balance_sheet",
    value_type="money",
    currency="VND",
    source_unit="VND",
    unit_multiplier_to_vnd=1.0,
    period_value_mode_quarter="point_in_time",
    period_value_mode_year="point_in_time",
)
MONEY_FLOW = FireAntItemRule(
    report_type="income_statement",
    value_type="money",
    currency="VND",
    source_unit="VND",
    unit_multiplier_to_vnd=1.0,
    period_value_mode_quarter="standalone",
    period_value_mode_year="cumulative",
)
MONEY_CASH_FLOW = FireAntItemRule(
    report_type="cash_flow",
    value_type="money",
    currency="VND",
    source_unit="VND",
    unit_multiplier_to_vnd=1.0,
    period_value_mode_quarter="standalone",
    period_value_mode_year="cumulative",
)

# Ba mục đã được so trực tiếp giữa FireAnt và VCI ở Bước 3.
CONFIRMED_FIREANT_ITEM_RULES: Mapping[str, FireAntItemRule] = {
    "TotalAsset": MONEY_POINT_IN_TIME,
    "ProfitAfterTax": MONEY_FLOW,
    "CashflowFromOperatingActivity": MONEY_CASH_FLOW,
}


def _company_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return COMPANY_TYPE_MAP.get(normalized, "unknown")


def _normalize_symbol(symbol: str) -> str:
    normalized = str(symbol).strip().upper()
    if not normalized:
        raise ValueError("symbol không được rỗng")
    return normalized


def _raw_string(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return str(value)


def _value_parts(value: Any, expected_type: str) -> tuple[float | None, str | None, str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None, None, "source_null"
    if isinstance(value, bool):
        return None, str(value), "parse_error" if expected_type != "unknown" else "unmapped"
    try:
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric, None, "valid" if expected_type != "unknown" else "unmapped"
    except (TypeError, ValueError):
        pass
    return None, str(value), "parse_error" if expected_type in {"money", "ratio", "count"} else "unmapped"


def _period_parts(period_key: str, expected_period_type: str) -> tuple[int, int | None]:
    match = PERIOD_COLUMN_PATTERN.fullmatch(str(period_key))
    if not match:
        raise ValueError(f"Tên kỳ không hợp lệ: {period_key}")
    quarter = int(match.group("quarter")) if match.group("quarter") else None
    actual_type = "quarter" if quarter is not None else "year"
    if actual_type != expected_period_type:
        raise ValueError(
            f"Tên kỳ {period_key} không khớp period_type={expected_period_type}"
        )
    return int(match.group("year")), quarter


def _period_mode(report_type: str, period_type: str) -> str:
    if report_type == "balance_sheet":
        return "point_in_time"
    if report_type in {"income_statement", "cash_flow"}:
        return "standalone" if period_type == "quarter" else "cumulative"
    return "unknown"


def _unit_for_vci(report_type: str) -> tuple[str, str, str, float | None]:
    if report_type in {"balance_sheet", "income_statement", "cash_flow"}:
        return "money", "VND", "VND", 1.0
    if report_type == "ratio":
        return "ratio", "not_applicable", "not_applicable", None
    return "unknown", "unknown", "unknown", None


def _quality_flags(*, company_type: str, source_unit: str, report_type: str) -> list[str]:
    flags = ["unknown_consolidation", "missing_publication_date"]
    if company_type == "unknown":
        flags.append("unknown_company_type")
    if source_unit == "unknown":
        flags.append("unknown_unit")
    if report_type == "unknown":
        flags.append("unclassified_report_type")
    return flags


def _record(
    *,
    run_id: str,
    source: str,
    provider: str,
    symbol: str,
    company_type: str,
    report_type: str,
    period_type: str,
    fiscal_year: int,
    fiscal_quarter: int | None,
    period_key: str,
    source_period_column_number: int,
    source_item_id: str,
    source_item_name: str | None,
    source_item_name_en: str | None,
    source_row_number: int,
    value: Any,
    value_type: str,
    currency: str,
    source_unit: str,
    multiplier: float | None,
    period_value_mode: str,
    collected_at: str,
    raw_file: str,
) -> dict[str, Any]:
    numeric, text, status = _value_parts(value, value_type)
    value_vnd = numeric * multiplier if numeric is not None and multiplier is not None else None
    item_key = (
        f"{provider}|{company_type}|{report_type}|{source_item_id}|"
        f"{source_row_number}|period_column={source_period_column_number}"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "source": source,
        "provider": provider,
        "symbol": symbol,
        "company_type": company_type,
        "report_type": report_type,
        "cash_flow_method": "unknown" if report_type == "cash_flow" else "not_applicable",
        "period_type": period_type,
        "fiscal_year": fiscal_year,
        "fiscal_quarter": fiscal_quarter,
        "period_key": period_key,
        "source_period_column_number": source_period_column_number,
        "period_value_mode": period_value_mode,
        "consolidation_status": "unknown",
        "publication_date": None,
        "availability_date": None,
        "source_item_id": source_item_id,
        "source_item_name": source_item_name,
        "source_item_name_en": source_item_name_en,
        "source_row_number": source_row_number,
        "source_item_key": item_key,
        "canonical_item_id": None,
        "mapping_version": None,
        "mapping_status": "unmapped",
        "value_raw": _raw_string(value),
        "value_numeric": numeric,
        "value_text": text,
        "value_type": value_type,
        "currency": currency,
        "source_unit": source_unit,
        "unit_multiplier_to_vnd": multiplier,
        "value_vnd": value_vnd,
        "record_status": status,
        "quality_flags": _quality_flags(
            company_type=company_type, source_unit=source_unit, report_type=report_type
        ),
        "collected_at": collected_at,
        "raw_file": raw_file,
    }


class BCTCNormalizer:
    """Biến đổi thuần: raw vào, DataFrame mới ra; không sửa object đầu vào."""

    def __init__(
        self,
        *,
        fireant_item_rules: Mapping[str, FireAntItemRule] = CONFIRMED_FIREANT_ITEM_RULES,
    ) -> None:
        self._fireant_item_rules = dict(fireant_item_rules)

    def normalize_vci(
        self,
        frame: pd.DataFrame,
        *,
        run_id: str,
        symbol: str,
        company_type: str,
        report_type: str,
        period_type: str,
        collected_at: str,
        raw_file: str,
    ) -> pd.DataFrame:
        if report_type not in {"balance_sheet", "income_statement", "cash_flow", "ratio"}:
            raise ValueError(f"report_type VCI không hợp lệ: {report_type}")
        if period_type not in {"quarter", "year"}:
            raise ValueError(f"period_type không hợp lệ: {period_type}")
        required = {"item_id"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"VCI thiếu cột bắt buộc: {missing}")
        for metadata_column in ("item_id", "item", "item_en"):
            if list(frame.columns).count(metadata_column) > 1:
                raise ValueError(f"VCI có cột thông tin bị trùng: {metadata_column}")

        normalized_symbol = _normalize_symbol(symbol)
        normalized_company = _company_type(company_type)
        period_columns: list[tuple[int, str, int, int | None, int]] = []
        ignored_opposite_period_columns: list[str] = []
        occurrences: dict[str, int] = {}
        for column_number, column in enumerate(frame.columns):
            match = PERIOD_COLUMN_PATTERN.fullmatch(str(column))
            if not match:
                continue
            column_is_quarter = match.group(2) is not None
            if (period_type == "quarter") != column_is_quarter:
                ignored_opposite_period_columns.append(str(column))
                continue
            year, quarter = _period_parts(str(column), period_type)
            occurrences[str(column)] = occurrences.get(str(column), 0) + 1
            period_columns.append(
                (column_number, str(column), year, quarter, occurrences[str(column)])
            )
        if not period_columns and not frame.empty:
            raise ValueError("VCI không có cột kỳ hợp lệ")

        value_type, currency, source_unit, multiplier = _unit_for_vci(report_type)
        item_id_column = list(frame.columns).index("item_id")
        item_column = list(frame.columns).index("item") if "item" in frame.columns else None
        item_en_column = (
            list(frame.columns).index("item_en") if "item_en" in frame.columns else None
        )
        records: list[dict[str, Any]] = []
        vci_control_item_ids = {"year", "quarter", "ratioTTMId", "ratioType"}
        for row_number in range(len(frame)):
            item_id = frame.iloc[row_number, item_id_column]
            if pd.isna(item_id) or not str(item_id).strip():
                raise ValueError(f"VCI thiếu item_id ở dòng {row_number + 1}")
            if report_type == "ratio" and str(item_id) in vci_control_item_ids:
                continue
            item_name = frame.iloc[row_number, item_column] if item_column is not None else None
            item_name_en = (
                frame.iloc[row_number, item_en_column] if item_en_column is not None else None
            )
            for column_number, period_key, year, quarter, occurrence in period_columns:
                record = _record(
                        run_id=run_id,
                        source="vnstock",
                        provider="vci",
                        symbol=normalized_symbol,
                        company_type=normalized_company,
                        report_type=report_type,
                        period_type=period_type,
                        fiscal_year=year,
                        fiscal_quarter=quarter,
                        period_key=period_key,
                        source_period_column_number=occurrence,
                        source_item_id=str(item_id),
                        source_item_name=None if pd.isna(item_name) else str(item_name),
                        source_item_name_en=None if pd.isna(item_name_en) else str(item_name_en),
                        source_row_number=row_number + 1,
                        value=frame.iloc[row_number, column_number],
                        value_type=value_type,
                        currency=currency,
                        source_unit=source_unit,
                        multiplier=multiplier,
                        period_value_mode=_period_mode(report_type, period_type),
                        collected_at=collected_at,
                        raw_file=raw_file,
                    )
                if ignored_opposite_period_columns:
                    record["quality_flags"].append("source_mixed_period_columns")
                records.append(record)
        return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)

    def normalize_fireant(
        self,
        payload: Sequence[Mapping[str, Any]],
        *,
        run_id: str,
        symbol: str,
        period_type: str,
        collected_at: str,
        raw_file: str,
    ) -> pd.DataFrame:
        if period_type not in {"quarter", "year"}:
            raise ValueError(f"period_type không hợp lệ: {period_type}")
        normalized_symbol = _normalize_symbol(symbol)
        records: list[dict[str, Any]] = []

        for envelope in payload:
            if not isinstance(envelope, Mapping):
                raise ValueError("FireAnt có kỳ không phải object")
            year = envelope.get("year")
            quarter = envelope.get("quarter")
            try:
                fiscal_year = int(year)
                fiscal_quarter = int(quarter) if period_type == "quarter" else None
            except (TypeError, ValueError) as error:
                raise ValueError("FireAnt có năm/quý không hợp lệ") from error
            if period_type == "quarter" and fiscal_quarter not in {1, 2, 3, 4}:
                raise ValueError(f"FireAnt có quý không hợp lệ: {quarter}")
            if period_type == "year" and quarter not in {0, "0", None}:
                raise ValueError(f"FireAnt trộn quý vào data năm: {quarter}")
            period_key = (
                f"{fiscal_year}-Q{fiscal_quarter}"
                if period_type == "quarter"
                else str(fiscal_year)
            )
            values = envelope.get("financialValues")
            if not isinstance(values, Mapping):
                raise ValueError(f"FireAnt thiếu financialValues tại kỳ {period_key}")
            company_type = _company_type(
                envelope.get("companyType") or values.get("CompanyType")
            )

            financial_items = [
                (key, value) for key, value in values.items() if key not in CONTROL_FIREANT_KEYS
            ]
            for row_number, (item_id, value) in enumerate(financial_items, start=1):
                rule = self._fireant_item_rules.get(str(item_id))
                report_type = rule.report_type if rule else "unknown"
                value_type = rule.value_type if rule else "unknown"
                currency = rule.currency if rule else "unknown"
                source_unit = rule.source_unit if rule else "unknown"
                multiplier = rule.unit_multiplier_to_vnd if rule else None
                period_mode = (
                    rule.period_value_mode_quarter
                    if rule and period_type == "quarter"
                    else rule.period_value_mode_year
                    if rule
                    else "unknown"
                )
                records.append(
                    _record(
                        run_id=run_id,
                        source="fireant",
                        provider="fireant_api",
                        symbol=normalized_symbol,
                        company_type=company_type,
                        report_type=report_type,
                        period_type=period_type,
                        fiscal_year=fiscal_year,
                        fiscal_quarter=fiscal_quarter,
                        period_key=period_key,
                        source_period_column_number=1,
                        source_item_id=str(item_id),
                        source_item_name=str(item_id),
                        source_item_name_en=None,
                        source_row_number=row_number,
                        value=value,
                        value_type=value_type,
                        currency=currency,
                        source_unit=source_unit,
                        multiplier=multiplier,
                        period_value_mode=period_mode,
                        collected_at=collected_at,
                        raw_file=raw_file,
                    )
                )
        return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)
