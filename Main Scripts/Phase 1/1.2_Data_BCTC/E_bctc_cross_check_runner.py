"""
Module:  E_bctc_cross_check_runner
Logic:   Execute offline cross-check between FireAnt and VCI raw data
Detail:  Đọc file raw trên đĩa, chuẩn hóa với Confirmed Mapping và đối chiếu chéo; không gọi API mạng.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
if str(BCTC_DIR) not in sys.path:
    sys.path.insert(0, str(BCTC_DIR))

from E_bctc_cross_checker import BCTCCrossChecker  # noqa: E402
from E_bctc_mapping import get_company_type_for_symbol  # noqa: E402
from E_bctc_normalizer import BCTCNormalizer  # noqa: E402
from E_bctc_schema import RECORD_COLUMNS, SCHEMA_VERSION  # noqa: E402



DEFAULT_RUN_ID = "run_260816_async_pilot"
DEFAULT_SYMBOLS = [
    "VNM", "FPT", "VCB", "ACB", "SSI", "VND", "BVH", "GAS", "FLC", "ANI", "UTT", "VPC", "A32"
]




def run_offline_cross_check(
    *,
    run_id: str,
    symbols: list[str],
    base_dir: Path = ROOT / "Phase_1_Data" / "E_BCTC",
) -> dict[str, Any]:
    fa_raw_dir = base_dir / "From_FireAnt" / "Raw" / run_id
    vci_raw_dir = base_dir / "From_vnstock" / "Raw" / run_id
    output_state_dir = base_dir / "state" / "cross_check_runs"
    output_state_dir.mkdir(parents=True, exist_ok=True)

    normalizer = BCTCNormalizer()
    checker = BCTCCrossChecker()

    overall_summary = {
        "run_id": run_id,
        "symbols_processed": [],
        "total_cross_check_rows": 0,
        "total_matched": 0,
        "total_different": 0,
        "total_only_fireant": 0,
        "total_only_vnstock": 0,
        "total_not_comparable": 0,
        "symbols_detail": {},
        "discrepancies": [],
    }

    for symbol in symbols:
        sym = symbol.strip().upper()
        comp_type = get_company_type_for_symbol(sym)
        sym_fa_frames = []
        sym_vci_frames = []

        # 1. Read & Normalize FireAnt
        sym_fa_dir = fa_raw_dir / sym
        if sym_fa_dir.is_dir():
            for p_type in ["quarter", "year"]:
                fa_file = sym_fa_dir / f"financial_data_{p_type}_fireant_api.json"
                if fa_file.exists():
                    try:
                        with open(fa_file, "r", encoding="utf-8") as f:
                            payload = json.load(f)
                        df_fa = normalizer.normalize_fireant(
                            payload,
                            run_id=run_id,
                            symbol=sym,
                            period_type=p_type,
                            collected_at="2026-08-16T15:30:00+07:00",
                            raw_file=str(fa_file),
                        )
                        sym_fa_frames.append(df_fa)
                    except Exception as e:
                        print(f"[{sym}] Error normalizing FireAnt {p_type}: {e}")

        # 2. Read & Normalize VCI
        sym_vci_dir = vci_raw_dir / sym
        if sym_vci_dir.is_dir():
            for rep_type in ["balance_sheet", "income_statement", "cash_flow", "ratio"]:
                for p_type in ["quarter", "year"]:
                    vci_file = sym_vci_dir / f"{rep_type}_{p_type}_vci.parquet"
                    if vci_file.exists():
                        try:
                            df_raw_vci = pd.read_parquet(vci_file)
                            df_vci = normalizer.normalize_vci(
                                df_raw_vci,
                                run_id=run_id,
                                symbol=sym,
                                company_type=comp_type,
                                report_type=rep_type,
                                period_type=p_type,
                                collected_at="2026-08-16T15:30:00+07:00",
                                raw_file=str(vci_file),
                            )
                            sym_vci_frames.append(df_vci)
                        except Exception as e:
                            print(f"[{sym}] Error normalizing VCI {rep_type}_{p_type}: {e}")

        if not sym_fa_frames or not sym_vci_frames:
            print(f"[{sym}] Skip: Missing raw frames (FireAnt={len(sym_fa_frames)}, VCI={len(sym_vci_frames)})")
            continue

        full_fa = pd.concat(sym_fa_frames, ignore_index=True)
        full_vci = pd.concat(sym_vci_frames, ignore_index=True)

        # 3. Cross-check
        comparison_df = checker.compare(full_fa, full_vci)
        sym_summary = checker.summarize(comparison_df)

        overall_summary["symbols_processed"].append(sym)
        overall_summary["total_cross_check_rows"] += sym_summary.total
        overall_summary["total_matched"] += sym_summary.matched
        overall_summary["total_different"] += sym_summary.different
        overall_summary["total_only_fireant"] += sym_summary.only_fireant
        overall_summary["total_only_vnstock"] += sym_summary.only_vnstock
        overall_summary["total_not_comparable"] += sym_summary.not_comparable

        overall_summary["symbols_detail"][sym] = {
            "company_type": comp_type,
            "total_rows": sym_summary.total,
            "matched": sym_summary.matched,
            "different": sym_summary.different,
            "only_fireant": sym_summary.only_fireant,
            "only_vnstock": sym_summary.only_vnstock,
            "not_comparable": sym_summary.not_comparable,
        }

        # Lưu các trường hợp different (nếu có)
        diff_rows = comparison_df[comparison_df["comparison_status"] == "different"]
        for _, row in diff_rows.iterrows():
            overall_summary["discrepancies"].append({
                "symbol": sym,
                "canonical_item_id": row.get("canonical_item_id"),
                "period_key": row.get("period_key"),
                "fireant_value_vnd": row.get("fireant_value_vnd"),
                "vnstock_value_vnd": row.get("vnstock_value_vnd"),
                "absolute_difference": row.get("absolute_difference"),
                "difference_percent": row.get("difference_percent"),
            })

    # 4. Ghi file tổng kết
    output_file = output_state_dir / f"{run_id}_cross_check.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(overall_summary, f, ensure_ascii=False, indent=2)

    return overall_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline cross-check on scraped BCTC data")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="Run ID to cross check")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS, help="Symbols list")
    args = parser.parse_args()

    print(f"=== Starting Offline Cross-Check for Run: {args.run_id} ===")
    summary = run_offline_cross_check(run_id=args.run_id, symbols=args.symbols)
    
    print("\n=== Cross-Check Summary ===")
    print(f"Symbols Processed: {len(summary['symbols_processed'])}")
    print(f"Total Rows:        {summary['total_cross_check_rows']:,}")
    print(f"Matched Rows:      {summary['total_matched']:,}")
    print(f"Different Rows:    {summary['total_different']:,}")
    print(f"Only FireAnt:      {summary['total_only_fireant']:,}")
    print(f"Only VCI:          {summary['total_only_vnstock']:,}")
    print(f"Not Comparable:    {summary['total_not_comparable']:,}")
    print(f"\nResult saved to:   Phase_1_Data/E_BCTC/state/cross_check_runs/{args.run_id}_cross_check.json")


if __name__ == "__main__":
    main()
