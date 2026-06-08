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
from UI_Scripts.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
