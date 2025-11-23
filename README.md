# 🌍 Global Insight Explorer

**다양한 관점으로 세계를 탐색하는 미디어 분석 플랫폼**

YouTube 영상과 뉴스 기사를 분석하여 주요 주장을 추출하고, 전 세계 언론사의 다양한 보도를 비교할 수 있는 AI 기반 팩트체크 도구입니다.

---

## 📌 주요 기능

### 1️⃣ **콘텐츠 분석 (1차 분석)**
- YouTube 영상 자막 및 웹 기사에서 핵심 주장 자동 추출
- Gemini AI 기반 한국어 요약 및 영어 검색 키워드 생성
- 관련 국가 및 주제 자동 태깅
- AI 기반 사용자 질문 최적화 (검색 키워드 변환)

### 2️⃣ **다양한 관점 탐색 (2차 분석)**
- GDELT BigQuery를 활용한 전 세계 언론 보도 검색
- 국가별, 언론사별 입장 비교 (지지/반대/중립)
- 병렬 본문 추출로 빠른 분석 (ThreadPool 10 workers)
- 제목 및 본문 자동 추출 with trafilatura

### 3️⃣ **언론사 정보 관리**
- Firestore 기반 언론사 메타데이터 관리 (`media_credibility` 컬렉션)
- 국영/민영 분류
- 도메인 및 이름 기반 자동 매칭
- 방송사/신문사 카테고리 구분

### 4️⃣ **분석 히스토리 관리**
- 분석 기록 자동 저장 (Firestore `analysis_history` 컬렉션)
- 인기 콘텐츠 및 최근 분석 조회
- 주제별 검색 및 통계
- 조회수 자동 추적

---

## 🏗️ 아키텍처

### Backend (Python Flask)
```
app/
├── main.py                     # Flask 앱 진입점
├── config.py                   # 환경 설정
├── routes/                     # API 엔드포인트
│   ├── analysis.py            # 분석 API (/api/analyze, /api/find-sources)
│   ├── media.py               # 언론사 정보 API
│   ├── history.py             # 히스토리 API
│   └── health.py              # 헬스체크
├── utils/                      # 비즈니스 로직
│   ├── analysis_service.py    # 핵심 분석 서비스
│   └── gdelt_search.py        # GDELT BigQuery 검색
├── models/                     # 데이터 모델
│   ├── extractor.py           # 콘텐츠 추출기 (YouTube/Article)
│   ├── media.py               # 언론사 정보 (Firestore)
│   └── history.py             # 히스토리 관리 (Firestore)
└── prompts/                    # AI 프롬프트 템플릿
    └── analysis_prompts.py
```

### Frontend (Vanilla JS ES Modules)
```
frontend/
├── index.html                  # 웹 앱 메인
├── popup.html                  # Chrome Extension 팝업
├── main.js                     # 웹 앱 로직
├── popup.js                    # Extension 로직
├── main.css                    # 스타일시트
└── modules/                    # 모듈화된 컴포넌트
    ├── api.js                 # API 호출 (표준화된 에러 핸들링)
    ├── ui.js                  # UI 렌더링
    ├── config.js              # 설정 (API_BASE_URL 등)
    ├── constants.js           # 상수 (UI 기본값, 국가 플래그)
    └── utils.js               # 유틸리티 함수
```

---

## 🔄 데이터 흐름

### 1차 분석 흐름
```
사용자 입력 (URL)
  ↓
[Frontend] POST /api/analyze
  {url, inputType}
  ↓
[Backend] AnalysisService.analyze_content()
  ↓
Extractor 선택:
  - YouTubeExtractor: 자막 추출 (youtube-transcript-api)
  - ArticleExtractor: 본문 + 제목 크롤링 (trafilatura/BeautifulSoup)
  ↓
Gemini AI 분석 (Vertex AI)
  ↓
{
  title_kr: "영상/기사 제목",
  summary_kr: "3문장 요약",
  key_claims: [
    {
      claim_kr: "한국어 주장",
      search_keywords_en: ["영어", "키워드"],
      target_country_codes: ["US", "CN"]
    }
  ],
  topics: ["주제1", "주제2"],
  related_countries: ["US", "KR"]
}
  ↓
[Firestore] analysis_history에 저장
  ↓
[Frontend] 주장 체크박스 + 커스텀 입력 필드 표시
```

### 2차 분석 흐름 (GDELT 검색)
```
사용자: 주장 선택 + (선택사항) 사용자 질문 입력
  ↓
사용자 질문 있으면:
  POST /api/optimize-query
  {user_input, context}
    ↓
  Gemini AI: 질문 → 검색 키워드 변환
  {search_keywords_en, target_country_codes}
  ↓
[Frontend] POST /api/find-sources
  {
    url, inputType,
    claims_data: [
      {
        claim_kr: "...",
        search_keywords_en: [...],
        target_country_codes: [...]
      }
    ]
  }
  ↓
[Backend] AnalysisService.find_sources_for_claims()
  ↓
각 주장별로 반복:
  ├─ GDELT BigQuery 검색
  │   - 영어 키워드 조합
  │   - 타겟 국가 필터링
  │   - 최근 7일 이내 기사
  ↓
  ├─ 병렬 본문 + 제목 추출 (ThreadPool 10 workers)
  │   - extract_with_title(url)
  │   - 제목 없으면 출처명을 제목으로
  ↓
  └─ 언론사 정보 추가
      - Firestore media_credibility 컬렉션 조회
      - 도메인/이름 기반 매칭
      - 국영/민영 정보 태깅
  ↓
Gemini AI: 입장 분석
  - 각 기사의 입장 (supporting/opposing/neutral)
  - 핵심 근거 (key_evidence)
  - 프레이밍 (framing)
  - 확신도 (confidence)
  ↓
{
  results: [
    {
      claim: "...",
      supporting_evidence: {articles: [...], count: N},
      opposing_evidence: {articles: [...], count: N},
      neutral_coverage: {articles: [...], count: N},
      diversity_metrics: {...}
    }
  ]
}
  ↓
[Frontend] 입장별 그룹화 표시
```

---

## 🗄️ Firestore 구조

```
/
├── analysis_history           # 분석 히스토리
│   └── {url_hash}
│       ├── url: string
│       ├── url_hash: string
│       ├── input_type: "youtube" | "article"
│       ├── title: string
│       ├── key_claims: array
│       ├── topics: array
│       ├── related_countries: array
│       ├── view_count: number
│       ├── created_at: timestamp
│       ├── last_analyzed_at: timestamp
│       ├── created_by: string
│       └── last_user_id: string
│
├── cache                      # 분석 캐시 (성능 최적화용)
│   └── {url_hash}
│       ├── url: string
│       ├── result: object
│       └── cached_at: timestamp
│
└── media_credibility          # 언론사 정보
    ├── KR                     # 국가 코드 (ISO 3166-1 alpha-2)
    │   ├── broadcasting: [
    │   │     {
    │   │       domain: "kbs.co.kr",
    │   │       name: "KBS",
    │   │       type: "국영"
    │   │     },
    │   │     ...
    │   │   ]
    │   └── newspapers: [
    │         {
    │           domain: "chosun.com",
    │           name: "조선일보",
    │           type: "민영"
    │         },
    │         ...
    │       ]
    ├── US
    │   ├── broadcasting: [...]
    │   └── newspapers: [...]
    └── ...
```

### 언론사 정보 구조

각 언론사는 다음 정보를 포함합니다:
- **name**: 언론사 이름 (예: "KBS", "CNN")
- **domain**: 도메인 (예: "kbs.co.kr", "cnn.com")
- **type**: 국영 또는 민영
- **category**: broadcasting (방송사) 또는 newspaper (신문사)

---

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일 생성)
cp .env.example .env
```

`.env` 파일 편집:
```env
GCP_PROJECT=your-project-id
GCP_REGION=us-central1
GCS_BUCKET_NAME=your-bucket-name  # YouTube 영상 분석용 (선택사항)
```

### 2. GCP 설정

```bash
# 1. Firestore 데이터베이스 생성 (Native 모드)
gcloud firestore databases create --location=us-central1

# 2. BigQuery API 활성화 (GDELT 검색용)
gcloud services enable bigquery.googleapis.com

# 3. Vertex AI API 활성화 (Gemini AI)
gcloud services enable aiplatform.googleapis.com

# 4. 서비스 계정 키 생성
gcloud iam service-accounts keys create key.json \
  --iam-account=your-service-account@your-project.iam.gserviceaccount.com

export GOOGLE_APPLICATION_CREDENTIALS="key.json"
```

**필요한 IAM 권한:**
- Firestore User
- BigQuery Data Viewer
- BigQuery Job User
- Vertex AI User
- Storage Object Viewer/Creator (GCS 사용 시)

### 3. Firestore 데이터 업로드

언론사 정보를 Firestore `media_credibility` 컬렉션에 업로드:

```bash
# 현재 Firestore 데이터 조회
python scripts/upload_media_to_firestore.py --view

# 초기 데이터 업로드
python scripts/upload_media_to_firestore.py
```

### 4. 서버 실행

```bash
# 개발 모드
python -m app.main

# 프로덕션 모드 (gunicorn)
gunicorn app.main:create_app() --bind 0.0.0.0:8080 --workers 4
```

서버가 `http://127.0.0.1:8080`에서 실행됩니다.

### 5. 프론트엔드 접속

- **웹 앱:** http://127.0.0.1:8080
- **Chrome Extension:** `frontend/` 폴더를 Chrome에서 로드 (개발자 모드)

---

## 📡 API 엔드포인트

### 분석 API

#### `POST /api/analyze`
1차 분석: URL에서 주장 추출

**Request:**
```json
{
  "url": "https://youtube.com/watch?v=...",
  "inputType": "youtube"
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "title_kr": "영상 제목",
    "summary_kr": "3문장 요약",
    "key_claims": [
      {
        "claim_kr": "한국어 주장",
        "search_keywords_en": ["keyword1", "keyword2"],
        "target_country_codes": ["US", "CN"]
      }
    ],
    "topics": ["경제", "정치"],
    "related_countries": ["US", "KR"]
  },
  "cached": false
}
```

#### `POST /api/find-sources`
2차 분석: 주장에 대한 언론 보도 검색 (GDELT)

**Request:**
```json
{
  "url": "https://...",
  "inputType": "youtube",
  "claims_data": [
    {
      "claim_kr": "한국어 주장",
      "search_keywords_en": ["keyword1", "keyword2"],
      "target_country_codes": ["US", "CN"]
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "results": [
      {
        "claim": "...",
        "supporting_evidence": {
          "count": 5,
          "articles": [...],
          "common_arguments": [...]
        },
        "opposing_evidence": {
          "count": 3,
          "articles": [...],
          "common_arguments": [...]
        },
        "neutral_coverage": {
          "count": 2,
          "articles": [...]
        },
        "diversity_metrics": {
          "total_sources": 10,
          "stance_distribution": {
            "supporting": 5,
            "opposing": 3,
            "neutral": 2
          }
        }
      }
    ]
  },
  "articles": [
    {
      "url": "...",
      "title": "기사 제목",
      "source": "CNN",
      "country": "US",
      "media_type": "민영",
      "media_category": "broadcasting",
      "content": "...",
      "snippet": "...",
      "published_date": "2025-01-15",
      "analysis": {
        "stance": "supporting",
        "confidence": 0.85,
        "key_evidence": ["..."],
        "framing": "..."
      }
    }
  ],
  "articles_count": 10
}
```

#### `POST /api/optimize-query`
사용자 질문을 검색 쿼리로 최적화

**Request:**
```json
{
  "user_input": "이 영상에서 말하는 금리 인상 시기가 언제인가요?",
  "context": {
    "title_kr": "2025년 경제 전망",
    "key_claims": [...]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "interpreted_intent": "금리 인상 시기에 대한 정보 확인",
    "search_keywords_en": ["interest rate", "hike", "timing", "2025"],
    "target_country_codes": ["US"],
    "confidence": 0.9
  }
}
```

### 언론사 API

#### `GET /api/media-credibility`
전체 언론사 목록 조회

**Response:**
```json
{
  "success": true,
  "data": [...],
  "count": 150
}
```

#### `GET /api/media-credibility/<source>`
특정 언론사 정보 조회

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "CNN",
    "country": "US",
    "type": "민영",
    "category": "broadcasting"
  }
}
```

#### `POST /api/media-credibility/reload`
Firestore 캐시 강제 새로고침

### 히스토리 API

#### `GET /api/history/recent?limit=20&type=youtube`
최근 분석 히스토리

**Response:**
```json
{
  "success": true,
  "data": [...],
  "count": 20
}
```

#### `GET /api/history/popular?limit=10&days=7`
인기 콘텐츠 (조회수 기준)

#### `GET /api/history/by-topic/<topic>?limit=20`
특정 주제로 검색

#### `GET /api/history/statistics`
전체 통계

**Response:**
```json
{
  "success": true,
  "data": {
    "total_analyses": 1523,
    "total_views": 8945,
    "youtube_count": 892,
    "article_count": 631
  }
}
```

---

## 🛠️ 주요 기술 스택

### Backend
- **Python 3.10+**
- **Flask** - 웹 프레임워크
- **Gemini 2.0 Flash** - AI 분석 (Vertex AI)
- **GDELT BigQuery** - 글로벌 뉴스 검색 (250M+ articles)
- **Firestore** - NoSQL 데이터베이스
- **BeautifulSoup4** - 웹 스크래핑
- **trafilatura** - 기사 본문 추출 (고품질)
- **youtube-transcript-api** - YouTube 자막 추출
- **ThreadPoolExecutor** - 병렬 처리

### Frontend
- **Vanilla JavaScript (ES6 Modules)**
- **Chrome Extension API**
- **Fetch API** - HTTP 요청
- **CommonMark** - 마크다운 렌더링

---

## 📚 문서

- **[파이프라인 분석](docs/PIPELINE_ANALYSIS.md)**: 1차/2차 분석 흐름 상세
- **[리팩토링 요약](docs/REFACTORING_SUMMARY.md)**: 코드 개선 내역
- **[가상 실행 테스트](docs/VIRTUAL_EXECUTION_TEST.md)**: 문법 및 흐름 검증

---

## 📄 라이선스

MIT License

---

## 👥 기여

이슈 및 Pull Request 환영합니다!

### 개발 가이드라인
1. 코드 포맷팅: `make format` (Black)
2. 린트 체크: `make lint` (Flake8)
3. 테스트 실행: `pytest tests/`

---

## 📞 문의

프로젝트 관련 문의는 GitHub Issues를 이용해주세요.

---

## 🎯 로드맵

- [ ] 실시간 뉴스 알림 (Pub/Sub)
- [ ] 다국어 지원 (EN, JP, ZH)
- [ ] 시각화 대시보드 (Chart.js)
- [ ] 사용자 인증 (Firebase Auth)
- [ ] 북마크 및 공유 기능
