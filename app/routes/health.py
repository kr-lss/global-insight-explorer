"""
Health check endpoints
"""
from flask import Blueprint, jsonify
from app.models.media import get_all_media

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health():
    """서버 상태 및 연결 상태 확인"""
    media_data = get_all_media()
    return jsonify(
        {'status': 'healthy', 'media_database_size': len(media_data)}
    )
