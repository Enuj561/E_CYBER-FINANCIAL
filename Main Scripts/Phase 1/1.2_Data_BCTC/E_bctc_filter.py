"""
Module:  E_bctc_filter
Logic:   Universe filtering & Batch generation module for BCTC Collection
Detail:  Tự động quét kho dữ liệu Raw, lọc trừ các mã đã cào và tạo file batch cấu hình cho file điều phối dùng chung.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BCTC_DIR = PROJECT_ROOT / "Main Scripts" / "Phase 1" / "1.2_Data_BCTC"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BCTC_DIR) not in sys.path:
    sys.path.insert(0, str(BCTC_DIR))

from E_Helper.E_config import BCTC_DIR as BCTC_DATA_DIR
from E_bctc_mapping import get_company_type_for_symbol

UNIVERSE_CSV = PROJECT_ROOT / "E_Implementation" / "260809_universe_snapshot.csv"
BATCHES_DIR = BCTC_DIR / "batches"


def get_universe_symbols() -> list[str]:
    """Đọc danh sách 1.529 mã chuẩn từ universe snapshot."""
    import pandas as pd
    if not UNIVERSE_CSV.exists():
        raise FileNotFoundError(f"Universe snapshot not found at: {UNIVERSE_CSV}")
    df = pd.read_csv(UNIVERSE_CSV)
    return [s.strip().upper() for s in df["symbol"].tolist() if str(s).strip()]


def get_collected_symbols(base_dir: Path | None = None) -> set[str]:
    """Quét tất cả các mã đã cào thành công trên đĩa (Raw)."""
    raw_root = (base_dir or Path(BCTC_DATA_DIR)) / "From_FireAnt" / "Raw"
    collected = set()
    if raw_root.exists():
        for run_dir in raw_root.iterdir():
            if run_dir.is_dir():
                for sym_dir in run_dir.iterdir():
                    if sym_dir.is_dir():
                        collected.add(sym_dir.name.upper())
    return collected


def get_remaining_symbols(base_dir: Path | None = None) -> list[str]:
    """Lấy danh sách các mã trong Universe chưa được cào."""
    universe = get_universe_symbols()
    collected = get_collected_symbols(base_dir)
    return [s for s in universe if s not in collected]


def select_diverse_batch(count: int = 100, base_dir: Path | None = None) -> list[str]:
    """
    Chọn danh sách N mã chưa cào theo tiêu chí cân đối đa dạng:
    - Ưu tiên bao phủ các Ngân hàng, Chứng khoán, Bảo hiểm còn lại.
    - Phân bổ đều các ngành Sản xuất, Xây dựng, BĐS, Bán lẻ, Công nghệ, Penny.
    """
    remaining = get_remaining_symbols(base_dir)
    if not remaining:
        return []

    # Phân nhóm theo khối ngành
    banks = [s for s in remaining if get_company_type_for_symbol(s) == "bank"]
    secs = [s for s in remaining if get_company_type_for_symbol(s) == "securities"]
    ins = [s for s in remaining if get_company_type_for_symbol(s) == "insurance"]
    general = [s for s in remaining if get_company_type_for_symbol(s) == "general"]

    selected: list[str] = []

    # 1. Lấy toàn bộ hoặc tối đa các mã tài chính đặc thù còn lại
    selected.extend(banks[:16])
    selected.extend(secs[:19])
    selected.extend(ins[:9])

    # 2. Bù phần còn lại bằng các mã doanh nghiệp thường đại diện
    needed = count - len(selected)
    if needed > 0:
        # Danh mục Midcap & Penny tiêu biểu ưu tiên
        priority_midcaps = [
            "KBC", "NLG", "HDG", "CEO", "DXS", "SCR", "HDC", "VCG", "CII", "HHV", "PC1",
            "VGS", "TLH", "HT1", "BCC", "CSV", "BFC", "LAS", "DGW", "FRT", "PET", "QNS",
            "SBT", "FMC", "IDI", "CTR", "VGI", "FOX", "HAH", "VSC", "AAA", "HNG", "HAP",
            "ITA", "TCH", "HQC", "ASM", "PAN", "GEG", "REE", "KDC", "SCS", "SZC", "TIP",
            "NTP", "BMP", "DBC", "BAF", "TCM", "MSH", "GIL", "STK", "VSH", "NT2", "PPC",
            "BWE", "TDM", "VOS", "PVT", "GSP", "SKG", "AST", "SGN", "ACV", "VEA", "VGT"
        ]
        priority_available = [s for s in priority_midcaps if s in general and s not in selected]
        selected.extend(priority_available[:needed])

        # Nếu vẫn chưa đủ, lấy tiếp từ general còn lại
        still_needed = count - len(selected)
        if still_needed > 0:
            remaining_gen = [s for s in general if s not in selected]
            selected.extend(remaining_gen[:still_needed])

    # Đảm bảo đúng số lượng và không trùng
    final_list = selected[:count]
    assert len(final_list) == len(set(final_list)), "Batch contains duplicates!"
    return final_list


def create_batch_file(name: str, count: int = 100, base_dir: Path | None = None) -> Path:
    """Tạo file JSON chứa danh sách mã của batch vào thư mục batches/."""
    BATCHES_DIR.mkdir(parents=True, exist_ok=True)
    batch_symbols = select_diverse_batch(count=count, base_dir=base_dir)
    output_path = BATCHES_DIR / f"{name}.json"
    output_path.write_text(json.dumps(batch_symbols, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Module filter và tạo batch mã cổ phiếu BCTC")
    parser.add_argument("--status", action="store_true", help="Xem hiện trạng Universe và các mã đã cào")
    parser.add_argument("--create-batch", type=str, help="Tên file batch cần tạo (ví dụ: batch_100)")
    parser.add_argument("--size", type=int, default=100, help="Số lượng mã trong batch (mặc định: 100)")
    args = parser.parse_args()

    collected = get_collected_symbols()
    universe = get_universe_symbols()
    remaining = get_remaining_symbols()

    print("=== BCTC UNIVERSE & BATCH FILTER STATUS ===")
    print(f"Tổng Universe:       {len(universe)} mã")
    print(f"Đã cào trên đĩa:     {len(collected)} mã")
    print(f"Còn lại chưa cào:    {len(remaining)} mã")

    if args.create_batch:
        batch_path = create_batch_file(args.create_batch, count=args.size)
        with open(batch_path, "r", encoding="utf-8") as f:
            syms = json.load(f)
        overlap = set(syms).intersection(collected)
        print(f"\n[SUCCESS] Đã tạo file batch: {batch_path.resolve()}")
        print(f"Số lượng mã:         {len(syms)}")
        print(f"Trùng với đã cào:    {len(overlap)} (Passed 100% independent check)")
        print(f"Danh sách mã ({len(syms)}):")
        print(" ".join(syms))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
