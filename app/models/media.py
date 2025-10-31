"""
언론사 신뢰도 및 편향성 데이터
"""

MEDIA_CREDIBILITY = {
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


def get_media_credibility(source_name):
    """언론사 이름으로 신뢰도 정보 가져오기"""
    if not source_name:
        return {"credibility": 50, "bias": "알 수 없음", "country": "Unknown"}

    # 정확한 매칭
    if source_name in MEDIA_CREDIBILITY:
        return MEDIA_CREDIBILITY[source_name]

    # 부분 매칭 (예: "BBC News" → "BBC")
    for media, info in MEDIA_CREDIBILITY.items():
        if media.lower() in source_name.lower():
            return info

    # 기본값 (알 수 없는 언론사)
    return {"credibility": 50, "bias": "알 수 없음", "country": "Unknown"}
