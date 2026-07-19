from PyQt6.QtWidgets import QMainWindow, QDockWidget
from PyQt6.QtCore import Qt
from IDE_UI.E_left_panel import LeftPanel
from IDE_UI.E_center_workspace import CenterWorkspace
from IDE_UI.E_right_panel import RightPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Dùng khoảng trắng để ép Windows đẩy title ra giữa (hack)
        self.setWindowTitle("                                                                                                    E_CYBER-FINANCIAL IDE")
        self.resize(1280, 720)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QDockWidget {
                color: #CCCCCC;
                font-weight: bold;
            }
            QDockWidget::title {
                background-color: #2D2D30;
                padding: 6px;
                padding-left: 10px;
                border: 1px solid #3F3F46;
            }
            QDockWidget > QWidget {
                border: 1px solid #3F3F46;
            }
        """)
        
        self.center_workspace = CenterWorkspace()
        self.setCentralWidget(self.center_workspace)
        
        self.left_dock = QDockWidget("Explorer / Functions", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.left_panel = LeftPanel()
        self.left_dock.setWidget(self.left_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)
        
        self.right_dock = QDockWidget("System Info", self)
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.right_panel = RightPanel()
        self.right_dock.setWidget(self.right_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)
        
        # Kết nối logger từ RightPanel vào CenterWorkspace
        self.center_workspace.set_logger(self.right_panel)
        
        # Kết nối sự kiện Click từ Left Panel
        self.left_panel.item_clicked_signal.connect(self.handle_navigation)
        
    def handle_navigation(self, item_name):
        self.right_panel.log("System", f"Đã mở tab: {item_name}")
        if "News" in item_name:
            self.center_workspace.stacked_widget.setCurrentIndex(1)
        else:
            self.center_workspace.stacked_widget.setCurrentIndex(0)
