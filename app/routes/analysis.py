"""
Analysis API endpoints
"""
from flask import Blueprint, request, jsonify
from app.utils.analysis_service import AnalysisService

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# 서비스 인스턴스 생성
analysis_service = AnalysisService()


@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """1차 분석: URL을 받아 콘텐츠의 핵심 주장을 추출"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL이 필요합니다'}), 400

        url = data.get('url')
        input_type = data.get('inputType', 'youtube')

        # 서비스에 분석 요청 위임
        result, from_cache = analysis_service.analyze_content(url, input_type)

        return jsonify({'success': True, 'analysis': result, 'cached': from_cache})

    except Exception as e:
        print(f"❌ /api/analyze 에러: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/find-sources', methods=['POST'])
def find_sources():
    """2차 분석: 선택된 주장에 대한 관련 기사 검색 및 분석"""
    try:
        data = request.get_json()
        if not data or 'url' not in data or 'selected_claims' not in data:
            return jsonify({'error': 'URL과 주장이 필요합니다'}), 400

        # 서비스에 2차 분석 요청 위임
        analysis_result, articles = analysis_service.find_sources_for_claims(
            url=data['url'],
            input_type=data.get('inputType', 'youtube'),
            selected_claims=data['selected_claims'],
            search_keywords=data.get('search_keywords', []),
        )

        return jsonify(
            {
                'success': True,
                'result': analysis_result,
                'articles': articles,
                'articles_count': len(articles),
            }
        )

    except Exception as e:
        print(f"❌ /api/find-sources 에러: {e}")
        return jsonify({'error': str(e)}), 500
