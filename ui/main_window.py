"""
메인 윈도우
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QSplitter, QPushButton, QComboBox, QLabel,
                              QFileDialog, QMessageBox, QToolBar, QAction,
                              QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from ui.request_tree_widget import RequestTreeWidget
from ui.request_editor_panel import RequestEditorPanel
from ui.response_panel import ResponsePanel
from ui.environment_dialog import EnvironmentDialog
from core.project_manager import ProjectManager
from core.http_client import HttpClient
from models.request_model import RequestModel
from models.response_model import ResponseModel


class RequestThread(QThread):
    """HTTP 요청을 백그라운드에서 실행하는 스레드"""

    finished = pyqtSignal(ResponseModel)

    def __init__(self, http_client: HttpClient, request: RequestModel):
        super().__init__()
        self.http_client = http_client
        self.request = request

    def run(self):
        """스레드 실행"""
        response = self.http_client.send_request(self.request)
        self.finished.emit(response)


class MainWindow(QMainWindow):
    """메인 윈도우"""

    def __init__(self):
        super().__init__()

        # 프로젝트 관리자 초기화
        self.project_manager = ProjectManager()
        self.project_manager.create_sample_project()  # 샘플 프로젝트 로드

        # HTTP 클라이언트 초기화
        self.http_client = HttpClient(self.project_manager.env_manager)

        # 현재 선택된 요청
        self.current_request: RequestModel = None

        # 요청 스레드
        self.request_thread: RequestThread = None

        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()

        # 초기 데이터 로드
        self.load_project_data()

    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Lumina ✨")
        self.resize(1400, 900)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 메인 스플리터 (좌우 분할)
        main_splitter = QSplitter(Qt.Horizontal)

        # 좌측 - 요청 트리
        self.request_tree = RequestTreeWidget()
        self.request_tree.request_selected.connect(self.on_request_selected)
        self.request_tree.request_changed.connect(self.on_request_changed)
        main_splitter.addWidget(self.request_tree)

        # 우측 - 요청 편집 및 응답 패널
        right_splitter = QSplitter(Qt.Vertical)

        # 요청 편집 패널
        self.request_editor = RequestEditorPanel()
        self.request_editor.request_updated.connect(self.on_request_updated)
        right_splitter.addWidget(self.request_editor)

        # 응답 패널
        self.response_panel = ResponsePanel()
        right_splitter.addWidget(self.response_panel)

        # 비율 설정
        right_splitter.setSizes([400, 400])

        main_splitter.addWidget(right_splitter)

        # 비율 설정 (좌측 300, 우측 1100)
        main_splitter.setSizes([300, 1100])

        layout.addWidget(main_splitter)

        # 상태바
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def setup_menu(self):
        """메뉴 설정"""
        menubar = self.menuBar()

        # File 메뉴
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        open_action = QAction("Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View 메뉴
        view_menu = menubar.addMenu("View")

        env_action = QAction("Manage Environments", self)
        env_action.triggered.connect(self.show_environment_dialog)
        view_menu.addAction(env_action)

        # Help 메뉴
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """툴바 설정"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Send 버튼
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        send_btn.clicked.connect(self.send_request)
        toolbar.addWidget(send_btn)

        toolbar.addSeparator()

        # 환경 선택
        toolbar.addWidget(QLabel("  Environment:  "))
        self.env_combo = QComboBox()
        self.env_combo.setMinimumWidth(150)
        self.env_combo.currentIndexChanged.connect(self.on_environment_changed)
        toolbar.addWidget(self.env_combo)

        # 환경 관리 버튼
        manage_env_btn = QPushButton("Manage...")
        manage_env_btn.clicked.connect(self.show_environment_dialog)
        toolbar.addWidget(manage_env_btn)

        toolbar.addSeparator()

        # 프로젝트 이름 표시
        self.project_label = QLabel()
        self.project_label.setStyleSheet("margin-left: 20px; font-weight: bold;")
        toolbar.addWidget(self.project_label)

        toolbar.addWidget(QWidget())  # 스페이서

    def load_project_data(self):
        """프로젝트 데이터 로드"""
        # 요청 트리 로드
        self.request_tree.load_folder(self.project_manager.root_folder)

        # 환경 콤보박스 로드
        self.load_environment_combo()

        # 프로젝트 이름 표시
        self.project_label.setText(f"Project: {self.project_manager.project_name}")

        # 상태바
        self.statusBar.showMessage(f"Loaded project: {self.project_manager.project_name}")

    def load_environment_combo(self):
        """환경 콤보박스 로드"""
        self.env_combo.clear()

        # No Environment 옵션
        self.env_combo.addItem("No Environment", None)

        # 환경 목록
        for env in self.project_manager.env_manager.environments:
            self.env_combo.addItem(env.name, env)

        # 활성 환경 선택
        if self.project_manager.env_manager.active_environment:
            for i in range(self.env_combo.count()):
                env = self.env_combo.itemData(i)
                if env and env.id == self.project_manager.env_manager.active_environment.id:
                    self.env_combo.setCurrentIndex(i)
                    break

    def on_request_selected(self, request: RequestModel):
        """요청 선택 시"""
        # 이전 요청 저장
        if self.current_request:
            self.request_editor.save_to_request()

        # 새 요청 로드
        self.current_request = request
        self.request_editor.load_request(request)
        self.response_panel.clear()

        self.statusBar.showMessage(f"Selected: {request.name}")

    def on_request_updated(self, request: RequestModel):
        """요청 업데이트 시"""
        # 트리 갱신 (메서드나 이름이 변경되었을 수 있음)
        self.request_tree.load_folder(self.project_manager.root_folder)

    def on_request_changed(self):
        """요청 구조 변경 시"""
        # 프로젝트 변경 표시
        self.setWindowTitle(f"Lumina ✨ - {self.project_manager.project_name} *")

    def on_environment_changed(self, index: int):
        """환경 변경 시"""
        env = self.env_combo.itemData(index)
        if env:
            self.project_manager.env_manager.set_active(env.id)
            self.statusBar.showMessage(f"Environment changed to: {env.name}")
        else:
            self.project_manager.env_manager.active_environment = None
            self.statusBar.showMessage("No environment selected")

    def send_request(self):
        """요청 전송"""
        if not self.current_request:
            QMessageBox.warning(self, "No Request", "Please select a request first.")
            return

        # 현재 편집 내용 저장
        self.request_editor.save_to_request()

        # URL 확인
        if not self.current_request.url:
            QMessageBox.warning(self, "No URL", "Please enter a URL.")
            return

        # 이전 스레드가 실행 중이면 대기
        if self.request_thread and self.request_thread.isRunning():
            self.statusBar.showMessage("Request already in progress...")
            return

        # 응답 패널 초기화
        self.response_panel.clear()

        # 상태 표시
        self.statusBar.showMessage(f"Sending {self.current_request.method.value} request to {self.current_request.url}...")

        # 백그라운드 스레드로 요청 전송
        self.request_thread = RequestThread(self.http_client, self.current_request)
        self.request_thread.finished.connect(self.on_request_finished)
        self.request_thread.start()

    def on_request_finished(self, response: ResponseModel):
        """요청 완료 시"""
        # 응답 표시
        self.response_panel.display_response(response)

        # 상태바 업데이트
        if response.is_error():
            self.statusBar.showMessage(f"Error: {response.error}")
        else:
            self.statusBar.showMessage(
                f"Response: {response.status_code} {response.status_text} | "
                f"Time: {response.elapsed_ms:.0f} ms | "
                f"Size: {response.size_bytes} bytes"
            )

    def show_environment_dialog(self):
        """환경 관리 다이얼로그 표시"""
        dialog = EnvironmentDialog(self.project_manager.env_manager, self)
        dialog.exec_()

        # 환경 콤보박스 갱신
        self.load_environment_combo()

    def new_project(self):
        """새 프로젝트"""
        reply = QMessageBox.question(self, "New Project",
                                      "Create a new project? Unsaved changes will be lost.",
                                      QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.project_manager = ProjectManager()
            self.project_manager.create_sample_project()
            self.http_client = HttpClient(self.project_manager.env_manager)
            self.current_request = None
            self.request_editor.clear()
            self.response_panel.clear()
            self.load_project_data()
            self.setWindowTitle("Lumina ✨")

    def open_project(self):
        """프로젝트 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Lumina Project (*.json)"
        )

        if file_path:
            try:
                self.project_manager = ProjectManager.load_from_file(file_path)
                self.http_client = HttpClient(self.project_manager.env_manager)
                self.current_request = None
                self.request_editor.clear()
                self.response_panel.clear()
                self.load_project_data()
                self.setWindowTitle(f"Lumina ✨ - {self.project_manager.project_name}")
                QMessageBox.information(self, "Success", "Project loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load project:\n{str(e)}")

    def save_project(self):
        """프로젝트 저장"""
        # 기본 파일명으로 저장
        file_path = f"{self.project_manager.project_name}.json"
        self.save_project_to_file(file_path)

    def save_project_as(self):
        """다른 이름으로 프로젝트 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "", "Lumina Project (*.json)"
        )

        if file_path:
            self.save_project_to_file(file_path)

    def save_project_to_file(self, file_path: str):
        """파일에 프로젝트 저장"""
        try:
            # 현재 편집 내용 저장
            if self.current_request:
                self.request_editor.save_to_request()

            self.project_manager.save_to_file(file_path)
            self.setWindowTitle(f"Lumina ✨ - {self.project_manager.project_name}")
            self.statusBar.showMessage(f"Project saved to: {file_path}")
            QMessageBox.information(self, "Success", "Project saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{str(e)}")

    def show_about(self):
        """About 다이얼로그"""
        QMessageBox.about(
            self,
            "About Lumina",
            "✨ Lumina v1.0 ✨\n\n"
            "Elegant REST API Client for Developers\n"
            "Illuminate your APIs with clarity and precision\n\n"
            "Features:\n"
            "• Multiple HTTP methods support\n"
            "• Request/Response management\n"
            "• Environment variables with {{placeholders}}\n"
            "• Authentication (Basic, Bearer, API Key)\n"
            "• Beautiful Pretty JSON formatting\n"
            "• Project sharing via JSON files\n\n"
            "Built with ❤️ using Python & PyQt5"
        )

    def closeEvent(self, event):
        """윈도우 닫기 이벤트"""
        # 현재 편집 내용 저장
        if self.current_request:
            self.request_editor.save_to_request()

        # HTTP 클라이언트 종료
        self.http_client.close()

        event.accept()
