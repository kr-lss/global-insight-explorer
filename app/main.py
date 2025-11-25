"""
글로벌 인사이트 탐색기 - API 서버
요청을 받아 서비스 레이어에 위임하는 역할
"""
import os
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Windows에서 UTF-8 인코딩 설정 (emoji 출력을 위해)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.config import config
from app.routes import health_bp, analysis_bp, media_bp, history_bp


def create_app():
    """Flask 애플리케이션 팩토리"""
    # 정적 파일 경로 설정
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    app = Flask(__name__, static_folder=static_folder, static_url_path='')

    # CORS 설정 (모든 origin 허용)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # 블루프린트 등록
    app.register_blueprint(health_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(history_bp)

    # 웹 애플리케이션 라우트 (정적 파일 서빙)
    @app.route('/')
    def index():
        """웹 애플리케이션 메인 페이지"""
        response = send_from_directory(app.static_folder, 'index.html')
        # 개발 모드에서는 캐싱 비활성화
        if config.DEBUG:
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
        return response

    @app.route('/<path:path>')
    def serve_static(path):
        """정적 파일 서빙"""
        if os.path.exists(os.path.join(app.static_folder, path)):
            response = send_from_directory(app.static_folder, path)
            # 개발 모드에서는 캐싱 비활성화
            if config.DEBUG:
                response.cache_control.no_cache = True
                response.cache_control.no_store = True
                response.cache_control.must_revalidate = True
            return response
        # 파일이 없으면 index.html로 리다이렉트 (SPA 지원)
        response = send_from_directory(app.static_folder, 'index.html')
        if config.DEBUG:
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
        return response

    return app


def main():
    """애플리케이션 진입점"""
    app = create_app()

    print(
        f"""
    ╔══════════════════════════════════════╗
    ║  🌍 글로벌 인사이트 탐색기 (v2)      ║
    ║  리팩토링된 API 서버                 ║
    ║  포트: {config.PORT}                        ║
    ╚══════════════════════════════════════╝
    """
    )

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == '__main__':
    main()
