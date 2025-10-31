"""
API routes package
"""
from flask import Blueprint

from .health import health_bp
from .analysis import analysis_bp
from .media import media_bp

__all__ = ['health_bp', 'analysis_bp', 'media_bp']
