# YouTube 영상 분석 & URL Context 가이드

## 📚 목차
- [개요](#개요)
- [설치](#설치)
- [1. Direct URL Processing (유튜브 영상 분석)](#1-direct-url-processing-유튜브-영상-분석)
- [2. URL Context (웹 크롤링)](#2-url-context-웹-크롤링)
- [3. 비동기 처리 (선택사항)](#3-비동기-처리-선택사항)
- [FAQ](#faq)

---

## 개요

이 프로젝트에 새롭게 추가된 두 가지 기능:

### ✅ 추가된 기능
1. **Direct URL Processing**: 유튜브 URL을 다운로드 없이 Gemini API에 직접 전달하여 분석
2. **URL Context**: 웹페이지 URL을 크롤링 없이 Gemini API에 전달하여 내용 추출

### 💭 주석 처리된 기능 (선택적 사용)
3. **Async Processing**: 여러 영상/페이지를 병렬로 빠르게 처리

---

## 설치

### 1. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

새로 추가된 패키지:
- `google-genai==0.3.0` - Gemini API 클라이언트
- `pydantic==2.10.5` - 데이터 검증
- `tenacity==9.0.0` - 재시도 로직
- `httpx==0.28.1` - 비동기 HTTP 클라이언트

### 2. 환경 변수 설정
`.env` 파일에 다음 설정 추가:
```bash
GCP_PROJECT=your-project-id
GCP_REGION=us-central1
```

---

## 1. Direct URL Processing (유튜브 영상 분석)

### 🎯 장점
- ✅ 유튜브 크롤링 차단 완전 우회
- ✅ 영상 다운로드 불필요 (저장공간 절약)
- ✅ 구현이 매우 간단
- ✅ 공개 영상 모두 분석 가능

### 📝 기본 사용법

```python
from app.utils.youtube_video_service import YouTubeVideoService

# 서비스 초기화
service = YouTubeVideoService()

# 영상 요약
result = service.analyze_video(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    analysis_type="summary"
)

print(result)
# {
#   "title": "영상 제목",
#   "summary": "핵심 내용 요약",
#   "key_points": ["포인트 1", "포인트 2"],
#   "duration_estimate": "10분",
#   "topics": ["주제1", "주제2"]
# }
```

### 📊 분석 타입

#### 1) Summary (요약)
```python
result = service.analyze_video(video_url, analysis_type="summary")
```
출력:
- title: 제목
- summary: 요약 (3-5문장)
- key_points: 주요 포인트
- duration_estimate: 재생 시간
- topics: 주제 목록

#### 2) Claims (주장 추출)
```python
result = service.analyze_video(video_url, analysis_type="claims")
```
출력:
- key_claims: 핵심 주장 목록
- related_countries: 관련 국가
- search_keywords: 검증용 키워드
- topics: 주제
- summary: 전체 요약

#### 3) Transcript (대화 내용)
```python
result = service.analyze_video(video_url, analysis_type="transcript")
```
출력:
- transcript: 전체 대화 내용
- speakers: 화자 목록
- key_moments: 주요 순간 (타임스탬프 포함)

### 🧪 테스트 방법
```bash
cd examples
python test_youtube_video_service.py
```

---

## 2. URL Context (웹 크롤링)

### 🎯 장점
- ✅ HTML 파싱 코드 불필요
- ✅ JavaScript 렌더링 자동 지원
- ✅ 최대 20개 URL 동시 분석
- ✅ CORS 문제 없음

### 📝 기본 사용법

#### 1) 단일 웹페이지 분석
```python
from app.utils.url_context_service import URLContextService

# 서비스 초기화
service = URLContextService()

# 웹페이지 분석
result = service.analyze_webpage("https://example.com/article")

print(result)
# {
#   "title": "기사 제목",
#   "summary": "내용 요약",
#   "key_claims": ["주장 1", "주장 2"],
#   "topics": ["주제1", "주제2"],
#   "related_countries": ["국가1", "국가2"],
#   "author": "작성자",
#   "published_date": "2024-01-01"
# }
```

#### 2) 여러 URL 비교 분석 (최대 20개)
```python
urls = [
    "https://bbc.com/news/article1",
    "https://cnn.com/news/article2",
    "https://reuters.com/news/article3"
]

result = service.analyze_multiple_urls(urls)

print(result)
# {
#   "common_topics": ["공통 주제1", "공통 주제2"],
#   "different_perspectives": [
#     {
#       "topic": "주제",
#       "url1_view": "첫 번째 관점",
#       "url2_view": "두 번째 관점"
#     }
#   ],
#   "summary": "전체 비교 요약",
#   "credibility_notes": "신뢰성 평가"
# }
```

#### 3) 기사 본문만 추출
```python
content = service.extract_article_content("https://example.com/article")
print(content)  # 순수 텍스트
```

### 🎨 커스텀 프롬프트
```python
custom_prompt = """
다음 기사에서 통계 데이터만 추출해주세요:

응답 형식:
{
  "statistics": [
    {"metric": "지표명", "value": "값", "source": "출처"}
  ]
}
"""

result = service.analyze_webpage(
    url="https://example.com/article",
    analysis_prompt=custom_prompt
)
```

### 🧪 테스트 방법
```bash
cd examples
python test_url_context_service.py
```

---

## 3. 비동기 처리 (선택사항)

### 🚀 언제 사용하나요?
- 5개 이상의 영상/페이지를 동시에 빠르게 처리해야 할 때
- 대시보드나 배치 작업에서 성능이 중요할 때

### 📦 활성화 방법

#### 1단계: 서비스 파일에서 주석 제거

**`app/utils/youtube_video_service.py`**:
```python
# 파일 하단의 주석 제거
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt

class AsyncYouTubeVideoService:
    # ... (주석 해제)
```

**`app/utils/url_context_service.py`**:
```python
# 파일 하단의 주석 제거
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt

class AsyncURLContextService:
    # ... (주석 해제)
```

#### 2단계: 비동기 코드 작성

```python
import asyncio
from app.utils.youtube_video_service import AsyncYouTubeVideoService

async def main():
    service = AsyncYouTubeVideoService()

    video_urls = [
        "https://www.youtube.com/watch?v=VIDEO_1",
        "https://www.youtube.com/watch?v=VIDEO_2",
        "https://www.youtube.com/watch?v=VIDEO_3",
        "https://www.youtube.com/watch?v=VIDEO_4",
        "https://www.youtube.com/watch?v=VIDEO_5",
    ]

    # 5개 영상을 동시에 처리 (최대 3개씩)
    results = await service.analyze_multiple_videos(
        video_urls,
        analysis_type="summary",
        max_concurrent=3
    )

    print(f"{len(results)}개 영상 분석 완료!")
    for result in results:
        print(result['title'])

# 실행
asyncio.run(main())
```

### ⚡ 성능 비교

| 방법 | 5개 영상 처리 시간 | 비고 |
|------|------------------|------|
| 순차 처리 | ~150초 (2.5분) | 영상당 30초 |
| 비동기 (동시 3개) | ~60초 (1분) | 2.5배 빠름 |
| 비동기 (동시 5개) | ~40초 | 3.7배 빠름 |

### 🧪 비동기 테스트

테스트 파일에서 주석 해제:
```python
# examples/test_youtube_video_service.py
asyncio.run(test_multiple_videos_async())

# examples/test_url_context_service.py
asyncio.run(test_multiple_webpages_async())
```

---

## FAQ

### Q1. 기존 YoutubeExtractor와 뭐가 다른가요?

| 항목 | YoutubeExtractor (기존) | YouTubeVideoService (신규) |
|------|------------------------|---------------------------|
| 방식 | 자막 추출 → 실패 시 영상 다운로드 | URL 직접 전달 (다운로드 없음) |
| 속도 | 느림 (다운로드 필요) | 빠름 |
| 저장공간 | 필요 (GCS 사용) | 불필요 |
| 자막 없는 영상 | 처리 가능 (다운로드) | 처리 가능 (직접 분석) |
| 권장 | 기존 호환성 유지 | 새로운 프로젝트 |

### Q2. URL Context와 ArticleExtractor 차이는?

| 항목 | ArticleExtractor (기존) | URLContextService (신규) |
|------|------------------------|-------------------------|
| 방식 | requests + BeautifulSoup | Gemini URL Context API |
| JavaScript | 지원 안 함 | 자동 지원 |
| 정확도 | HTML 구조 의존 | AI 기반 (높음) |
| 구현 복잡도 | 높음 (파싱 로직 필요) | 낮음 |
| 비용 | 무료 | API 비용 발생 |

### Q3. 비동기 처리를 무조건 써야 하나요?

**아니요.** 다음 경우에만 사용하세요:
- ✅ 5개 이상 동시 처리
- ✅ 실시간 성능이 중요
- ✅ 배치 작업

**사용하지 않아도 되는 경우:**
- ❌ 1-3개 정도만 처리
- ❌ 성능보다 안정성 우선
- ❌ 코드 복잡도를 낮추고 싶을 때

### Q4. API 비용은 얼마나 드나요?

**Gemini 2.0 Flash 기준:**
- 영상 분석: 약 $0.01-0.05 per video
- 웹페이지 분석: 약 $0.001-0.005 per page

**절감 팁:**
- 캐싱 활용 (이미 분석한 URL은 재사용)
- Batch Processing 사용 (50% 할인)
- 짧은 영상 우선 처리

### Q5. 오류가 발생하면 어떻게 하나요?

#### 1) "Gemini API를 사용할 수 없습니다"
```bash
# GCP 인증 확인
gcloud auth application-default login

# 환경 변수 확인
echo $GCP_PROJECT
echo $GCP_REGION
```

#### 2) "URL을 로드할 수 없습니다"
- URL이 공개 접근 가능한지 확인
- 로그인이 필요한 페이지는 지원 안 됨
- 차단된 사이트인지 확인

#### 3) "JSON 파싱 실패"
- temperature를 0.0으로 설정 (이미 설정됨)
- 프롬프트에 "반드시 JSON만 출력" 명시 (이미 포함)

---

## 📚 추가 리소스

- [Gemini API 문서](https://ai.google.dev/gemini-api/docs)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai/docs)

---

## 🎓 요약

1. **Direct URL Processing**: 유튜브 크롤링 걱정 없이 간단하게 영상 분석
2. **URL Context**: 웹 크롤링 코드 없이 페이지 내용 추출
3. **Async Processing**: 필요할 때만 주석 해제해서 사용

**권장 사용 순서:**
```
1단계: Direct URL Processing으로 단일 영상 테스트
2단계: URL Context로 뉴스 기사 수집 테스트
3단계: 필요하면 Async Processing 활성화
```
