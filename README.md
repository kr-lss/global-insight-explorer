Global Insight Explorer
다양한 관점으로 세계를 탐색하는 미디어 분석 플랫폼

주요 기능
1차 분석
YouTube 영상 및 웹 기사에서 핵심 주장 추출
Gemini AI 기반 요약 및 검색 키워드 생성
관련 국가 및 주제 자동 태깅
2차 분석
GDELT BigQuery를 활용한 전 세계 언론 보도 검색
국가별, 언론사별 입장 비교 (지지/반대/중립)
언론사 정보 자동 매칭 (Firestore 기반)
분석 히스토리
Firestore 기반 분석 기록 관리
인기 콘텐츠 및 최근 분석 조회
설치
1. 환경 설정
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
2. GCP 설정
# Firestore 생성
gcloud firestore databases create --location=us-central1

# API 활성화
gcloud services enable bigquery.googleapis.com aiplatform.googleapis.com

# 서비스 계정 키 생성
gcloud iam service-accounts keys create key.json \
  --iam-account=your-service-account@your-project.iam.gserviceaccount.com

export GOOGLE_APPLICATION_CREDENTIALS="key.json"
3. 환경 변수
.env 파일 생성:

GCP_PROJECT=your-project-id
GCP_REGION=us-central1
GCS_BUCKET_NAME=your-bucket-name
4. Firestore 데이터 업로드
python scripts/upload_media_to_firestore.py
5. 서버 실행
python -m app.main
서버: http://127.0.0.1:8080

API 엔드포인트
1차 분석
POST /api/analyze

{
  "url": "https://youtube.com/watch?v=...",
  "inputType": "youtube"
}
2차 분석
POST /api/find-sources

{
  "url": "https://...",
  "inputType": "youtube",
  "claims_data": [
    {
      "claim_kr": "주장",
      "search_keywords_en": ["keyword1", "keyword2"],
      "target_country_codes": ["US", "CN"]
    }
  ]
}
언론사 정보
GET /api/media-credibility

히스토리
GET /api/history/recent?limit=20

GET /api/history/popular?limit=10&days=7

기술 스택
Backend
Python 3.10+
Flask
Gemini 2.0 Flash (Vertex AI)
GDELT BigQuery
Firestore
BeautifulSoup4
trafilatura
youtube-transcript-api
Frontend
Vanilla JavaScript
Chrome Extension API
프로젝트 구조
app/
├── main.py                 # Flask 앱
├── config.py               # 설정
├── routes/                 # API 엔드포인트
├── utils/                  # 비즈니스 로직
├── models/                 # 데이터 모델
└── prompts/                # AI 프롬프트

frontend/
├── index.html              # 웹 앱
├── popup.html              # Chrome Extension
├── main.js
└── popup.js
라이선스
MIT License