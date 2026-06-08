from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

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
        self.log_area.append("[System] Đã khởi động E_CYBER-FINANCIAL.")
        self.log_area.append("[System] Sẵn sàng xử lý dữ liệu tài chính...")
        
        layout.addWidget(self.log_area)
