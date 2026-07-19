from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import pyqtSignal

class LeftPanel(QTreeWidget):
    item_clicked_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #252526; 
                color: #CCCCCC; 
                border: none;
                font-size: 13px;
            }
            QTreeWidget::item:hover {
                background-color: #2A2D2E;
            }
            QTreeWidget::item:selected {
                background-color: #37373D;
            }
        """)
        
        # Root Items
        home_item = QTreeWidgetItem(self, ["Trang chủ"])
        news_item = QTreeWidgetItem(self, ["Tin tức thị trường (News)"])
        
        self.expandAll()
        self.itemClicked.connect(self.on_item_clicked)
        
    def on_item_clicked(self, item, column):
        self.item_clicked_signal.emit(item.text(0))
