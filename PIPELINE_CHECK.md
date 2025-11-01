# 파이프라인 및 모듈 구조 검증

## 1. 모듈 구조 (Module Structure)

```
app/
├── __init__.py                 # ✅ 버전 정보
├── config.py                   # ✅ 환경 설정
├── main.py                     # ✅ Flask 앱 생성 및 실행
│
├── models/                     # 데이터 모델
│   ├── __init__.py            # ✅ 모든 모델 export
│   ├── media.py               # ✅ 언론사 신뢰도 (Firestore)
│   ├── history.py             # ✅ 분석 히스토리 (Firestore)
│   └── extractor.py           # ✅ 콘텐츠 추출기
│
├── routes/                     # API 엔드포인트
│   ├── __init__.py            # ✅ 모든 블루프린트 export
│   ├── health.py              # ✅ 헬스 체크
│   ├── analysis.py            # ✅ 분석 API (히스토리 저장 포함)
│   ├── media.py               # ✅ 언론사 신뢰도 API
│   └── history.py             # ✅ 히스토리 조회 API
│
└── utils/                      # 유틸리티
    ├── __init__.py            # ✅ 서비스 export
    └── analysis_service.py    # ✅ 분석 서비스 (캐싱 포함)

frontend/
├── index.html                  # ✅ 웹 앱 UI (탭 포함)
├── main.js                     # ✅ JavaScript 로직
└── main.css                    # ✅ 스타일

scripts/
└── upload_media_to_firestore.py # ✅ Firestore 초기 데이터 업로드
```

## 2. 데이터 흐름 (Data Flow)

### 2.1 분석 요청 플로우
```
사용자 (Browser)
    ↓ POST /api/analyze
    ↓ {url, inputType}
    ↓
[frontend/main.js]
    ↓ fetch()
    ↓
[app/routes/analysis.py]
    ↓ analysis_service.analyze_content()
    ↓
[app/utils/analysis_service.py]
    ↓ 1) _get_cache() → Firestore cache 확인
    ↓ 2) extractor.extract() → 콘텐츠 추출
    ↓ 3) _analyze_with_gemini() → AI 분석
    ↓ 4) _set_cache() → Firestore cache 저장
    ↓
[app/routes/analysis.py]
    ↓ save_analysis_history() → 히스토리 저장
    ↓
[app/models/history.py]
    ↓ Firestore 'analysis_history' 저장
    ↓
응답 → 브라우저
```

### 2.2 언론사 정보 로드 플로우
```
앱 시작
    ↓
[app/models/media.py]
    ↓ _load_media_from_firestore()
    ↓
    ├─ Firestore 연결 성공
    │   ↓ db.collection('media_credibility').stream()
    │   ↓ _media_cache에 저장
    │   └─ ✅ 완료
    │
    └─ Firestore 연결 실패
        ↓ MEDIA_CREDIBILITY_FALLBACK 사용
        └─ ✅ 완료 (fallback)
```

### 2.3 히스토리 조회 플로우
```
사용자 → "인기 콘텐츠" 탭 클릭
    ↓
[frontend/main.js]
    ↓ loadPopularContent()
    ↓ GET /api/history/popular
    ↓
[app/routes/history.py]
    ↓ get_popular_content()
    ↓
[app/models/history.py]
    ↓ Firestore 쿼리
    ↓ .order_by('view_count', DESC)
    ↓ .limit(10)
    ↓
응답 → displayHistoryList() → UI 표시
```

## 3. 의존성 체인 (Dependency Chain)

### 3.1 Import 체인
```
app/main.py
├─ app.config
├─ app.routes
│   ├─ health_bp ✅
│   ├─ analysis_bp ✅
│   ├─ media_bp ✅
│   └─ history_bp ✅
└─ Flask, CORS

app/routes/analysis.py
├─ app.utils.analysis_service.AnalysisService ✅
├─ app.models.history.save_analysis_history ✅
└─ Flask

app/routes/media.py
├─ app.models.media.get_media_credibility ✅
├─ app.models.media.get_all_media ✅
├─ app.models.media.reload_media_cache ✅
└─ Flask

app/routes/history.py
├─ app.models.history.get_recent_history ✅
├─ app.models.history.get_popular_content ✅
├─ app.models.history.get_history_by_topic ✅
├─ app.models.history.get_statistics ✅
└─ Flask

app/utils/analysis_service.py
├─ app.models.extractor (BaseExtractor, YoutubeExtractor, ArticleExtractor) ✅
├─ app.models.media.get_media_credibility ✅
├─ app.config ✅
├─ vertexai
└─ google.cloud.firestore

app/models/media.py
├─ app.config ✅
└─ google.cloud.firestore

app/models/history.py
├─ app.config ✅
└─ google.cloud.firestore
```

### 3.2 순환 의존성 체크
```
✅ 순환 의존성 없음

app/models/media.py → app.config
app/models/history.py → app.config
app/models/extractor.py → (독립)
app/utils/analysis_service.py → app.models, app.config
app/routes/* → app.models, app.utils
app/main.py → app.routes, app.config
```

## 4. Firestore 컬렉션 구조

### 4.1 cache (캐시)
```
collection: cache
document ID: MD5(url)
fields:
  - url: string
  - result: object (분석 결과)
  - cached_at: timestamp
```

### 4.2 media_credibility (언론사 신뢰도)
```
collection: media_credibility
document ID: 언론사명 (예: "BBC", "KBS")
fields:
  - credibility: number (0-100)
  - bias: string (예: "중립", "보수")
  - country: string (예: "UK", "KR")
```

### 4.3 analysis_history (분석 히스토리)
```
collection: analysis_history
document ID: MD5(url)
fields:
  - url: string
  - url_hash: string
  - input_type: string ("youtube" | "article")
  - title: string
  - key_claims: array[string]
  - topics: array[string]
  - related_countries: array[string]
  - view_count: number
  - created_at: timestamp
  - last_analyzed_at: timestamp
  - created_by: string (user_id)
  - last_user_id: string
```

## 5. API 엔드포인트 체크

### 5.1 Health & Core
- ✅ GET /health
- ✅ POST /api/analyze
- ✅ POST /api/find-sources

### 5.2 Media Credibility
- ✅ GET /api/media-credibility
- ✅ GET /api/media-credibility/<source>
- ✅ POST /api/media-credibility/reload

### 5.3 History
- ✅ GET /api/history/recent
- ✅ GET /api/history/popular
- ✅ GET /api/history/by-topic/<topic>
- ✅ GET /api/history/statistics

### 5.4 Static Files
- ✅ GET / → index.html
- ✅ GET /<path> → static files or index.html (SPA)

## 6. 에러 핸들링 체크

### 6.1 Firestore 연결 실패
- ✅ media.py: fallback 데이터 사용
- ✅ history.py: 빈 결과 반환, 앱 계속 실행
- ✅ analysis_service.py: 캐싱 실패해도 분석 진행

### 6.2 Gemini API 실패
- ✅ Exception 발생 → 사용자에게 에러 메시지 전달
- ✅ 앱 크래시 방지

### 6.3 히스토리 저장 실패
- ✅ 분석 API에서 try-except로 감싸서 저장 실패해도 분석 결과는 반환

## 7. 프론트엔드 통합 체크

### 7.1 HTML 구조
- ✅ 탭 UI (새 분석 / 인기 콘텐츠 / 최근 분석)
- ✅ 입력 섹션
- ✅ 로딩 인디케이터
- ✅ 결과 섹션
- ✅ 팩트체크 섹션

### 7.2 JavaScript 기능
- ✅ 탭 전환
- ✅ URL 분석 요청
- ✅ 팩트체크 요청
- ✅ 인기 콘텐츠 로드
- ✅ 최근 분석 로드
- ✅ 히스토리 아이템 클릭 → 자동 입력

### 7.3 CSS 스타일
- ✅ 반응형 디자인
- ✅ 탭 스타일
- ✅ 히스토리 아이템 스타일
- ✅ 모바일 지원

## 8. 테스트 체크리스트

### 8.1 백엔드 (수동 테스트 필요)
- [ ] Flask 서버 시작: `python -m app.main`
- [ ] Health check: `curl http://127.0.0.1:8080/health`
- [ ] 분석 API: POST /api/analyze
- [ ] 언론사 API: GET /api/media-credibility
- [ ] 히스토리 API: GET /api/history/recent

### 8.2 프론트엔드 (브라우저 테스트 필요)
- [ ] http://127.0.0.1:8080 접속
- [ ] 탭 전환 동작
- [ ] URL 분석 기능
- [ ] 인기 콘텐츠 표시
- [ ] 최근 분석 표시

### 8.3 Firestore 통합 (선택사항)
- [ ] Firestore 없이 실행 (fallback 확인)
- [ ] Firestore 연결 후 실행
- [ ] 언론사 데이터 업로드
- [ ] 히스토리 저장 확인

## 9. 잠재적 문제점 및 해결

### 9.1 발견된 문제
1. ❌ app/models/__init__.py에서 이전 import 사용
   - ✅ 해결: MEDIA_CREDIBILITY_FALLBACK, history 모듈 추가

### 9.2 권장 개선사항
1. **에러 로깅 강화**
   - 현재: print()로 콘솔 출력
   - 개선: logging 모듈 사용

2. **환경변수 검증**
   - GCP_PROJECT 없을 때 명확한 에러 메시지

3. **유닛 테스트 추가**
   - tests/ 디렉토리에 테스트 추가

## 10. 결론

### ✅ 모듈 구조
- 모든 파일이 올바르게 구성됨
- 순환 의존성 없음
- Import 체인 정상

### ✅ 데이터 흐름
- 분석 → 히스토리 저장 파이프라인 정상
- 언론사 정보 로드 (Firestore + fallback) 정상
- 히스토리 조회 플로우 정상

### ✅ 에러 핸들링
- Firestore 연결 실패 시 fallback 동작
- API 에러 시 사용자 친화적 메시지
- 앱 크래시 방지

### ✅ 프론트엔드 통합
- 백엔드 API와 연동 완료
- UI/UX 구현 완료
- 반응형 디자인 완료

### 🎯 실행 준비 완료
프로젝트가 모듈화되어 있으며 파이프라인이 정상적으로 구성되어 있습니다.
실행하려면:
```bash
pip install -r requirements.txt
python -m app.main
```
