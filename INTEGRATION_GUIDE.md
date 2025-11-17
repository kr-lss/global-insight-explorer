# 기존 프로젝트 통합 가이드

## 📌 개요
이 가이드는 새로 추가된 기능을 기존 `analysis_service.py`와 통합하는 방법을 설명합니다.

---

## 🔧 통합 옵션

### 옵션 1: 기존 서비스 개선 (권장)

기존 `YoutubeExtractor`를 개선하여 Direct URL Processing을 우선 사용하도록 변경

#### 수정 위치: `app/models/extractor.py`

```python
class YoutubeExtractor(BaseExtractor):
    """하이브리드 유튜브 추출기"""

    def __init__(self):
        # 기존 초기화
        # ...

        # 새로운 Direct URL Service 추가
        try:
            from app.utils.youtube_video_service import YouTubeVideoService
            self.direct_service = YouTubeVideoService()
            print("✅ Direct URL Processing 활성화")
        except Exception as e:
            print(f"⚠️ Direct URL Processing 비활성화: {e}")
            self.direct_service = None

    def extract(self, url: str) -> str:
        """우선순위: Direct URL > 자막 > 영상 다운로드"""

        # 1순위: Direct URL Processing (가장 빠름)
        if self.direct_service:
            try:
                print("🎬 Direct URL Processing 시도 중...")
                result = self.direct_service.analyze_video(url, analysis_type="transcript")
                transcript = result.get('transcript', '')
                if transcript:
                    print(f"✅ Direct URL 성공: {len(transcript)} 글자")
                    return transcript
            except Exception as e:
                print(f"⚠️ Direct URL 실패: {e}")

        # 2순위: 자막 추출 (기존 방식)
        try:
            print("📝 자막 추출 시도 중...")
            transcript_text = self._extract_transcript(url)
            print(f"✅ 자막 추출 성공: {len(transcript_text)} 글자")
            return transcript_text
        except Exception as transcript_error:
            print(f"⚠️ 자막 추출 실패: {transcript_error}")

        # 3순위: 영상 다운로드 분석 (마지막 수단)
        if self.gemini_model and self.bucket:
            print("🎬 영상 다운로드 분석 시도 중...")
            try:
                video_analysis = self._analyze_video_with_gemini(url)
                print(f"✅ 영상 분석 성공: {len(video_analysis)} 글자")
                return video_analysis
            except Exception as video_error:
                print(f"❌ 영상 분석 실패: {video_error}")
                raise Exception(
                    f"모든 방식 실패\n"
                    f"Direct URL: 실패\n"
                    f"자막: {transcript_error}\n"
                    f"영상: {video_error}"
                )
        else:
            raise Exception(f"Direct URL과 자막 모두 실패: {transcript_error}")
```

**장점:**
- ✅ 기존 코드 수정 최소화
- ✅ 하위 호환성 유지
- ✅ 자동 폴백 (Direct URL 실패 시 자막 시도)

---

### 옵션 2: ArticleExtractor 개선

URL Context를 사용하여 웹 크롤링 개선

#### 수정 위치: `app/models/extractor.py`

```python
class ArticleExtractor(BaseExtractor):
    """기사 추출기 (URL Context 우선)"""

    def __init__(self):
        try:
            from app.utils.url_context_service import URLContextService
            self.url_service = URLContextService()
            print("✅ URL Context Service 활성화")
        except Exception as e:
            print(f"⚠️ URL Context Service 비활성화: {e}")
            self.url_service = None

    def extract(self, url: str) -> str:
        # 1순위: URL Context (AI 기반)
        if self.url_service:
            try:
                print("🌐 URL Context 시도 중...")
                content = self.url_service.extract_article_content(url)
                if content:
                    print(f"✅ URL Context 성공: {len(content)} 글자")
                    return content
            except Exception as e:
                print(f"⚠️ URL Context 실패: {e}")

        # 2순위: BeautifulSoup (기존 방식)
        try:
            print("🔍 BeautifulSoup 파싱 시도 중...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # (기존 로직)
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                tag.decompose()

            article = (
                soup.find('article')
                or soup.find('main')
                or soup.find(id='content')
                or soup.find(class_='content')
                or soup.body
            )

            if article:
                text = article.get_text(separator=' ', strip=True)
                text = ' '.join(text.split())
                print(f"✅ BeautifulSoup 성공: {len(text)} 글자")
                return text

        except Exception as e:
            print(f"❌ 기사 추출 실패: {e}")
            raise Exception("기사 내용을 가져오는 데 실패했습니다.")
```

**장점:**
- ✅ JavaScript 렌더링 자동 지원
- ✅ HTML 파싱 실패 시 폴백
- ✅ 정확도 향상

---

### 옵션 3: 새로운 API 엔드포인트 추가

기존 코드 수정 없이 새로운 엔드포인트로 제공

#### 새 파일: `app/routes/video_analysis.py`

```python
"""
Direct URL Processing을 위한 새로운 API 엔드포인트
"""
from flask import Blueprint, request, jsonify
from app.utils.youtube_video_service import YouTubeVideoService
from app.utils.url_context_service import URLContextService

video_bp = Blueprint('video_analysis', __name__, url_prefix='/api/v2')

youtube_service = YouTubeVideoService()
url_service = URLContextService()


@video_bp.route('/analyze-video', methods=['POST'])
def analyze_video():
    """유튜브 영상 Direct URL Processing"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL이 필요합니다'}), 400

        url = data.get('url')
        analysis_type = data.get('analysis_type', 'summary')

        result = youtube_service.analyze_video(url, analysis_type)

        return jsonify({
            'success': True,
            'result': result,
            'method': 'direct_url_processing'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@video_bp.route('/analyze-webpage', methods=['POST'])
def analyze_webpage():
    """웹페이지 URL Context 분석"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL이 필요합니다'}), 400

        url = data.get('url')
        prompt = data.get('prompt')

        result = url_service.analyze_webpage(url, prompt)

        return jsonify({
            'success': True,
            'result': result,
            'method': 'url_context'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@video_bp.route('/compare-urls', methods=['POST'])
def compare_urls():
    """여러 URL 비교 분석"""
    try:
        data = request.get_json()
        if not data or 'urls' not in data:
            return jsonify({'error': 'URLs가 필요합니다'}), 400

        urls = data.get('urls')
        if len(urls) > 20:
            return jsonify({'error': '최대 20개 URL까지 지원합니다'}), 400

        prompt = data.get('prompt')

        result = url_service.analyze_multiple_urls(urls, prompt)

        return jsonify({
            'success': True,
            'result': result,
            'urls_count': len(urls)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### `app/main.py`에 등록:

```python
from app.routes.video_analysis import video_bp

# 블루프린트 등록
app.register_blueprint(video_bp)
```

**API 사용 예시:**

```bash
# 유튜브 영상 분석
curl -X POST http://localhost:8080/api/v2/analyze-video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "analysis_type": "summary"}'

# 웹페이지 분석
curl -X POST http://localhost:8080/api/v2/analyze-webpage \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'

# 여러 URL 비교
curl -X POST http://localhost:8080/api/v2/compare-urls \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://bbc.com/news", "https://cnn.com/news"]}'
```

**장점:**
- ✅ 기존 API 영향 없음
- ✅ 새로운 기능만 별도 제공
- ✅ 테스트 및 롤백 용이

---

## 🎯 권장 통합 전략

### 단계별 적용

#### 1단계: 테스트 (1일)
```bash
# 예제 스크립트로 기능 확인
python examples/test_youtube_video_service.py
python examples/test_url_context_service.py
```

#### 2단계: 옵션 3 적용 (2-3일)
- 새로운 API 엔드포인트 추가
- 프론트엔드에서 신규 API 호출
- 기존 기능과 병행 운영

#### 3단계: 옵션 1, 2 적용 (1주일)
- 안정성 확인 후 기존 Extractor 개선
- Direct URL을 1순위로 변경
- 폴백 로직 유지

#### 4단계: 비동기 처리 검토 (선택)
- 성능 요구사항 발생 시
- Async Processing 주석 해제
- 배치 작업에 적용

---

## ⚠️ 주의사항

### 1. API 비용
- Direct URL Processing은 비용 발생
- 캐싱 전략 필수
- 무료 할당량 모니터링

### 2. 하위 호환성
- 기존 API 엔드포인트 유지
- 옵션 1, 2 적용 시 폴백 로직 필수
- 충분한 테스트 후 배포

### 3. 에러 처리
- 네트워크 오류 대비
- 재시도 로직 (tenacity 활용)
- 사용자에게 명확한 에러 메시지

---

## 📊 성능 비교

| 방법 | 속도 | 비용 | 정확도 | 권장 |
|------|------|------|--------|------|
| Direct URL (유튜브) | ⭐⭐⭐⭐⭐ | $$ | ⭐⭐⭐⭐⭐ | ✅ |
| 자막 추출 (유튜브) | ⭐⭐⭐⭐ | Free | ⭐⭐⭐⭐ | ✅ |
| 영상 다운로드 (유튜브) | ⭐⭐ | $$$ | ⭐⭐⭐⭐ | 폴백용 |
| URL Context (웹) | ⭐⭐⭐⭐ | $ | ⭐⭐⭐⭐⭐ | ✅ |
| BeautifulSoup (웹) | ⭐⭐⭐ | Free | ⭐⭐⭐ | 폴백용 |

---

## 🔗 다음 단계

1. `examples/` 디렉토리의 테스트 스크립트 실행
2. `YOUTUBE_ANALYSIS_GUIDE.md` 참고하여 사용법 숙지
3. 위 통합 옵션 중 하나 선택하여 적용
4. 필요 시 비동기 처리 활성화

질문이나 문제가 있으면 이슈를 등록해주세요!
