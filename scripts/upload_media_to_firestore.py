#!/usr/bin/env python3
"""
Firestore에 언론사 신뢰도 초기 데이터를 업로드하는 스크립트

사용법:
    python scripts/upload_media_to_firestore.py
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore
from app.config import config
from app.models.media import MEDIA_CREDIBILITY_FALLBACK


def upload_media_data():
    """Fallback 데이터를 Firestore에 업로드"""
    try:
        # Firestore 클라이언트 초기화
        db = firestore.Client(project=config.GCP_PROJECT)
        print(f"✅ Firestore 연결 성공 (프로젝트: {config.GCP_PROJECT})")

        collection_ref = db.collection('media_credibility')

        # 기존 데이터 확인
        existing_docs = list(collection_ref.stream())
        print(f"\n📊 기존 데이터: {len(existing_docs)}개 언론사")

        # 사용자 확인
        if existing_docs:
            response = input(
                "\n⚠️ 기존 데이터가 존재합니다. 덮어쓰시겠습니까? (y/N): "
            )
            if response.lower() != 'y':
                print("❌ 업로드 취소")
                return

        # 데이터 업로드
        print(f"\n📤 {len(MEDIA_CREDIBILITY_FALLBACK)}개 언론사 데이터 업로드 중...")
        success_count = 0
        fail_count = 0

        for media_name, info in MEDIA_CREDIBILITY_FALLBACK.items():
            try:
                collection_ref.document(media_name).set({
                    'credibility': info['credibility'],
                    'bias': info['bias'],
                    'country': info['country']
                })
                success_count += 1
                print(f"  ✓ {media_name}: {info}")
            except Exception as e:
                fail_count += 1
                print(f"  ✗ {media_name} 실패: {e}")

        print(f"\n{'='*60}")
        print(f"✅ 업로드 완료!")
        print(f"  - 성공: {success_count}개")
        print(f"  - 실패: {fail_count}개")
        print(f"{'='*60}")

        # 확인
        print("\n🔍 업로드 확인 중...")
        uploaded_docs = list(collection_ref.stream())
        print(f"✅ Firestore에 저장된 언론사: {len(uploaded_docs)}개")

        return success_count

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n💡 확인 사항:")
        print("  1. GCP_PROJECT 환경 변수가 설정되어 있는지 확인")
        print("  2. Google Cloud 인증이 완료되었는지 확인")
        print("     (gcloud auth application-default login)")
        print("  3. Firestore API가 활성화되어 있는지 확인")
        return 0


def view_current_data():
    """현재 Firestore에 저장된 데이터 조회"""
    try:
        db = firestore.Client(project=config.GCP_PROJECT)
        docs = db.collection('media_credibility').stream()

        print(f"\n{'='*60}")
        print("📋 현재 Firestore에 저장된 언론사 목록")
        print(f"{'='*60}\n")

        count = 0
        for doc in docs:
            data = doc.to_dict()
            print(
                f"{doc.id:20s} | 신뢰도: {data.get('credibility', 0):3d} | "
                f"편향: {data.get('bias', 'N/A'):10s} | 국가: {data.get('country', 'N/A')}"
            )
            count += 1

        print(f"\n총 {count}개 언론사")

    except Exception as e:
        print(f"❌ 조회 실패: {e}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Firestore 언론사 데이터 관리')
    parser.add_argument(
        '--view',
        action='store_true',
        help='현재 저장된 데이터만 조회 (업로드 안함)',
    )

    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════╗
║     Firestore 언론사 신뢰도 데이터 업로드 도구           ║
╚══════════════════════════════════════════════════════════╝
    """)

    if args.view:
        view_current_data()
    else:
        upload_media_data()
