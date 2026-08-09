"""
Module:  E_right_panel
Logic:   Live E_BlackBox event panel for the IDE
Detail:  Panel bên phải chỉ hiển thị các sự kiện do E_BlackBox phát ra. Việc ghi file
         thuộc E_BlackBox và nằm cạnh script chính của từng tính năng.
"""
from html import escape

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import pyqtSignal

from E_Helper.E_BlackBox import get_black_box, subscribe, unsubscribe


class RightPanel(QWidget):
    event_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._black_box = get_black_box(__file__)
        self.setStyleSheet("background-color: #252526; color: #CCCCCC;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("E_BlackBox — Live Events")
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
        
        self.event_received.connect(self._show_event)
        self._subscriber = self.event_received.emit
        subscribe(self._subscriber)
        self._black_box.info("E_BlackBox panel đã sẵn sàng")

    def _show_event(self, event):
        """Hiển thị một event đã được E_BlackBox chuẩn hóa."""
        timestamp = escape(str(event.get("timestamp", ""))[-8:])
        level = escape(str(event.get("level", "INFO")))
        feature = escape(str(event.get("feature", "Unknown")))
        message = escape(str(event.get("message", "")))
        color_map = {
            "DEBUG": "#CE9178",
            "INFO": "#9CDCFE",
            "WARNING": "#DCDCAA",
            "ERROR": "#F44747",
            "CRITICAL": "#FF0000",
        }
        color = color_map.get(level, "#CCCCCC")
        html_line = (
            f'<span style="color:#6A9955;">[{timestamp}]</span> '
            f'<span style="color:{color};">[{level}]</span> '
            f'<span style="color:#4EC9B0;">[{feature}]</span> '
            f'<span style="color:#D4D4D4;">{message}</span>'
        )
        self.log_area.append(html_line)

    def closeEvent(self, event):
        unsubscribe(self._subscriber)
        super().closeEvent(event)
