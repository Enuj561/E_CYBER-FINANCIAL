"""
Module:  Warden
Logic:   Start the PyQt application
Detail:  Entry point cấu hình import path, khởi động IDE và ghi lỗi biên qua E_BlackBox.
"""

import sys
import os

# Chỉnh sửa lại đường dẫn hệ thống để code hiểu được thư mục dự án
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Thêm Main Scripts vào path để import News được
main_scripts_path = os.path.join(project_root, "Main Scripts")
if main_scripts_path not in sys.path:
    sys.path.insert(0, main_scripts_path)

from PyQt6.QtWidgets import QApplication
from E_Helper.E_BlackBox import get_black_box
from IDE_UI.E_main_window import MainWindow


black_box = get_black_box(__file__, console=True)

def main():
    try:
        black_box.info("Warden khởi động")
        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        window = MainWindow()
        window.show()
        exit_code = app.exec()
        black_box.info("Warden kết thúc", exit_code=exit_code)
        return exit_code
    except Exception:
        black_box.exception("IDE dừng vì lỗi không dự kiến")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
