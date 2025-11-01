"""
언론사 신뢰도 및 편향성 데이터
Firestore에서 동적으로 로드하며, 연결 실패 시 fallback 데이터 사용
"""
from google.cloud import firestore
from app.config import config

# Fallback 데이터 (Firestore 연결 실패 시 사용)
MEDIA_CREDIBILITY_FALLBACK = {
    # 한국 언론
    "KBS": {"credibility": 85, "bias": "중립", "country": "KR"},
    "MBC": {"credibility": 80, "bias": "중립", "country": "KR"},
    "SBS": {"credibility": 78, "bias": "중립", "country": "KR"},
    "연합뉴스": {"credibility": 90, "bias": "중립", "country": "KR"},
    "조선일보": {"credibility": 70, "bias": "보수", "country": "KR"},
    "중앙일보": {"credibility": 72, "bias": "보수", "country": "KR"},
    "한겨레": {"credibility": 75, "bias": "진보", "country": "KR"},
    "경향신문": {"credibility": 73, "bias": "진보", "country": "KR"},

    # 해외 주요 언론
    "BBC": {"credibility": 92, "bias": "중립", "country": "UK"},
    "Reuters": {"credibility": 95, "bias": "중립", "country": "UK"},
    "AP": {"credibility": 94, "bias": "중립", "country": "US"},
    "CNN": {"credibility": 75, "bias": "중도좌파", "country": "US"},
    "Fox News": {"credibility": 65, "bias": "보수", "country": "US"},
    "New York Times": {"credibility": 88, "bias": "중도좌파", "country": "US"},
    "The Guardian": {"credibility": 85, "bias": "중도좌파", "country": "UK"},
    "Al Jazeera": {"credibility": 80, "bias": "중립", "country": "QA"},
    "NHK": {"credibility": 88, "bias": "중립", "country": "JP"},
    "Deutsche Welle": {"credibility": 87, "bias": "중립", "country": "DE"},
    "Le Monde": {"credibility": 86, "bias": "중도좌파", "country": "FR"},
}

# Firestore 클라이언트 초기화
db = None
try:
    db = firestore.Client(project=config.GCP_PROJECT)
    print("✅ (Media) Firestore 연결 성공")
except Exception as e:
    print(f"⚠️ (Media) Firestore 연결 실패, fallback 데이터 사용: {e}")

# 메모리 캐시 (Firestore 조회 최소화)
_media_cache = {}
_cache_loaded = False


def _load_media_from_firestore():
    """Firestore에서 모든 언론사 정보를 로드하여 캐시"""
    global _media_cache, _cache_loaded

    if _cache_loaded:
        return

    if not db:
        print("⚠️ Firestore 미연결, fallback 데이터 사용")
        _media_cache = MEDIA_CREDIBILITY_FALLBACK.copy()
        _cache_loaded = True
        return

    try:
        # Firestore의 'media_credibility' 컬렉션에서 모든 문서 로드
        docs = db.collection('media_credibility').stream()

        for doc in docs:
            data = doc.to_dict()
            _media_cache[doc.id] = {
                'credibility': data.get('credibility', 50),
                'bias': data.get('bias', '알 수 없음'),
                'country': data.get('country', 'Unknown')
            }

        if _media_cache:
            print(f"✅ Firestore에서 {len(_media_cache)}개 언론사 정보 로드")
        else:
            print("⚠️ Firestore에 언론사 데이터 없음, fallback 사용")
            _media_cache = MEDIA_CREDIBILITY_FALLBACK.copy()

        _cache_loaded = True

    except Exception as e:
        print(f"⚠️ Firestore 로드 실패, fallback 사용: {e}")
        _media_cache = MEDIA_CREDIBILITY_FALLBACK.copy()
        _cache_loaded = True


def get_media_credibility(source_name):
    """언론사 이름으로 신뢰도 정보 가져오기 (Firestore 우선, fallback 지원)"""
    # 캐시 로드 (최초 1회만 실행)
    if not _cache_loaded:
        _load_media_from_firestore()

    if not source_name:
        return {"credibility": 50, "bias": "알 수 없음", "country": "Unknown"}

    # 정확한 매칭
    if source_name in _media_cache:
        return _media_cache[source_name]

    # 부분 매칭 (예: "BBC News" → "BBC")
    for media, info in _media_cache.items():
        if media.lower() in source_name.lower():
            return info

    # 기본값 (알 수 없는 언론사)
    return {"credibility": 50, "bias": "알 수 없음", "country": "Unknown"}


def get_all_media():
    """모든 언론사 정보 반환"""
    if not _cache_loaded:
        _load_media_from_firestore()
    return _media_cache.copy()


def reload_media_cache():
    """캐시 강제 새로고침 (관리 목적)"""
    global _cache_loaded
    _cache_loaded = False
    _load_media_from_firestore()
    return len(_media_cache)
