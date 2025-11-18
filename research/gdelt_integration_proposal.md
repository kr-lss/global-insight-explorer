# GDELT 통합 제안서

## 문제점
현재 Gemini Google Search Grounding은 다음 국가의 언론사 접근 불가:
- 🇨🇳 중국: 人民日报, 环球时报 (국내 버전)
- 🇷🇺 러시아: Pravda, Izvestia (제재 대상)
- 🇰🇵 북한: 조선중앙통신(KCNA)
- 🇮🇷 이란: Press TV
- 기타 제재/방화벽 국가

→ **글로벌 관점 비교 서비스의 핵심 가치 상실**

## 해결책: GDELT Project

### GDELT란?
- **Global Database of Events, Language, and Tone**
- Google Jigsaw + Google Cloud 지원
- 전 세계 언론사 실시간 모니터링 (100개 언어)
- BigQuery 무료 퍼블릭 데이터셋

### 포함 언론사 예시
| 국가 | 언론사 | GDELT 포함 |
|------|--------|-----------|
| 🇰🇵 북한 | KCNA (조선중앙통신) | ✅ |
| 🇨🇳 중국 | 新华社 (Xinhua) | ✅ |
| 🇨🇳 중국 | 人民日报 (People's Daily) | ✅ |
| 🇷🇺 러시아 | TASS | ✅ |
| 🇷🇺 러시아 | RT (Russia Today) | ✅ |
| 🇮🇷 이란 | Press TV | ✅ |
| 🇻🇪 베네수엘라 | TeleSUR | ✅ |

### 데이터 구조
```sql
-- BigQuery GDELT 스키마
SELECT
  GKGRECORDID,              -- 고유 ID
  DocumentIdentifier,       -- 기사 URL
  SourceCommonName,         -- 언론사명
  Themes,                   -- 주제 태그
  Persons,                  -- 언급된 인물
  Organizations,            -- 언급된 조직
  Locations,                -- 언급된 장소
  Tone,                     -- 감정 점수 (-100 ~ +100)
  DATE                      -- 발행일
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE = CURRENT_DATE()
  AND SourceCommonName LIKE '%Xinhua%'
```

## 통합 아키텍처

### 현재 시스템
```
User → Gemini Google Search → 검색 결과 (제한적)
```

### 개선 시스템
```
User → Keyword 추출 (Gemini)
     ↓
     → GDELT BigQuery 검색 (전 세계)
     ↓
     → 기사 URL 수집
     ↓
     → URL Context API로 본문 추출
     ↓
     → Gemini로 분석
```

## 구현 예시

### 1. GDELT 검색 함수
```python
from google.cloud import bigquery

def search_gdelt_articles(keywords: list, countries: list = None, days: int = 7):
    """
    GDELT에서 키워드 관련 기사 검색

    Args:
        keywords: 검색 키워드 리스트
        countries: 특정 국가 필터 (예: ['CN', 'RU', 'KP'])
        days: 검색 기간 (기본 7일)

    Returns:
        기사 리스트
    """
    client = bigquery.Client()

    # 키워드 조건
    keyword_conditions = " OR ".join([f"Themes LIKE '%{kw}%'" for kw in keywords])

    # 국가 필터
    country_filter = ""
    if countries:
        country_names = {
            'CN': '%China%',
            'RU': '%Russia%',
            'KP': '%North Korea%',
            'IR': '%Iran%'
        }
        country_conditions = " OR ".join([
            f"Locations LIKE '{country_names.get(c, c)}'"
            for c in countries
        ])
        country_filter = f"AND ({country_conditions})"

    query = f"""
    SELECT
        DocumentIdentifier as url,
        SourceCommonName as source,
        Themes,
        Locations,
        Tone,
        DATE as published_date
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE DATE >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      AND ({keyword_conditions})
      {country_filter}
      AND DocumentIdentifier IS NOT NULL
      AND SourceCommonName IS NOT NULL
    ORDER BY DATE DESC
    LIMIT 50
    """

    results = client.query(query).result()

    articles = []
    for row in results:
        articles.append({
            'url': row.url,
            'source': row.source,
            'published_date': str(row.published_date),
            'tone': row.Tone,
            'themes': row.Themes.split(';') if row.Themes else []
        })

    return articles
```

### 2. 통합 서비스
```python
# app/utils/gdelt_service.py
class GDELTNewsService:
    def __init__(self):
        self.bq_client = bigquery.Client()
        self.url_context = URLContextService()

    def search_global_news(self, keywords: list, include_restricted: bool = True):
        """
        제재 국가 포함 전 세계 뉴스 검색

        Args:
            keywords: 검색 키워드
            include_restricted: 중국/러시아/북한 등 포함 여부
        """
        # 1. GDELT에서 URL 수집
        articles = self._search_gdelt(keywords)

        # 2. URL Context로 본문 추출 (비동기 병렬)
        for article in articles:
            try:
                content = self.url_context.extract_article_content(article['url'])
                article['content'] = content
            except Exception as e:
                print(f"⚠️ 본문 추출 실패: {article['url']} - {e}")
                article['content'] = ""

        # 3. 국가별 그룹화
        by_country = self._group_by_country(articles)

        return by_country
```

## 비용 분석

### BigQuery 비용
- **GDELT 데이터셋**: 무료 (Google 제공)
- **쿼리 비용**: 매월 1TB 무료
- **예상 사용량**:
  - 1회 쿼리당 약 50MB
  - 월 10,000회 쿼리 = 500GB
  - **완전 무료** (1TB 이내)

### 대안 비교
| 방법 | 월 비용 | 커버리지 | 복잡도 | 법적 위험 |
|------|---------|----------|--------|-----------|
| **GDELT** | $0 | 전 세계 | 낮음 | 없음 |
| NewsAPI | $449 | 150개국 | 낮음 | 없음 |
| 프록시 크롤링 | $200+ | 제한적 | 높음 | **높음** |
| RSS Feed | $0 | 중간 | 중간 | 낮음 |

## 구현 단계

### Phase 1: GDELT 통합 (1-2일)
- [ ] BigQuery 연결 설정
- [ ] `gdelt_service.py` 구현
- [ ] 키워드 → GDELT 검색 파이프라인
- [ ] 국가별 언론사 매핑

### Phase 2: URL Context 연동 (1일)
- [ ] GDELT URL → URL Context API
- [ ] 본문 추출 및 캐싱
- [ ] 에러 핸들링

### Phase 3: 분석 통합 (1일)
- [ ] `analysis_service.py` 수정
- [ ] GDELT + Google Search 하이브리드
- [ ] 국가별 관점 비교 UI

## 테스트 시나리오

### 테스트 1: 북한 관련 뉴스
```python
keywords = ["North Korea", "missile", "DPRK"]
articles = search_gdelt_articles(keywords, countries=['KP', 'KR', 'US', 'JP'])

# 예상 결과:
# - KCNA (북한): "성공적인 국방력 강화"
# - 조선일보 (한국): "북한 도발 위협"
# - CNN (미국): "안보 우려"
# - NHK (일본): "배타적경제수역 낙하"
```

### 테스트 2: 우크라이나 전쟁
```python
keywords = ["Ukraine", "Russia", "war"]
articles = search_gdelt_articles(keywords, countries=['RU', 'UA', 'US', 'EU'])

# 예상 결과:
# - TASS (러시아): "특수군사작전"
# - Kyiv Post (우크라이나): "러시아 침공"
# - Reuters (영국): "중립적 보도"
```

## 추가 고려사항

### 1. 언어 번역
GDELT는 원문 언어로 저장
- Gemini 2.0에 번역 요청
- 또는 Cloud Translation API

### 2. 신뢰도 점수
GDELT Tone 활용:
- Positive (+100) ~ Negative (-100)
- 감정 편향 탐지

### 3. 중복 제거
같은 기사의 여러 버전:
- URL 정규화
- 제목 유사도 비교

## 결론

**GDELT 통합은 필수**입니다.

이유:
1. ✅ 북한/중국/러시아 등 모든 국가 커버
2. ✅ 완전 무료 (BigQuery 1TB 이내)
3. ✅ 법적 문제 없음 (공개 데이터)
4. ✅ 실시간 업데이트 (15분 간격)
5. ✅ Google Cloud 기반 (기존 인프라 활용)

**프록시 크롤링은 불필요**하며 오히려 위험합니다:
- ❌ 법적 위험 (제재 국가 접근)
- ❌ 기술적 복잡도 (반크롤링 대응)
- ❌ 유지보수 비용
- ❌ 차단 위험

## 다음 단계

바로 GDELT 통합을 시작할까요?
1. 간단한 테스트 스크립트로 실제 데이터 확인
2. 북한/중국/러시아 언론사 검색 가능 여부 검증
3. 통합 결정
