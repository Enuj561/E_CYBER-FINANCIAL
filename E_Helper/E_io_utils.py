"""
Module:  io_utils
Logic:   Atomic file write utilities for safe data persistence
Detail:  Cung cấp hàm ghi file an toàn (JSON, Parquet) — tránh corrupt khi crash giữa chừng
"""
import tempfile
import os
import json
import pandas as pd

def safe_write_json(filepath, data):
    """Ghi JSON an toàn: ghi file tạm → rename atomic."""
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=dir_name, suffix='.tmp',
                                      delete=False, encoding='utf-8') as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, filepath)

def safe_write_parquet(filepath, df):
    """Ghi Parquet an toàn: ghi file tạm → rename atomic."""
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    tmp_path = filepath + ".tmp"
    df.to_parquet(tmp_path, index=False)
    os.replace(tmp_path, filepath)
