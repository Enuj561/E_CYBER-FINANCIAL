"""
Module:  E_step_00_inventory
Logic:   Build the frozen Phase 1/BCTC baseline inventory
Detail:  Đọc artifact local và snapshot listing đã lưu để tạo universe, inventory BCTC
         legacy và metadata môi trường; không gọi API và không sửa data nguồn.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

import pandas as pd
import pyarrow.parquet as pq


SNAPSHOT_DATE = "2026-08-09"
PROJECT_DIR = Path(__file__).resolve().parent.parent
IMPLEMENTATION_DIR = PROJECT_DIR / "E_Implementation"
PHASE_1_DIR = PROJECT_DIR / "Phase_1_Data"
FIREANT_DIR = PHASE_1_DIR / "E_OHLCV" / "From_FireAnt"
VNSTOCK_DIR = PHASE_1_DIR / "E_OHLCV" / "From_vnstock"
BCTC_DIR = PHASE_1_DIR / "E_BCTC"
BCTC_STATE_DIR = BCTC_DIR / "state"
LISTING_SNAPSHOT = IMPLEMENTATION_DIR / "260809_vnstock_listing_snapshot.csv"
UNIVERSE_CSV = IMPLEMENTATION_DIR / "260809_universe_snapshot.csv"
UNIVERSE_PARQUET = BCTC_STATE_DIR / "universe_2026-08-09.parquet"
INVENTORY_JSON = IMPLEMENTATION_DIR / "260809_Step_00_Inventory.json"
STATE_INVENTORY_JSON = BCTC_STATE_DIR / "legacy_inventory_2026-08-09.json"
LEGACY_CHECKPOINT = PROJECT_DIR / "Log_Debug" / "Phase 1" / "checkpoint_bctc.json"
PROJECT_CONFIG = PROJECT_DIR / "E_Helper" / "E_config.py"
COLLECTOR_CONFIG = (
    PROJECT_DIR / "Main Scripts" / "Phase 1" / "1.1_Data_Collector" / "config.json"
)
ENV_FILE = PROJECT_DIR / "System" / ".env"

PACKAGE_NAMES = (
    "beautifulsoup4",
    "feedparser",
    "google-genai",
    "numpy",
    "pandas",
    "pyarrow",
    "PyQt6",
    "python-dotenv",
    "requests",
    "scikit-learn",
    "vnstock",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def symbols_from_files(folder: Path, suffix: str) -> set[str]:
    return {
        file.name.removesuffix(suffix).strip().upper()
        for file in folder.glob(f"*{suffix}")
    }


def parquet_inventory(path: Path) -> dict:
    parquet = pq.ParquetFile(path)
    return {
        "path": path.relative_to(PROJECT_DIR).as_posix(),
        "classification": "legacy_sample_not_production",
        "bytes": path.stat().st_size,
        "rows": parquet.metadata.num_rows,
        "columns": parquet.schema.names,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(),
        "sha256": sha256_file(path),
    }


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in PACKAGE_NAMES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def config_artifact(path: Path) -> dict:
    return {
        "path": path.relative_to(PROJECT_DIR).as_posix(),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
    }


def build_universe() -> pd.DataFrame:
    if not LISTING_SNAPSHOT.exists():
        raise FileNotFoundError(f"Thiếu listing snapshot: {LISTING_SNAPSHOT}")

    fireant_symbols = symbols_from_files(FIREANT_DIR, "_historical_fireant.parquet")
    vnstock_symbols = symbols_from_files(VNSTOCK_DIR, "_historical_vnstock.parquet")
    union = sorted(fireant_symbols | vnstock_symbols)

    listing = pd.read_csv(LISTING_SNAPSHOT, encoding="utf-8-sig", dtype=str).fillna("")
    listing["symbol"] = listing["symbol"].str.strip().str.upper()
    listing = listing.drop_duplicates("symbol").set_index("symbol")
    current_listing = set(listing.index)

    records = []
    for symbol in union:
        in_listing = symbol in current_listing
        records.append(
            {
                "symbol": symbol,
                "has_fireant_ohlcv": symbol in fireant_symbols,
                "has_vnstock_ohlcv": symbol in vnstock_symbols,
                "in_vnstock_listing_snapshot": in_listing,
                "vnstock_organ_name": listing.at[symbol, "organ_name"] if in_listing else "",
                "listing_evidence_status": (
                    "present_in_current_vnstock_listing"
                    if in_listing
                    else "absent_from_current_listing_unverified"
                ),
                "activity_status": "unknown",
                "delisted_status": "unverified",
                "snapshot_date": SNAPSHOT_DATE,
            }
        )

    universe = pd.DataFrame.from_records(records).sort_values("symbol").reset_index(drop=True)
    if len(universe) != 1529:
        raise ValueError(f"Universe phải có 1529 mã, thực tế có {len(universe)}")
    return universe


def main() -> None:
    BCTC_STATE_DIR.mkdir(parents=True, exist_ok=True)
    universe = build_universe()
    universe.to_csv(UNIVERSE_CSV, index=False, encoding="utf-8-sig")
    universe.to_parquet(UNIVERSE_PARQUET, index=False)

    legacy_files = [
        parquet_inventory(path)
        for path in sorted(BCTC_DIR.rglob("*.parquet"))
        if BCTC_STATE_DIR not in path.parents
    ]

    checkpoint = None
    checkpoint_artifact = None
    if LEGACY_CHECKPOINT.exists():
        checkpoint = json.loads(LEGACY_CHECKPOINT.read_text(encoding="utf-8"))
        checkpoint_artifact = {
            "path": LEGACY_CHECKPOINT.relative_to(PROJECT_DIR).as_posix(),
            "classification": "legacy_checkpoint_preserved",
            "bytes": LEGACY_CHECKPOINT.stat().st_size,
            "sha256": sha256_file(LEGACY_CHECKPOINT),
            "status": checkpoint.get("status"),
            "completed_symbols": checkpoint.get("completed", []),
            "failed_symbols": sorted(checkpoint.get("failed", {})),
        }

    absent = universe.loc[
        ~universe["in_vnstock_listing_snapshot"], "symbol"
    ].tolist()
    listing_symbols = set(
        pd.read_csv(LISTING_SNAPSHOT, encoding="utf-8-sig", dtype=str)["symbol"]
        .str.strip()
        .str.upper()
    )
    listing_only = sorted(listing_symbols - set(universe["symbol"]))
    inventory = {
        "inventory_version": 1,
        "created_at": datetime.now().astimezone().isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "status": "step_00_complete",
        "scope": "local baseline only; no BCTC API crawl",
        "universe": {
            "total_symbols": len(universe),
            "fireant_ohlcv_symbols": int(universe["has_fireant_ohlcv"].sum()),
            "vnstock_ohlcv_symbols": int(universe["has_vnstock_ohlcv"].sum()),
            "symbols_in_both_ohlcv_sources": int(
                (universe["has_fireant_ohlcv"] & universe["has_vnstock_ohlcv"]).sum()
            ),
            "symbols_in_current_vnstock_listing": int(
                universe["in_vnstock_listing_snapshot"].sum()
            ),
            "absent_from_current_listing_unverified": absent,
            "current_listing_only_not_in_ohlcv_baseline": listing_only,
            "activity_delisted_note": (
                "Listing API chỉ trả symbol/organ_name. Không đủ bằng chứng để gắn active "
                "hoặc delisted; các mã vắng mặt giữ trạng thái unverified. Mã chỉ có trong "
                "listing được ghi nhận nhưng chưa tự thêm vào baseline OHLCV 1529 mã."
            ),
            "csv_path": UNIVERSE_CSV.relative_to(PROJECT_DIR).as_posix(),
            "parquet_path": UNIVERSE_PARQUET.relative_to(PROJECT_DIR).as_posix(),
        },
        "legacy_bctc": {
            "artifact_count": len(legacy_files),
            "artifacts": legacy_files,
            "checkpoint": checkpoint_artifact,
            "checkpoint_findings": {
                "symbol_marked_completed_despite_partial_failure": bool(
                    checkpoint
                    and set(checkpoint.get("completed", []))
                    & set(checkpoint.get("failed", {}))
                )
            },
        },
        "environment": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "packages": package_versions(),
        },
        "configuration": {
            "non_secret_artifacts": [
                config_artifact(PROJECT_CONFIG),
                config_artifact(COLLECTOR_CONFIG),
            ],
            "secret_environment": {
                "path": ENV_FILE.relative_to(PROJECT_DIR).as_posix(),
                "exists": ENV_FILE.exists(),
                "content_read_or_copied": False,
                "expected_keys_from_code": ["FIREANT_BEARER_TOKEN", "GEMINI_API_KEY"],
            },
        },
        "source_artifacts_preserved": True,
    }

    payload = json.dumps(inventory, ensure_ascii=False, indent=2)
    INVENTORY_JSON.write_text(payload + "\n", encoding="utf-8")
    STATE_INVENTORY_JSON.write_text(payload + "\n", encoding="utf-8")

    print(f"UNIVERSE={len(universe)}")
    print(f"LEGACY_BCTC={len(legacy_files)}")
    print(f"ABSENT_UNVERIFIED={','.join(absent)}")
    print(f"LISTING_ONLY={','.join(listing_only)}")
    print(f"INVENTORY={INVENTORY_JSON.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()
