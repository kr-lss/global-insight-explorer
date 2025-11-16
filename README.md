# Global Insight Explorer

글로벌 인사이트 탐색기 - 미디어 콘텐츠 분석 및 사실 검증 웹 애플리케이션

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
├── frontend/           # 웹 애플리케이션 (프론트엔드)
│   ├── index.html      # 메인 HTML 페이지
│   ├── main.js         # JavaScript 로직
│   └── main.css        # 스타일시트
│
├── app/                # 백엔드 API 서버
│   ├── __init__.py
│   ├── main.py         # Flask 서버 진입점
│   ├── config.py       # 설정 관리
│   ├── models/         # 데이터 모델
│   │   ├── __init__.py
│   │   ├── media.py    # 언론사 신뢰도 데이터 (Firestore)
│   │   ├── history.py  # 분석 히스토리 (Firestore)
│   │   └── extractor.py # 콘텐츠 추출기 (YouTube/Article)
│   ├── routes/         # API 라우트
│   │   ├── __init__.py
│   │   ├── health.py   # 헬스 체크
│   │   ├── analysis.py # 분석 API
│   │   ├── media.py    # 미디어 신뢰도 API
│   │   └── history.py  # 히스토리 조회 API
│   └── utils/          # 유틸리티
│       ├── __init__.py
│       └── analysis_service.py # 분석 서비스
│
├── tests/              # 테스트 코드
└── scripts/            # 유틸리티 스크립트
    └── upload_media_to_firestore.py
```

## 기능

### 핵심 기능
- **YouTube 영상 분석**: 자막 우선, 실패 시 GCS 버킷에 영상 다운로드 후 Gemini 2.0으로 영상 분석
- **기사 콘텐츠 분석**: 웹 기사 자동 추출 및 핵심 주장 분석
- **AI 기반 핵심 주장 추출**: Gemini 2.5 Flash를 사용한 정교한 분석
- **관련 뉴스 기사 검색**: Gemini Google Search Grounding을 통한 실시간 기사 검색
- **언론사 신뢰도 평가**: Firestore 기반 동적 신뢰도 데이터 (fallback 지원)
- **다양한 관점의 정보 수집**: 여러 언론사의 보도를 종합하여 균형잡힌 시각 제공

### 고급 기능 (Firestore 활용)
- **분석 히스토리**: 사용자가 분석한 콘텐츠 기록 자동 저장 및 조회수 추적
- **인기 콘텐츠**: 조회수 기준 인기 콘텐츠 랭킹 (기간별 필터링 지원)
- **최근 분석**: 최근 분석된 콘텐츠 목록 (타입별 필터링)
- **주제별 검색**: 주제 태그를 통한 콘텐츠 검색
- **통계 대시보드**: 전체 분석 통계 및 인사이트
- **결과 캐싱**: 동일 URL 재분석 시 즉시 응답 (Firestore 캐시)

### YouTube 영상 분석 상세
**하이브리드 방식**:
1. **1단계 (자막 추출)**: `youtube-transcript-api`를 사용한 자막 추출 시도
2. **2단계 (영상 분석)**: 자막 없는 경우
   - `yt-dlp`로 영상 다운로드 (720p 이하, MP4)
   - Google Cloud Storage 버킷에 임시 업로드
   - Gemini 2.0 Flash Exp로 영상 프레임 및 오디오 분석
   - 분석 완료 후 GCS 및 로컬 파일 자동 삭제

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
GCS_BUCKET_NAME=your-bucket-name  # YouTube 영상 분석용 (선택사항)
```

**참고**:
- `GCS_BUCKET_NAME`이 설정되지 않으면 YouTube 자막 추출만 가능합니다.
- 자막이 없는 영상을 분석하려면 GCS 버킷 설정이 필요합니다.
- Firestore 설정이 없어도 애플리케이션은 fallback 데이터로 정상 작동합니다.

### Firestore 초기 설정 (선택사항)

언론사 신뢰도 데이터는 Firestore에서 동적으로 로드됩니다. Firestore 연결이 실패하면 자동으로 fallback 데이터를 사용합니다.

**Firestore에 초기 데이터 업로드:**
```bash
# 현재 Firestore 데이터 조회
python scripts/upload_media_to_firestore.py --view

# 초기 데이터 업로드 (기존 데이터 덮어쓰기)
python scripts/upload_media_to_firestore.py
```

**참고:** Firestore 없이도 애플리케이션은 정상 작동합니다 (fallback 데이터 사용)

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

서버가 시작되면 브라우저에서 다음 주소로 접속:
- **웹 애플리케이션**: http://127.0.0.1:8080
- **API 엔드포인트**: http://127.0.0.1:8080/api/

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

Docker로 실행 시에도 동일하게 http://127.0.0.1:8080 으로 접속

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
# 전체 언론사 목록 (Firestore에서 로드)
GET /api/media-credibility

# 특정 언론사 조회
GET /api/media-credibility/<source>

# 캐시 새로고침 (Firestore 재로드)
POST /api/media-credibility/reload
```

### 분석 히스토리 조회
```
# 최근 분석 목록
GET /api/history/recent?limit=20&type=youtube

# 인기 콘텐츠 (조회수 기준)
GET /api/history/popular?limit=10&days=7&type=youtube

# 특정 주제로 검색
GET /api/history/by-topic/<topic>?limit=20

# 통계 조회
GET /api/history/statistics
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

## 사용 방법

1. 서버를 실행합니다 (`python -m app.main` 또는 `make run`)
2. 브라우저에서 http://127.0.0.1:8080 으로 접속합니다
3. YouTube 링크 또는 뉴스 기사 URL을 입력합니다
4. "분석 시작" 버튼을 클릭하여 주요 주장을 추출합니다
5. 추출된 주장 중 팩트체크하고 싶은 항목을 선택합니다
6. "선택한 주장 팩트 체크" 버튼을 클릭하여 관련 기사를 검색합니다
7. 다양한 언론사의 보도와 신뢰도를 확인합니다

## 기술 스택

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
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
