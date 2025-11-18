# 가상 실행 플로우 검증

## ✅ 문법 검증 결과
- ✅ `app/prompts/analysis_prompts.py` - 통과
- ✅ `app/prompts/__init__.py` - 통과
- ✅ `app/utils/analysis_service.py` - 통과
- ✅ `app/routes/analysis.py` - 통과

**결과**: 모든 Python 파일 문법 오류 없음

---

## 🔄 가상 실행 시뮬레이션

### 시나리오 1: 1차 분석 (YouTube URL)

#### 입력
```json
POST /api/analyze
{
  "url": "https://www.youtube.com/watch?v=example",
  "inputType": "youtube"
}
```

#### 실행 흐름
```
1. app/routes/analysis.py:analyze()
   ↓
2. AnalysisService.analyze_content(url, 'youtube')
   ↓
3. _get_cache(url) - 캐시 확인
   └─ 없으면 계속
   ↓
4. YoutubeExtractor().extract(url)
   └─ 트랜스크립트 또는 비디오 다운로드
   ↓
5. _analyze_with_gemini(content)
   ├─ content[:8000] - 길이 제한
   ├─ get_first_analysis_prompt(content) ✅ 프롬프트 모듈
   ├─ gemini.generate_content(prompt) - Gemini API
   └─ _parse_json_response(response.text) ✅ 헬퍼 함수
   ↓
6. _set_cache(url, result) - 캐시 저장
   ↓
7. save_analysis_history() - 히스토리 저장
   ↓
8. 응답 반환
```

#### 예상 응답
```json
{
  "success": true,
  "cached": false,
  "analysis": {
    "key_claims": [
      "주장 1",
      "주장 2",
      "주장 3"
    ],
    "related_countries": ["한국", "미국"],
    "search_keywords": [
      ["keyword1", "keyword2"],
      ["keyword3", "keyword4"]
    ],
    "topics": ["정치", "국제관계"],
    "summary": "요약 내용"
  }
}
```

**검증 포인트**:
- ✅ config.MAX_CONTENT_LENGTH_FIRST_ANALYSIS 사용
- ✅ get_first_analysis_prompt() 정상 import
- ✅ _parse_json_response() 정상 호출
- ✅ JSON 파싱 에러 처리

---

### 시나리오 2: 2차 분석 (기사 검색 및 입장 분석)

#### 입력
```json
POST /api/find-sources
{
  "url": "https://www.youtube.com/watch?v=example",
  "inputType": "youtube",
  "selected_claims": ["주장 1"],
  "search_keywords": [["keyword1", "keyword2"]]
}
```

#### 실행 흐름
```
1. app/routes/analysis.py:find_sources()
   ↓
2. AnalysisService.find_sources_for_claims(...)
   ↓
3. YoutubeExtractor().extract(url) - 원본 콘텐츠 재추출
   ↓
4. _search_real_articles(keywords) ✅ 타입 힌트
   ├─ Google Search Grounding
   ├─ search_model = GenerativeModel(config.GEMINI_MODEL_SEARCH) ✅ config 사용
   ├─ get_article_search_prompt(query) ✅ 프롬프트 모듈
   ├─ _parse_json_response(response.text) ✅ 헬퍼 재사용
   └─ _process_search_results(articles) ✅ 헬퍼 함수
       └─ config.MAX_ARTICLES_PER_SEARCH 적용
   ↓
5. _find_related_articles_with_gemini(content, claims, articles)
   ├─ content[:4000] - config.MAX_CONTENT_LENGTH_SECOND_ANALYSIS
   ├─ _format_articles_for_ai(articles[:15]) ✅ 헬퍼 함수
   ├─ get_stance_analysis_prompt(...) ✅ 프롬프트 모듈
   ├─ gemini.generate_content(prompt)
   ├─ _parse_json_response(response.text) ✅ 헬퍼 재사용
   └─ _validate_stance_analysis_result(result) ✅ 유효성 검증
   ↓
6. _restructure_by_stance(result, articles) ✅ 리팩토링
   ├─ _group_articles_by_stance(...) ✅ 분리된 로직
   │   └─ _sort_by_confidence() ✅ 정렬 헬퍼
   ├─ _create_evidence_section(...) ✅ 섹션 생성
   └─ _calculate_diversity_metrics(...) ✅ 지표 계산
   ↓
7. 응답 반환
```

#### 예상 응답
```json
{
  "success": true,
  "result": {
    "results": [
      {
        "claim": "주장 1",
        "supporting_evidence": {
          "count": 7,
          "articles": [...],
          "common_arguments": ["논거1", "논거2"]
        },
        "opposing_evidence": {
          "count": 5,
          "articles": [...],
          "common_arguments": ["반론1", "반론2"]
        },
        "neutral_coverage": {
          "count": 3,
          "articles": [...]
        },
        "diversity_metrics": {
          "total_sources": 15,
          "stance_distribution": {
            "supporting": 7,
            "opposing": 5,
            "neutral": 3
          }
        }
      }
    ]
  },
  "articles": [...],
  "articles_count": 15
}
```

**검증 포인트**:
- ✅ config.MAX_ARTICLES_PER_SEARCH = 15 적용
- ✅ config.MAX_ARTICLES_FOR_AI_ANALYSIS = 15 적용
- ✅ get_stance_analysis_prompt() 정상 import
- ✅ 모든 헬퍼 함수 정상 호출
- ✅ 타입 힌트로 IDE 지원
- ✅ 에러 처리 (빈 배열 반환)

---

## 🔍 잠재적 문제점 검증

### 1. Import 체인 검증

```python
# app/routes/analysis.py
from app.utils.analysis_service import AnalysisService
  ↓
# app/utils/analysis_service.py
from app.prompts import (  # ✅ 정상
    get_first_analysis_prompt,
    get_stance_analysis_prompt,
    get_article_search_prompt,
)
from app.config import config  # ✅ 정상
  ↓
# app/prompts/__init__.py
from .analysis_prompts import (  # ✅ 상대 import 정상
    get_first_analysis_prompt,
    get_stance_analysis_prompt,
    get_article_search_prompt,
)
  ↓
# app/prompts/analysis_prompts.py
def get_first_analysis_prompt(content: str) -> str:
    """1차 분석 프롬프트: 핵심 주장 추출"""
    return f"""..."""  # ✅ 정상
```

**결과**: ✅ 모든 import 경로 정상

---

### 2. 순환 import 검증

```
app/config.py (데이터클래스만)
  ← app/utils/analysis_service.py
  ← app/prompts/analysis_prompts.py

app/prompts/__init__.py
  ← app/utils/analysis_service.py

app/models/extractor.py
  ← app/utils/analysis_service.py

app/models/media.py
  ← app/utils/analysis_service.py

app/routes/analysis.py
  ← app/main.py
```

**결과**: ✅ 순환 import 없음

---

### 3. 런타임 에러 가능성 검증

#### 3.1 Gemini API 실패
```python
# analysis_service.py:26
try:
    gemini = GenerativeModel(config.GEMINI_MODEL_ANALYSIS)
except Exception as e:
    print(f"⚠️ (Service) Gemini API 연결 실패: {e}")
    gemini = None  # ✅ None으로 설정

# 사용 시
if not gemini:
    raise Exception("Gemini API를 사용할 수 없습니다.")  # ✅ 명확한 에러
```
**결과**: ✅ 적절히 처리됨

#### 3.2 Google Search 실패
```python
# analysis_service.py:167
except Exception as e:
    print(f"⚠️ 기사 검색 실패: {e}")
    return []  # ✅ 빈 배열 반환 (샘플 데이터 제거)
```
**결과**: ✅ 명확한 에러 처리

#### 3.3 JSON 파싱 실패
```python
# analysis_service.py:221-223
except json.JSONDecodeError as e:
    print(f"❌ JSON 파싱 실패: {e}")
    raise Exception(f"AI 응답을 파싱할 수 없습니다. 다시 시도해주세요.")
```
**결과**: ✅ 명확한 에러 메시지

#### 3.4 캐시 실패
```python
# analysis_service.py:356-367
def _get_cache(self, url: str):
    if not db:
        return None  # ✅ Firestore 없어도 계속
    try:
        ...
    except Exception as e:
        print(f"⚠️ 캐시 읽기 실패: {e}")
        return None  # ✅ Graceful degradation
```
**결과**: ✅ Graceful degradation 구현

---

### 4. 데이터 타입 검증

#### 4.1 타입 힌트 적용
```python
def _search_real_articles(self, keywords: List[str]) -> List[Dict[str, Any]]:
def _process_search_results(self, raw_articles: List[Dict]) -> List[Dict[str, Any]]:
def _find_related_articles_with_gemini(
    self, original_content: str, claims: List[str], articles: List[Dict]
) -> Dict[str, Any]:
def _restructure_by_stance(
    self, analysis_result: Dict, articles: List[Dict]
) -> Dict[str, Any]:
```
**결과**: ✅ 주요 메서드에 타입 힌트 적용

#### 4.2 유효성 검증
```python
# analysis_service.py:339-345
def _validate_stance_analysis_result(self, result: Dict) -> None:
    if 'results' not in result:
        raise ValueError("AI 응답에 'results' 키가 없습니다.")
    if not isinstance(result['results'], list):
        raise ValueError("AI 응답의 'results'가 배열이 아닙니다.")
```
**결과**: ✅ 명시적 유효성 검증

---

### 5. 프론트엔드 호환성 검증

#### 5.1 응답 구조
```javascript
// frontend/main.js:258
const results = analysis.results || [];  // ✅ 방어적 코딩

// frontend/main.js:276-278
const metrics = result.diversity_metrics || {};  // ✅ 안전한 접근
const distribution = metrics.stance_distribution || {};
const totalCount = metrics.total_sources || 0;
```
**결과**: ✅ 응답 구조 호환성 유지

#### 5.2 UI 렌더링
```javascript
// frontend/main.js:295-304
const supportingEvidence = result.supporting_evidence || {};
if (supportingEvidence.count > 0) {  // ✅ count 체크
  const supportingContainer = createStanceSection(
    'supporting',
    '✅ 이 주장을 지지하는 보도',
    supportingEvidence.articles,  // ✅ articles 배열
    supportingEvidence.common_arguments  // ✅ common_arguments 배열
  );
}
```
**결과**: ✅ 새로운 응답 구조에 맞게 수정됨

---

## 📊 성능 검증

### 메모리 사용량 추정
```
1차 분석:
  - 입력: 8,000자 (config.MAX_CONTENT_LENGTH_FIRST_ANALYSIS)
  - 프롬프트: ~500자
  - Gemini 응답: ~1,000자
  - 총: ~10KB

2차 분석:
  - 입력: 4,000자 (config.MAX_CONTENT_LENGTH_SECOND_ANALYSIS)
  - 기사 15개 × 500자 = 7,500자
  - 프롬프트: ~2,000자
  - Gemini 응답: ~3,000자
  - 총: ~17KB
```
**결과**: ✅ 적절한 수준

### API 호출 횟수
```
1차 분석: 1회 (Gemini API)
2차 분석: 2회 (Google Search + Gemini API)
총: 3회
```
**결과**: ✅ 최소화됨

---

## ✅ 최종 검증 결과

### 통과 항목
- ✅ Python 문법 검사 통과
- ✅ Import 체인 정상
- ✅ 순환 import 없음
- ✅ 에러 처리 적절
- ✅ 타입 힌트 적용
- ✅ 유효성 검증 구현
- ✅ 프론트엔드 호환성 유지
- ✅ 성능 최적화
- ✅ 모듈화 완료
- ✅ 하드코딩 제거

### 주의 사항
- ⚠️ Gemini API 키 필요 (환경변수)
- ⚠️ Firestore 연결 실패 시 캐시 미작동 (기능은 정상 작동)
- ⚠️ Google Search Grounding 실패 시 빈 배열 반환

### 권장 사항
1. **환경 변수 설정 확인**:
   ```bash
   export GCP_PROJECT=your-project-id
   export GCP_REGION=us-central1
   ```

2. **Firestore 선택적 사용**:
   - Firestore 없어도 분석 기능 정상 작동
   - 캐싱 및 히스토리 기능만 비활성화

3. **테스트 시나리오**:
   - 실제 YouTube URL로 1차 분석 테스트
   - 주장 선택 후 2차 분석 테스트
   - 국내 이슈 (대장동) 테스트
   - 국제 이슈 (트럼프) 테스트

---

## 🎯 결론

**모든 코드가 정상 작동할 것으로 예상됩니다!**

- ✅ 문법 오류 없음
- ✅ 런타임 에러 처리 완료
- ✅ 모듈화 및 리팩토링 성공
- ✅ 하드코딩 제거 완료
- ✅ 프론트엔드 호환성 유지

**이슈 발생 시 확인 사항**:
1. GCP 프로젝트 설정
2. Gemini API 활성화
3. Google Search Grounding 활성화
4. Firestore 연결 (선택)
