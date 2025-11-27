"""
GDELT Search Service - DOC API 기반 전문 검색 엔진 (v2 - Bug Fixed)

[Architecture]
- Primary: GDELT DOC 2.0 API (본문 전문 검색)
- Fallback: BigQuery GKG (메타데이터 검색)

[Design Pattern]
- Strategy Pattern: 검색 전략 교체 가능
- Template Method: 검색 파이프라인 표준화

[v2 수정사항]
- timespan 파라미터 규격 수정 (GDELT 공식 형식)
- 기존 로직 호환성 (entities/themes → keywords 병합)
- API 레벨 중복 URL 제거
"""

import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.cloud import bigquery
from app.config import config


# ============================================================
# Data Models
# ============================================================

@dataclass
class ArticleResult:
    """검색된 기사 데이터 모델"""
    url: str
    title: str
    source: str
    date: str
    snippet: str = ""
    country: str = "Unknown"
    tone: float = 0.0
    relevance_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'url': self.url,
            'title': self.title,
            'source': self.source,
            'date': self.date,
            'snippet': self.snippet,
            'country': self.country,
            'tone': self.tone,
            'relevance_score': self.relevance_score,
        }


# ============================================================
# URL Utilities (중복 제거용)
# ============================================================

def normalize_url(url: str) -> str:
    """
    URL 정규화 - 중복 판별용
    쿼리 파라미터와 프래그먼트를 제거하여 동일 기사 판별
    """
    try:
        parsed = urlparse(url)
        # scheme, netloc, path만 유지 (query, fragment 제거)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip('/'),  # 후행 슬래시 제거
            '', '', ''
        ))
        return normalized.lower()
    except:
        return url.lower()


def deduplicate_articles(articles: List[ArticleResult]) -> List[ArticleResult]:
    """
    기사 리스트에서 중복 URL 제거 (정규화 후 비교)
    """
    seen_urls: Set[str] = set()
    unique_articles: List[ArticleResult] = []

    for article in articles:
        normalized = normalize_url(article.url)
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique_articles.append(article)

    return unique_articles


# ============================================================
# Search Strategy Interface (Strategy Pattern)
# ============================================================

class SearchStrategy(ABC):
    """검색 전략 인터페이스"""

    @abstractmethod
    def search(self, keywords: List[str], **kwargs) -> List[ArticleResult]:
        """키워드로 기사 검색"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """검색 전략 사용 가능 여부"""
        pass


# ============================================================
# DOC API Strategy (Primary)
# ============================================================

class GDELTDocAPIStrategy(SearchStrategy):
    """
    GDELT DOC 2.0 API 검색 전략 (Primary)

    장점:
    - 기사 본문 전문 검색 (Full Text Search)
    - 실시간 업데이트
    - 무료

    단점:
    - Rate Limit 존재
    - 최근 3개월 데이터만 검색 가능

    [v2 수정]
    - timespan 파라미터 GDELT 공식 형식 사용
    """

    def __init__(self):
        self.base_url = config.GDELT_DOC_API_URL
        self.timeout = config.GDELT_DOC_TIMEOUT
        self._available = True

    def is_available(self) -> bool:
        return self._available

    def search(self, keywords: List[str], **kwargs) -> List[ArticleResult]:
        """DOC API로 기사 본문 전문 검색"""
        if not keywords:
            return []

        try:
            # 1. 검색 쿼리 구성
            query = self._build_query(keywords, kwargs.get('domains'))

            # 2. API 요청 파라미터
            params = {
                'query': query,
                'mode': 'artlist',
                'maxrecords': config.GDELT_DOC_MAX_RECORDS,
                'format': 'json',
                'sort': 'DateDesc',
            }

            # [수정됨] timespan은 GDELT 공식 형식 사용 ("1w", "1m", "3m" 등)
            timespan = kwargs.get('timespan', config.GDELT_SEARCH_TIMESPAN)
            if timespan:
                params['timespan'] = timespan

            print(f"🔍 [DOC API] 검색 쿼리: {query[:100]}...")
            print(f"   timespan: {timespan}")

            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            # 3. 결과 파싱
            data = response.json()
            articles = self._parse_response(data)

            # [추가됨] API 레벨 중복 제거
            articles = deduplicate_articles(articles)

            print(f"✅ [DOC API] {len(articles)}개 기사 발견 (중복 제거 후)")
            return articles

        except requests.exceptions.Timeout:
            print(f"⚠️ [DOC API] 타임아웃 ({self.timeout}초)")
            self._available = False
            return []
        except requests.exceptions.RequestException as e:
            print(f"⚠️ [DOC API] 요청 실패: {e}")
            self._available = False
            return []
        except Exception as e:
            print(f"❌ [DOC API] 예외 발생: {e}")
            return []

    def _build_query(self, keywords: List[str], domains: Optional[tuple] = None) -> str:
        """GDELT DOC API 쿼리 문자열 생성 (경량화 버전)"""

        # [수정 1] 상위 3개 키워드만 사용 (API 제한 고려)
        top_keywords = keywords[:3]

        refined_keywords = []
        for kw in top_keywords:
            # [수정 2] 쿼리가 너무 길어지는 것을 방지하기 위해 3단어 이상은 핵심만 추출하거나 앞부분만 사용
            parts = kw.split()
            if len(parts) > 3:
                # 예: "Japan China trade war impact" -> "Japan China trade"
                kw = " ".join(parts[:3])

            # 따옴표로 감싸서 구문 검색 (정확도 향상)
            refined_keywords.append(f'"{kw}"')

        if not refined_keywords:
            return ""

        # [수정 3] 도메인 필터 제거!
        # (쿼리 길이 확보를 위해 제거하고, 품질 관리는 LLM Judge에게 위임)
        keyword_query = " OR ".join(refined_keywords)
        query = f"({keyword_query})"

        return query

    def _parse_response(self, data: Dict) -> List[ArticleResult]:
        """API 응답을 ArticleResult 리스트로 변환"""
        articles = []

        if 'articles' not in data:
            return articles

        for item in data['articles']:
            try:
                # 날짜 포맷 변환 (20240501T120000Z → 2024-05-01)
                raw_date = item.get('seendate', '')
                formatted_date = self._format_date(raw_date)

                # 도메인에서 소스명 추출
                source = item.get('domain', 'Unknown')

                article = ArticleResult(
                    url=item.get('url', ''),
                    title=item.get('title', ''),
                    source=source,
                    date=formatted_date,
                    snippet=item.get('socialimage', '') or '',
                    country=self._extract_country(item),
                )

                if article.url:  # URL이 있는 경우만 추가
                    articles.append(article)

            except Exception as e:
                print(f"⚠️ 기사 파싱 오류: {e}")
                continue

        return articles

    def _format_date(self, raw_date: str) -> str:
        """날짜 포맷 변환"""
        if not raw_date:
            return ""
        try:
            # 20240501T120000Z 형식
            dt = datetime.strptime(raw_date[:8], '%Y%m%d')
            return dt.strftime('%Y-%m-%d')
        except:
            return raw_date[:10] if len(raw_date) >= 10 else raw_date

    def _extract_country(self, item: Dict) -> str:
        """도메인에서 국가 추론"""
        domain = item.get('domain', '')

        # 도메인 기반 국가 매핑
        country_mapping = {
            '.kr': 'KR', '.co.kr': 'KR',
            '.jp': 'JP', '.co.jp': 'JP',
            '.cn': 'CN', '.com.cn': 'CN',
            '.uk': 'GB', '.co.uk': 'GB',
            '.de': 'DE',
            '.fr': 'FR',
            '.ru': 'RU',
        }

        for suffix, country in country_mapping.items():
            if domain.endswith(suffix):
                return country

        return 'US' if domain.endswith('.com') else 'Unknown'


# ============================================================
# BigQuery Strategy (Fallback)
# ============================================================

class GDELTBigQueryStrategy(SearchStrategy):
    """
    GDELT BigQuery GKG 검색 전략 (Fallback)

    장점:
    - 과거 데이터 검색 가능
    - 구조적 쿼리 (테마, 인물, 조직)

    단점:
    - 메타데이터만 검색 (본문 X)
    - 쿼리 비용 (1TB 무료)
    """

    def __init__(self):
        self.client = None
        try:
            self.client = bigquery.Client(project=config.GCP_PROJECT)
            print("✅ [BigQuery] 클라이언트 연결 성공")
        except Exception as e:
            print(f"⚠️ [BigQuery] 연결 실패: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def search(self, keywords: List[str], **kwargs) -> List[ArticleResult]:
        """BigQuery GKG 테이블에서 메타데이터 검색"""
        if not self.client or not keywords:
            return []

        try:
            # 시간 범위 설정
            days = kwargs.get('days', config.SEARCH_WINDOW_DAYS)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            start_int = int(start_date.strftime('%Y%m%d000000'))
            end_int = int(end_date.strftime('%Y%m%d235959'))

            # [수정됨] URL(DocumentIdentifier) 와일드카드 검색 전략
            # AllNames는 일반 명사(trade, war 등)가 없어 검색 실패 확률이 높음.
            # 대신 URL에서 공백을 %로 바꿔서 유연하게 검색.
            safe_conditions = []
            for kw in keywords[:3]:  # 상위 3개만
                if "'" in kw:
                    continue  # SQL Injection 방지 (단순)

                # 핵심: 공백을 %로 변환 (예: "trade war" -> "%trade%war%")
                # URL은 "japan-trade-war" 처럼 되어 있으므로 공백으로는 검색 안됨
                url_friendly_kw = kw.replace(" ", "%")
                safe_conditions.append(f"DocumentIdentifier LIKE '%{url_friendly_kw}%'")

            if not safe_conditions:
                return []

            keyword_conditions = " OR ".join(safe_conditions)

            # 도메인 필터 (BigQuery는 성능 문제없으므로 유지)
            domains = config.TRUSTED_DOMAINS
            domain_filter = ",".join([f"'{d}'" for d in domains])

            query = f"""
            SELECT
                DocumentIdentifier as url,
                SourceCommonName as source,
                FORMAT_DATE('%Y-%m-%d', PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING))) as date,
                V2Tone as tone,
                Locations
            FROM `gdelt-bq.gdeltv2.gkg_partitioned`
            WHERE DATE >= {start_int}
              AND DATE <= {end_int}
              AND SourceCommonName IN ({domain_filter})
              AND ({keyword_conditions})
              AND DocumentIdentifier IS NOT NULL
            ORDER BY DATE DESC
            LIMIT {config.GDELT_MAX_RESULTS}
            """

            print(f"🔍 [BigQuery] 쿼리 실행: {keyword_conditions}")

            results = self.client.query(query).result()
            articles = []

            for row in results:
                article = ArticleResult(
                    url=row.url or '',
                    title='',  # GKG에는 제목 없음
                    source=row.source or 'Unknown',
                    date=str(row.date) if row.date else '',
                    tone=float(row.tone.split(',')[0]) if row.tone else 0.0,
                    country=self._extract_country_from_locations(row.Locations),
                )
                if article.url:
                    articles.append(article)

            # [추가됨] 중복 제거
            articles = deduplicate_articles(articles)

            print(f"✅ [BigQuery] {len(articles)}개 기사 발견 (중복 제거 후)")
            return articles

        except Exception as e:
            print(f"❌ [BigQuery] 쿼리 실패: {e}")
            return []

    def _extract_country_from_locations(self, locations: str) -> str:
        """Locations 필드에서 국가 코드 추출"""
        if not locations:
            return 'Unknown'
        try:
            parts = locations.split('#')
            if len(parts) > 2:
                return parts[2]
        except:
            pass
        return 'Unknown'


# ============================================================
# Main Search Engine (Facade Pattern)
# ============================================================

class GDELTSearcher:
    """
    GDELT 통합 검색 엔진

    [사용법]
    searcher = GDELTSearcher()
    results = searcher.search({'keywords': ['trade war', 'China']})

    [전략]
    1. DOC API (Primary) - 본문 전문 검색
    2. BigQuery (Fallback) - DOC API 실패 시

    [v2 수정]
    - 기존 로직 호환성: entities, themes를 keywords로 자동 병합
    """

    def __init__(self):
        # 검색 전략 초기화
        self.doc_api = GDELTDocAPIStrategy()
        self.bigquery = GDELTBigQueryStrategy()

        print("✅ [GDELTSearcher] 초기화 완료")

    def search(self, search_params: dict) -> List[Dict]:
        """
        통합 검색 메서드

        Args:
            search_params: {
                'keywords': ['keyword1', 'keyword2'],  # 권장
                'entities': ['Person', 'Org'],  # 선택 (자동 병합됨)
                'themes': ['ECON_TRADE'],  # 선택 (자동 병합됨)
                'timespan': '3m',  # 선택 (DOC API용, 기본값: config에서)
                'days': 30,  # 선택 (BigQuery용)
            }

        Returns:
            기사 딕셔너리 리스트
        """
        # [추가됨] 호환성 보완: entities/themes가 있으면 keywords로 병합
        keywords = self._merge_search_params(search_params)

        if not keywords:
            print("⚠️ 검색 키워드가 없습니다")
            return []

        # search_params에 병합된 keywords 업데이트
        merged_params = {**search_params, 'keywords': keywords}

                

        # 1. DOC API 시도 (Primary)
        if self.doc_api.is_available():
            try:
                # ⭕ 해결책: 딕셔너리에서 'keywords' 키를 제외한 나머지 옵션만 분리
                api_kwargs = {k: v for k, v in merged_params.items() if k != 'keywords'}
                
                # 분리된 옵션(**api_kwargs)만 추가로 전달
                results = self.doc_api.search(keywords, **api_kwargs)
                
                if results:
                    return [r.to_dict() for r in results]
                print("⚠️ [DOC API] 결과 없음, BigQuery로 전환")
                
            except Exception as e:
                print(f"⚠️ [DOC API] 실행 중 오류: {e}")
                # 오류 발생 시 BigQuery로 넘어가도록 예외 처리
                pass

        # 2. BigQuery Fallback
        if self.bigquery.is_available():
            results = self.bigquery.search(keywords, **merged_params)
            if results:
                return [r.to_dict() for r in results]

        print("❌ 모든 검색 전략 실패")
        return []

    def _merge_search_params(self, search_params: dict) -> List[str]:
        """
        [추가됨] 기존 로직 호환성을 위한 파라미터 병합

        entities, themes가 있으면 keywords에 병합하여 DOC API 검색에 사용
        """
        keywords = list(search_params.get('keywords', []))

        # entities 병합 (인물, 조직)
        entities = search_params.get('entities', [])
        if entities:
            keywords.extend(entities)
            print(f"   📌 entities → keywords 병합: {entities}")

        # themes 병합 (GDELT 테마 코드는 일반 텍스트로 변환)
        themes = search_params.get('themes', [])
        if themes:
            # 테마 코드를 검색 가능한 형태로 변환 (예: ECON_TRADE → trade)
            theme_keywords = [
                t.replace('_', ' ').lower()
                for t in themes
                if t and len(t) > 2
            ]
            keywords.extend(theme_keywords)
            print(f"   📌 themes → keywords 병합: {themes} → {theme_keywords}")

        # locations 병합 (국가명)
        locations = search_params.get('locations', [])
        if locations:
            keywords.extend(locations)
            print(f"   📌 locations → keywords 병합: {locations}")

        # 중복 제거 및 빈 문자열 필터링
        keywords = list(set(k.strip() for k in keywords if k and len(k.strip()) > 1))

        print(f"   🔑 최종 검색 키워드: {keywords}")
        return keywords

    def search_with_fallback(self, search_params: dict) -> List[Dict]:
        """
        Fallback이 보장된 검색 (항상 결과 반환 시도)
        """
        results = self.search(search_params)

        if not results:
            # 키워드 확장 시도: 첫 번째 키워드만으로 재검색
            keywords = self._merge_search_params(search_params)
            if keywords:
                simplified_params = {**search_params, 'keywords': keywords[:1]}
                results = self.search(simplified_params)

        return results
