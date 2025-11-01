#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로젝트 구조 및 모듈 검증 스크립트
의존성 설치 없이 구문 체크만 수행
"""
import os
import sys
import io
import py_compile
from pathlib import Path

# Windows 콘솔 UTF-8 출력 지원
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent


def check_file_exists(file_path, description):
    """파일 존재 확인"""
    full_path = PROJECT_ROOT / file_path
    if full_path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} 없음: {file_path}")
        return False


def check_syntax(file_path):
    """Python 파일 구문 검증"""
    full_path = PROJECT_ROOT / file_path
    try:
        py_compile.compile(str(full_path), doraise=True)
        print(f"  ✅ 구문 OK")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ❌ 구문 오류: {e}")
        return False


def main():
    print("=" * 60)
    print("프로젝트 구조 및 모듈 검증")
    print("=" * 60)

    all_passed = True

    # 1. 핵심 파일 존재 확인
    print("\n[1] 핵심 파일 존재 확인")
    print("-" * 60)

    core_files = [
        ("requirements.txt", "의존성 파일"),
        ("app/main.py", "메인 진입점"),
        ("app/config.py", "설정 파일"),
        ("frontend/index.html", "웹 UI"),
        ("frontend/main.js", "JavaScript"),
        ("frontend/main.css", "스타일시트"),
    ]

    for file_path, desc in core_files:
        if not check_file_exists(file_path, desc):
            all_passed = False

    # 2. 모델 파일 검증
    print("\n[2] 모델 파일 검증")
    print("-" * 60)

    model_files = [
        "app/models/__init__.py",
        "app/models/media.py",
        "app/models/history.py",
        "app/models/extractor.py",
    ]

    for file_path in model_files:
        print(f"📄 {file_path}")
        if not check_file_exists(file_path, ""):
            all_passed = False
        elif not check_syntax(file_path):
            all_passed = False

    # 3. 라우트 파일 검증
    print("\n[3] 라우트 파일 검증")
    print("-" * 60)

    route_files = [
        "app/routes/__init__.py",
        "app/routes/health.py",
        "app/routes/analysis.py",
        "app/routes/media.py",
        "app/routes/history.py",
    ]

    for file_path in route_files:
        print(f"📄 {file_path}")
        if not check_file_exists(file_path, ""):
            all_passed = False
        elif not check_syntax(file_path):
            all_passed = False

    # 4. 유틸리티 파일 검증
    print("\n[4] 유틸리티 파일 검증")
    print("-" * 60)

    util_files = [
        "app/utils/__init__.py",
        "app/utils/analysis_service.py",
    ]

    for file_path in util_files:
        print(f"📄 {file_path}")
        if not check_file_exists(file_path, ""):
            all_passed = False
        elif not check_syntax(file_path):
            all_passed = False

    # 5. 스크립트 파일 검증
    print("\n[5] 스크립트 파일 검증")
    print("-" * 60)

    script_files = [
        "scripts/upload_media_to_firestore.py",
    ]

    for file_path in script_files:
        print(f"📄 {file_path}")
        if not check_file_exists(file_path, ""):
            all_passed = False
        elif not check_syntax(file_path):
            all_passed = False

    # 6. 프론트엔드 파일 검증
    print("\n[6] 프론트엔드 파일 검증")
    print("-" * 60)

    frontend_files = [
        ("frontend/index.html", "HTML"),
        ("frontend/main.js", "JavaScript"),
        ("frontend/main.css", "CSS"),
    ]

    for file_path, desc in frontend_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {desc}: {file_path} ({size} bytes)")
        else:
            print(f"❌ {desc} 없음: {file_path}")
            all_passed = False

    # 결과 출력
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 모든 검증 통과!")
        print("=" * 60)
        print("\n실행 방법:")
        print("  1. pip install -r requirements.txt")
        print("  2. python -m app.main")
        print("  3. http://127.0.0.1:8080 접속")
        return 0
    else:
        print("❌ 일부 검증 실패")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
