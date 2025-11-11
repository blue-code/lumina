"""
응답 표시 패널
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                              QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from models.response_model import ResponseModel
import json


class ResponsePanel(QWidget):
    """응답 표시 패널"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 상태 표시 영역
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.status_label)

        self.time_label = QLabel("")
        status_layout.addWidget(self.time_label)

        self.size_label = QLabel("")
        status_layout.addWidget(self.size_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)

        # 탭 위젯
        self.tabs = QTabWidget()

        # Body 탭
        self.body_tab = QWidget()
        body_layout = QVBoxLayout(self.body_tab)
        body_layout.setContentsMargins(0, 0, 0, 0)

        # Pretty / Raw 전환 버튼
        body_controls = QHBoxLayout()
        self.pretty_btn = QPushButton("Pretty")
        self.pretty_btn.setCheckable(True)
        self.pretty_btn.setChecked(True)
        self.pretty_btn.clicked.connect(self.show_pretty)

        self.raw_btn = QPushButton("Raw")
        self.raw_btn.setCheckable(True)
        self.raw_btn.clicked.connect(self.show_raw)

        body_controls.addWidget(self.pretty_btn)
        body_controls.addWidget(self.raw_btn)
        body_controls.addStretch()

        body_layout.addLayout(body_controls)

        # Body 텍스트 에디터
        self.body_text = QTextEdit()
        self.body_text.setReadOnly(True)
        self.body_text.setFont(QFont("Monaco, Courier New", 11))
        body_layout.addWidget(self.body_text)

        self.tabs.addTab(self.body_tab, "Body")

        # Headers 탭
        self.headers_table = QTableWidget()
        self.headers_table.setColumnCount(2)
        self.headers_table.setHorizontalHeaderLabels(["Name", "Value"])
        self.headers_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.headers_table, "Headers")

        layout.addWidget(self.tabs)

        # 초기 상태
        self.current_response: ResponseModel = None
        self.is_pretty_mode = True

    def display_response(self, response: ResponseModel):
        """응답 표시"""
        self.current_response = response

        if response.is_error():
            # 에러 표시
            self.status_label.setText(f"Error: {response.error}")
            self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            self.time_label.setText("")
            self.size_label.setText("")
            self.body_text.setPlainText(response.error)
            self.headers_table.setRowCount(0)
        else:
            # 성공 응답 표시
            status_color = "green" if response.is_success() else "orange"
            self.status_label.setText(f"Status: {response.status_code} {response.status_text}")
            self.status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; padding: 5px;")

            self.time_label.setText(f"Time: {response.elapsed_ms:.0f} ms")
            self.size_label.setText(f"Size: {response.size_bytes} bytes")

            # Body 표시
            self._display_body()

            # Headers 표시
            self._display_headers()

    def _display_body(self):
        """Body 내용 표시"""
        if not self.current_response:
            return

        body = self.current_response.body

        if self.is_pretty_mode and self.current_response.is_json():
            # Pretty JSON
            try:
                json_obj = json.loads(body)
                pretty_json = json.dumps(json_obj, indent=2, ensure_ascii=False)
                self.body_text.setPlainText(pretty_json)
            except:
                # JSON 파싱 실패시 Raw로
                self.body_text.setPlainText(body)
        else:
            # Raw
            self.body_text.setPlainText(body)

    def _display_headers(self):
        """Headers 표시"""
        if not self.current_response:
            return

        headers = self.current_response.headers
        self.headers_table.setRowCount(len(headers))

        for i, (name, value) in enumerate(headers.items()):
            self.headers_table.setItem(i, 0, QTableWidgetItem(name))
            self.headers_table.setItem(i, 1, QTableWidgetItem(value))

        self.headers_table.resizeColumnToContents(0)

    def show_pretty(self):
        """Pretty 모드로 전환"""
        self.is_pretty_mode = True
        self.pretty_btn.setChecked(True)
        self.raw_btn.setChecked(False)
        self._display_body()

    def show_raw(self):
        """Raw 모드로 전환"""
        self.is_pretty_mode = False
        self.pretty_btn.setChecked(False)
        self.raw_btn.setChecked(True)
        self._display_body()

    def clear(self):
        """응답 패널 초기화"""
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.time_label.setText("")
        self.size_label.setText("")
        self.body_text.clear()
        self.headers_table.setRowCount(0)
        self.current_response = None
