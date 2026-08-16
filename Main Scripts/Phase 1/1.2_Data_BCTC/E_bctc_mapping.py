"""
Module:  E_bctc_mapping
Logic:   Define confirmed mapping dictionary between FireAnt and VCI items
Detail:  Chứa định nghĩa canonical items và tra cứu rule ánh xạ; không gọi API, không đọc/ghi file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


MAPPING_VERSION = "v1.0.0"


@dataclass(frozen=True)
class CanonicalItem:
    canonical_item_id: str
    vietnamese_name: str
    english_name: str
    report_type: str
    company_type: str
    value_type: str = "money"
    currency: str = "VND"
    source_unit: str = "VND"
    unit_multiplier_to_vnd: float | None = 1.0
    period_value_mode_quarter: str = "point_in_time"
    period_value_mode_year: str = "point_in_time"


@dataclass(frozen=True)
class MappingRule:
    source: str  # "fireant" | "vnstock"
    provider: str  # "fireant_api" | "vci"
    source_item_id: str
    company_type: str  # "general" | "bank" | "securities" | "insurance" | "all"
    report_type: str  # "balance_sheet" | "income_statement" | "cash_flow" | "ratio" | "financial_data"
    canonical_item_id: str
    mapping_status: str = "confirmed"
    mapping_version: str = MAPPING_VERSION
    sign_multiplier: float = 1.0


# Danh mục Canonical Items chuẩn mực
CANONICAL_ITEMS: Sequence[CanonicalItem] = [
    # 1. Doanh nghiệp thường (General - TT 200)
    CanonicalItem("total_assets", "Tổng tài sản", "Total assets", "balance_sheet", "general", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("current_assets", "Tài sản ngắn hạn", "Current assets", "balance_sheet", "general", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("cash_and_equivalents", "Tiền và tương đương tiền", "Cash and cash equivalents", "balance_sheet", "general", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("total_liabilities", "Nợ phải trả", "Total liabilities", "balance_sheet", "general", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("owners_equity", "Vốn chủ sở hữu", "Owners equity", "balance_sheet", "general", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("net_revenue", "Doanh thu thuần", "Net revenue", "income_statement", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("cost_of_goods_sold", "Giá vốn hàng bán", "Cost of goods sold", "income_statement", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("gross_profit", "Lợi nhuận gộp", "Gross profit", "income_statement", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("operating_profit", "Lợi nhuận thuần từ HĐKD", "Operating profit", "income_statement", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("profit_before_tax", "Lợi nhuận trước thuế", "Profit before tax", "income_statement", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("profit_after_tax", "Lợi nhuận sau thuế TNDN", "Profit after tax", "income_statement", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("profit_after_tax_parent", "LNST của CĐ công ty mẹ", "Profit after tax parent", "income_statement", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("cfo_net", "Lưu chuyển tiền thuần từ HĐKD", "Net cash from operating activities", "cash_flow", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("cfi_net", "Lưu chuyển tiền thuần từ HĐĐT", "Net cash from investing activities", "cash_flow", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("cff_net", "Lưu chuyển tiền thuần từ HĐTC", "Net cash from financing activities", "cash_flow", "general", "money", "VND", "VND", 1.0, "standalone", "cumulative"),

    # 2. Ngân hàng (Bank - TT 49)
    CanonicalItem("bank_total_assets", "Tổng tài sản", "Total assets", "balance_sheet", "bank", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("customer_loans", "Cho vay khách hàng", "Customer loans", "balance_sheet", "bank", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("customer_deposits", "Tiền gửi của khách hàng", "Customer deposits", "balance_sheet", "bank", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("bank_owners_equity", "Vốn chủ sở hữu", "Owners equity", "balance_sheet", "bank", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("net_interest_income", "Thu nhập lãi thuần", "Net interest income", "income_statement", "bank", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("net_fee_income", "Lãi thuần từ hoạt động dịch vụ", "Net fee income", "income_statement", "bank", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("bank_profit_before_tax", "Lợi nhuận trước thuế", "Profit before tax", "income_statement", "bank", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("bank_profit_after_tax", "Lợi nhuận sau thuế TNDN", "Profit after tax", "income_statement", "bank", "money", "VND", "VND", 1.0, "standalone", "cumulative"),

    # 3. Chứng khoán (Securities - TT 334)
    CanonicalItem("sec_total_assets", "Tổng tài sản CTCK", "Total assets", "balance_sheet", "securities", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("sec_fvtpl_assets", "Tài sản tài chính FVTPL", "FVTPL assets", "balance_sheet", "securities", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("sec_owners_equity", "Vốn chủ sở hữu", "Owners equity", "balance_sheet", "securities", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("sec_operating_revenue", "Doanh thu hoạt động", "Operating revenue", "income_statement", "securities", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("sec_profit_before_tax", "Lợi nhuận trước thuế", "Profit before tax", "income_statement", "securities", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("sec_profit_after_tax", "Lợi nhuận sau thuế TNDN", "Profit after tax", "income_statement", "securities", "money", "VND", "VND", 1.0, "standalone", "cumulative"),

    # 4. Bảo hiểm (Insurance)
    CanonicalItem("ins_total_assets", "Tổng tài sản", "Total assets", "balance_sheet", "insurance", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("ins_owners_equity", "Vốn chủ sở hữu", "Owners equity", "balance_sheet", "insurance", "money", "VND", "VND", 1.0, "point_in_time", "point_in_time"),
    CanonicalItem("ins_profit_before_tax", "Lợi nhuận trước thuế", "Profit before tax", "income_statement", "insurance", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
    CanonicalItem("ins_profit_after_tax", "Lợi nhuận sau thuế TNDN", "Profit after tax", "income_statement", "insurance", "money", "VND", "VND", 1.0, "standalone", "cumulative"),
]


# Quy tắc ánh xạ chính xác giữa nguồn và canonical_item_id
MAPPING_RULES: Sequence[MappingRule] = [
    # ------------------ 1. DOANH NGHIỆP THƯỜNG (General) ------------------
    # FireAnt
    MappingRule("fireant", "fireant_api", "TotalAsset", "general", "financial_data", "total_assets"),
    MappingRule("fireant", "fireant_api", "ShortTermAsset", "general", "financial_data", "current_assets"),
    MappingRule("fireant", "fireant_api", "CashAndCashEquivalent", "general", "financial_data", "cash_and_equivalents"),
    MappingRule("fireant", "fireant_api", "TotalLiabilities", "general", "financial_data", "total_liabilities"),
    MappingRule("fireant", "fireant_api", "TotalStockHolderEquity", "general", "financial_data", "owners_equity"),
    MappingRule("fireant", "fireant_api", "NetSales", "general", "financial_data", "net_revenue"),
    MappingRule("fireant", "fireant_api", "CostOfGoodsSold", "general", "financial_data", "cost_of_goods_sold"),
    MappingRule("fireant", "fireant_api", "GrossProfit", "general", "financial_data", "gross_profit"),
    MappingRule("fireant", "fireant_api", "OperatingProfit", "general", "financial_data", "operating_profit"),
    MappingRule("fireant", "fireant_api", "TotalProfitBeforeTax", "general", "financial_data", "profit_before_tax"),
    MappingRule("fireant", "fireant_api", "ProfitAfterTax", "general", "financial_data", "profit_after_tax"),
    MappingRule("fireant", "fireant_api", "PostTaxProfitOfParentCompany", "general", "financial_data", "profit_after_tax_parent"),
    MappingRule("fireant", "fireant_api", "CashflowFromOperatingActivity", "general", "financial_data", "cfo_net"),
    MappingRule("fireant", "fireant_api", "CashflowFromInvestingActivity", "general", "financial_data", "cfi_net"),
    MappingRule("fireant", "fireant_api", "CashflowFromFinancingActivity", "general", "financial_data", "cff_net"),

    # VCI / vnstock
    MappingRule("vnstock", "vci", "asset_total", "general", "balance_sheet", "total_assets"),
    MappingRule("vnstock", "vci", "asset_current", "general", "balance_sheet", "current_assets"),
    MappingRule("vnstock", "vci", "cash_and_cash_equivalents", "general", "balance_sheet", "cash_and_equivalents"),
    MappingRule("vnstock", "vci", "liabilities_total", "general", "balance_sheet", "total_liabilities"),
    MappingRule("vnstock", "vci", "equity_total", "general", "balance_sheet", "owners_equity"),
    MappingRule("vnstock", "vci", "net_sales", "general", "income_statement", "net_revenue"),
    MappingRule("vnstock", "vci", "cost_of_sales", "general", "income_statement", "cost_of_goods_sold"),
    MappingRule("vnstock", "vci", "gross_profit", "general", "income_statement", "gross_profit"),
    MappingRule("vnstock", "vci", "operating_profit_loss", "general", "income_statement", "operating_profit"),
    MappingRule("vnstock", "vci", "profit_before_tax", "general", "income_statement", "profit_before_tax"),
    MappingRule("vnstock", "vci", "profit_after_tax", "general", "income_statement", "profit_after_tax"),
    MappingRule("vnstock", "vci", "attributable_to_parent_company", "general", "income_statement", "profit_after_tax_parent"),
    MappingRule("vnstock", "vci", "net_cash_from_operating_activities", "general", "cash_flow", "cfo_net"),
    MappingRule("vnstock", "vci", "net_cash_from_investing_activities", "general", "cash_flow", "cfi_net"),
    MappingRule("vnstock", "vci", "net_cash_from_financing_activities", "general", "cash_flow", "cff_net"),

    # ------------------ 2. NGÂN HÀNG (Bank) ------------------
    # FireAnt
    MappingRule("fireant", "fireant_api", "TotalAsset", "bank", "financial_data", "bank_total_assets"),
    MappingRule("fireant", "fireant_api", "CustomerLoans", "bank", "financial_data", "customer_loans"),
    MappingRule("fireant", "fireant_api", "CustomerDeposits", "bank", "financial_data", "customer_deposits"),
    MappingRule("fireant", "fireant_api", "TotalStockHolderEquity", "bank", "financial_data", "bank_owners_equity"),
    MappingRule("fireant", "fireant_api", "NetInterestIncome", "bank", "financial_data", "net_interest_income"),
    MappingRule("fireant", "fireant_api", "NetFeeIncome", "bank", "financial_data", "net_fee_income"),
    MappingRule("fireant", "fireant_api", "TotalProfitBeforeTax", "bank", "financial_data", "bank_profit_before_tax"),
    MappingRule("fireant", "fireant_api", "ProfitAfterTax", "bank", "financial_data", "bank_profit_after_tax"),

    # VCI / vnstock
    MappingRule("vnstock", "vci", "total_assets", "bank", "balance_sheet", "bank_total_assets"),
    MappingRule("vnstock", "vci", "loans_and_advances_to_customers", "bank", "balance_sheet", "customer_loans"),
    MappingRule("vnstock", "vci", "deposits_from_customers", "bank", "balance_sheet", "customer_deposits"),
    MappingRule("vnstock", "vci", "owners_equity", "bank", "balance_sheet", "bank_owners_equity"),
    MappingRule("vnstock", "vci", "net_interest_income", "bank", "income_statement", "net_interest_income"),
    MappingRule("vnstock", "vci", "net_fee_and_commission_income", "bank", "income_statement", "net_fee_income"),
    MappingRule("vnstock", "vci", "net_accounting_profit_loss_before_tax", "bank", "income_statement", "bank_profit_before_tax"),
    MappingRule("vnstock", "vci", "net_profit_loss_after_tax", "bank", "income_statement", "bank_profit_after_tax"),

    # ------------------ 3. CHỨNG KHOÁN (Securities) ------------------
    # FireAnt
    MappingRule("fireant", "fireant_api", "TotalAsset", "securities", "financial_data", "sec_total_assets"),
    MappingRule("fireant", "fireant_api", "FinancialAssetAtFVTPL", "securities", "financial_data", "sec_fvtpl_assets"),
    MappingRule("fireant", "fireant_api", "TotalStockHolderEquity", "securities", "financial_data", "sec_owners_equity"),
    MappingRule("fireant", "fireant_api", "OperatingRevenue", "securities", "financial_data", "sec_operating_revenue"),
    MappingRule("fireant", "fireant_api", "TotalProfitBeforeTax", "securities", "financial_data", "sec_profit_before_tax"),
    MappingRule("fireant", "fireant_api", "ProfitAfterTax", "securities", "financial_data", "sec_profit_after_tax"),

    # VCI / vnstock
    MappingRule("vnstock", "vci", "asset_total", "securities", "balance_sheet", "sec_total_assets"),
    MappingRule("vnstock", "vci", "financial_assets_at_fair_value_through_profit_or_loss_fvtpl", "securities", "balance_sheet", "sec_fvtpl_assets"),
    MappingRule("vnstock", "vci", "equity_total", "securities", "balance_sheet", "sec_owners_equity"),
    MappingRule("vnstock", "vci", "owners_equity", "securities", "balance_sheet", "sec_owners_equity"),
    MappingRule("vnstock", "vci", "operating_sales", "securities", "income_statement", "sec_operating_revenue"),
    MappingRule("vnstock", "vci", "profit_before_tax", "securities", "income_statement", "sec_profit_before_tax"),
    MappingRule("vnstock", "vci", "profit_after_tax", "securities", "income_statement", "sec_profit_after_tax"),

    # ------------------ 4. BẢO HIỂM (Insurance) ------------------
    # FireAnt
    MappingRule("fireant", "fireant_api", "TotalAsset", "insurance", "financial_data", "ins_total_assets"),
    MappingRule("fireant", "fireant_api", "TotalStockHolderEquity", "insurance", "financial_data", "ins_owners_equity"),
    MappingRule("fireant", "fireant_api", "TotalProfitBeforeTax", "insurance", "financial_data", "ins_profit_before_tax"),
    MappingRule("fireant", "fireant_api", "ProfitAfterTax", "insurance", "financial_data", "ins_profit_after_tax"),

    # VCI / vnstock
    MappingRule("vnstock", "vci", "asset_total", "insurance", "balance_sheet", "ins_total_assets"),
    MappingRule("vnstock", "vci", "total_assets", "insurance", "balance_sheet", "ins_total_assets"),
    MappingRule("vnstock", "vci", "equity_total", "insurance", "balance_sheet", "ins_owners_equity"),
    MappingRule("vnstock", "vci", "owners_equity", "insurance", "balance_sheet", "ins_owners_equity"),
    MappingRule("vnstock", "vci", "profit_before_tax", "insurance", "income_statement", "ins_profit_before_tax"),
    MappingRule("vnstock", "vci", "profit_after_tax", "insurance", "income_statement", "ins_profit_after_tax"),
]


# Tra cứu nhanh theo key: (source, provider, source_item_id, company_type, report_type)
_RULES_LOOKUP: dict[tuple[str, str, str, str, str], MappingRule] = {
    (r.source, r.provider, r.source_item_id, r.company_type, r.report_type): r
    for r in MAPPING_RULES
}

# Tra cứu canonical item
_CANONICAL_LOOKUP: dict[str, CanonicalItem] = {
    item.canonical_item_id: item for item in CANONICAL_ITEMS
}


def get_mapping_rule(
    *,
    source: str,
    provider: str,
    source_item_id: str,
    company_type: str,
    report_type: str,
) -> MappingRule | None:
    """Tra cứu quy tắc mapping confirmed. Nếu không có trả về None (unmapped)."""
    # 1. Tìm chính xác (exact match)
    key = (source, provider, source_item_id, company_type, report_type)
    if key in _RULES_LOOKUP:
        return _RULES_LOOKUP[key]
    
    # 2. Tìm fallback company_type="all"
    key_all = (source, provider, source_item_id, "all", report_type)
    if key_all in _RULES_LOOKUP:
        return _RULES_LOOKUP[key_all]

    return None


def get_canonical_item(canonical_item_id: str) -> CanonicalItem | None:
    """Tra cứu thông tin metadata của CanonicalItem."""
    return _CANONICAL_LOOKUP.get(canonical_item_id)


SECTOR_COMPANY_TYPES: dict[str, str] = {
    # Banks
    **{sym: "bank" for sym in [
        "VCB", "ACB", "MBB", "TCB", "BID", "CTG", "STB", "VPB", "HDB", "TPB",
        "VIB", "LPB", "MSB", "OCB", "SSB", "EIB", "SHB", "BAB", "BVB", "NAB",
        "NVB", "PGB", "SGB", "VAB", "VBB", "KLB"
    ]},
    # Securities
    **{sym: "securities" for sym in [
        "SSI", "VND", "HCM", "VIX", "MBS", "SHS", "VCI", "BSI", "CTS", "FTS",
        "AGR", "ORS", "TCI", "VDS", "BVS", "APG", "EVS", "IVS", "TVB", "TVS",
        "HBS", "WSS", "PSI", "VIG", "APS"
    ]},
    # Insurance
    **{sym: "insurance" for sym in [
        "BVH", "PVI", "BIC", "BMI", "MIG", "VNR", "PRE", "PTI", "ABI", "BLI"
    ]},
}


def get_company_type_for_symbol(symbol: str) -> str:
    """Trả về loại doanh nghiệp (bank, securities, insurance, hoặc general)."""
    return SECTOR_COMPANY_TYPES.get(symbol.strip().upper(), "general")

