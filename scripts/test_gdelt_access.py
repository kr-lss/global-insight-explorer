"""
GDELT 접근성 테스트 스크립트
북한, 중국, 러시아 언론사 검색 가능 여부 확인
"""
from google.cloud import bigquery
from app.config import config

def test_restricted_countries():
    """제재/제한 국가 언론사 검색 테스트"""
    client = bigquery.Client(project=config.GCP_PROJECT)

    # 테스트 대상 언론사
    test_sources = {
        '🇰🇵 북한': [
            'KCNA',
            'Korean Central News Agency',
            'Rodong Sinmun',
            'Naenara'
        ],
        '🇨🇳 중국': [
            'Xinhua',
            'People\'s Daily',
            'Global Times',
            'CCTV',
            'China Daily'
        ],
        '🇷🇺 러시아': [
            'TASS',
            'RT',
            'Russia Today',
            'Sputnik',
            'Pravda'
        ],
        '🇮🇷 이란': [
            'Press TV',
            'IRNA',
            'Tasnim'
        ]
    }

    print("=" * 70)
    print("GDELT 제재/제한 국가 언론사 접근성 테스트")
    print("=" * 70)
    print()

    for country, sources in test_sources.items():
        print(f"\n{country}")
        print("-" * 50)

        for source in sources:
            # 최근 7일간 해당 언론사 기사 검색
            query = f"""
            SELECT
                SourceCommonName,
                COUNT(*) as article_count,
                MIN(DATE) as oldest_date,
                MAX(DATE) as newest_date
            FROM `gdelt-bq.gdeltv2.gkg_partitioned`
            WHERE DATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
              AND SourceCommonName LIKE '%{source}%'
              AND DocumentIdentifier IS NOT NULL
            GROUP BY SourceCommonName
            ORDER BY article_count DESC
            LIMIT 5
            """

            try:
                results = client.query(query).result()
                found = False

                for row in results:
                    found = True
                    print(f"  ✅ {row.SourceCommonName}")
                    print(f"     └─ 기사 수: {row.article_count}개")
                    print(f"     └─ 기간: {row.oldest_date} ~ {row.newest_date}")

                if not found:
                    print(f"  ❌ {source}: 검색 결과 없음")

            except Exception as e:
                print(f"  ⚠️ {source}: 쿼리 실패 - {e}")

    print("\n" + "=" * 70)
    print()


def test_specific_topic_search():
    """특정 주제로 다국적 언론사 검색 테스트"""
    client = bigquery.Client(project=config.GCP_PROJECT)

    # 테스트 주제: 북한 미사일
    print("=" * 70)
    print("테스트 주제: '북한 미사일' 관련 다국적 보도")
    print("=" * 70)
    print()

    query = """
    SELECT
        SourceCommonName as source,
        DocumentIdentifier as url,
        Locations,
        Tone,
        DATE as published_date
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE DATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      AND (
          Themes LIKE '%NORTH_KOREA%'
          OR Themes LIKE '%MISSILE%'
          OR Themes LIKE '%DPRK%'
      )
      AND DocumentIdentifier IS NOT NULL
      AND SourceCommonName IS NOT NULL
    ORDER BY DATE DESC
    LIMIT 30
    """

    try:
        results = client.query(query).result()

        # 국가별 그룹화
        by_country = {}
        for row in results:
            source = row.source

            # 간단한 국가 분류
            if any(k in source for k in ['KCNA', 'Rodong', 'Naenara']):
                country = '🇰🇵 북한'
            elif any(k in source for k in ['Xinhua', 'People', 'CCTV', 'China']):
                country = '🇨🇳 중국'
            elif any(k in source for k in ['TASS', 'RT', 'Sputnik', 'Pravda']):
                country = '🇷🇺 러시아'
            elif any(k in source for k in ['Yonhap', 'Chosun', 'Korea']):
                country = '🇰🇷 한국'
            elif any(k in source for k in ['CNN', 'Fox', 'NBC', 'Washington', 'New York']):
                country = '🇺🇸 미국'
            elif any(k in source for k in ['NHK', 'Asahi', 'Mainichi']):
                country = '🇯🇵 일본'
            else:
                country = '🌍 기타'

            if country not in by_country:
                by_country[country] = []

            by_country[country].append({
                'source': source,
                'url': row.url,
                'tone': row.Tone,
                'date': row.published_date
            })

        # 출력
        for country, articles in sorted(by_country.items()):
            print(f"\n{country} ({len(articles)}개 기사)")
            print("-" * 50)
            for article in articles[:3]:  # 상위 3개만
                print(f"  📰 {article['source']}")
                print(f"     └─ {article['url'][:60]}...")
                print(f"     └─ Tone: {article['tone']} | {article['date']}")

        print(f"\n총 {len(results)}개 기사 발견")
        print("=" * 70)

    except Exception as e:
        print(f"❌ 쿼리 실패: {e}")


def test_sample_article_fetch():
    """샘플 기사 URL 가져오기"""
    client = bigquery.Client(project=config.GCP_PROJECT)

    print("\n" + "=" * 70)
    print("실제 기사 URL 샘플 (URL Context API 테스트용)")
    print("=" * 70)
    print()

    query = """
    SELECT
        SourceCommonName,
        DocumentIdentifier as url
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE DATE = CURRENT_DATE()
      AND (
          SourceCommonName LIKE '%KCNA%'
          OR SourceCommonName LIKE '%Xinhua%'
          OR SourceCommonName LIKE '%TASS%'
      )
      AND DocumentIdentifier IS NOT NULL
    LIMIT 5
    """

    try:
        results = client.query(query).result()

        for row in results:
            print(f"📰 {row.SourceCommonName}")
            print(f"   {row.url}")
            print()

    except Exception as e:
        print(f"❌ 쿼리 실패: {e}")


if __name__ == '__main__':
    print("\n🌍 GDELT 글로벌 언론사 접근성 테스트 시작...\n")

    # 1. 제재 국가 언론사 검색
    test_restricted_countries()

    # 2. 특정 주제 다국적 검색
    test_specific_topic_search()

    # 3. 샘플 URL 가져오기
    test_sample_article_fetch()

    print("\n✅ 테스트 완료\n")
