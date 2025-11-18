"""
언론사 데이터를 Firestore에 업로드하는 스크립트
JSON 파일을 읽어서 Firestore의 'countries' 컬렉션에 저장

사용법:
    python scripts/upload_media_to_firestore.py
"""
import json
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.cloud import firestore
from app.config import config


def upload_media_data():
    """JSON 파일을 읽어서 Firestore에 업로드"""

    # Firestore 클라이언트 초기화
    print("🔌 Firestore 연결 중...")
    db = firestore.Client(project=config.GCP_PROJECT)
    print(f"✅ Firestore 연결 성공: {config.GCP_PROJECT}")

    # JSON 파일 읽기
    json_path = project_root / "data" / "media_countries.json"
    print(f"\n📂 JSON 파일 읽는 중: {json_path}")

    if not json_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        media_data = json.load(f)

    print(f"✅ {len(media_data)}개 국가 데이터 로드 완료")

    # Firestore에 업로드
    print("\n⬆️ Firestore에 업로드 중...")
    collection = db.collection('countries')

    uploaded = 0
    for country_code, country_info in media_data.items():
        try:
            # 문서 ID를 국가 코드로 사용
            doc_ref = collection.document(country_code)
            doc_ref.set(country_info)

            broadcasting_count = len(country_info.get('broadcasting', []))
            newspapers_count = len(country_info.get('newspapers', []))

            print(f"  ✓ {country_code} ({country_info['name']}): "
                  f"방송 {broadcasting_count}개, 신문 {newspapers_count}개")
            uploaded += 1

        except Exception as e:
            print(f"  ✗ {country_code} 업로드 실패: {e}")

    print(f"\n🎉 완료! {uploaded}/{len(media_data)}개 국가 업로드 성공")

    # 업로드 확인
    print("\n🔍 업로드 확인 중...")
    verify_upload(db)


def verify_upload(db):
    """업로드된 데이터 확인"""
    try:
        docs = db.collection('countries').stream()
        countries = []

        for doc in docs:
            data = doc.to_dict()
            countries.append(f"{doc.id} ({data.get('name', 'Unknown')})")

        print(f"✅ Firestore에 저장된 국가: {len(countries)}개")
        for country in sorted(countries):
            print(f"  - {country}")

    except Exception as e:
        print(f"❌ 확인 실패: {e}")


def delete_all_data():
    """기존 데이터 전체 삭제 (주의!)"""
    print("\n⚠️ 경고: 기존 데이터를 모두 삭제합니다!")
    confirm = input("계속하시겠습니까? (yes/no): ")

    if confirm.lower() != 'yes':
        print("❌ 취소됨")
        return

    db = firestore.Client(project=config.GCP_PROJECT)
    collection = db.collection('countries')

    deleted = 0
    docs = collection.stream()
    for doc in docs:
        doc.reference.delete()
        deleted += 1
        print(f"  🗑️ 삭제: {doc.id}")

    print(f"\n✅ {deleted}개 문서 삭제 완료")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Firestore 언론사 데이터 관리')
    parser.add_argument(
        '--delete',
        action='store_true',
        help='기존 데이터 전체 삭제'
    )

    args = parser.parse_args()

    if args.delete:
        delete_all_data()
    else:
        upload_media_data()
