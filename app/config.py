"""
Application configuration management
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration"""

    # Server settings
    PORT: int = int(os.environ.get('PORT', 8080))
    HOST: str = os.environ.get('HOST', '0.0.0.0')
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'

    # GCP settings
    GCP_PROJECT: str = os.environ.get('GCP_PROJECT', 'your-project-id')
    GCP_REGION: str = os.environ.get('GCP_REGION', 'us-central1')
    GCS_BUCKET_NAME: str = os.environ.get('GCS_BUCKET_NAME', '')

    # API settings
    API_VERSION: str = 'v1'
    API_PREFIX: str = '/api'

    # CORS settings
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', '*')

    # Content processing limits
    MAX_CONTENT_LENGTH_FIRST_ANALYSIS: int = 8000  # Gemini 1차 분석 최대 글자 수
    MAX_CONTENT_LENGTH_SECOND_ANALYSIS: int = 4000  # Gemini 2차 분석 최대 글자 수

    # Article search settings
    MAX_ARTICLES_PER_SEARCH: int = 15  # Google Search로 검색할 최대 기사 수
    MAX_ARTICLES_FOR_AI_ANALYSIS: int = 15  # AI에게 전달할 최대 기사 수
    ERROR_LOG_PREVIEW_LENGTH: int = 500  # 에러 로그에 표시할 응답 길이

    # [리팩토링] AI Model settings (중앙 관리)
    GEMINI_MODEL_ANALYSIS: str = 'gemini-2.0-flash'      # 분석용 메인 모델
    GEMINI_MODEL_SEARCH: str = 'gemini-2.0-flash'        # 검색용 (Grounding)
    GEMINI_MODEL_EMBEDDING: str = 'text-embedding-004'   # [신규] 스마트 필터링용 임베딩 모델

    # [신규] Smart Filtering settings
    SIMILARITY_THRESHOLD: float = 0.15  # [임시 완화] 유사도 기준점 (0.0 ~ 1.0, 높을수록 엄격)

    # Stance analysis settings
    STANCE_TYPES: tuple = ('supporting', 'opposing', 'neutral')
    CONFIDENCE_DECIMAL_PLACES: int = 2  # 확신도 소수점 자리수

    # GDELT Search settings
    MAX_ENTITIES: int = 3  # GDELT 검색에 사용할 최대 entities 수
    MAX_THEMES: int = 3  # GDELT 검색에 사용할 최대 themes 수
    MAX_LOCATIONS: int = 2  # GDELT 검색에 사용할 최대 locations 수
    MAX_KEYWORDS: int = 5  # GDELT 검색에 사용할 최대 keywords 수
    SEARCH_WINDOW_DAYS: int = 4  # 사건 발생일 기준 ±N일 검색
    GDELT_MAX_RESULTS: int = 30  # GDELT 쿼리 결과 최대 개수
    THREAD_POOL_WORKERS: int = 10  # 병렬 기사 크롤링 워커 수

    # GDELT DOC API settings (add_docsapi branch)
    GDELT_DOC_API_URL: str = 'https://api.gdeltproject.org/api/v2/doc/doc'
    GDELT_DOC_TIMEOUT: int = 10  # DOC API 타임아웃 (초)
    GDELT_DOC_MAX_RECORDS: int = 250  # DOC API 최대 레코드 수
    GDELT_SEARCH_TIMESPAN: str = '3m'  # 검색 시간 범위 (3개월)

    # Trusted news sources for GDELT filtering
    TRUSTED_DOMAINS: tuple = (
        # 북미/유럽 주요 언론
        'cnn.com', 'bbc.co.uk', 'reuters.com', 'apnews.com', 'nytimes.com',
        # 한국 주요 언론
        'yna.co.kr', 'koreaherald.com', 'koreatimes.co.kr',
        # 아시아 주요 언론
        'xinhuanet.com', 'globaltimes.cn', 'tass.com', 'rt.com',
        # 중동 주요 언론
        'aljazeera.com', 'jpost.com', 'kyivindependent.com'
    )


# Global config instance
config = Config()
