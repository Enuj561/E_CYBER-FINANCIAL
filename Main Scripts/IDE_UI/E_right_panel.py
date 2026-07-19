"""
Module:  E_right_panel
Logic:   System log panel UI for the IDE
Detail:  Panel bên phải hiển thị log hệ thống. Ghi log ra cả UI lẫn file text.
         Sửa lỗi: except pass → log lỗi ghi file vào console thay vì nuốt im lặng.
"""
import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

# Import centralized paths
from E_Helper.E_config import LOG_DIR

logger = logging.getLogger(__name__)


class RightPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #252526; color: #CCCCCC;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("System Logs & Properties")
        title.setStyleSheet("font-weight: bold; padding: 5px; color: #E0E0E0;")
        layout.addWidget(title)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E; 
                border: 1px solid #333333;
                font-family: Consolas;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_area)
        
        # Đảm bảo folder Log_Debug tồn tại
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Ghi log khởi động
        self.log("System", "Đã khởi động E_CYBER-FINANCIAL.")
        self.log("System", "Sẵn sàng xử lý dữ liệu tài chính...")

    def _get_log_filepath(self):
        """Trả về đường dẫn file log theo ngày hiện tại: Log_dd_mm_yy.txt"""
        filename = f"Log_{datetime.now().strftime('%d_%m_%y')}.txt"
        return os.path.join(LOG_DIR, filename)

    def log(self, tag, message):
        """
        Ghi 1 dòng log với timestamp.
        - Hiển thị lên UI (log_area) có màu sắc.
        - Đồng thời append vào file Log_dd_mm_yy.txt.
        
        tag: nhãn phân loại (System, News, Error, User, ...)
        message: nội dung log.
        """
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S")
        
        # Màu sắc theo tag
        color_map = {
            "System": "#569CD6",   # Xanh dương
            "News": "#4EC9B0",     # Xanh ngọc
            "Error": "#F44747",    # Đỏ
            "User": "#DCDCAA",     # Vàng nhạt
            "Info": "#9CDCFE",     # Xanh nhạt
            "Debug": "#CE9178",    # Cam
        }
        color = color_map.get(tag, "#CCCCCC")
        
        # Hiển thị lên UI
        html_line = (
            f'<span style="color:#6A9955;">[{timestamp}]</span> '
            f'<span style="color:{color};">[{tag}]</span> '
            f'<span style="color:#D4D4D4;">{message}</span>'
        )
        self.log_area.append(html_line)
        
        # Ghi vào file debug (append)
        plain_line = f"[{timestamp}] [{tag}] {message}"
        try:
            filepath = self._get_log_filepath()
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(plain_line + "\n")
        except Exception as e:
            # Log lỗi ghi file ra console thay vì nuốt im lặng (except: pass)
            logger.warning(f"Không ghi được log file: {e}")
