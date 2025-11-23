"""
GDELT BigQuery Search Service
전 세계 뉴스 기사 URL을 BigQuery로 검색하는 핵심 엔진
"""
from google.cloud import bigquery
from app.config import config


class GDELTSearcher:
    """GDELT BigQuery 검색 클래스"""

    def __init__(self):
        """BigQuery 클라이언트 초기화"""
        self.client = None
        try:
            self.client = bigquery.Client(project=config.GCP_PROJECT)
            print("✅ (GDELT) BigQuery 클라이언트 연결 성공")
        except Exception as e:
            print(f"⚠️ (GDELT) BigQuery 연결 실패: {e}")

    def search(
        self, keywords: list, target_countries: list = None, days: int = 7, limit: int = 30
    ):
        """
        GDELT에서 키워드와 국가 코드로 뉴스 URL 검색

        Args:
            keywords: 영어 검색 키워드 리스트 (예: ['Trump', 'tariff', 'China'])
            target_countries: ISO 국가 코드 리스트 (예: ['US', 'CN', 'KR'])
            days: 과거 며칠치 데이터 검색 (기본 7일)
            limit: 최대 결과 개수 (기본 30개)

        Returns:
            [{url, source, title, date, tone, country}, ...]
        """
        if not self.client or not keywords:
            return []

        # 키워드 최적화: 띄어쓰기 제거, 핵심 단어만 사용
        # GDELT Themes는 연속된 단어가 아닌 개별 키워드로 저장됨
        optimized_keywords = []
        for k in keywords[:3]:  # 최대 3개만 사용 (너무 많으면 매칭 실패)
            # "North Korea missile" → ["North", "Korea", "missile"]
            words = k.split()
            for word in words:
                if len(word) > 2:  # 2글자 이상만 추가
                    optimized_keywords.append(word)

        # 중복 제거 및 최대 5개로 제한
        optimized_keywords = list(set(optimized_keywords))[:5]

        # 키워드 필터: GDELT Themes는 대문자로 저장되므로 .upper() 필수
        # OR 조건으로 연결 (하나라도 매칭되면 OK)
        theme_conditions = [f"Themes LIKE '%{k.upper()}%'" for k in optimized_keywords]
        theme_query = " OR ".join(theme_conditions) if theme_conditions else "1=1"

        # 국가 필터: Locations 필드 형식 예시: "1#China#CN#CH#39.9042#116.4074"
        country_query = "1=1"  # 기본값 (모든 국가)
        if target_countries and len(target_countries) > 0:
            # #{COUNTRY_CODE}# 패턴으로 검색
            country_conditions = [f"Locations LIKE '%#{c}#%'" for c in target_countries]
            country_query = f"({' OR '.join(country_conditions)})"

        # BigQuery SQL 쿼리 작성
        query = f"""
        SELECT
            DocumentIdentifier as url,
            SourceCommonName as source,
            FORMAT_TIMESTAMP('%Y-%m-%d', PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING))) as date,
            SUBSTR(V2Themes, 0, 200) as themes,
            Locations,
            V2Tone as tone
        FROM `gdelt-bq.gdeltv2.gkg_partitioned`
        WHERE
            _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            AND ({theme_query})
            AND ({country_query})
            AND DocumentIdentifier IS NOT NULL
            AND SourceCommonName IS NOT NULL
            AND LENGTH(DocumentIdentifier) < 500
            -- 영상 플랫폼 제외 (기사만)
            AND SourceCommonName NOT IN ('youtube.com', 'twitter.com', 'facebook.com', 'instagram.com')
        ORDER BY DATE DESC
        LIMIT {limit}
        """

        try:
            print(f"📊 GDELT 쿼리 실행 중... (원본: {keywords[:3]}, 최적화: {optimized_keywords}, 국가: {target_countries})")
            query_job = self.client.query(query)

            results = []
            for row in query_job:
                # Locations 필드에서 국가 코드 추출
                country = self._extract_country_from_locations(
                    row.Locations, target_countries
                )

                results.append(
                    {
                        'url': row.url,
                        'source': row.source or 'Unknown',
                        'title': '',  # GDELT에는 제목이 없으므로 나중에 본문에서 추출
                        'date': str(row.date) if row.date else '',
                        'tone': float(row.tone.split(',')[0]) if row.tone else 0.0,  # Tone은 CSV 형식
                        'country': country,
                        'themes': row.themes or '',
                    }
                )

            print(f"✅ GDELT 검색 완료: {len(results)}개 발견")
            return results

        except Exception as e:
            print(f"❌ GDELT 쿼리 실행 실패: {e}")
            return []

    def _extract_country_from_locations(self, locations_str: str, target_countries: list):
        """
        GDELT Locations 필드에서 국가 코드 추출

        Locations 형식 예시:
        "1#United States#US#US#40.7128#-74.0060;1#China#CN#CH#39.9042#116.4074"

        Args:
            locations_str: GDELT Locations 필드 값
            target_countries: 검색 대상 국가 리스트

        Returns:
            국가 코드 (예: 'US', 'CN', 'KR')
        """
        if not locations_str:
            return 'Unknown'

        try:
            # 세미콜론으로 분리된 여러 위치 정보
            location_entries = locations_str.split(';')

            for entry in location_entries:
                parts = entry.split('#')
                if len(parts) >= 3:
                    country_code = parts[2]  # 3번째 필드가 ISO 코드

                    # target_countries에 있는 국가 우선 반환
                    if target_countries and country_code in target_countries:
                        return country_code

                    # 없으면 첫 번째 국가 반환
                    if country_code:
                        return country_code

        except Exception as e:
            print(f"⚠️ 국가 코드 추출 실패: {e}")

        return 'Unknown'

    def _guess_country_from_source(self, source: str, targets: list = None):
        """
        소스 도메인으로 국가 추정 (보조 로직)

        Args:
            source: 도메인 이름 (예: 'cnn.com')
            targets: 검색 대상 국가 리스트

        Returns:
            국가 코드 (예: 'US')
        """
        if not source:
            return 'Unknown'

        source_lower = source.lower()

        # 주요 언론사 매핑
        country_mapping = {
            'cnn.com': 'US',
            'nytimes.com': 'US',
            'washingtonpost.com': 'US',
            'foxnews.com': 'US',
            'bbc.co.uk': 'UK',
            'bbc.com': 'UK',
            'theguardian.com': 'UK',
            'reuters.com': 'UK',
            'xinhua': 'CN',
            'globaltimes.cn': 'CN',
            'chinadaily.com.cn': 'CN',
            'yonhapnews.co.kr': 'KR',
            'chosun.com': 'KR',
            'joongang.co.kr': 'KR',
            'nhk.or.jp': 'JP',
            'asahi.com': 'JP',
            'rt.com': 'RU',
            'tass.com': 'RU',
            'france24.com': 'FR',
            'dw.com': 'DE',
        }

        for domain, country in country_mapping.items():
            if domain in source_lower:
                return country

        # 타겟 국가 중 하나로 추정
        if targets:
            for country in targets:
                if country.lower() in source_lower:
                    return country

        return 'Unknown'
