"""
Analysis API endpoints
Global Insight Explorer - Refactored for Perspective Analysis
"""
from flask import Blueprint, request, jsonify
from app.utils.analysis_service import AnalysisService
from app.models.history import save_analysis_history

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# 서비스 인스턴스 생성
analysis_service = AnalysisService()


@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    [Legacy Support] 1차 분석: URL 콘텐츠 분석
    (영상 요약 기능은 유지하되, 핵심 로직은 optimize-query -> find-sources 흐름으로 이동)
    """
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL이 필요합니다'}), 400

        url = data.get('url')
        input_type = data.get('inputType', 'youtube')

        result, from_cache = analysis_service.analyze_content(url, input_type)

        # 히스토리 저장 (에러 무시)
        try:
            save_analysis_history(url, input_type, result)
        except Exception:
            pass

        return jsonify({'success': True, 'analysis': result, 'cached': from_cache})

    except Exception as e:
        print(f"❌ /api/analyze 에러: {e}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/optimize-query', methods=['POST'])
def optimize_query():
    """
    [Step 1] 사용자 질문 분석 및 국가별 검색 전략 수립
    Input: "캄보디아 납치 사건"
    Output: { "issue_type": "multi", "target_countries": ["KR", "KH", "CN"], ... }
    """
    try:
        data = request.get_json()
        user_input = data.get('user_input')

        if not user_input:
            return jsonify({'error': '사용자 입력이 필요합니다'}), 400

        context = data.get('context', {})

        # AI 서비스 호출 (Step 1)
        result = analysis_service.optimize_search_query(user_input, context)

        return jsonify(result), 200

    except Exception as e:
        print(f"❌ /api/optimize-query 에러: {e}")
        # Fallback: 최소한의 검색 조건 반환
        return jsonify({
            'success': False,
            'data': {
                'issue_type': 'multi_country',
                'target_countries': [
                    {'code': 'US', 'role': 'global', 'reason': 'Fallback'},
                    {'code': 'KR', 'role': 'local', 'reason': 'Fallback'}
                ],
                'gdelt_params': {
                    'keywords': [data.get('user_input', '')],
                    'themes': [],
                    'event_date': None
                }
            }
        }), 200


@analysis_bp.route('/find-sources', methods=['POST'])
def find_sources():
    """
    [Step 2] 확정된 국가별 전략으로 실제 기사 검색 (Loop Search)

    새로운 API 형식:
    - Input: optimize-query의 결과 JSON (target_countries 등 포함)
    - Output: { "status": "success", "data": { "KR": [...], "US": [...] } }

    하위 호환성:
    - 기존 claims_data 방식도 지원 (자동 변환)
    """
    try:
        data = request.get_json()

        # 1. 새로운 방식: search_params가 있는 경우
        if 'search_params' in data:
            search_params = data.get('search_params')

            if not search_params:
                return jsonify({'error': '검색 파라미터가 필요합니다'}), 400

            print(f"🚀 글로벌 관점 검색 시작: {search_params.get('topic_en', 'Unknown Topic')}")

            # 새로운 서비스 함수 호출 (Step 2: 국가별 루프 검색)
            response_data = analysis_service.get_global_perspectives(search_params)

            return jsonify({'success': True, 'result': response_data}), 200

        # 2. 하위 호환성: 기존 claims_data 방식 (Legacy)
        elif 'claims_data' in data:
            print("⚠️ Legacy 요청 감지: claims_data 방식 사용")

            url = data.get('url')
            input_type = data.get('inputType', 'youtube')
            claims_data = data.get('claims_data')

            if not claims_data or not isinstance(claims_data, list) or len(claims_data) == 0:
                return jsonify({'error': '최소 하나의 주장을 선택해주세요'}), 400

            # 기존 함수 호출 (하위 호환성)
            analysis_result, articles = analysis_service.find_sources_for_claims(
                url=url,
                input_type=input_type,
                claims_data=claims_data
            )

            return jsonify({
                'success': True,
                'result': analysis_result,
                'articles': articles,
                'articles_count': len(articles),
            }), 200

        else:
            return jsonify({'error': 'search_params 또는 claims_data가 필요합니다'}), 400

    except Exception as e:
        print(f"❌ /api/find-sources 에러: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500
