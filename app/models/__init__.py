"""
Data models package
"""
from .media import (
    get_media_credibility,
    get_all_media,
    reload_media_cache
)
from .extractor import BaseExtractor, YoutubeExtractor, ArticleExtractor
from .history import (
    save_analysis_history,
    get_recent_history,
    get_popular_content,
    get_history_by_topic,
    get_statistics
)

__all__ = [
    # Media
    'get_media_credibility',
    'get_all_media',
    'reload_media_cache',
    # Extractor
    'BaseExtractor',
    'YoutubeExtractor',
    'ArticleExtractor',
    # History
    'save_analysis_history',
    'get_recent_history',
    'get_popular_content',
    'get_history_by_topic',
    'get_statistics',
]
