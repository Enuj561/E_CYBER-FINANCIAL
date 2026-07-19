"""
Module:  E_config
Logic:   Centralized project paths and constants for E_CYBER-FINANCIAL
Detail:  Tập trung mọi đường dẫn và hằng số dự án vào 1 nơi duy nhất.
         Mọi file khác import từ đây — KHÔNG được hardcode path riêng.
"""
import os

# ═══════════════════════════════════════════════════════════════
# PROJECT ROOT — Tính tự động từ vị trí file này
# E_Helper/ nằm ngay trong E_CYBER-FINANCIAL/, nên lùi 1 cấp = project root
# ═══════════════════════════════════════════════════════════════
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════
# PHASE 1 — Data thô
# ═══════════════════════════════════════════════════════════════
PHASE_1_DATA_DIR = os.path.join(PROJECT_DIR, "Phase_1_Data")

# E_OHLCV — Giá + Khối lượng + Khối ngoại
OHLCV_DIR = os.path.join(PHASE_1_DATA_DIR, "E_OHLCV")
VNSTOCK_DIR = os.path.join(OHLCV_DIR, "From_vnstock")
FIREANT_DIR = os.path.join(OHLCV_DIR, "From_FireAnt")

# E_BCTC — Báo cáo Tài chính
BCTC_DIR = os.path.join(PHASE_1_DATA_DIR, "E_BCTC")
BCTC_BALANCE_SHEET_DIR = os.path.join(BCTC_DIR, "Balance_Sheet")
BCTC_INCOME_STMT_DIR = os.path.join(BCTC_DIR, "Income_Statement")
BCTC_CASH_FLOW_DIR = os.path.join(BCTC_DIR, "Cash_Flow")
BCTC_RATIO_DIR = os.path.join(BCTC_DIR, "Ratio")
BCTC_NOTE_DIR = os.path.join(BCTC_DIR, "Note")

# ═══════════════════════════════════════════════════════════════
# PHASE 5 — News JSON
# ═══════════════════════════════════════════════════════════════
PHASE_5_DATA_DIR = os.path.join(PROJECT_DIR, "Phase_5_Data")

# ═══════════════════════════════════════════════════════════════
# HỆ THỐNG — Log, System, Main Scripts
# ═══════════════════════════════════════════════════════════════
LOG_DIR = os.path.join(PROJECT_DIR, "Log_Debug")
SYSTEM_DIR = os.path.join(PROJECT_DIR, "System")
MAIN_SCRIPTS_DIR = os.path.join(PROJECT_DIR, "Main Scripts")
ENV_PATH = os.path.join(SYSTEM_DIR, ".env")

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTION
# ═══════════════════════════════════════════════════════════════
def ensure_dirs():
    """Tạo các thư mục data nếu chưa tồn tại."""
    for d in [PHASE_1_DATA_DIR,
              OHLCV_DIR, VNSTOCK_DIR, FIREANT_DIR,
              BCTC_DIR, BCTC_BALANCE_SHEET_DIR, BCTC_INCOME_STMT_DIR,
              BCTC_CASH_FLOW_DIR, BCTC_RATIO_DIR, BCTC_NOTE_DIR,
              PHASE_5_DATA_DIR, LOG_DIR]:
        os.makedirs(d, exist_ok=True)
