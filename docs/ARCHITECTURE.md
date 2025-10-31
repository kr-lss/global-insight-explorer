# 프로젝트 아키텍처

## 개요

Global Insight Explorer는 Flask 기반의 RESTful API 서버로, 미디어 콘텐츠 분석 및 사실 검증 기능을 제공합니다.

## 디렉토리 구조

```
global-insight-explorer/
├── app/                    # 메인 애플리케이션 패키지
│   ├── __init__.py         # 패키지 초기화
│   ├── main.py             # 애플리케이션 진입점 및 팩토리
│   ├── config.py           # 설정 관리 (환경 변수, 상수)
│   │
│   ├── models/             # 데이터 모델 및 비즈니스 엔티티
│   │   ├── media.py        # 언론사 신뢰도 데이터베이스
│   │   └── extractor.py    # 콘텐츠 추출기 (Strategy 패턴)
│   │
│   ├── routes/             # API 엔드포인트 (Controller)
│   │   ├── health.py       # 헬스 체크 라우트
│   │   ├── analysis.py     # 분석 API 라우트
│   │   └── media.py        # 미디어 신뢰도 API 라우트
│   │
│   └── utils/              # 유틸리티 및 서비스
│       └── analysis_service.py  # 분석 비즈니스 로직 (Facade 패턴)
│
├── tests/                  # 테스트 코드
│   ├── test_example.py     # 예제 테스트
│   └── ...
│
├── scripts/                # 유틸리티 스크립트
│   └── cleanup.sh          # 캐시 정리 스크립트
│
├── docs/                   # 문서
│   ├── API.md              # API 문서
│   └── ARCHITECTURE.md     # 아키텍처 문서
│
├── requirements.txt        # Python 의존성
├── setup.py                # 패키지 설정
├── Makefile                # 자동화 명령어
├── Dockerfile              # Docker 이미지 정의
├── docker-compose.yml      # Docker Compose 설정
├── pytest.ini              # 테스트 설정
├── .env.example            # 환경 변수 예제
├── .gitignore              # Git 제외 파일
└── README.md               # 프로젝트 설명
```

## 아키텍처 패턴

### 1. Application Factory Pattern

[app/main.py](../app/main.py)에서 Flask 애플리케이션을 생성하는 팩토리 함수 사용:

```python
def create_app():
    app = Flask(__name__)
    # 설정 및 블루프린트 등록
    return app
```

**장점:**
- 테스트 용이성
- 여러 인스턴스 생성 가능
- 설정 분리

### 2. Blueprint Pattern

각 기능별로 라우트를 블루프린트로 분리:

- `health_bp`: 헬스 체크
- `analysis_bp`: 분석 API
- `media_bp`: 미디어 신뢰도 API

**장점:**
- 모듈화 및 재사용성
- URL 프리픽스 관리 용이

### 3. Strategy Pattern

[app/models/extractor.py](../app/models/extractor.py)에서 콘텐츠 추출 전략 구현:

```python
BaseExtractor (추상 클래스)
├── YoutubeExtractor    # YouTube 자막 추출
└── ArticleExtractor    # 웹 기사 추출
```

**장점:**
- 새로운 추출기 추가 용이
- 런타임에 전략 교체 가능

### 4. Facade Pattern

[app/utils/analysis_service.py](../app/utils/analysis_service.py)에서 복잡한 분석 로직을 단순한 인터페이스로 제공:

```python
AnalysisService
├── analyze_content()           # 1차 분석
├── find_sources_for_claims()   # 2차 분석
└── 내부 헬퍼 메서드들
```

**장점:**
- 복잡도 숨김
- 클라이언트 코드 단순화

## 데이터 흐름

### 1차 분석 (Content Analysis)

```
Client Request
    ↓
[routes/analysis.py] analyze()
    ↓
[utils/analysis_service.py] analyze_content()
    ↓
[models/extractor.py] YoutubeExtractor/ArticleExtractor
    ↓
External API (YouTube/Web)
    ↓
[Vertex AI] Gemini 분석
    ↓
[Firestore] 캐시 저장
    ↓
Response to Client
```

### 2차 분석 (Find Related Sources)

```
Client Request (with selected claims)
    ↓
[routes/analysis.py] find_sources()
    ↓
[utils/analysis_service.py] find_sources_for_claims()
    ↓
Google Web Search
    ↓
[models/media.py] get_media_credibility()
    ↓
[Vertex AI] Gemini 관련성 분석
    ↓
Response to Client
```

## 주요 의존성

### 프레임워크 및 웹
- **Flask**: 웹 프레임워크
- **Flask-CORS**: CORS 지원

### AI 및 머신러닝
- **google-cloud-aiplatform**: Vertex AI (Gemini)
- **google-cloud-firestore**: Firestore 데이터베이스

### 콘텐츠 추출
- **youtube-transcript-api**: YouTube 자막 추출
- **requests**: HTTP 요청
- **beautifulsoup4**: HTML 파싱

### 개발 도구
- **pytest**: 테스트 프레임워크
- **python-dotenv**: 환경 변수 관리

## 설정 관리

[app/config.py](../app/config.py)에서 중앙화된 설정 관리:

```python
@dataclass
class Config:
    PORT: int
    HOST: str
    DEBUG: bool
    GCP_PROJECT: str
    GCP_REGION: str
    # ...
```

환경 변수를 통해 설정 주입:
- 개발: `.env` 파일
- 프로덕션: Docker 환경 변수

## 에러 처리

모든 API 엔드포인트는 try-except로 에러를 캐치하고 적절한 HTTP 상태 코드와 에러 메시지를 반환:

```python
try:
    # 비즈니스 로직
    return jsonify({'success': True, ...})
except Exception as e:
    print(f"❌ 에러: {e}")
    return jsonify({'error': str(e)}), 500
```

## 캐싱 전략

Firestore를 사용한 분석 결과 캐싱:

- **캐시 키**: URL의 MD5 해시
- **캐시 데이터**: 분석 결과, 타임스탬프
- **만료 정책**: 수동 관리 (향후 TTL 추가 가능)

## 보안 고려사항

1. **환경 변수**: 민감한 정보는 `.env` 파일로 관리
2. **CORS**: 필요한 오리진만 허용 (현재는 모든 오리진 허용)
3. **입력 검증**: 모든 API 엔드포인트에서 필수 파라미터 검증
4. **에러 메시지**: 민감한 정보 노출 방지

## 확장성

### 수평 확장
- 상태 비저장(stateless) 설계
- Docker 컨테이너화로 쉬운 복제

### 수직 확장
- Firestore 캐싱으로 데이터베이스 부하 감소
- 비동기 처리 추가 가능 (Celery 등)

### 새로운 기능 추가
1. **새로운 추출기**: `BaseExtractor` 상속
2. **새로운 API**: 새 Blueprint 생성
3. **새로운 분석 기능**: `AnalysisService`에 메서드 추가

## 테스트 전략

- **단위 테스트**: 각 모듈별 독립 테스트
- **통합 테스트**: API 엔드포인트 테스트
- **마커 사용**: `@pytest.mark.unit`, `@pytest.mark.integration`

## 배포

### Docker
```bash
docker-compose up -d
```

### 클라우드
- Google Cloud Run 권장
- Kubernetes 지원 가능

## 모니터링 및 로깅

현재: 콘솔 로그 출력
향후:
- Structured logging (JSON)
- Cloud Logging 연동
- 성능 모니터링 (APM)

## 라이선스

MIT License
