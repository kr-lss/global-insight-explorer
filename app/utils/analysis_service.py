"""
분석 비즈니스 로직을 처리하는 서비스 (Facade 패턴)
"""
import os
import json
import hashlib
from datetime import datetime

import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore

from app.models.extractor import BaseExtractor, YoutubeExtractor, ArticleExtractor
from app.models.media import get_media_credibility
from app.config import config

# Gemini 모델 로드
gemini = None
try:
    vertexai.init(project=config.GCP_PROJECT, location=config.GCP_REGION)
    gemini = GenerativeModel('gemini-1.5-flash')
    print("✅ (Service) Gemini API 연결 성공")
except Exception as e:
    print(f"⚠️ (Service) Gemini API 연결 실패: {e}")

# Firestore 클라이언트
db = None
try:
    db = firestore.Client(project=config.GCP_PROJECT)
    print("✅ (Service) Firestore 연결 성공")
except Exception as e:
    print(f"⚠️ (Service) Firestore 연결 실패: {e}")


class AnalysisService:
    def __init__(self):
        self.extractors = {
            'youtube': YoutubeExtractor(),
            'article': ArticleExtractor(),
        }

    def _get_extractor(self, input_type: str) -> BaseExtractor:
        extractor = self.extractors.get(input_type)
        if not extractor:
            raise ValueError(f"지원하지 않는 입력 타입: {input_type}")
        return extractor

    # --- 1차 분석 ---
    def analyze_content(self, url: str, input_type: str):
        # 캐시 확인
        cached = self._get_cache(url)
        if cached:
            return cached, True

        # 콘텐츠 추출
        print(f"📥 콘텐츠 추출 중: {url[:50]}...")
        extractor = self._get_extractor(input_type)
        content = extractor.extract(url)
        print(f"✅ 추출 완료: {len(content)} 글자")

        # AI 분석
        print("🤖 Gemini로 1차 분석 중...")
        result = self._analyze_with_gemini(content)
        print("✅ 1차 분석 완료")

        # 캐시 저장
        self._set_cache(url, result)
        return result, False

    def _analyze_with_gemini(self, content: str):
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        content = content[:8000]  # 컨텍스트 길이 조절

        prompt = f"""
        다음 텍스트를 분석하여 JSON 형식으로 답변해주세요.

        텍스트:
        ---
        {content}
        ---

        요구사항:
        1. key_claims: 텍스트에서 언급된 핵심적인 주장이나 사실 (3-7개, 각각 명확하고 간결한 한 문장)
        2. related_countries: 주된 관련 국가 (최대 5개, 국가 코드가 아닌 이름으로)
        3. search_keywords: 각 주장을 검증하기 위한 영어 검색 키워드 (주장당 2-3개)
        4. topics: 주제 분류 (예: 정치, 경제, 사회, 과학기술, 국제관계)
        5. summary: 전체 내용을 요약 (2-3 문장)

        응답 형식 (JSON):
        {{
          "key_claims": ["주장 1", "주장 2"],
          "related_countries": ["국가1", "국가2"],
          "search_keywords": [["keyword1", "keyword2"], ["keyword3", "keyword4"]],
          "topics": ["주제1", "주제2"],
          "summary": "요약 내용"
        }}

        주의: 반드시 JSON 객체만 출력하고 다른 설명은 덧붙이지 마세요.
        """

        try:
            response = gemini.generate_content(prompt)
            result_text = (
                response.text.strip().replace('```json', '').replace('```', '').strip()
            )
            return json.loads(result_text)
        except Exception as e:
            print(f"❌ AI 1차 분석 실패: {e}")
            raise Exception(f"AI 분석 중 오류가 발생했습니다: {e}")

    # --- 2차 분석 ---
    def find_sources_for_claims(
        self, url: str, input_type: str, selected_claims: list, search_keywords: list
    ):
        # 원본 콘텐츠 다시 추출
        extractor = self._get_extractor(input_type)
        original_content = extractor.extract(url)

        # 실제 기사 검색
        articles = self._search_real_articles(search_keywords)

        # AI로 관련성 분석
        print("🤖 Gemini로 2차 분석 (관련 기사 매칭) 중...")
        analysis_result = self._find_related_articles_with_gemini(
            original_content, selected_claims, articles
        )
        print("✅ 2차 분석 완료")

        return analysis_result, articles

    def _search_real_articles(self, keywords: list):
        if not keywords:
            return []
        try:
            query = " OR ".join(keywords)
            print(f"🔍 Google 검색 실행: {query}")

            # 내장 웹 검색 도구 호출
            from Gemini.google_web_search import google_web_search

            search_results = google_web_search(query=query)

            articles = []
            if search_results and 'results' in search_results:
                for result in search_results['results']:
                    source = result.get('source', '출처 불명')
                    credibility_info = get_media_credibility(source)

                    articles.append(
                        {
                            'title': result.get('title', '제목 없음'),
                            'snippet': result.get('snippet', '내용 없음'),
                            'url': result.get('url', '#'),
                            'source': source,
                            'country': credibility_info.get('country', 'Unknown'),
                            'credibility': credibility_info.get('credibility', 50),
                            'bias': credibility_info.get('bias', '알 수 없음'),
                            'published_date': result.get('publishDate', '날짜 없음'),
                        }
                    )
            return articles
        except Exception as e:
            print(f"⚠️ 실제 기사 검색 실패: {e}")
            return []

    def _find_related_articles_with_gemini(
        self, original_content: str, claims: list, articles: list
    ):
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        original_content = original_content[:4000]
        articles_text = "\n\n".join(
            [
                f"[기사 {i+1}]\n제목: {article.get('title', '')}\n출처: {article.get('source', '')}\n내용: {article.get('snippet', '')}"
                for i, article in enumerate(articles[:15])  # 컨텍스트 조절
            ]
        )

        prompt = f"""
        당신은 편견 없는 정보 분석가입니다. 원본 콘텐츠의 주장과 수집된 기사들의 연관성을 분석해주세요.
        **절대로 주장의 참/거짓을 판단하지 마세요.**

        [원본 콘텐츠 요약]
        {original_content}

        [사용자가 선택한 검증 대상 주장]
        {chr(10).join([f'- {c}' for c in claims])}

        [수집된 최신 기사 목록]
        {articles_text}

        [요청 작업]
        각 주장에 대해, 수집된 기사 목록 중 어떤 기사가 가장 관련 있는지 분석하고, 각 기사가 어떤 새로운 정보나 다른 관점을 제공하는지 설명해주세요.

        [응답 형식 (JSON)]
        {{
          "results": [
            {{
              "claim": "사용자가 선택한 첫 번째 주장",
              "related_articles": [
                  {{
                      "article_index": 1, // 기사 번호
                      "relevance_score": 90, // 0-100점
                      "perspective": "이 기사는 주장에 대해 구체적인 통계를 제공하며, 다른 원인을 제시합니다."
                  }}
              ],
              "missing_context": "원본 콘텐츠에는 없지만, 이 주장을 이해하는 데 필요한 추가적인 배경지식이나 맥락을 서술합니다.",
              "coverage_countries": ["미국", "영국"] // 이 주장을 주로 다룬 국가
            }}
          ]
        }}

        [주의사항]
        - `related_articles`에는 관련성 높은 기사만 포함시키세요.
        - `perspective`는 기사의 객관적인 내용을 요약해야 합니다. (예: 지지/반대/중립이 아닌 정보 요약)
        - `missing_context`는 모든 기사를 종합하여 추론한 내용을 담습니다.
        - 반드시 JSON 객체만 출력하고 다른 설명은 덧붙이지 마세요.
        """
        try:
            response = gemini.generate_content(prompt)
            result_text = (
                response.text.strip().replace('```json', '').replace('```', '').strip()
            )
            return json.loads(result_text)
        except Exception as e:
            print(f"❌ AI 2차 분석 실패: {e}")
            raise Exception(f"관련 기사 분석 중 오류가 발생했습니다: {e}")

    # --- 캐싱 헬퍼 ---
    def _get_cache(self, url: str):
        if not db:
            return None
        try:
            cache_key = hashlib.md5(url.encode()).hexdigest()
            doc = db.collection('cache').document(cache_key).get()
            if doc.exists:
                print(f"✅ 캐시 히트: {url[:50]}...")
                return doc.to_dict().get('result')
            return None
        except Exception as e:
            print(f"⚠️ 캐시 읽기 실패: {e}")
            return None

    def _set_cache(self, url: str, result):
        if not db:
            return
        try:
            cache_key = hashlib.md5(url.encode()).hexdigest()
            db.collection('cache').document(cache_key).set(
                {'url': url, 'result': result, 'cached_at': datetime.now()}
            )
            print(f"✅ 캐시 저장: {url[:50]}...")
        except Exception as e:
            print(f"⚠️ 캐시 저장 실패: {e}")
