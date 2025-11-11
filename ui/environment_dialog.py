"""
환경 변수 관리 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                              QPushButton, QLabel, QLineEdit, QMessageBox,
                              QListWidgetItem, QSplitter)
from PyQt5.QtCore import Qt
from models.environment import Environment, EnvironmentManager
from ui.request_editor_panel import KeyValueTable


class EnvironmentDialog(QDialog):
    """환경 변수 관리 다이얼로그"""

    def __init__(self, env_manager: EnvironmentManager, parent=None):
        super().__init__(parent)
        self.env_manager = env_manager
        self.current_env: Environment = None

        self.setWindowTitle("Manage Environments")
        self.resize(800, 500)
        self.setup_ui()
        self.load_environments()

    def setup_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)

        # 좌측 - 환경 목록
        left_panel = QVBoxLayout()

        left_panel.addWidget(QLabel("Environments:"))

        self.env_list = QListWidget()
        self.env_list.currentItemChanged.connect(self.on_env_selected)
        left_panel.addWidget(self.env_list)

        # 환경 추가/삭제 버튼
        btn_layout = QHBoxLayout()
        self.add_env_btn = QPushButton("Add")
        self.add_env_btn.clicked.connect(self.add_environment)
        btn_layout.addWidget(self.add_env_btn)

        self.delete_env_btn = QPushButton("Delete")
        self.delete_env_btn.clicked.connect(self.delete_environment)
        btn_layout.addWidget(self.delete_env_btn)

        left_panel.addLayout(btn_layout)

        # 우측 - 환경 변수 편집
        right_panel = QVBoxLayout()

        # 환경 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.env_name_edit = QLineEdit()
        self.env_name_edit.textChanged.connect(self.on_name_changed)
        name_layout.addWidget(self.env_name_edit)
        right_panel.addLayout(name_layout)

        # 변수 테이블
        right_panel.addWidget(QLabel("Variables:"))
        self.variables_table = KeyValueTable()
        right_panel.addWidget(self.variables_table)

        # 저장 버튼
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_current_env)
        save_btn_layout.addWidget(self.save_btn)
        right_panel.addLayout(save_btn_layout)

        # 레이아웃 조합
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(250)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        layout.addWidget(left_widget)
        layout.addWidget(right_widget, 1)

        # 하단 - 닫기 버튼
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout, 1)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def load_environments(self):
        """환경 목록 로드"""
        self.env_list.clear()

        # Global 환경 추가
        global_item = QListWidgetItem("🌍 Global")
        global_item.setData(Qt.UserRole, self.env_manager.global_environment)
        self.env_list.addItem(global_item)

        # 사용자 환경 추가
        for env in self.env_manager.environments:
            item = QListWidgetItem(env.name)
            item.setData(Qt.UserRole, env)
            self.env_list.addItem(item)

            # 활성 환경 표시
            if self.env_manager.active_environment and env.id == self.env_manager.active_environment.id:
                item.setText(f"✓ {env.name}")

        # 첫 번째 항목 선택
        if self.env_list.count() > 0:
            self.env_list.setCurrentRow(0)

    def on_env_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """환경 선택 시"""
        if not current:
            return

        # 이전 환경 저장 (자동 저장)
        if self.current_env and previous:
            self.save_current_env(show_message=False)

        # 새 환경 로드
        self.current_env = current.data(Qt.UserRole)

        if self.current_env:
            # Global 환경인 경우 이름 편집 불가
            is_global = self.current_env == self.env_manager.global_environment
            self.env_name_edit.setEnabled(not is_global)
            self.delete_env_btn.setEnabled(not is_global)

            self.env_name_edit.setText(self.current_env.name)
            self.variables_table.set_data(self.current_env.variables)

    def on_name_changed(self, text: str):
        """이름 변경 시"""
        if self.current_env and self.current_env != self.env_manager.global_environment:
            self.current_env.name = text

    def save_current_env(self, show_message=True):
        """현재 환경 저장"""
        if not self.current_env:
            return

        # 변수 저장
        self.current_env.variables = self.variables_table.get_data()

        if show_message:
            QMessageBox.information(self, "Saved", "Environment saved successfully.")

    def add_environment(self):
        """새 환경 추가"""
        from PyQt5.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "New Environment", "Environment name:")
        if ok and name:
            new_env = Environment(name)
            self.env_manager.add_environment(new_env)
            self.load_environments()

            # 새 환경 선택
            for i in range(self.env_list.count()):
                item = self.env_list.item(i)
                if item.data(Qt.UserRole) == new_env:
                    self.env_list.setCurrentItem(item)
                    break

    def delete_environment(self):
        """환경 삭제"""
        if not self.current_env or self.current_env == self.env_manager.global_environment:
            return

        reply = QMessageBox.question(self, "Delete Environment",
                                      f"Delete environment '{self.current_env.name}'?",
                                      QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.env_manager.remove_environment(self.current_env.id)
            self.current_env = None
            self.load_environments()

    def closeEvent(self, event):
        """다이얼로그 닫을 때"""
        # 현재 환경 저장
        if self.current_env:
            self.save_current_env(show_message=False)
        super().closeEvent(event)


# QWidget import 추가
from PyQt5.QtWidgets import QWidget
