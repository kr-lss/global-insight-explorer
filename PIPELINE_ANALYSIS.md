# 파이프라인 및 데이터 흐름 분석

## 📊 전체 파이프라인

### 1차 분석 (/api/analyze)
```
사용자 URL 입력
  ↓
Flask: analysis.py → analyze()
  ↓
AnalysisService.analyze_content()
  ↓
BaseExtractor.extract() (YouTube 또는 Article)
  ↓
Gemini 2.5 Flash (최대 8000자)
  ↓
결과: {
  key_claims: ["주장1", "주장2", ...],
  related_countries: ["한국", "미국", ...],
  search_keywords: [["kw1", "kw2"], ...],
  topics: ["정치", "경제", ...],
  summary: "요약 내용"
}
  ↓
Firestore 캐싱 (MD5(url) 키)
  ↓
프론트엔드: displayAnalysisResults()
```

### 2차 분석 (/api/find-sources) - **새로운 입장 기반 방식**
```
사용자 claim 선택
  ↓
Flask: analysis.py → find_sources()
  ↓
AnalysisService.find_sources_for_claims()
  ↓
Step 1: Google Search Grounding (최대 15개 기사)
  - Gemini 2.0 Flash Exp
  - search_keywords 사용
  ↓
Step 2: 각 기사의 입장 분석
  _find_related_articles_with_gemini()
  - Gemini 2.5 Flash (최대 4000자)
  - 프롬프트: "각 기사가 주장에 대해 어떤 입장인가?"
  ↓
  AI 응답: {
    results: [{
      claim: "...",
      article_analyses: [
        {
          article_index: 1,
          stance: "supporting" | "opposing" | "neutral",
          confidence: 0.0~1.0,
          key_evidence: ["근거1", "근거2"],
          framing: "프레임 설명"
        }
      ],
      stance_summary: {
        supporting_count: N,
        opposing_count: M,
        neutral_count: K,
        common_supporting_arguments: [...],
        common_opposing_arguments: [...]
      }
    }]
  }
  ↓
Step 3: 입장별 재구조화
  _restructure_by_stance()
  - supporting_evidence: {count, articles, common_arguments}
  - opposing_evidence: {count, articles, common_arguments}
  - neutral_coverage: {count, articles}
  - diversity_metrics: {total_sources, stance_distribution}
  ↓
프론트엔드: displaySourcesResults()
  - 입장 분포 요약
  - 지지 입장 섹션 (녹색 테두리)
  - 반대 입장 섹션 (빨간색 테두리)
  - 중립 보도 섹션 (회색 테두리)
```

---

## ✅ 주요 개선사항

### 1. **내용 기반 입장 분류**
- **이전**: `related_articles` + `perspective` (일반 설명)
- **현재**: `stance` (supporting/opposing/neutral) + `key_evidence` (구체적 인용)

### 2. **사전 라벨링 제거**
- **이전**: 언론사 DB에 political_leaning 저장 필요
- **현재**: 각 기사의 내용을 기준으로 동적 분석
- **장점**: 같은 언론사도 이슈마다 다른 입장 가능

### 3. **국내/국제 구분 없음**
- **이전**: 국가별 언론사로만 대립 구조 파악 가능
- **현재**: 내용 기반이므로 국내 정치 이슈도 동일하게 작동
- **예시**:
  - 국제: "트럼프 관세" → BBC(반대), Fox(지지)
  - 국내: "대장동 의혹" → 조선일보(지지), 한겨레(반대)

### 4. **투명한 근거 제시**
- `key_evidence`: 각 기사의 핵심 인용문
- `framing`: 기사가 사용하는 서술 방식
- `confidence`: AI의 확신도 (0.0 ~ 1.0)

---

## ⚠️ 잠재적 문제점 및 해결 방안

### 1. **AI 응답 일관성 문제**
**문제**: AI가 항상 정확한 JSON을 반환하지 않을 수 있음

**해결**:
- Try-catch로 에러 처리 (이미 구현됨)
- JSON 파싱 실패 시 명확한 에러 메시지

**추가 개선안**:
```python
# analysis_service.py Line 307-319
try:
    response = gemini.generate_content(prompt)
    result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
    parsed_result = json.loads(result_text)

    # 유효성 검증 추가
    if 'results' not in parsed_result:
        raise ValueError("AI 응답에 'results' 키가 없습니다.")

    return self._restructure_by_stance(parsed_result, articles)
except json.JSONDecodeError as e:
    print(f"❌ JSON 파싱 실패: {e}")
    print(f"AI 응답 원본: {result_text[:500]}")
    raise Exception(f"AI 응답을 파싱할 수 없습니다.")
```

### 2. **stance_summary 카운트 불일치**
**문제**: AI가 생성한 `supporting_count`와 실제 분류된 기사 수가 다를 수 있음

**해결**: `_restructure_by_stance()`에서 실제 카운트를 재계산 (이미 구현됨)
```python
# Line 364: count는 실제 배열 길이 사용
'count': len(supporting_articles)
```

### 3. **컨텍스트 길이 제한**
**문제**: 15개 기사 전체를 AI에게 보내면 토큰 초과 가능

**현재 설정**:
- 원본 콘텐츠: 최대 4000자
- 기사: 15개 (각 제목+출처+snippet)

**모니터링 필요**:
- 기사 snippet이 너무 길면 잘라야 할 수 있음
- 15개 → 10개로 줄이는 것도 고려

### 4. **Google Search 실패 시**
**문제**: 샘플 데이터가 반환되면 stance 분석이 무의미

**현재 처리**:
```python
# Line 195-199: Fallback to sample data
except Exception as e:
    print(f"⚠️ 기사 검색 실패: {e}")
    return self._get_sample_articles(keywords)
```

**개선안**:
```python
# 샘플 데이터 대신 빈 배열 반환
except Exception as e:
    print(f"⚠️ 기사 검색 실패: {e}")
    return []  # 또는 에러를 사용자에게 명확히 전달
```

### 5. **프론트엔드 에러 처리**
**문제**: 백엔드가 새로운 구조를 반환하는데 예외 케이스 처리 부족

**개선안** (main.js):
```javascript
// Line 295-304: 안전한 접근
const supportingEvidence = result.supporting_evidence || {};
if (supportingEvidence.count > 0) {  // count가 undefined면 false
  // ...
}
```
이미 구현됨 ✅

---

## 🔍 데이터 구조 비교

### 이전 응답 형식
```json
{
  "results": [
    {
      "claim": "주장",
      "related_articles": [1, 3, 5],  // article_index 배열
      "perspectives": {
        "기사1": "이 기사는 ..."
      },
      "missing_context": "...",
      "coverage_countries": ["미국", "영국"]
    }
  ]
}
```

### 새로운 응답 형식
```json
{
  "results": [
    {
      "claim": "주장",
      "supporting_evidence": {
        "count": 7,
        "articles": [
          {
            "title": "...",
            "source": "조선일보",
            "url": "...",
            "credibility": 75,
            "analysis": {
              "stance": "supporting",
              "confidence": 0.9,
              "key_evidence": ["근거1", "근거2"],
              "framing": "부패 의혹 프레임"
            }
          }
        ],
        "common_arguments": ["공통 논거1", "공통 논거2"]
      },
      "opposing_evidence": { /* 동일 구조 */ },
      "neutral_coverage": { /* articles만 */ },
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
}
```

---

## 🎯 테스트 시나리오

### 시나리오 1: 국제 이슈
**입력**: https://www.youtube.com/watch?v=... (트럼프 관세 관련)
**기대 결과**:
- 1차: key_claims = ["트럼프가 관세를 인상한다", ...]
- 2차:
  - supporting: Fox News, Breitbart 등
  - opposing: CNN, BBC 등
  - 각각 핵심 근거와 프레임 제시

### 시나리오 2: 국내 정치
**입력**: https://news.sbs.co.kr/... (대장동 의혹)
**기대 결과**:
- 1차: key_claims = ["대장동 개발에서 특혜가 있었다", ...]
- 2차:
  - supporting: 조선일보, 중앙일보 등
  - opposing: 한겨레, 경향신문 등
  - 각각 핵심 근거와 프레임 제시

### 시나리오 3: 중립적 이슈
**입력**: 과학 기술 뉴스 (예: AI 개발)
**기대 결과**:
- 대부분의 기사가 neutral로 분류
- supporting/opposing이 적거나 없음

---

## 📝 향후 개선 사항

1. **AI 프롬프트 최적화**
   - 더 명확한 지침으로 일관성 향상
   - Few-shot 예시 추가 고려

2. **에러 처리 강화**
   - Google Search 실패 시 사용자에게 명확한 안내
   - AI 응답 검증 로직 추가

3. **성능 최적화**
   - 기사 수 조정 (15개 → 10개)
   - 캐싱 전략 개선

4. **UI/UX 개선**
   - 입장 분포 시각화 (차트)
   - 필터링 기능 (입장별 토글)

5. **다국어 지원**
   - 프롬프트 언어 감지
   - 응답 언어 일치

---

## ✅ 결론

### 주요 성과
- ✅ 사전 라벨링 없이 내용 기반 입장 분류
- ✅ 국내/국제 이슈 모두 동일한 파이프라인 사용
- ✅ 투명한 근거 제시 (key_evidence, framing)
- ✅ 입장별 UI 구분 (색상 코딩)

### 잠재적 위험
- ⚠️ AI 응답 일관성 (모니터링 필요)
- ⚠️ 토큰 제한 (기사 수 조정 가능)
- ⚠️ Google Search 의존성 (Fallback 개선 필요)

### 다음 단계
1. 실제 데이터로 테스트
2. AI 응답 로깅 및 품질 모니터링
3. 사용자 피드백 수집
4. 필요 시 프롬프트 튜닝
