"""
Analysis API endpoints
"""
from flask import Blueprint, request, jsonify
from app.utils.analysis_service import AnalysisService
from app.models.history import save_analysis_history

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

        # 히스토리 저장 (비동기적으로, 실패해도 응답에 영향 없음)
        try:
            save_analysis_history(url, input_type, result)
        except Exception as history_error:
            print(f"⚠️ 히스토리 저장 실패 (계속 진행): {history_error}")

        return jsonify({'success': True, 'analysis': result, 'cached': from_cache})

    except Exception as e:
        print(f"❌ /api/analyze 에러: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/find-sources', methods=['POST'])
def find_sources():
    """2차 분석: 선택된 주장에 대한 관련 기사 검색 및 분석"""
    try:
        data = request.get_json()

        # 필수 파라미터 확인
        if not data or 'url' not in data:
            return jsonify({'error': 'URL이 필요합니다'}), 400

        # claims_data 확인 (없으면 에러)
        claims_data = data.get('claims_data')

        if not claims_data or not isinstance(claims_data, list) or len(claims_data) == 0:
            # 하위 호환성: selected_claims가 있으면 변환 시도 (선택사항)
            if 'selected_claims' in data:
                claims_data = [{'claim_kr': c, 'search_keywords_en': [], 'target_country_codes': []} for c in data['selected_claims']]
            else:
                return jsonify({'error': '최소 하나의 주장을 선택해주세요'}), 400

        # 서비스 호출
        analysis_result, articles = analysis_service.find_sources_for_claims(
            url=data['url'],
            input_type=data.get('inputType', 'youtube'),
            claims_data=claims_data
        )

        return jsonify({
            'success': True,
            'result': analysis_result,
            'articles': articles,
            'articles_count': len(articles),
        })

    except Exception as e:
        print(f"❌ /api/find-sources 에러: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/optimize-query', methods=['POST'])
def optimize_query():
    """사용자 질문을 GDELT 검색 쿼리로 최적화"""
    try:
        data = request.get_json()

        # 필수 파라미터 확인
        if not data or 'user_input' not in data:
            return jsonify({'error': '사용자 입력이 필요합니다'}), 400

        user_input = data.get('user_input')
        context = data.get('context', {})  # 선택적 컨텍스트

        # 서비스 호출
        result = analysis_service.optimize_search_query(user_input, context)

        # 실패해도 Fallback 데이터를 반환하므로 항상 200 OK
        return jsonify(result), 200

    except Exception as e:
        print(f"❌ /api/optimize-query 에러: {e}")
        # 최악의 경우에도 Fallback 응답
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'interpreted_intent': 'Error fallback',
                'search_keywords_en': [data.get('user_input', '')],
                'search_keywords_kr': [data.get('user_input', '')],
                'target_country_codes': [],
                'confidence': 0.0
            }
        }), 200
