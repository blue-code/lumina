"""
요청 편집 패널
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QComboBox, QPushButton, QTabWidget,
                              QTextEdit, QTableWidget, QTableWidgetItem,
                              QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from models.request_model import RequestModel, HttpMethod, BodyType, AuthType
from typing import Optional


class KeyValueTable(QTableWidget):
    """키-값 쌍 입력 테이블"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Key", "Value", ""])
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setColumnWidth(0, 150)
        self.setColumnWidth(2, 30)

    def set_data(self, data: dict):
        """데이터 설정"""
        self.setRowCount(len(data) + 1)  # +1은 빈 행

        for i, (key, value) in enumerate(data.items()):
            self.setItem(i, 0, QTableWidgetItem(key))
            self.setItem(i, 1, QTableWidgetItem(value))

            # 삭제 버튼
            delete_btn = QPushButton("X")
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_row(row))
            self.setCellWidget(i, 2, delete_btn)

        # 마지막 빈 행
        self.setItem(len(data), 0, QTableWidgetItem(""))
        self.setItem(len(data), 1, QTableWidgetItem(""))

        # 셀 변경 시 자동으로 새 행 추가
        self.cellChanged.connect(self.on_cell_changed)

    def get_data(self) -> dict:
        """데이터 가져오기"""
        data = {}
        for i in range(self.rowCount()):
            key_item = self.item(i, 0)
            value_item = self.item(i, 1)

            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                if key:  # 키가 있는 경우만 추가
                    data[key] = value

        return data

    def delete_row(self, row: int):
        """행 삭제"""
        self.removeRow(row)

    def on_cell_changed(self, row, col):
        """셀 변경 시"""
        # 마지막 행에 입력이 있으면 새 행 추가
        if row == self.rowCount() - 1:
            key_item = self.item(row, 0)
            value_item = self.item(row, 1)

            if key_item and key_item.text().strip():
                # 새 빈 행 추가
                self.setRowCount(self.rowCount() + 1)
                self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(""))
                self.setItem(self.rowCount() - 1, 1, QTableWidgetItem(""))


class RequestEditorPanel(QWidget):
    """요청 편집 패널"""

    # 시그널
    request_updated = pyqtSignal(RequestModel)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_request: Optional[RequestModel] = None
        self.setup_ui()

    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 상단 - 메서드 및 URL
        top_layout = QHBoxLayout()

        # HTTP 메서드 선택
        self.method_combo = QComboBox()
        for method in HttpMethod:
            self.method_combo.addItem(method.value, method)
        self.method_combo.setMaximumWidth(100)
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        top_layout.addWidget(self.method_combo)

        # URL 입력
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Enter request URL (e.g., https://api.example.com/users)")
        self.url_edit.textChanged.connect(self.on_url_changed)
        top_layout.addWidget(self.url_edit)

        layout.addLayout(top_layout)

        # 탭 위젯
        self.tabs = QTabWidget()

        # Params 탭
        self.params_table = KeyValueTable()
        self.tabs.addTab(self.params_table, "Params")

        # Headers 탭
        self.headers_table = KeyValueTable()
        self.tabs.addTab(self.headers_table, "Headers")

        # Body 탭
        self.body_tab = self._create_body_tab()
        self.tabs.addTab(self.body_tab, "Body")

        # Auth 탭
        self.auth_tab = self._create_auth_tab()
        self.tabs.addTab(self.auth_tab, "Auth")

        layout.addWidget(self.tabs)

    def _create_body_tab(self) -> QWidget:
        """Body 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Body 타입 선택
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Body Type:"))

        self.body_type_combo = QComboBox()
        self.body_type_combo.addItem("None", BodyType.NONE)
        self.body_type_combo.addItem("Raw (JSON/Text)", BodyType.RAW)
        self.body_type_combo.addItem("Form URL-Encoded", BodyType.FORM_URLENCODED)
        self.body_type_combo.addItem("Form Data", BodyType.FORM_DATA)
        self.body_type_combo.currentIndexChanged.connect(self.on_body_type_changed)

        type_layout.addWidget(self.body_type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Raw Body 입력
        self.body_raw_edit = QTextEdit()
        self.body_raw_edit.setFont(QFont("Monaco, Courier New", 11))
        self.body_raw_edit.setPlaceholderText('Enter raw body (e.g., JSON)\n\n{\n  "key": "value"\n}')
        layout.addWidget(self.body_raw_edit)

        # Form Body 입력
        self.body_form_table = KeyValueTable()
        self.body_form_table.setVisible(False)
        layout.addWidget(self.body_form_table)

        return widget

    def _create_auth_tab(self) -> QWidget:
        """Auth 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Auth 타입 선택
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Auth Type:"))

        self.auth_type_combo = QComboBox()
        self.auth_type_combo.addItem("No Auth", AuthType.NONE)
        self.auth_type_combo.addItem("Basic Auth", AuthType.BASIC)
        self.auth_type_combo.addItem("Bearer Token", AuthType.BEARER)
        self.auth_type_combo.addItem("API Key", AuthType.API_KEY)
        self.auth_type_combo.currentIndexChanged.connect(self.on_auth_type_changed)

        type_layout.addWidget(self.auth_type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Basic Auth
        self.basic_auth_widget = QWidget()
        basic_layout = QVBoxLayout(self.basic_auth_widget)

        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.auth_basic_username = QLineEdit()
        username_layout.addWidget(self.auth_basic_username)
        basic_layout.addLayout(username_layout)

        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.auth_basic_password = QLineEdit()
        self.auth_basic_password.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.auth_basic_password)
        basic_layout.addLayout(password_layout)

        basic_layout.addStretch()
        self.basic_auth_widget.setVisible(False)
        layout.addWidget(self.basic_auth_widget)

        # Bearer Token
        self.bearer_auth_widget = QWidget()
        bearer_layout = QVBoxLayout(self.bearer_auth_widget)

        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Token:"))
        self.auth_bearer_token = QLineEdit()
        self.auth_bearer_token.setPlaceholderText("Enter bearer token")
        token_layout.addWidget(self.auth_bearer_token)
        bearer_layout.addLayout(token_layout)

        bearer_layout.addStretch()
        self.bearer_auth_widget.setVisible(False)
        layout.addWidget(self.bearer_auth_widget)

        # API Key
        self.api_key_auth_widget = QWidget()
        api_key_layout = QVBoxLayout(self.api_key_auth_widget)

        key_name_layout = QHBoxLayout()
        key_name_layout.addWidget(QLabel("Key Name:"))
        self.auth_api_key_name = QLineEdit()
        self.auth_api_key_name.setPlaceholderText("e.g., X-API-Key")
        key_name_layout.addWidget(self.auth_api_key_name)
        api_key_layout.addLayout(key_name_layout)

        key_value_layout = QHBoxLayout()
        key_value_layout.addWidget(QLabel("Key Value:"))
        self.auth_api_key_value = QLineEdit()
        key_value_layout.addWidget(self.auth_api_key_value)
        api_key_layout.addLayout(key_value_layout)

        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Add to:"))
        self.auth_api_key_location = QComboBox()
        self.auth_api_key_location.addItem("Header", "header")
        self.auth_api_key_location.addItem("Query Params", "query")
        location_layout.addWidget(self.auth_api_key_location)
        location_layout.addStretch()
        api_key_layout.addLayout(location_layout)

        api_key_layout.addStretch()
        self.api_key_auth_widget.setVisible(False)
        layout.addWidget(self.api_key_auth_widget)

        layout.addStretch()
        return widget

    def load_request(self, request: RequestModel):
        """요청 로드"""
        self.current_request = request

        # 메서드
        index = self.method_combo.findData(request.method)
        if index >= 0:
            self.method_combo.setCurrentIndex(index)

        # URL
        self.url_edit.setText(request.url)

        # Params
        self.params_table.set_data(request.params)

        # Headers
        self.headers_table.set_data(request.headers)

        # Body
        index = self.body_type_combo.findData(request.body_type)
        if index >= 0:
            self.body_type_combo.setCurrentIndex(index)

        self.body_raw_edit.setPlainText(request.body_raw)
        self.body_form_table.set_data(request.body_form)
        self._update_body_visibility()

        # Auth
        index = self.auth_type_combo.findData(request.auth_type)
        if index >= 0:
            self.auth_type_combo.setCurrentIndex(index)

        self.auth_basic_username.setText(request.auth_basic_username)
        self.auth_basic_password.setText(request.auth_basic_password)
        self.auth_bearer_token.setText(request.auth_bearer_token)
        self.auth_api_key_name.setText(request.auth_api_key_name)
        self.auth_api_key_value.setText(request.auth_api_key_value)

        location_index = self.auth_api_key_location.findData(request.auth_api_key_location)
        if location_index >= 0:
            self.auth_api_key_location.setCurrentIndex(location_index)

        self._update_auth_visibility()

    def save_to_request(self):
        """현재 입력값을 요청에 저장"""
        if not self.current_request:
            return

        # 메서드
        self.current_request.method = self.method_combo.currentData()

        # URL
        self.current_request.url = self.url_edit.text()

        # Params
        self.current_request.params = self.params_table.get_data()

        # Headers
        self.current_request.headers = self.headers_table.get_data()

        # Body
        self.current_request.body_type = self.body_type_combo.currentData()
        self.current_request.body_raw = self.body_raw_edit.toPlainText()
        self.current_request.body_form = self.body_form_table.get_data()

        # Auth
        self.current_request.auth_type = self.auth_type_combo.currentData()
        self.current_request.auth_basic_username = self.auth_basic_username.text()
        self.current_request.auth_basic_password = self.auth_basic_password.text()
        self.current_request.auth_bearer_token = self.auth_bearer_token.text()
        self.current_request.auth_api_key_name = self.auth_api_key_name.text()
        self.current_request.auth_api_key_value = self.auth_api_key_value.text()
        self.current_request.auth_api_key_location = self.auth_api_key_location.currentData()

        self.request_updated.emit(self.current_request)

    def on_method_changed(self):
        """메서드 변경 시"""
        self.save_to_request()

    def on_url_changed(self):
        """URL 변경 시"""
        # 변경 사항은 Send 시점에 저장됨
        pass

    def on_body_type_changed(self):
        """Body 타입 변경 시"""
        self._update_body_visibility()

    def on_auth_type_changed(self):
        """Auth 타입 변경 시"""
        self._update_auth_visibility()

    def _update_body_visibility(self):
        """Body 타입에 따라 UI 표시 변경"""
        body_type = self.body_type_combo.currentData()

        if body_type == BodyType.RAW:
            self.body_raw_edit.setVisible(True)
            self.body_form_table.setVisible(False)
        elif body_type in [BodyType.FORM_URLENCODED, BodyType.FORM_DATA]:
            self.body_raw_edit.setVisible(False)
            self.body_form_table.setVisible(True)
        else:  # NONE
            self.body_raw_edit.setVisible(False)
            self.body_form_table.setVisible(False)

    def _update_auth_visibility(self):
        """Auth 타입에 따라 UI 표시 변경"""
        auth_type = self.auth_type_combo.currentData()

        self.basic_auth_widget.setVisible(auth_type == AuthType.BASIC)
        self.bearer_auth_widget.setVisible(auth_type == AuthType.BEARER)
        self.api_key_auth_widget.setVisible(auth_type == AuthType.API_KEY)

    def clear(self):
        """패널 초기화"""
        self.current_request = None
        self.method_combo.setCurrentIndex(0)
        self.url_edit.clear()
        self.params_table.setRowCount(0)
        self.headers_table.setRowCount(0)
        self.body_raw_edit.clear()
        self.body_form_table.setRowCount(0)
        self.body_type_combo.setCurrentIndex(0)
        self.auth_type_combo.setCurrentIndex(0)
        self.auth_basic_username.clear()
        self.auth_basic_password.clear()
        self.auth_bearer_token.clear()
        self.auth_api_key_name.clear()
        self.auth_api_key_value.clear()
