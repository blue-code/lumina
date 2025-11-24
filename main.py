#!/usr/bin/env python3
"""
Lumina - Elegant REST API Client

✨ Illuminate your APIs with clarity and precision
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow


def main():
    """메인 함수"""
    # 고해상도 디스플레이 지원
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 애플리케이션 생성
    app = QApplication(sys.argv)
    app.setApplicationName("Lumina")
    app.setOrganizationName("Lumina")

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    # 이벤트 루프 실행
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
