"""
Media credibility API endpoints
"""
from flask import Blueprint, jsonify, request
from app.models.media import get_media_credibility, get_all_media, reload_media_cache

media_bp = Blueprint('media', __name__, url_prefix='/api')


@media_bp.route('/media-credibility', methods=['GET'])
def list_media_credibility():
    """전체 언론사 신뢰도 목록 반환 (Firestore에서 로드)"""
    all_media = get_all_media()
    return jsonify({
        'success': True,
        'count': len(all_media),
        'data': all_media
    })


@media_bp.route('/media-credibility/<source>', methods=['GET'])
def get_source_credibility(source):
    """특정 언론사 신뢰도 조회"""
    info = get_media_credibility(source)
    return jsonify({
        'success': True,
        'source': source,
        'credibility': info['credibility'],
        'bias': info['bias'],
        'country': info['country'],
    })


@media_bp.route('/media-credibility/reload', methods=['POST'])
def reload_media():
    """언론사 캐시 강제 새로고침 (Firestore 재로드)"""
    try:
        count = reload_media_cache()
        return jsonify({
            'success': True,
            'message': f'{count}개 언론사 정보 재로드 완료',
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
