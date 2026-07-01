from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(35)
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D30;
                border-bottom: 1px solid #1E1E1E;
            }
            QLabel {
                color: #CCCCCC;
                font-weight: bold;
                font-size: 13px;
                background: transparent;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #CCCCCC;
                font-size: 14px;
                padding: 0px 10px;
            }
            QPushButton:hover {
                background-color: #3F3F46;
            }
            QPushButton#closeBtn:hover {
                background-color: #E81123;
                color: white;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Trái (Khoảng trống hoặc icon)
        self.left_spacer = QWidget()
        self.left_spacer.setFixedWidth(100)
        layout.addWidget(self.left_spacer)

        layout.addStretch()

        # Giữa (Tiêu đề)
        self.title_label = QLabel("E_CYBER-FINANCIAL IDE")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Phải (Nút bấm)
        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("☐")
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("closeBtn")

        self.btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max_restore)
        self.btn_close.clicked.connect(self.parent.close)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        btn_layout.addWidget(self.btn_min)
        btn_layout.addWidget(self.btn_max)
        btn_layout.addWidget(self.btn_close)

        # Chỉnh kích thước cố định cho nút
        for btn in [self.btn_min, self.btn_max, self.btn_close]:
            btn.setFixedSize(45, 35)

        layout.addLayout(btn_layout)

        # Dragging support
        self.start_pos = QPoint()

    def toggle_max_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.btn_max.setText("☐")
        else:
            self.parent.showMaximized()
            self.btn_max.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.start_pos.isNull() and not self.parent.isMaximized():
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = QPoint()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_max_restore()
