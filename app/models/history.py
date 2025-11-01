"""
분석 히스토리 관리 (Firestore)
사용자가 분석한 콘텐츠 기록 저장 및 조회
"""
import hashlib
from datetime import datetime, timedelta
from google.cloud import firestore
from app.config import config

# Firestore 클라이언트
db = None
try:
    db = firestore.Client(project=config.GCP_PROJECT)
    print("✅ (History) Firestore 연결 성공")
except Exception as e:
    print(f"⚠️ (History) Firestore 연결 실패: {e}")


def _get_url_hash(url: str) -> str:
    """URL을 해시로 변환 (문서 ID로 사용)"""
    return hashlib.md5(url.encode()).hexdigest()


def save_analysis_history(url: str, input_type: str, analysis_result: dict, user_id: str = "anonymous"):
    """
    분석 히스토리 저장

    Args:
        url: 분석한 URL
        input_type: 콘텐츠 타입 (youtube, article)
        analysis_result: 분석 결과
        user_id: 사용자 ID (현재는 anonymous, 향후 로그인 기능 추가 시 사용)
    """
    if not db:
        print("⚠️ Firestore 미연결, 히스토리 저장 실패")
        return False

    try:
        url_hash = _get_url_hash(url)
        doc_ref = db.collection('analysis_history').document(url_hash)

        # 기존 문서 확인
        doc = doc_ref.get()

        if doc.exists:
            # 기존 문서가 있으면 조회수 증가
            doc_ref.update({
                'view_count': firestore.Increment(1),
                'last_analyzed_at': datetime.now(),
                'last_user_id': user_id
            })
            print(f"✅ 히스토리 업데이트: {url[:50]}... (조회수 +1)")
        else:
            # 새 문서 생성
            doc_ref.set({
                'url': url,
                'url_hash': url_hash,
                'input_type': input_type,
                'title': analysis_result.get('summary', '')[:100],  # 요약의 일부를 제목으로
                'key_claims': analysis_result.get('key_claims', []),
                'topics': analysis_result.get('topics', []),
                'related_countries': analysis_result.get('related_countries', []),
                'view_count': 1,
                'created_at': datetime.now(),
                'last_analyzed_at': datetime.now(),
                'created_by': user_id,
                'last_user_id': user_id
            })
            print(f"✅ 히스토리 저장: {url[:50]}...")

        return True

    except Exception as e:
        print(f"⚠️ 히스토리 저장 실패: {e}")
        return False


def get_recent_history(limit: int = 20, input_type: str = None):
    """
    최근 분석 히스토리 조회

    Args:
        limit: 조회할 최대 개수
        input_type: 필터링할 콘텐츠 타입 (None이면 전체)

    Returns:
        최근 분석 목록
    """
    if not db:
        return []

    try:
        query = db.collection('analysis_history').order_by(
            'last_analyzed_at', direction=firestore.Query.DESCENDING
        ).limit(limit)

        if input_type:
            query = query.where('input_type', '==', input_type)

        docs = query.stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append({
                'url': data.get('url'),
                'url_hash': data.get('url_hash'),
                'input_type': data.get('input_type'),
                'title': data.get('title', '제목 없음'),
                'topics': data.get('topics', []),
                'view_count': data.get('view_count', 0),
                'last_analyzed_at': data.get('last_analyzed_at'),
            })

        print(f"✅ 최근 히스토리 {len(results)}개 조회")
        return results

    except Exception as e:
        print(f"⚠️ 히스토리 조회 실패: {e}")
        return []


def get_popular_content(limit: int = 10, days: int = 7, input_type: str = None):
    """
    인기 콘텐츠 조회 (조회수 기준)

    Args:
        limit: 조회할 최대 개수
        days: 최근 며칠 이내 (0이면 전체 기간)
        input_type: 필터링할 콘텐츠 타입

    Returns:
        인기 콘텐츠 목록
    """
    if not db:
        return []

    try:
        query = db.collection('analysis_history').order_by(
            'view_count', direction=firestore.Query.DESCENDING
        ).limit(limit)

        # 기간 필터
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.where('last_analyzed_at', '>=', cutoff_date)

        # 타입 필터
        if input_type:
            query = query.where('input_type', '==', input_type)

        docs = query.stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append({
                'url': data.get('url'),
                'url_hash': data.get('url_hash'),
                'input_type': data.get('input_type'),
                'title': data.get('title', '제목 없음'),
                'topics': data.get('topics', []),
                'view_count': data.get('view_count', 0),
                'last_analyzed_at': data.get('last_analyzed_at'),
            })

        print(f"✅ 인기 콘텐츠 {len(results)}개 조회")
        return results

    except Exception as e:
        print(f"⚠️ 인기 콘텐츠 조회 실패: {e}")
        return []


def get_history_by_topic(topic: str, limit: int = 20):
    """
    특정 주제로 분석 히스토리 검색

    Args:
        topic: 검색할 주제
        limit: 조회할 최대 개수

    Returns:
        해당 주제의 분석 목록
    """
    if not db:
        return []

    try:
        query = db.collection('analysis_history').where(
            'topics', 'array_contains', topic
        ).order_by(
            'last_analyzed_at', direction=firestore.Query.DESCENDING
        ).limit(limit)

        docs = query.stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append({
                'url': data.get('url'),
                'url_hash': data.get('url_hash'),
                'input_type': data.get('input_type'),
                'title': data.get('title', '제목 없음'),
                'topics': data.get('topics', []),
                'view_count': data.get('view_count', 0),
                'last_analyzed_at': data.get('last_analyzed_at'),
            })

        print(f"✅ 주제별 히스토리 {len(results)}개 조회 (주제: {topic})")
        return results

    except Exception as e:
        print(f"⚠️ 주제별 히스토리 조회 실패: {e}")
        return []


def get_statistics():
    """
    전체 통계 조회

    Returns:
        총 분석 수, 총 조회수 등
    """
    if not db:
        return {
            'total_analyses': 0,
            'total_views': 0,
            'youtube_count': 0,
            'article_count': 0
        }

    try:
        docs = db.collection('analysis_history').stream()

        total_analyses = 0
        total_views = 0
        youtube_count = 0
        article_count = 0

        for doc in docs:
            data = doc.to_dict()
            total_analyses += 1
            total_views += data.get('view_count', 0)

            if data.get('input_type') == 'youtube':
                youtube_count += 1
            elif data.get('input_type') == 'article':
                article_count += 1

        return {
            'total_analyses': total_analyses,
            'total_views': total_views,
            'youtube_count': youtube_count,
            'article_count': article_count
        }

    except Exception as e:
        print(f"⚠️ 통계 조회 실패: {e}")
        return {
            'total_analyses': 0,
            'total_views': 0,
            'youtube_count': 0,
            'article_count': 0
        }
