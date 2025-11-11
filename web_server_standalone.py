#!/usr/bin/env python3
"""
Lumina Web Server - Standalone Mode

웹 서버만 단독으로 실행하는 스크립트
데스크톱 앱 없이 브라우저에서만 사용할 수 있습니다.
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.web_server import main

if __name__ == '__main__':
    print("=" * 60)
    print("✨ Lumina Web Server - Standalone Mode")
    print("=" * 60)
    print()
    print("Access the web interface at:")
    print("  http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    main()
