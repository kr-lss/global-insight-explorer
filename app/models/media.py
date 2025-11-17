"""
언론사 기본 정보
국가별 대표 방송사/신문사 목록 (공영/민영 구분)
추후 Firestore로 이전 예정
"""

# 국가별 언론사 정보 (임시 데이터 - 내일 Firestore로 이전)
MEDIA_DATA = {
    "US": {
        "name": "미국",
        "broadcasting": [
            {"name": "PBS", "type": "공영"},
            {"name": "NBC", "type": "민영"},
            {"name": "ABC", "type": "민영"},
            {"name": "CBS", "type": "민영"},
        ],
        "newspapers": [
            {"name": "The New York Times", "type": "민영"},
            {"name": "Washington Post", "type": "민영"},
        ],
    },
    "UK": {
        "name": "영국",
        "broadcasting": [
            {"name": "BBC", "type": "공영"},
            {"name": "Sky News", "type": "민영"},
        ],
        "newspapers": [
            {"name": "The Guardian", "type": "민영"},
            {"name": "The Times", "type": "민영"},
        ],
    },
    "FR": {
        "name": "프랑스",
        "broadcasting": [
            {"name": "France 2", "type": "공영"},
            {"name": "TF1", "type": "민영"},
            {"name": "France 24", "type": "공영"},
        ],
        "newspapers": [
            {"name": "Le Monde", "type": "민영"},
            {"name": "Le Figaro", "type": "민영"},
        ],
    },
    "DE": {
        "name": "독일",
        "broadcasting": [
            {"name": "ARD", "type": "공영"},
            {"name": "ZDF", "type": "공영"},
            {"name": "DW", "type": "공영"},
        ],
        "newspapers": [
            {"name": "Süddeutsche Zeitung", "type": "민영"},
            {"name": "Bild", "type": "민영"},
        ],
    },
    "JP": {
        "name": "일본",
        "broadcasting": [
            {"name": "NHK", "type": "공영"},
            {"name": "NTV", "type": "민영"},
        ],
        "newspapers": [
            {"name": "Asahi Shimbun", "type": "민영"},
            {"name": "Yomiuri Shimbun", "type": "민영"},
        ],
    },
    "CN": {
        "name": "중국",
        "broadcasting": [
            {"name": "CCTV", "type": "공영"},
            {"name": "CGTN", "type": "공영"},
        ],
        "newspapers": [
            {"name": "People's Daily", "type": "공영"},
            {"name": "인민일보", "type": "공영"},
        ],
    },
    "RU": {
        "name": "러시아",
        "broadcasting": [
            {"name": "Первый канал", "type": "공영"},
            {"name": "Россия-1", "type": "공영"},
            {"name": "RT", "type": "공영"},
        ],
        "newspapers": [
            {"name": "Izvestia", "type": "민영"},
            {"name": "Kommersant", "type": "민영"},
        ],
    },
    "CA": {
        "name": "캐나다",
        "broadcasting": [
            {"name": "CBC", "type": "공영"},
            {"name": "Radio-Canada", "type": "공영"},
            {"name": "CTV", "type": "민영"},
        ],
        "newspapers": [
            {"name": "The Globe and Mail", "type": "민영"},
            {"name": "Toronto Star", "type": "민영"},
        ],
    },
    "KR": {
        "name": "대한민국",
        "broadcasting": [
            {"name": "KBS", "type": "공영"},
            {"name": "MBC", "type": "공영"},
            {"name": "SBS", "type": "민영"},
        ],
        "newspapers": [
            {"name": "조선일보", "type": "민영"},
            {"name": "중앙일보", "type": "민영"},
            {"name": "한겨레", "type": "민영"},
            {"name": "경향신문", "type": "민영"},
            {"name": "연합뉴스", "type": "공영"},
        ],
    },
}


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
    return MEDIA_DATA.get(country_code)


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
    for country_code, country_data in MEDIA_DATA.items():
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

    return None


def get_all_countries():
    """모든 국가 목록 조회"""
    return [
        {"code": code, "name": data["name"]}
        for code, data in MEDIA_DATA.items()
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
