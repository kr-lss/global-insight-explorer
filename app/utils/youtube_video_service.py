"""
YouTube Video Analysis Service using Direct URL Processing
유튜브 URL을 직접 Gemini API에 전달하여 분석 (다운로드 불필요)
"""
import json
from google import genai
from google.genai import types
from app.config import config


class YouTubeVideoService:
    """Direct URL Processing으로 유튜브 영상 분석"""

    def __init__(self, api_key: str = None):
        """
        Initialize YouTube Video Service

        Args:
            api_key: Gemini API key (없으면 환경변수에서 가져옴)
        """
        try:
            # Vertex AI 방식 사용
            self.client = genai.Client(
                vertexai=True,
                project=config.GCP_PROJECT,
                location=config.GCP_REGION
            )
            self.model = "gemini-2.0-flash"
            print("✅ (YouTubeVideoService) Gemini API 연결 성공")
        except Exception as e:
            print(f"⚠️ (YouTubeVideoService) Gemini API 연결 실패: {e}")
            self.client = None

    def analyze_video(self, video_url: str, analysis_type: str = "summary") -> dict:
        """
        유튜브 영상을 직접 분석 (다운로드 없음)

        Args:
            video_url: 유튜브 URL (https://www.youtube.com/watch?v=...)
            analysis_type: 분석 타입 (summary, claims, transcript)

        Returns:
            분석 결과 딕셔너리
        """
        if not self.client:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        print(f"🎬 Direct URL Processing: {video_url[:50]}...")

        # 분석 프롬프트 선택
        prompt = self._get_prompt(analysis_type)

        # Gemini에 직접 URL 전달
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_uri(
                    file_uri=video_url,
                    mime_type="video/webm"  # 유튜브는 webm 형식
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
        )

        # JSON 파싱
        result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(result_text)

        print(f"✅ 영상 분석 완료")
        return result

    def _get_prompt(self, analysis_type: str) -> str:
        """분석 타입에 따른 프롬프트 반환"""
        prompts = {
            "summary": """
이 영상을 분석하여 JSON 형식으로 답변해주세요.

응답 형식:
{
  "title": "영상 제목 또는 주제",
  "summary": "핵심 내용 요약 (3-5문장)",
  "key_points": ["주요 포인트 1", "주요 포인트 2", ...],
  "duration_estimate": "예상 재생 시간",
  "topics": ["주제1", "주제2"]
}

반드시 JSON 객체만 출력하세요.
""",
            "claims": """
이 영상에서 언급된 핵심 주장들을 분석하여 JSON 형식으로 답변해주세요.

응답 형식:
{
  "key_claims": ["주장 1", "주장 2", ...],
  "related_countries": ["국가1", "국가2"],
  "search_keywords": [["keyword1", "keyword2"], ["keyword3", "keyword4"]],
  "topics": ["주제1", "주제2"],
  "summary": "전체 내용 요약"
}

반드시 JSON 객체만 출력하세요.
""",
            "transcript": """
이 영상의 내용을 텍스트로 변환하여 JSON 형식으로 답변해주세요.

응답 형식:
{
  "transcript": "영상의 모든 대화 내용을 텍스트로 변환",
  "speakers": ["화자1", "화자2"],
  "key_moments": [
    {"time": "MM:SS", "description": "주요 순간 설명"}
  ]
}

반드시 JSON 객체만 출력하세요.
"""
        }
        return prompts.get(analysis_type, prompts["summary"])


# ============================================================
# 🔄 비동기 병렬 처리 버전 (Async Processing)
# 여러 영상을 동시에 빠르게 처리하고 싶을 때 주석 해제하여 사용
# ============================================================

# import asyncio
# from tenacity import retry, wait_exponential, stop_after_attempt
#
# class AsyncYouTubeVideoService:
#     """비동기 방식으로 여러 영상을 병렬 처리"""
#
#     def __init__(self, api_key: str = None):
#         try:
#             self.client = genai.Client(
#                 vertexai=True,
#                 project=config.GCP_PROJECT,
#                 location=config.GCP_REGION
#             )
#             self.model = "gemini-2.0-flash"
#             print("✅ (AsyncYouTubeVideoService) Gemini API 연결 성공")
#         except Exception as e:
#             print(f"⚠️ (AsyncYouTubeVideoService) 연결 실패: {e}")
#             self.client = None
#
#     @retry(
#         wait=wait_exponential(multiplier=2, min=2, max=60),
#         stop=stop_after_attempt(3)
#     )
#     async def analyze_video_async(self, video_url: str, prompt: str) -> dict:
#         """
#         단일 영상 비동기 분석 (재시도 로직 포함)
#
#         Args:
#             video_url: 유튜브 URL
#             prompt: 분석 프롬프트
#
#         Returns:
#             분석 결과
#         """
#         if not self.client:
#             raise Exception("Gemini API를 사용할 수 없습니다.")
#
#         print(f"🎬 비동기 분석 시작: {video_url[:50]}...")
#
#         response = await self.client.aio.models.generate_content(
#             model=self.model,
#             contents=[
#                 types.Part.from_uri(file_uri=video_url, mime_type="video/webm"),
#                 prompt
#             ],
#             config=types.GenerateContentConfig(
#                 temperature=0.0,
#                 response_mime_type="application/json"
#             )
#         )
#
#         result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
#         return json.loads(result_text)
#
#     async def analyze_multiple_videos(
#         self,
#         video_urls: list[str],
#         analysis_type: str = "summary",
#         max_concurrent: int = 5
#     ) -> list[dict]:
#         """
#         여러 영상을 병렬로 분석
#
#         Args:
#             video_urls: 유튜브 URL 리스트
#             analysis_type: 분석 타입
#             max_concurrent: 최대 동시 처리 수
#
#         Returns:
#             분석 결과 리스트
#         """
#         semaphore = asyncio.Semaphore(max_concurrent)
#         prompt = self._get_prompt(analysis_type)
#
#         async def analyze_with_semaphore(url):
#             async with semaphore:
#                 try:
#                     return await self.analyze_video_async(url, prompt)
#                 except Exception as e:
#                     print(f"❌ 분석 실패: {url} - {e}")
#                     return None
#
#         tasks = [analyze_with_semaphore(url) for url in video_urls]
#         results = await asyncio.gather(*tasks)
#
#         # None 제외
#         return [r for r in results if r is not None]
#
#     def _get_prompt(self, analysis_type: str) -> str:
#         """분석 타입에 따른 프롬프트 반환"""
#         # (위의 동기 버전과 동일)
#         pass
#
#
# # 사용 예시:
# # async def main():
# #     service = AsyncYouTubeVideoService()
# #     video_urls = [
# #         "https://www.youtube.com/watch?v=VIDEO_ID_1",
# #         "https://www.youtube.com/watch?v=VIDEO_ID_2",
# #         "https://www.youtube.com/watch?v=VIDEO_ID_3",
# #     ]
# #     results = await service.analyze_multiple_videos(video_urls, max_concurrent=5)
# #     print(results)
# #
# # asyncio.run(main())
