"""
분석 비즈니스 로직을 처리하는 서비스 (Facade 패턴)
"""
import os
import json
import hashlib
from datetime import datetime

import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import firestore

from app.models.extractor import BaseExtractor, YoutubeExtractor, ArticleExtractor
from app.models.media import get_media_credibility
from app.config import config

# Gemini 모델 로드
gemini = None
try:
    vertexai.init(project=config.GCP_PROJECT, location=config.GCP_REGION)
    gemini = GenerativeModel('gemini-2.5-flash')
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

        content = content[:config.MAX_CONTENT_LENGTH_FIRST_ANALYSIS]  # 컨텍스트 길이 조절

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
        """Gemini Google Search Grounding을 사용한 실제 기사 검색"""
        if not keywords:
            return []
        try:
            from vertexai.preview.generative_models import GenerativeModel, Tool, grounding

            query = " ".join(keywords[:5])  # 최대 5개 키워드 결합
            print(f"🔍 Gemini Google Search로 검색 중: {query}")

            # Google Search Grounding 도구 설정
            search_tool = Tool.from_google_search_retrieval(
                grounding.GoogleSearchRetrieval()
            )

            # Gemini 모델에 검색 도구 추가
            search_model = GenerativeModel(
                'gemini-2.0-flash-exp',
                tools=[search_tool]
            )

            # 검색 쿼리 실행
            search_prompt = f"""
            다음 키워드와 관련된 최신 뉴스 기사를 검색하고, 각 기사에 대해 다음 정보를 JSON 배열로 반환해주세요:
            - title: 기사 제목
            - snippet: 기사 요약 (2-3문장)
            - url: 기사 URL
            - source: 언론사명
            - published_date: 발행일 (YYYY-MM-DD 형식)

            키워드: {query}

            응답 형식:
            {{"articles": [...]}}
            """

            response = search_model.generate_content(search_prompt)

            # JSON 파싱
            import json
            result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            search_data = json.loads(result_text)

            articles = []
            for result in search_data.get('articles', [])[:15]:  # 최대 15개
                source = result.get('source', '출처 불명')
                credibility_info = get_media_credibility(source)

                articles.append({
                    'title': result.get('title', '제목 없음'),
                    'snippet': result.get('snippet', '내용 없음'),
                    'url': result.get('url', '#'),
                    'source': source,
                    'country': credibility_info.get('country', 'Unknown'),
                    'credibility': credibility_info.get('credibility', 50),
                    'bias': credibility_info.get('bias', '알 수 없음'),
                    'published_date': result.get('published_date', '날짜 없음'),
                })

            print(f"✅ {len(articles)}개 기사 검색 완료")
            return articles

        except Exception as e:
            print(f"⚠️ 기사 검색 실패: {e}")
            print(f"⚠️ Fallback: 샘플 기사 반환")
            # Fallback: 샘플 데이터 반환
            return self._get_sample_articles(keywords)

    def _find_related_articles_with_gemini(
        self, original_content: str, claims: list, articles: list
    ):
        """입장 기반 분석 - 국내/국제 이슈 모두 적용 가능"""
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        original_content = original_content[:config.MAX_CONTENT_LENGTH_SECOND_ANALYSIS]
        articles_text = "\n\n".join(
            [
                f"[기사 {i+1}]\n제목: {article.get('title', '')}\n출처: {article.get('source', '')}\n내용: {article.get('snippet', '')}"
                for i, article in enumerate(articles[:15])  # 컨텍스트 조절
            ]
        )

        prompt = f"""
        당신은 편견 없는 정보 분석가입니다.
        **각 기사가 선택한 주장에 대해 어떤 입장인지 분석해주세요.**

        중요: 언론사의 "고정된 성향"이 아니라, "이 기사의 내용"만 기준으로 판단하세요.
        - 같은 언론사도 이슈마다 다른 입장을 가질 수 있습니다.
        - 절대로 사전에 정해진 라벨(보수/진보)을 사용하지 마세요.

        [원본 콘텐츠 요약]
        {original_content}

        [사용자가 선택한 검증 대상 주장]
        {chr(10).join([f'- {c}' for c in claims])}

        [수집된 최신 기사 목록]
        {articles_text}

        [요청 작업]
        각 기사에 대해 다음을 분석하세요:
        1. 이 기사는 주장에 대해 어떤 입장인가?
           - supporting: 주장을 지지하거나 동의하는 내용
           - opposing: 주장에 반대하거나 부정하는 내용
           - neutral: 입장 없이 사실만 보도하거나 양쪽 입장 병기

        2. 확신도 (0.0 ~ 1.0): 입장이 얼마나 명확한가?

        3. 핵심 근거: 이 기사가 제시하는 구체적인 증거나 인용문 (1-2개)

        4. 프레이밍: 이 기사가 사용하는 서술 방식이나 관점

        [응답 형식 (JSON)]
        {{
          "results": [
            {{
              "claim": "사용자가 선택한 첫 번째 주장",
              "article_analyses": [
                {{
                  "article_index": 1,
                  "stance": "supporting",
                  "confidence": 0.85,
                  "key_evidence": [
                    "첫 번째 핵심 증거나 인용문",
                    "두 번째 핵심 증거나 인용문"
                  ],
                  "framing": "이 기사가 사용하는 프레임 설명"
                }},
                {{
                  "article_index": 2,
                  "stance": "opposing",
                  "confidence": 0.80,
                  "key_evidence": [
                    "첫 번째 핵심 증거나 인용문",
                    "두 번째 핵심 증거나 인용문"
                  ],
                  "framing": "이 기사가 사용하는 프레임 설명"
                }},
                {{
                  "article_index": 3,
                  "stance": "neutral",
                  "confidence": 0.70,
                  "key_evidence": [
                    "첫 번째 핵심 증거나 인용문",
                    "두 번째 핵심 증거나 인용문"
                  ],
                  "framing": "이 기사가 사용하는 프레임 설명"
                }}
              ],
              "stance_summary": {{
                "supporting_count": 0,
                "opposing_count": 0,
                "neutral_count": 0,
                "common_supporting_arguments": [
                  "지지 입장의 공통 논거",
                  "또 다른 공통 논거"
                ],
                "common_opposing_arguments": [
                  "반대 입장의 공통 논거",
                  "또 다른 공통 논거"
                ]
              }}
            }}
          ]
        }}

        [주의사항]
        - 절대로 주장의 참/거짓을 판단하지 마세요.
        - 오직 "이 기사의 내용"을 기준으로 입장을 분석하세요.
        - 언론사 이름으로 입장을 추측하지 마세요.
        - 반드시 JSON 객체만 출력하고 다른 설명은 덧붙이지 마세요.
        """

        try:
            response = gemini.generate_content(prompt)
            result_text = (
                response.text.strip().replace('```json', '').replace('```', '').strip()
            )
            parsed_result = json.loads(result_text)

            # 유효성 검증
            if 'results' not in parsed_result:
                raise ValueError("AI 응답에 'results' 키가 없습니다.")

            if not isinstance(parsed_result['results'], list):
                raise ValueError("AI 응답의 'results'가 배열이 아닙니다.")

            # 결과를 사용자 친화적으로 재구조화
            return self._restructure_by_stance(parsed_result, articles)

        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            print(f"AI 응답 원본 (처음 500자): {result_text[:500]}")
            raise Exception(f"AI 응답을 파싱할 수 없습니다. 다시 시도해주세요.")
        except Exception as e:
            print(f"❌ AI 2차 분석 실패: {e}")
            raise Exception(f"입장 분석 중 오류가 발생했습니다: {e}")

    def _restructure_by_stance(self, analysis_result, articles):
        """
        AI 분석 결과를 입장별로 그룹화
        국내/국제 구분 없이 동일하게 작동
        """
        restructured = []

        for claim_result in analysis_result.get('results', []):
            supporting_articles = []
            opposing_articles = []
            neutral_articles = []

            # 각 기사를 입장별로 분류
            for analysis in claim_result.get('article_analyses', []):
                article_idx = analysis.get('article_index') - 1
                if article_idx < 0 or article_idx >= len(articles):
                    continue

                article = articles[article_idx].copy()
                article['analysis'] = {
                    'stance': analysis.get('stance'),
                    'confidence': analysis.get('confidence'),
                    'key_evidence': analysis.get('key_evidence', []),
                    'framing': analysis.get('framing', '')
                }

                # 입장별로 분류
                stance = analysis.get('stance')
                if stance == 'supporting':
                    supporting_articles.append(article)
                elif stance == 'opposing':
                    opposing_articles.append(article)
                elif stance == 'neutral':
                    neutral_articles.append(article)

            # 확신도 순으로 정렬
            supporting_articles.sort(key=lambda x: x['analysis']['confidence'], reverse=True)
            opposing_articles.sort(key=lambda x: x['analysis']['confidence'], reverse=True)
            neutral_articles.sort(key=lambda x: x['analysis']['confidence'], reverse=True)

            restructured.append({
                'claim': claim_result.get('claim'),
                'supporting_evidence': {
                    'count': len(supporting_articles),
                    'articles': supporting_articles,
                    'common_arguments': claim_result.get('stance_summary', {}).get('common_supporting_arguments', [])
                },
                'opposing_evidence': {
                    'count': len(opposing_articles),
                    'articles': opposing_articles,
                    'common_arguments': claim_result.get('stance_summary', {}).get('common_opposing_arguments', [])
                },
                'neutral_coverage': {
                    'count': len(neutral_articles),
                    'articles': neutral_articles
                },
                'diversity_metrics': {
                    'total_sources': len(supporting_articles) + len(opposing_articles) + len(neutral_articles),
                    'stance_distribution': {
                        'supporting': len(supporting_articles),
                        'opposing': len(opposing_articles),
                        'neutral': len(neutral_articles)
                    }
                }
            })

        return {'results': restructured}

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

    def _get_sample_articles(self, keywords: list):
        """검색 실패 시 샘플 기사 반환"""
        print("⚠️ 샘플 기사 데이터 반환 (검색 기능 비활성화)")
        return [
            {
                'title': f'{" ".join(keywords[:2])}에 대한 샘플 기사',
                'snippet': '실제 기사 검색 기능을 사용하려면 Google Search Grounding API를 활성화하세요.',
                'url': '#',
                'source': 'Sample News',
                'country': 'Unknown',
                'credibility': 50,
                'bias': '중립',
                'published_date': '2024-01-01',
            }
        ]
