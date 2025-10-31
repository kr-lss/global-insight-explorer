"""
Media credibility API endpoints
"""
from flask import Blueprint, jsonify
from app.models.media import MEDIA_CREDIBILITY, get_media_credibility

media_bp = Blueprint('media', __name__, url_prefix='/api')


@media_bp.route('/media-credibility', methods=['GET'])
def list_media_credibility():
    """전체 언론사 신뢰도 목록 반환"""
    return jsonify(MEDIA_CREDIBILITY)


@media_bp.route('/media-credibility/<source>', methods=['GET'])
def get_source_credibility(source):
    """특정 언론사 신뢰도 조회"""
    info = get_media_credibility(source)
    return jsonify(
        {
            'source': source,
            'credibility': info['credibility'],
            'bias': info['bias'],
            'country': info['country'],
        }
    )
