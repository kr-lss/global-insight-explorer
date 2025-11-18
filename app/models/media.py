"""
언론사 기본 정보
국가별 대표 방송사/신문사 목록 (공영/민영 구분)
Firestore에서 동적으로 로드
"""
from google.cloud import firestore
from app.config import config

# Firestore 클라이언트 초기화
db = None
try:
    db = firestore.Client(project=config.GCP_PROJECT)
    print("✅ (Media) Firestore 연결 성공")
except Exception as e:
    print(f"⚠️ (Media) Firestore 연결 실패: {e}")

# 메모리 캐시 (Firestore 조회 최소화)
_media_cache = {}
_cache_loaded = False


def _load_media_from_firestore():
    """Firestore에서 모든 국가 언론사 정보를 로드하여 캐시"""
    global _media_cache, _cache_loaded

    if _cache_loaded:
        return

    if not db:
        print("⚠️ Firestore 미연결, 빈 캐시 사용")
        _cache_loaded = True
        return

    try:
        # Firestore의 'countries' 컬렉션에서 모든 문서 로드
        docs = db.collection('countries').stream()

        for doc in docs:
            _media_cache[doc.id] = doc.to_dict()

        if _media_cache:
            print(f"✅ Firestore에서 {len(_media_cache)}개 국가 정보 로드")
        else:
            print("⚠️ Firestore에 국가 데이터 없음")

        _cache_loaded = True

    except Exception as e:
        print(f"⚠️ Firestore 로드 실패: {e}")
        _cache_loaded = True


def get_country_media(country_code):
    """
    국가별 언론사 정보 조회

    Args:
        country_code: 국가 코드 (예: "US", "KR")

    Returns:
        {
            "name": "국가명",
            "broadcasting": [{"name": "방송사명", "type": "공영/민영"}],
            "newspapers": [{"name": "신문사명", "type": "공영/민영"}]
        }
    """
    # 캐시 로드 (최초 1회만 실행)
    if not _cache_loaded:
        _load_media_from_firestore()

    return _media_cache.get(country_code)


def get_media_info(source_name):
    """
    특정 언론사 정보 조회

    Args:
        source_name: 언론사 이름

    Returns:
        {
            "name": "언론사명",
            "type": "공영/민영",
            "category": "broadcasting/newspaper",
            "country": "국가코드"
        }
        또는 None (찾지 못한 경우)
    """
    # 캐시 로드
    if not _cache_loaded:
        _load_media_from_firestore()

    # 정확한 매칭
    for country_code, country_data in _media_cache.items():
        # 방송사에서 찾기
        for media in country_data.get("broadcasting", []):
            if media["name"] == source_name:
                return {
                    "name": media["name"],
                    "type": media["type"],
                    "category": "broadcasting",
                    "country": country_code,
                }

        # 신문사에서 찾기
        for media in country_data.get("newspapers", []):
            if media["name"] == source_name:
                return {
                    "name": media["name"],
                    "type": media["type"],
                    "category": "newspaper",
                    "country": country_code,
                }

    # 부분 매칭 (예: "BBC News" → "BBC")
    source_lower = source_name.lower()
    for country_code, country_data in _media_cache.items():
        # 방송사에서 부분 매칭
        for media in country_data.get("broadcasting", []):
            if media["name"].lower() in source_lower or source_lower in media["name"].lower():
                return {
                    "name": media["name"],
                    "type": media["type"],
                    "category": "broadcasting",
                    "country": country_code,
                }

        # 신문사에서 부분 매칭
        for media in country_data.get("newspapers", []):
            if media["name"].lower() in source_lower or source_lower in media["name"].lower():
                return {
                    "name": media["name"],
                    "type": media["type"],
                    "category": "newspaper",
                    "country": country_code,
                }

    return None


def get_all_countries():
    """모든 국가 목록 조회"""
    if not _cache_loaded:
        _load_media_from_firestore()

    return [
        {"code": code, "name": data.get("name", "Unknown")}
        for code, data in _media_cache.items()
    ]


def get_all_media_by_country(country_code):
    """국가별 전체 언론사 목록 (방송사 + 신문사)"""
    country = get_country_media(country_code)
    if not country:
        return []

    all_media = []

    # 방송사 추가
    for media in country.get("broadcasting", []):
        all_media.append({
            **media,
            "category": "broadcasting",
            "country": country_code,
        })

    # 신문사 추가
    for media in country.get("newspapers", []):
        all_media.append({
            **media,
            "category": "newspaper",
            "country": country_code,
        })

    return all_media


def reload_media_cache():
    """캐시 강제 새로고침 (관리 목적)"""
    global _cache_loaded
    _cache_loaded = False
    _media_cache.clear()
    _load_media_from_firestore()
    return len(_media_cache)


# 하위 호환성을 위한 함수 (기존 코드가 호출하는 경우)
def get_media_credibility(source_name):
    """
    기존 코드 호환용 함수
    credibility, bias는 제거되었으므로 기본 정보만 반환
    """
    media_info = get_media_info(source_name)

    if media_info:
        return {
            "country": media_info["country"],
            "type": media_info["type"],
            "category": media_info["category"],
            # 기존 코드 호환을 위해 기본값 제공
            "credibility": 70,  # 임시 기본값
            "bias": "알 수 없음",
        }

    # 찾지 못한 경우 기본값
    return {
        "country": "Unknown",
        "type": "알 수 없음",
        "category": "알 수 없음",
        "credibility": 50,
        "bias": "알 수 없음",
    }
