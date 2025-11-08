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


# Global config instance
config = Config()
