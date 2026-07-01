import os
import json
import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QStackedWidget, 
                             QComboBox, QPushButton, QTextEdit, QHBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from News.news_scraper import fetch_news, RSS_FEEDS
from News.gemini_ai import summarize_news

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_JSON_DIR = os.path.join(PROJECT_DIR, "News_JSON")
ALL_CATEGORIES = ["Vĩ mô & Tiền tệ", "Thị trường & Đầu tư", "Công nghệ"]

class WorkerThread(QThread):
    finished_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str)
    
    def __init__(self, source, category):
        super().__init__()
        self.source = source
        self.category = category
        
    def run(self):
        try:
            # Bước 1: Cào tin
            news_list, debug_logs = fetch_news(self.source, self.category)
            # Bước 2: Tóm tắt
            def progress_callback(msg):
                self.progress_signal.emit(msg)
                
            tf_text = "Bản tin tài chính (18:00 → 18:00)"
            summary = summarize_news(news_list, tf_text, self.source == "Tổng hợp", debug_logs, progress_callback)
            self.finished_signal.emit(summary)
        except Exception as e:
            self.finished_signal.emit(f"Lỗi hệ thống: {str(e)}")


class JsonWorkerThread(QThread):
    """Thread chạy nền để cào tất cả tin tức và lưu JSON."""
    finished_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str)

    def run(self):
        try:
            from News.news_manager import NewsManager
            
            # Callback để emit tiến trình lên giao diện dưới dạng HTML
            def progress_callback(msg):
                # Làm đẹp log msg một chút cho UI
                html_msg = f'<div style="color:#FFA500; font-family:Segoe UI; font-size:15px; font-style:italic;">{msg}</div>'
                self.progress_signal.emit(html_msg)
                
            self.progress_signal.emit('<div style="color:#CCCCCC; font-family:Segoe UI; font-size:15px;">🔄 Đang khởi động hệ thống cào tin...</div>')
            
            # Chạy toàn bộ tiến trình (quét thiếu ngày, backfill, cào hôm nay)
            full_log = NewsManager.run_full_pipeline(log_callback=progress_callback)
            
            # Format lại log thành HTML để hiển thị ở cửa sổ kết thúc
            html_report = f'<div style="color:#4EC9B0; font-family:Segoe UI; font-size:15px; white-space: pre-wrap;">{full_log}</div>'
            self.finished_signal.emit(html_report)

        except Exception as e:
            self.finished_signal.emit(
                f'<div style="color:#FF6B6B; font-family:Segoe UI; font-size:15px;">'
                f'❌ Lỗi: {str(e)}</div>'
            )

class CenterWorkspace(QWidget):
    def __init__(self):
        super().__init__()
        self._logger = None
        self.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        self.setup_welcome_page()
        self.setup_news_page()

    def set_logger(self, right_panel):
        """Kết nối với RightPanel để ghi log."""
        self._logger = right_panel

    def _log(self, tag, message):
        """Ghi log nếu logger đã được kết nối."""
        if self._logger:
            self._logger.log(tag, message)
        
    def setup_welcome_page(self):
        page = QWidget()
        l = QVBoxLayout(page)
        
        title = QLabel("E_CYBER-FINANCIAL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: magenta;")
        
        subtitle = QLabel("Hệ thống Phân tích & Tự động hóa Tài chính\n\n(Chọn một chức năng bên trái để bắt đầu)")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: cyan;")
        
        l.addStretch()
        l.addWidget(title)
        l.addWidget(subtitle)
        l.addStretch()
        self.stacked_widget.addWidget(page)
        
    def setup_news_page(self):
        self.news_page = QWidget()
        l = QVBoxLayout(self.news_page)
        l.setContentsMargins(20, 20, 20, 20)
        
        # Khung công cụ Top Bar
        top_bar = QHBoxLayout()
        
        combo_style = """
            QComboBox { background-color: #333; color: white; padding: 5px; border: 1px solid #555; font-size: 13px; }
        """
        
        # Ô chọn Nguồn báo
        self.cb_source = QComboBox()
        self.cb_source.addItems(["<Nguồn báo>", "Báo Đầu tư", "Tạp chí kinh tế VN", "Tạp chí ĐT Kinh doanh", "Vietnamnet", "Tổng hợp"])
        self.cb_source.setStyleSheet(combo_style)
        self.cb_source.currentIndexChanged.connect(self.check_run_button_state)

        # Ô chọn Lĩnh vực
        self.cb_category = QComboBox()
        self.cb_category.addItems(["<Lĩnh vực>", "Vĩ mô & Tiền tệ", "Thị trường & Đầu tư", "Công nghệ"])
        self.cb_category.setStyleSheet(combo_style)
        self.cb_category.currentIndexChanged.connect(self.check_run_button_state)
        
        self.btn_run = QPushButton("⚡ Chạy Gemini Tổng Hợp")
        self.btn_run.setStyleSheet("""
            QPushButton { background-color: #0E639C; color: white; padding: 8px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; }
            QPushButton:hover { background-color: #1177BB; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
        """)
        self.btn_run.clicked.connect(self.run_news_aggregation)
        self.btn_run.setEnabled(False) # Khóa mặc định ban đầu
        
        self.btn_json = QPushButton("📁 Tổng hợp JSON")
        self.btn_json.setStyleSheet("""
            QPushButton { background-color: #2D7D46; color: white; padding: 8px 15px; font-weight: bold; border-radius: 3px; font-size: 13px; }
            QPushButton:hover { background-color: #3A9956; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
        """)
        self.btn_json.clicked.connect(self.run_json_export)
        
        top_bar.addWidget(self.cb_source)
        top_bar.addWidget(self.cb_category)
        top_bar.addWidget(self.btn_run)
        top_bar.addWidget(self.btn_json)
        top_bar.addStretch()
        l.addLayout(top_bar)
        
        # Khung văn bản hiển thị
        self.news_display = QTextEdit()
        self.news_display.setReadOnly(True)
        self.news_display.setStyleSheet("""
            QTextEdit { background-color: #1E1E1E; border: 1px solid #3F3F46; font-size: 15px; line-height: 1.6; padding: 15px; font-family: Segoe UI, sans-serif;}
        """)
        self.news_display.setText("Bấm nút 'Chạy Gemini Tổng Hợp' để bắt đầu lấy tin.")
        l.addWidget(self.news_display)
        
        self.stacked_widget.addWidget(self.news_page)
        
    def check_run_button_state(self):
        source = self.cb_source.currentText()
        category = self.cb_category.currentText()
        if source != "<Nguồn báo>" and category != "<Lĩnh vực>":
            self.btn_run.setEnabled(True)
        else:
            self.btn_run.setEnabled(False)
        
    def run_news_aggregation(self):
        source = self.cb_source.currentText()
        category = self.cb_category.currentText()
        
        self._log("News", f"Bắt đầu cào tin: {source} / {category}")
            
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Đang cập nhật...")
        
        base_style = 'style="color: #CCCCCC; font-family: Segoe UI, sans-serif; font-size: 15px; background: transparent;"'
        if source == "Tổng hợp":
            self.news_display.setHtml(f'<div {base_style}>Đang tổng hợp tin từ tất cả nguồn báo có sẵn...<br><br>Quá trình này mất khoảng 5-15 giây, Sếp đợi chút nhé...</div>')
        else:
            self.news_display.setHtml(f'<div {base_style}>Đang lấy tin tức mới nhất từ {source} và gửi cho Gemini xử lý.<br><br>Quá trình này mất khoảng 5-15 giây, Sếp đợi chút nhé...</div>')
        
        self.worker = WorkerThread(source, category)
        self.worker.progress_signal.connect(self.on_aggregation_progress)
        self.worker.finished_signal.connect(self.on_aggregation_done)
        self.worker.start()

    def on_aggregation_progress(self, msg):
        base_style = 'style="color: #FFA500; font-family: Segoe UI, sans-serif; font-size: 15px; background: transparent; font-style: italic;"'
        self.news_display.setHtml(f'<div {base_style}>{msg}</div>')
        
    def on_aggregation_done(self, summary):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("⚡ Chạy Gemini Tổng Hợp")
        self.news_display.setHtml(summary)
        self._log("News", "Hoàn tất cào tin và tóm tắt bằng Gemini.")

    # === JSON Export ===
    def run_json_export(self):
        self._log("News", "Bắt đầu tổng hợp JSON...")
        self.btn_json.setEnabled(False)
        self.btn_json.setText("Đang tổng hợp...")
        self.news_display.setHtml(
            '<div style="color:#CCCCCC; font-family:Segoe UI; font-size:15px;">'
            '📁 Đang cào tất cả tin tức và lưu thành file JSON...<br><br>'
            'Sếp đợi chút nhé...</div>'
        )
        self.json_worker = JsonWorkerThread()
        self.json_worker.progress_signal.connect(self.on_aggregation_progress)
        self.json_worker.finished_signal.connect(self.on_json_done)
        self.json_worker.start()

    def on_json_done(self, result):
        self.btn_json.setEnabled(True)
        self.btn_json.setText("📁 Tổng hợp JSON")
        self.news_display.setHtml(result)
        self._log("News", "Hoàn tất tổng hợp JSON.")
