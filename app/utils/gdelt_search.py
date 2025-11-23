"""
GDELT BigQuery Search Service - AI 기반 5대 요소 동적 검색 엔진
전 세계 뉴스 기사 URL을 BigQuery로 검색하는 핵심 엔진
"""
from datetime import datetime, timedelta
from google.cloud import bigquery
from app.config import config


class GDELTSearcher:
    """
    AI 기반 5대 요소(Who, Where, When, What, Source)를 활용한 동적 GDELT 검색 엔진
    """
    def __init__(self):
        self.client = None
        try:
            self.client = bigquery.Client(project=config.GCP_PROJECT)
            print("✅ (GDELT) BigQuery 클라이언트 연결 성공")
        except Exception as e:
            print(f"⚠️ (GDELT) BigQuery 연결 실패: {e}")

    def search(self, search_params: dict):
        """
        AI가 추출한 5대 요소로 최적화된 SQL을 생성하여 검색

        Args:
            search_params: {
                'keywords': [...],      # 핵심 키워드
                'themes': [...],        # GDELT 테마 코드
                'entities': [...],      # 인물/조직명
                'locations': [...],     # 장소
                'event_date': 'YYYY-MM-DD'  # 사건 발생일
            }

        Returns:
            [{url, source, title, date, tone, country}, ...]
        """
        if not self.client:
            return []

        # 1. 파라미터 해제 (안전한 get 사용)
        keywords = search_params.get('keywords', [])
        themes = search_params.get('themes', [])
        entities = search_params.get('entities', [])
        locations = search_params.get('locations', [])

        # 2. [WHEN] 시간 범위 설정 (가장 중요 ⭐)
        target_date_str = search_params.get('event_date')
        if not target_date_str:
            target_date = datetime.now()
        else:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
            except:
                target_date = datetime.now()

        # 검색 범위: 사건 발생일 기준 ±4일 (총 9일)
        start_date = (target_date - timedelta(days=4)).strftime('%Y%m%d000000')
        end_date = (target_date + timedelta(days=4)).strftime('%Y%m%d235959')

        # 3. [WHERE/WHO/WHAT] 내용 조건 구성 (OR 논리 - 유연한 검색)
        or_conditions = []

        # A. 인물/조직 (Persons, Organizations) - 정확도 높음
        if entities:
            entity_conds = [f"Persons LIKE '%{e}%' OR Organizations LIKE '%{e}%'" for e in entities[:3]]
            or_conditions.append(f"({' OR '.join(entity_conds)})")

        # B. 테마 (Themes) - 문맥 파악
        if themes:
            theme_conds = [f"Themes LIKE '%{t.upper()}%'" for t in themes[:3]]
            or_conditions.append(f"({' OR '.join(theme_conds)})")

        # C. 장소 (Locations) - 로컬 이슈
        if locations:
            loc_conds = [f"Locations LIKE '%{l}%'" for l in locations[:2]]
            or_conditions.append(f"({' OR '.join(loc_conds)})")

        # D. 키워드 (URL/DocumentIdentifier) - 최후의 보루
        if keywords:
            kw_conds = [f"DocumentIdentifier LIKE '%{k}%'" for k in keywords[:3]]
            or_conditions.append(f"({' OR '.join(kw_conds)})")

        if not or_conditions:
            print("⚠️ 유효한 검색 조건이 없어 검색을 중단합니다.")
            return []

        # 모든 조건을 OR로 묶음 (하나라도 걸리면 OK)
        final_content_query = f"({' OR '.join(or_conditions)})"

        # 4. [SOURCE] 신뢰할 수 있는 언론사 필터 (AND 논리 - 엄격한 출처 관리)
        trusted_domains = [
            'cnn.com', 'bbc.co.uk', 'reuters.com', 'apnews.com', 'nytimes.com',
            'yna.co.kr', 'koreaherald.com', 'koreatimes.co.kr',
            'xinhuanet.com', 'globaltimes.cn', 'tass.com', 'rt.com',
            'aljazeera.com', 'jpost.com', 'kyivindependent.com'
        ]
        # repr()을 사용하여 안전하게 문자열 포맷팅
        domain_filter = f"SourceCommonName IN ({','.join([repr(d) for d in trusted_domains])})"

        # 5. 최종 SQL 작성
        query = f"""
        SELECT
            DocumentIdentifier as url,
            SourceCommonName as source,
            FORMAT_DATE('%Y-%m-%d', PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING))) as date,
            V2Tone as tone,
            Locations,
            Themes
        FROM `gdelt-bq.gdeltv2.gkg_partitioned`
        WHERE DATE >= PARSE_TIMESTAMP('%Y%m%d%H%M%S', '{start_date}')
          AND DATE <= PARSE_TIMESTAMP('%Y%m%d%H%M%S', '{end_date}')
          AND {domain_filter}          -- 신뢰할 수 있는 언론사
          AND {final_content_query}    -- 내용 관련성
          AND DocumentIdentifier IS NOT NULL
          AND LENGTH(DocumentIdentifier) < 500
        ORDER BY DATE DESC
        LIMIT 30
        """

        try:
            print(f"📊 GDELT 5대 요소 검색 (기준일: {target_date.strftime('%Y-%m-%d')})")
            print(f"   조건: entities={entities[:2]}, themes={themes[:2]}, keywords={keywords[:2]}")
            query_job = self.client.query(query)

            results = []
            for row in query_job:
                # Locations 필드에서 국가 코드 추출
                country = 'Unknown'
                if row.Locations:
                    parts = row.Locations.split('#')
                    if len(parts) > 2:
                        country = parts[2]

                results.append({
                    'url': row.url,
                    'source': row.source,
                    'title': '',  # GDELT GKG는 제목 없음 (나중에 크롤링)
                    'date': str(row.date) if row.date else '',
                    'tone': float(row.tone.split(',')[0]) if row.tone else 0.0,
                    'country': country,
                    'themes': row.Themes[:200] if row.Themes else ''
                })

            print(f"✅ GDELT 검색 완료: {len(results)}개 발견")
            return results

        except Exception as e:
            print(f"❌ GDELT 쿼리 실패: {e}")
            return []
