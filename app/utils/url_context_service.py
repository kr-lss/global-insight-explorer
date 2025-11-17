"""
URL Context Service for Web Crawling
웹페이지 URL을 직접 Gemini API에 전달하여 내용 추출 (크롤링 불필요)
"""
import json
from google import genai
from google.genai import types
from app.config import config


class URLContextService:
    """URL Context API를 사용한 웹 크롤링 우회"""

    def __init__(self, api_key: str = None):
        """
        Initialize URL Context Service

        Args:
            api_key: Gemini API key (없으면 환경변수에서 가져옴)
        """
        try:
            # Vertex AI 방식 사용
            self.client = genai.Client(
                vertexai=True,
                project=config.GCP_PROJECT,
                location=config.GCP_REGION,
                http_options=types.HttpOptions(api_version="v1beta1")
            )
            self.model = "gemini-2.0-flash"
            print("✅ (URLContextService) Gemini API 연결 성공")
        except Exception as e:
            print(f"⚠️ (URLContextService) Gemini API 연결 실패: {e}")
            self.client = None

    def analyze_webpage(self, url: str, analysis_prompt: str = None) -> dict:
        """
        웹페이지를 직접 분석 (HTML 파싱 불필요)

        Args:
            url: 분석할 웹페이지 URL
            analysis_prompt: 분석 요청 프롬프트 (기본값: 요약)

        Returns:
            분석 결과 딕셔너리
        """
        if not self.client:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        print(f"🌐 URL Context Processing: {url[:50]}...")

        # URL Context 도구 활성화
        url_context_tool = types.Tool(url_context=types.UrlContext)

        # 기본 프롬프트
        if not analysis_prompt:
            analysis_prompt = f"""
다음 웹페이지를 분석하여 JSON 형식으로 답변해주세요: {url}

응답 형식:
{{
  "title": "페이지 제목",
  "summary": "주요 내용 요약 (3-5문장)",
  "key_claims": ["주장 1", "주장 2", ...],
  "topics": ["주제1", "주제2"],
  "related_countries": ["국가1", "국가2"],
  "author": "작성자 (있는 경우)",
  "published_date": "발행일 (있는 경우)"
}}

반드시 JSON 객체만 출력하세요.
"""
        else:
            analysis_prompt = f"{analysis_prompt}\n\nURL: {url}\n\n반드시 JSON 형식으로 답변하세요."

        # Gemini에 URL 전달
        response = self.client.models.generate_content(
            model=self.model,
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                tools=[url_context_tool],
                temperature=0.0,
                response_mime_type="application/json"
            )
        )

        # 메타데이터 확인 (디버깅용)
        if hasattr(response, 'candidates') and len(response.candidates) > 0:
            metadata = getattr(response.candidates[0], 'url_context_metadata', None)
            if metadata:
                print(f"✅ URL 로드 성공: {metadata}")

        # JSON 파싱
        result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(result_text)

        print(f"✅ 웹페이지 분석 완료")
        return result

    def analyze_multiple_urls(self, urls: list[str], comparison_prompt: str = None) -> dict:
        """
        여러 URL을 한 번에 비교 분석 (최대 20개)

        Args:
            urls: URL 리스트 (최대 20개)
            comparison_prompt: 비교 분석 프롬프트

        Returns:
            비교 분석 결과
        """
        if not self.client:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        if len(urls) > 20:
            raise ValueError("최대 20개 URL까지 지원합니다.")

        print(f"🌐 다중 URL 분석: {len(urls)}개 페이지...")

        # URL Context 도구 활성화
        url_context_tool = types.Tool(url_context=types.UrlContext)

        # 기본 비교 프롬프트
        if not comparison_prompt:
            urls_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(urls)])
            comparison_prompt = f"""
다음 웹페이지들을 비교 분석하여 JSON 형식으로 답변해주세요:

{urls_text}

응답 형식:
{{
  "common_topics": ["공통 주제1", "공통 주제2"],
  "different_perspectives": [
    {{
      "topic": "주제",
      "url1_view": "첫 번째 페이지의 관점",
      "url2_view": "두 번째 페이지의 관점"
    }}
  ],
  "summary": "전체 비교 요약",
  "credibility_notes": "각 출처의 신뢰성 평가"
}}

반드시 JSON 객체만 출력하세요.
"""

        # Gemini에 여러 URL 전달
        response = self.client.models.generate_content(
            model=self.model,
            contents=comparison_prompt,
            config=types.GenerateContentConfig(
                tools=[url_context_tool],
                temperature=0.0,
                response_mime_type="application/json"
            )
        )

        # JSON 파싱
        result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(result_text)

        print(f"✅ 다중 URL 분석 완료")
        return result

    def extract_article_content(self, url: str) -> str:
        """
        기사 본문만 추출 (간단한 텍스트 추출)

        Args:
            url: 기사 URL

        Returns:
            본문 텍스트
        """
        if not self.client:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        print(f"📰 기사 본문 추출: {url[:50]}...")

        url_context_tool = types.Tool(url_context=types.UrlContext)

        prompt = f"""
다음 기사의 본문 내용만 추출해주세요: {url}

광고, 네비게이션, 사이드바 등은 제외하고 순수한 기사 내용만 반환하세요.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[url_context_tool],
                temperature=0.0
            )
        )

        print(f"✅ 본문 추출 완료")
        return response.text.strip()


# ============================================================
# 🔄 비동기 병렬 처리 버전 (Async Processing)
# 여러 웹페이지를 동시에 빠르게 처리하고 싶을 때 주석 해제하여 사용
# ============================================================

# import asyncio
# from tenacity import retry, wait_exponential, stop_after_attempt
#
# class AsyncURLContextService:
#     """비동기 방식으로 여러 웹페이지를 병렬 처리"""
#
#     def __init__(self, api_key: str = None):
#         try:
#             self.client = genai.Client(
#                 vertexai=True,
#                 project=config.GCP_PROJECT,
#                 location=config.GCP_REGION,
#                 http_options=types.HttpOptions(api_version="v1beta1")
#             )
#             self.model = "gemini-2.0-flash"
#             print("✅ (AsyncURLContextService) Gemini API 연결 성공")
#         except Exception as e:
#             print(f"⚠️ (AsyncURLContextService) 연결 실패: {e}")
#             self.client = None
#
#     @retry(
#         wait=wait_exponential(multiplier=2, min=2, max=60),
#         stop=stop_after_attempt(3)
#     )
#     async def analyze_webpage_async(self, url: str, prompt: str) -> dict:
#         """
#         단일 웹페이지 비동기 분석 (재시도 로직 포함)
#
#         Args:
#             url: 웹페이지 URL
#             prompt: 분석 프롬프트
#
#         Returns:
#             분석 결과
#         """
#         if not self.client:
#             raise Exception("Gemini API를 사용할 수 없습니다.")
#
#         print(f"🌐 비동기 분석 시작: {url[:50]}...")
#
#         url_context_tool = types.Tool(url_context=types.UrlContext)
#         full_prompt = f"{prompt}\n\nURL: {url}\n\n반드시 JSON 형식으로 답변하세요."
#
#         response = await self.client.aio.models.generate_content(
#             model=self.model,
#             contents=full_prompt,
#             config=types.GenerateContentConfig(
#                 tools=[url_context_tool],
#                 temperature=0.0,
#                 response_mime_type="application/json"
#             )
#         )
#
#         result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
#         return json.loads(result_text)
#
#     async def analyze_multiple_webpages(
#         self,
#         urls: list[str],
#         analysis_prompt: str,
#         max_concurrent: int = 10
#     ) -> list[dict]:
#         """
#         여러 웹페이지를 병렬로 분석
#
#         Args:
#             urls: URL 리스트
#             analysis_prompt: 분석 프롬프트
#             max_concurrent: 최대 동시 처리 수
#
#         Returns:
#             분석 결과 리스트
#         """
#         semaphore = asyncio.Semaphore(max_concurrent)
#
#         async def analyze_with_semaphore(url):
#             async with semaphore:
#                 try:
#                     return await self.analyze_webpage_async(url, analysis_prompt)
#                 except Exception as e:
#                     print(f"❌ 분석 실패: {url} - {e}")
#                     return None
#
#         tasks = [analyze_with_semaphore(url) for url in urls]
#         results = await asyncio.gather(*tasks)
#
#         # None 제외
#         return [r for r in results if r is not None]
#
#
# # 사용 예시:
# # async def main():
# #     service = AsyncURLContextService()
# #     urls = [
# #         "https://news.example.com/article1",
# #         "https://news.example.com/article2",
# #         "https://news.example.com/article3",
# #     ]
# #     prompt = "이 기사의 핵심 주장을 추출해주세요."
# #     results = await service.analyze_multiple_webpages(urls, prompt, max_concurrent=10)
# #     print(results)
# #
# # asyncio.run(main())
