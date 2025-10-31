"""
글로벌 인사이트 탐색기 - API 서버
요청을 받아 서비스 레이어에 위임하는 역할
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# 비즈니스 로직을 담고 있는 서비스 임포트
from services.analysis_service import AnalysisService
from database.media_db import MEDIA_CREDIBILITY, get_media_credibility

app = Flask(__name__)
CORS(app) # 모든 출처에서의 요청 허용

# 서비스 인스턴스 생성
analysis_service = AnalysisService()


# ============= API 엔드포인트 =============

@app.route('/health', methods=['GET'])
def health():
    """서버 상태 및 연결 상태 확인"""
    # 서비스 레이어를 통해 외부 서비스 상태 확인도 가능 (여기서는 단순화)
    return jsonify({
        'status': 'healthy',
        'media_database_size': len(MEDIA_CREDIBILITY)
    })


@app.route('/api/analyze', methods=['POST'])
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

        return jsonify({
            'success': True,
            'analysis': result,
            'cached': from_cache
        })

    except Exception as e:
        print(f"❌ /api/analyze 에러: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/find-sources', methods=['POST'])
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
            search_keywords=data.get('search_keywords', [])
        )

        return jsonify({
            'success': True,
            'result': analysis_result,
            'articles': articles,
            'articles_count': len(articles)
        })

    except Exception as e:
        print(f"❌ /api/find-sources 에러: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/media-credibility', methods=['GET'])
def list_media_credibility():
    """전체 언론사 신뢰도 목록 반환"""
    return jsonify(MEDIA_CREDIBILITY)


@app.route('/api/media-credibility/<source>', methods=['GET'])
def get_source_credibility(source):
    """특정 언론사 신뢰도 조회"""
    info = get_media_credibility(source)
    return jsonify({
        'source': source,
        'credibility': info['credibility'],
        'bias': info['bias'],
        'country': info['country']
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"""
    ╔══════════════════════════════════════╗
    ║  🌍 글로벌 인사이트 탐색기 (v2)      ║
    ║  리팩토링된 API 서버                 ║
    ║  포트: {port}                        ║
    ╚══════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=True)