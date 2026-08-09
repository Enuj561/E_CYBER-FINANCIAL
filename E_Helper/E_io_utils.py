"""
Module:  E_io_utils
Logic:   Atomic file write utilities for safe data persistence
Detail:  Cung cấp hàm ghi file an toàn (JSON, Parquet) — tránh corrupt khi crash giữa chừng
"""
import tempfile
import os
import json
import pandas as pd

def safe_write_json(filepath, data):
    """Ghi JSON an toàn: ghi file tạm → rename atomic."""
    filepath = os.fspath(filepath)
    dir_name = os.path.dirname(filepath) or "."
    os.makedirs(dir_name, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            'w', dir=dir_name, suffix='.tmp', delete=False, encoding='utf-8'
        ) as tmp:
            tmp_path = tmp.name
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, filepath)
        tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

def safe_write_parquet(filepath, df):
    """Ghi Parquet an toàn: ghi file tạm → rename atomic."""
    filepath = os.fspath(filepath)
    dir_name = os.path.dirname(filepath) or "."
    os.makedirs(dir_name, exist_ok=True)
    handle, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.parquet.tmp')
    os.close(handle)
    try:
        df.to_parquet(tmp_path, index=False)
        os.replace(tmp_path, filepath)
        tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
