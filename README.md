# Global Insight Explorer

글로벌 인사이트 탐색기 - 미디어 콘텐츠 분석 및 사실 검증 도구

## 프로젝트 구조

```
global-insight-explorer/
├── run.sh              # 실행 스크립트
├── .env                # 환경 변수 (비밀 정보)
├── .env.example        # 환경 변수 예제
├── docker-compose.yml  # Docker 구성
├── Dockerfile          # Docker 이미지 빌드
├── requirements.txt    # Python 의존성
├── setup.py            # 패키지 설치 설정
├── Makefile            # 자동화 명령어
├── README.md           # 프로젝트 설명
├── .gitignore          # Git 제외 파일
├── pytest.ini          # 테스트 설정
│
├── app/                # 애플리케이션 코드
│   ├── __init__.py
│   ├── main.py         # 진입점
│   ├── config.py       # 설정 관리
│   ├── models/         # 데이터 모델
│   │   ├── __init__.py
│   │   ├── media.py    # 언론사 신뢰도 데이터
│   │   └── extractor.py # 콘텐츠 추출기
│   ├── routes/         # API 라우트
│   │   ├── __init__.py
│   │   ├── health.py   # 헬스 체크
│   │   ├── analysis.py # 분석 API
│   │   └── media.py    # 미디어 신뢰도 API
│   └── utils/          # 유틸리티
│       ├── __init__.py
│       └── analysis_service.py # 분석 서비스
│
├── tests/              # 테스트 코드
├── scripts/            # 유틸리티 스크립트
└── docs/               # 문서
```

## 기능

- YouTube 영상 및 기사 콘텐츠 분석
- AI 기반 핵심 주장 추출
- 관련 뉴스 기사 검색 및 분석
- 언론사 신뢰도 평가
- 다양한 관점의 정보 수집

## 설치

### 환경 변수 설정

1. `.env.example`을 `.env`로 복사:
```bash
cp .env.example .env
```

2. `.env` 파일 편집하여 GCP 프로젝트 정보 입력:
```
GCP_PROJECT=your-project-id
GCP_REGION=us-central1
```

### 로컬 설치

```bash
# 의존성 설치
make install

# 또는
pip install -r requirements.txt
```

### Docker 설치

```bash
# Docker 이미지 빌드
make docker-build

# 또는
docker-compose build
```

## 실행

### 로컬 실행

```bash
# 방법 1: Makefile 사용
make run

# 방법 2: 실행 스크립트 사용
chmod +x run.sh
./run.sh

# 방법 3: Python 직접 실행
python -m app.main
```

### Docker 실행

```bash
# 방법 1: Makefile 사용
make docker-run

# 방법 2: docker-compose 직접 사용
docker-compose up -d

# 로그 확인
make docker-logs
# 또는
docker-compose logs -f

# 중지
make docker-stop
# 또는
docker-compose down
```

## API 엔드포인트

### Health Check
```
GET /health
```

### 1차 분석 (콘텐츠 추출 및 주장 분석)
```
POST /api/analyze
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=...",
  "inputType": "youtube"
}
```

### 2차 분석 (관련 기사 검색 및 분석)
```
POST /api/find-sources
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=...",
  "inputType": "youtube",
  "selected_claims": ["주장 1", "주장 2"],
  "search_keywords": ["keyword1", "keyword2"]
}
```

### 언론사 신뢰도 조회
```
GET /api/media-credibility
GET /api/media-credibility/<source>
```

## 개발

### 테스트

```bash
# 전체 테스트 실행
make test

# 또는
pytest tests/ -v
```

### 코드 포맷팅

```bash
# Black으로 코드 포맷팅
make format

# Flake8으로 린트 체크
make lint
```

### 개발 모드 실행

```bash
make dev
```

## 기술 스택

- **Backend**: Flask, Python 3.9+
- **AI**: Google Vertex AI (Gemini)
- **Database**: Google Cloud Firestore
- **Content Extraction**: BeautifulSoup4, YouTube Transcript API
- **Deployment**: Docker, Docker Compose

## 라이선스

MIT License

## 기여

이슈와 풀 리퀘스트는 언제나 환영합니다!

## 문의

문의사항이 있으시면 이슈를 등록해주세요.
