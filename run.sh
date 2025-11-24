#!/bin/bash
# Lumina 실행 스크립트
# ✨ Elegant REST API Client

# 현재 디렉토리로 이동
cd "$(dirname "$0")"

# Python 버전 확인
python3 --version

# 의존성 확인
echo "Checking dependencies..."
pip3 show PyQt5 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "PyQt5 not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

# 프로그램 실행
echo "✨ Starting Lumina..."
python3 main.py
