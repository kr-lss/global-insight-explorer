"""
YouTube Video Service 테스트 스크립트
Direct URL Processing 방식으로 유튜브 영상 분석
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.youtube_video_service import YouTubeVideoService


def test_single_video():
    """단일 영상 분석 테스트"""
    print("=" * 60)
    print("📹 단일 영상 분석 테스트")
    print("=" * 60)

    service = YouTubeVideoService()

    # 테스트할 유튜브 URL (공개 영상)
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    try:
        # 요약 분석
        result = service.analyze_video(video_url, analysis_type="summary")
        print("\n✅ 분석 결과:")
        print(f"제목: {result.get('title')}")
        print(f"요약: {result.get('summary')}")
        print(f"주요 포인트:")
        for point in result.get('key_points', []):
            print(f"  - {point}")
        print(f"주제: {', '.join(result.get('topics', []))}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")


def test_claims_extraction():
    """주장 추출 테스트"""
    print("\n" + "=" * 60)
    print("📋 주장 추출 테스트")
    print("=" * 60)

    service = YouTubeVideoService()

    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    try:
        result = service.analyze_video(video_url, analysis_type="claims")
        print("\n✅ 추출된 주장:")
        for i, claim in enumerate(result.get('key_claims', []), 1):
            print(f"{i}. {claim}")

        print(f"\n관련 국가: {', '.join(result.get('related_countries', []))}")
        print(f"\n검색 키워드:")
        for i, keywords in enumerate(result.get('search_keywords', []), 1):
            print(f"{i}. {', '.join(keywords)}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")


# ============================================================
# 비동기 버전 테스트 (주석 해제 시 사용 가능)
# ============================================================

# import asyncio
# from app.utils.youtube_video_service import AsyncYouTubeVideoService
#
# async def test_multiple_videos_async():
#     """여러 영상 병렬 분석 테스트"""
#     print("\n" + "=" * 60)
#     print("🚀 비동기 병렬 분석 테스트")
#     print("=" * 60)
#
#     service = AsyncYouTubeVideoService()
#
#     video_urls = [
#         "https://www.youtube.com/watch?v=VIDEO_ID_1",
#         "https://www.youtube.com/watch?v=VIDEO_ID_2",
#         "https://www.youtube.com/watch?v=VIDEO_ID_3",
#     ]
#
#     try:
#         results = await service.analyze_multiple_videos(
#             video_urls,
#             analysis_type="summary",
#             max_concurrent=3
#         )
#
#         print(f"\n✅ {len(results)}개 영상 분석 완료:")
#         for i, result in enumerate(results, 1):
#             print(f"\n[영상 {i}]")
#             print(f"제목: {result.get('title')}")
#             print(f"요약: {result.get('summary')}")
#
#     except Exception as e:
#         print(f"❌ 에러 발생: {e}")


if __name__ == "__main__":
    # 기본 테스트 실행
    test_single_video()
    test_claims_extraction()

    # 비동기 테스트 실행 (주석 해제 시)
    # asyncio.run(test_multiple_videos_async())
