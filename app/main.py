"""
글로벌 인사이트 탐색기 - API 서버
요청을 받아 서비스 레이어에 위임하는 역할
"""
from flask import Flask
from flask_cors import CORS

from app.config import config
from app.routes import health_bp, analysis_bp, media_bp


def create_app():
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__)

    # CORS 설정
    CORS(app)

    # 블루프린트 등록
    app.register_blueprint(health_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(media_bp)

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
