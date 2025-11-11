"""
좌측 요청 트리 위젯
"""
from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QMenu, QAction,
                              QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from models.request_model import RequestModel, RequestFolder, HttpMethod
from typing import Optional


class RequestTreeWidget(QTreeWidget):
    """요청 트리 위젯"""

    # 시그널 정의
    request_selected = pyqtSignal(RequestModel)  # 요청이 선택되었을 때
    request_changed = pyqtSignal()  # 트리 구조가 변경되었을 때

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_folder: Optional[RequestFolder] = None

        self.setup_ui()
        self.setup_context_menu()

    def setup_ui(self):
        """UI 초기화"""
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemClicked.connect(self.on_item_clicked)

    def setup_context_menu(self):
        """컨텍스트 메뉴 설정"""
        pass  # show_context_menu에서 동적으로 생성

    def load_folder(self, folder: RequestFolder):
        """폴더 구조 로드"""
        self.root_folder = folder
        self.clear()
        self._add_folder_items(folder, self.invisibleRootItem())
        self.expandAll()

    def _add_folder_items(self, folder: RequestFolder, parent_item: QTreeWidgetItem):
        """재귀적으로 폴더와 요청 추가"""
        # 하위 폴더 추가
        for sub_folder in folder.folders:
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, f"📁 {sub_folder.name}")
            folder_item.setData(0, Qt.UserRole, {"type": "folder", "data": sub_folder})

            # 폴더 텍스트를 굵게
            font = folder_item.font(0)
            font.setBold(True)
            folder_item.setFont(0, font)

            # 재귀 호출
            self._add_folder_items(sub_folder, folder_item)

        # 요청 추가
        for request in folder.requests:
            request_item = QTreeWidgetItem(parent_item)
            method_label = self._get_method_label(request.method)
            request_item.setText(0, f"{method_label} {request.name}")
            request_item.setData(0, Qt.UserRole, {"type": "request", "data": request})

    def _get_method_label(self, method: HttpMethod) -> str:
        """HTTP 메서드 라벨"""
        labels = {
            HttpMethod.GET: "[GET]",
            HttpMethod.POST: "[POST]",
            HttpMethod.PUT: "[PUT]",
            HttpMethod.DELETE: "[DEL]",
            HttpMethod.PATCH: "[PATCH]",
            HttpMethod.HEAD: "[HEAD]",
            HttpMethod.OPTIONS: "[OPT]",
        }
        return labels.get(method, "[???]")

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """아이템 클릭 시"""
        data = item.data(0, Qt.UserRole)
        if data and data["type"] == "request":
            request = data["data"]
            self.request_selected.emit(request)

    def show_context_menu(self, position):
        """컨텍스트 메뉴 표시"""
        item = self.itemAt(position)
        menu = QMenu(self)

        if item:
            data = item.data(0, Qt.UserRole)
            if data:
                if data["type"] == "folder":
                    # 폴더 메뉴
                    add_request_action = QAction("새 요청 추가", self)
                    add_request_action.triggered.connect(lambda: self.add_new_request(item))
                    menu.addAction(add_request_action)

                    add_folder_action = QAction("새 폴더 추가", self)
                    add_folder_action.triggered.connect(lambda: self.add_new_folder(item))
                    menu.addAction(add_folder_action)

                    menu.addSeparator()

                    rename_action = QAction("이름 변경", self)
                    rename_action.triggered.connect(lambda: self.rename_folder(item))
                    menu.addAction(rename_action)

                    delete_action = QAction("폴더 삭제", self)
                    delete_action.triggered.connect(lambda: self.delete_folder(item))
                    menu.addAction(delete_action)

                elif data["type"] == "request":
                    # 요청 메뉴
                    duplicate_action = QAction("복제", self)
                    duplicate_action.triggered.connect(lambda: self.duplicate_request(item))
                    menu.addAction(duplicate_action)

                    rename_action = QAction("이름 변경", self)
                    rename_action.triggered.connect(lambda: self.rename_request(item))
                    menu.addAction(rename_action)

                    menu.addSeparator()

                    delete_action = QAction("삭제", self)
                    delete_action.triggered.connect(lambda: self.delete_request(item))
                    menu.addAction(delete_action)
        else:
            # 빈 영역 - 루트에 추가
            add_request_action = QAction("새 요청 추가", self)
            add_request_action.triggered.connect(lambda: self.add_new_request(None))
            menu.addAction(add_request_action)

            add_folder_action = QAction("새 폴더 추가", self)
            add_folder_action.triggered.connect(lambda: self.add_new_folder(None))
            menu.addAction(add_folder_action)

        menu.exec_(self.viewport().mapToGlobal(position))

    def add_new_request(self, parent_item: Optional[QTreeWidgetItem]):
        """새 요청 추가"""
        name, ok = QInputDialog.getText(self, "새 요청", "요청 이름:")
        if ok and name:
            new_request = RequestModel(name)

            # 부모 폴더 찾기
            if parent_item:
                data = parent_item.data(0, Qt.UserRole)
                if data and data["type"] == "folder":
                    folder = data["data"]
                    folder.add_request(new_request)
            else:
                # 루트 폴더에 추가
                if self.root_folder:
                    self.root_folder.add_request(new_request)

            # UI 갱신
            self.load_folder(self.root_folder)
            self.request_changed.emit()

    def add_new_folder(self, parent_item: Optional[QTreeWidgetItem]):
        """새 폴더 추가"""
        name, ok = QInputDialog.getText(self, "새 폴더", "폴더 이름:")
        if ok and name:
            new_folder = RequestFolder(name)

            # 부모 폴더 찾기
            if parent_item:
                data = parent_item.data(0, Qt.UserRole)
                if data and data["type"] == "folder":
                    folder = data["data"]
                    folder.add_folder(new_folder)
            else:
                # 루트 폴더에 추가
                if self.root_folder:
                    self.root_folder.add_folder(new_folder)

            # UI 갱신
            self.load_folder(self.root_folder)
            self.request_changed.emit()

    def duplicate_request(self, item: QTreeWidgetItem):
        """요청 복제"""
        data = item.data(0, Qt.UserRole)
        if data and data["type"] == "request":
            original = data["data"]
            cloned = original.clone()

            # 같은 폴더에 추가
            parent_item = item.parent()
            if parent_item:
                parent_data = parent_item.data(0, Qt.UserRole)
                if parent_data and parent_data["type"] == "folder":
                    folder = parent_data["data"]
                    folder.add_request(cloned)
            else:
                if self.root_folder:
                    self.root_folder.add_request(cloned)

            # UI 갱신
            self.load_folder(self.root_folder)
            self.request_changed.emit()

    def rename_request(self, item: QTreeWidgetItem):
        """요청 이름 변경"""
        data = item.data(0, Qt.UserRole)
        if data and data["type"] == "request":
            request = data["data"]
            name, ok = QInputDialog.getText(self, "이름 변경", "새 이름:", text=request.name)
            if ok and name:
                request.name = name
                self.load_folder(self.root_folder)
                self.request_changed.emit()

    def rename_folder(self, item: QTreeWidgetItem):
        """폴더 이름 변경"""
        data = item.data(0, Qt.UserRole)
        if data and data["type"] == "folder":
            folder = data["data"]
            name, ok = QInputDialog.getText(self, "이름 변경", "새 이름:", text=folder.name)
            if ok and name:
                folder.name = name
                self.load_folder(self.root_folder)
                self.request_changed.emit()

    def delete_request(self, item: QTreeWidgetItem):
        """요청 삭제"""
        reply = QMessageBox.question(self, "삭제 확인", "이 요청을 삭제하시겠습니까?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            data = item.data(0, Qt.UserRole)
            if data and data["type"] == "request":
                request = data["data"]

                # 부모 폴더에서 제거
                parent_item = item.parent()
                if parent_item:
                    parent_data = parent_item.data(0, Qt.UserRole)
                    if parent_data and parent_data["type"] == "folder":
                        folder = parent_data["data"]
                        folder.remove_request(request.id)
                else:
                    if self.root_folder:
                        self.root_folder.remove_request(request.id)

                # UI 갱신
                self.load_folder(self.root_folder)
                self.request_changed.emit()

    def delete_folder(self, item: QTreeWidgetItem):
        """폴더 삭제"""
        reply = QMessageBox.question(self, "삭제 확인",
                                      "이 폴더와 하위 항목을 모두 삭제하시겠습니까?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            data = item.data(0, Qt.UserRole)
            if data and data["type"] == "folder":
                folder = data["data"]

                # 부모 폴더에서 제거
                parent_item = item.parent()
                if parent_item:
                    parent_data = parent_item.data(0, Qt.UserRole)
                    if parent_data and parent_data["type"] == "folder":
                        parent_folder = parent_data["data"]
                        parent_folder.remove_folder(folder.id)
                else:
                    if self.root_folder:
                        self.root_folder.remove_folder(folder.id)

                # UI 갱신
                self.load_folder(self.root_folder)
                self.request_changed.emit()
