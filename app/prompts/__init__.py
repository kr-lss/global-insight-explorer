"""
AI 프롬프트 템플릿 모듈
"""

from .analysis_prompts import (
    get_first_analysis_prompt,
    get_stance_analysis_prompt,
    get_article_search_prompt,
)

__all__ = [
    'get_first_analysis_prompt',
    'get_stance_analysis_prompt',
    'get_article_search_prompt',
]
