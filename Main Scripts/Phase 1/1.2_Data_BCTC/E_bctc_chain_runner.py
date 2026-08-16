"""
Script chạy nối tiếp (Chain Runner) tự động kích hoạt Batch 50 đợt 3 ngay sau khi Batch 100 hoàn tất.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

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

from E_Helper.E_BlackBox import get_black_box
from E_Helper.E_config import BCTC_STATE_DIR
from E_bctc_pilot import run_pilot

LOGGER = get_black_box(__file__).bind()


def wait_for_batch100_completion() -> bool:
    """Chờ cho đến khi file pilot summary của batch 100 xuất hiện và hoàn tất 100 mã."""
    batch100_summary_path = Path(BCTC_STATE_DIR) / "pilot_runs" / "run_260816_batch100.json"
    batch100_state_path = Path(BCTC_STATE_DIR) / "runs" / "run_260816_batch100.json"
    
    print("[CHAIN RUNNER] Đang theo dõi tiến độ Batch 100...", flush=True)
    while True:
        if batch100_summary_path.exists():
            try:
                data = json.loads(batch100_summary_path.read_text(encoding="utf-8"))
                finished = data.get("symbols_finished", [])
                if len(finished) == 100:
                    print(f"\n[CHAIN RUNNER] ✅ Batch 100 đã hoàn tất xuất sắc 100/100 mã!", flush=True)
                    return True
            except Exception:
                pass

        # Kiểm tra qua file checkpoint runs
        if batch100_state_path.exists():
            try:
                state_data = json.loads(batch100_state_path.read_text(encoding="utf-8"))
                items = state_data.get("items", {})
                # Đếm số items hợp lệ
                done_items = sum(1 for it in items.values() if it.get("status") in ("complete", "partial", "no_data_confirmed", "unsupported"))
                if done_items == 1000 and batch100_summary_path.exists():
                    print(f"\n[CHAIN RUNNER] ✅ Checkpoint ghi nhận đủ 1000/1000 items!", flush=True)
                    return True
            except Exception:
                pass

        time.sleep(15)


def run_batch50_03() -> None:
    """Tự động kích hoạt cào Batch 50 đợt 3."""
    batch_file = BCTC_DIR / "batches" / "batch_50_03.json"
    if not batch_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {batch_file}")

    symbols = json.loads(batch_file.read_text(encoding="utf-8"))
    print(f"\n[CHAIN RUNNER] 🚀 BẮT ĐẦU CHẠY NỐI TIẾP BATCH 50 ĐỢT 3 ({len(symbols)} mã)...", flush=True)
    LOGGER.info("Bắt đầu chạy nối tiếp Batch 50 đợt 3 qua Chain Runner", symbol_count=len(symbols))

    summary = run_pilot(
        symbols=symbols,
        run_id="run_260816_batch50_03",
        quarter_count=64,
        year_count=20,
        mode="parallel",
        delay_seconds=1.0,
    )
    print(f"\n[CHAIN RUNNER] 🎉 HOÀN TẤT TRỌN VẸN BATCH 50 ĐỢT 3! File tổng kết: {summary.get('summary_file')}", flush=True)
    LOGGER.info("Hoàn tất trọn vẹn Batch 50 đợt 3 qua Chain Runner", summary_file=summary.get("summary_file"))


def main() -> None:
    print("[CHAIN RUNNER] Khởi động tiến trình chờ chạy nối tiếp qua đêm...", flush=True)
    wait_for_batch100_completion()
    print("[CHAIN RUNNER] Nghỉ 5 giây trước khi vào Batch 50 đợt 3...", flush=True)
    time.sleep(5)
    run_batch50_03()


if __name__ == "__main__":
    main()
