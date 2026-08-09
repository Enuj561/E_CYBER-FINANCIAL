"""
Module:  E_bctc_schema
Logic:   Define the active BCTC schema constants
Detail:  Là nguồn sự thật dùng chung cho version và danh sách cột BCTC. Không chứa
         logic gọi nguồn, biến đổi, kiểm tra hoặc ghi file.
"""

SCHEMA_VERSION = "bctc_v1.1.0"

RECORD_COLUMNS = [
    "schema_version",
    "run_id",
    "source",
    "provider",
    "symbol",
    "company_type",
    "report_type",
    "cash_flow_method",
    "period_type",
    "fiscal_year",
    "fiscal_quarter",
    "period_key",
    "source_period_column_number",
    "period_value_mode",
    "consolidation_status",
    "publication_date",
    "availability_date",
    "source_item_id",
    "source_item_name",
    "source_item_name_en",
    "source_row_number",
    "source_item_key",
    "canonical_item_id",
    "mapping_version",
    "mapping_status",
    "value_raw",
    "value_numeric",
    "value_text",
    "value_type",
    "currency",
    "source_unit",
    "unit_multiplier_to_vnd",
    "value_vnd",
    "record_status",
    "quality_flags",
    "collected_at",
    "raw_file",
]

VALID_SOURCES = frozenset({"fireant", "vnstock"})
VALID_PROVIDERS = frozenset({"fireant_api", "vci", "kbs"})
SOURCE_PROVIDER_PAIRS = frozenset(
    {("fireant", "fireant_api"), ("vnstock", "vci"), ("vnstock", "kbs")}
)
VALID_PERIOD_TYPES = frozenset({"quarter", "year"})
VALID_REPORT_TYPES = frozenset(
    {"balance_sheet", "income_statement", "cash_flow", "ratio", "unknown"}
)
VALID_SOURCE_UNITS = frozenset(
    {"VND", "thousand_VND", "million_VND", "unknown", "not_applicable"}
)
