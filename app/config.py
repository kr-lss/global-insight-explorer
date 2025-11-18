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

    # AI Model settings
    GEMINI_MODEL_ANALYSIS: str = 'gemini-2.5-flash'  # 1차/2차 분석용
    GEMINI_MODEL_SEARCH: str = 'gemini-2.0-flash-exp'  # Google Search용

    # Stance analysis settings
    STANCE_TYPES: tuple = ('supporting', 'opposing', 'neutral')
    CONFIDENCE_DECIMAL_PLACES: int = 2  # 확신도 소수점 자리수


# Global config instance
config = Config()
