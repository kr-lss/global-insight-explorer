"""
URL Context Service 테스트 스크립트
URL Context API 방식으로 웹페이지 분석 (크롤링 불필요)
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.url_context_service import URLContextService


def test_single_webpage():
    """단일 웹페이지 분석 테스트"""
    print("=" * 60)
    print("🌐 단일 웹페이지 분석 테스트")
    print("=" * 60)

    service = URLContextService()

    # 테스트할 URL (공개 뉴스 기사)
    url = "https://www.bbc.com/news"

    try:
        result = service.analyze_webpage(url)
        print("\n✅ 분석 결과:")
        print(f"제목: {result.get('title')}")
        print(f"요약: {result.get('summary')}")
        print(f"주요 주장:")
        for claim in result.get('key_claims', []):
            print(f"  - {claim}")
        print(f"주제: {', '.join(result.get('topics', []))}")
        print(f"관련 국가: {', '.join(result.get('related_countries', []))}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")


def test_multiple_urls():
    """여러 URL 비교 분석 테스트"""
    print("\n" + "=" * 60)
    print("📊 다중 URL 비교 분석 테스트")
    print("=" * 60)

    service = URLContextService()

    urls = [
        "https://www.bbc.com/news",
        "https://www.cnn.com",
        "https://www.reuters.com"
    ]

    try:
        result = service.analyze_multiple_urls(urls)
        print("\n✅ 비교 분석 결과:")
        print(f"공통 주제: {', '.join(result.get('common_topics', []))}")
        print(f"\n전체 요약:")
        print(result.get('summary'))

        print(f"\n관점 차이:")
        for perspective in result.get('different_perspectives', []):
            print(f"\n주제: {perspective.get('topic')}")
            print(f"  - URL 1: {perspective.get('url1_view')}")
            print(f"  - URL 2: {perspective.get('url2_view')}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")


def test_article_extraction():
    """기사 본문 추출 테스트"""
    print("\n" + "=" * 60)
    print("📰 기사 본문 추출 테스트")
    print("=" * 60)

    service = URLContextService()

    url = "https://www.bbc.com/news"

    try:
        content = service.extract_article_content(url)
        print("\n✅ 추출된 본문:")
        print(content[:500] + "..." if len(content) > 500 else content)

    except Exception as e:
        print(f"❌ 에러 발생: {e}")


# ============================================================
# 비동기 버전 테스트 (주석 해제 시 사용 가능)
# ============================================================

# import asyncio
# from app.utils.url_context_service import AsyncURLContextService
#
# async def test_multiple_webpages_async():
#     """여러 웹페이지 병렬 분석 테스트"""
#     print("\n" + "=" * 60)
#     print("🚀 비동기 병렬 분석 테스트")
#     print("=" * 60)
#
#     service = AsyncURLContextService()
#
#     urls = [
#         "https://www.bbc.com/news/world",
#         "https://www.cnn.com/world",
#         "https://www.reuters.com/world",
#     ]
#
#     prompt = """
#     이 뉴스 페이지의 주요 헤드라인을 추출해주세요.
#
#     응답 형식:
#     {
#       "headlines": ["헤드라인 1", "헤드라인 2", ...],
#       "top_story": "가장 중요한 뉴스"
#     }
#     """
#
#     try:
#         results = await service.analyze_multiple_webpages(
#             urls,
#             analysis_prompt=prompt,
#             max_concurrent=3
#         )
#
#         print(f"\n✅ {len(results)}개 페이지 분석 완료:")
#         for i, result in enumerate(results, 1):
#             print(f"\n[페이지 {i}]")
#             print(f"헤드라인: {', '.join(result.get('headlines', []))}")
#             print(f"톱 스토리: {result.get('top_story')}")
#
#     except Exception as e:
#         print(f"❌ 에러 발생: {e}")


if __name__ == "__main__":
    # 기본 테스트 실행
    test_single_webpage()
    test_multiple_urls()
    test_article_extraction()

    # 비동기 테스트 실행 (주석 해제 시)
    # asyncio.run(test_multiple_webpages_async())
