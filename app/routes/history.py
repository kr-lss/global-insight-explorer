"""
Analysis History API endpoints
분석 히스토리 조회 및 통계
"""
from flask import Blueprint, request, jsonify
from app.models.history import (
    get_recent_history,
    get_popular_content,
    get_history_by_topic,
    get_statistics
)

history_bp = Blueprint('history', __name__, url_prefix='/api')


@history_bp.route('/history/recent', methods=['GET'])
def recent_history():
    """최근 분석 히스토리 조회"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)  # 최대 100개로 제한
        input_type = request.args.get('type', None)  # youtube, article, or None

        results = get_recent_history(limit=limit, input_type=input_type)

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })

    except Exception as e:
        print(f"❌ /api/history/recent 에러: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history/popular', methods=['GET'])
def popular_content():
    """인기 콘텐츠 조회 (조회수 기준)"""
    try:
        limit = min(int(request.args.get('limit', 10)), 100)  # 최대 100개로 제한
        days = max(0, int(request.args.get('days', 7)))  # 음수 방지
        input_type = request.args.get('type', None)

        results = get_popular_content(limit=limit, days=days, input_type=input_type)

        return jsonify({
            'success': True,
            'count': len(results),
            'period_days': days,
            'data': results
        })

    except Exception as e:
        print(f"❌ /api/history/popular 에러: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history/by-topic/<topic>', methods=['GET'])
def history_by_topic(topic):
    """특정 주제로 히스토리 검색"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)  # 최대 100개로 제한

        results = get_history_by_topic(topic=topic, limit=limit)

        return jsonify({
            'success': True,
            'topic': topic,
            'count': len(results),
            'data': results
        })

    except Exception as e:
        print(f"❌ /api/history/by-topic 에러: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history/statistics', methods=['GET'])
def statistics():
    """전체 통계 조회"""
    try:
        stats = get_statistics()

        return jsonify({
            'success': True,
            'statistics': stats
        })

    except Exception as e:
        print(f"❌ /api/history/statistics 에러: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
