"""
분석 비즈니스 로직을 처리하는 서비스 (Global Insight Explorer v2)
- 한국어 사용자 최적화
- [New] 임베딩 기반 스마트 필터링(Smart Filtering) 적용
- [Refactor] Config 기반 설정 관리
- [Update] 기사 제목 한글 번역 기능 추가
"""
import os
import json
import hashlib
from datetime import datetime
import numpy as np  # 벡터 계산용

import vertexai
from vertexai.generative_models import GenerativeModel, Tool, grounding
from vertexai.language_models import TextEmbeddingModel  # [신규] 임베딩 모델
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPICallError

from app.models.extractor import BaseExtractor, YoutubeExtractor, ArticleExtractor
from app.models.media import get_media_credibility
from app.config import config
from app.utils.gdelt_search import GDELTSearcher
from app.prompts.analysis_prompts import QUERY_OPTIMIZATION_PROMPT
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 초기화 ---
gemini = None
embedding_model = None
try:
    vertexai.init(project=config.GCP_PROJECT, location=config.GCP_REGION)

    # [리팩토링] Config에서 모델명 가져오기
    gemini = GenerativeModel(config.GEMINI_MODEL_ANALYSIS)

    # [신규] 임베딩 모델 초기화
    embedding_model = TextEmbeddingModel.from_pretrained(config.GEMINI_MODEL_EMBEDDING)

    print(f"✅ (Service) AI 모델 연결 성공: {config.GEMINI_MODEL_ANALYSIS}, {config.GEMINI_MODEL_EMBEDDING}")
except Exception as e:
    print(f"⚠️ (Service) AI 모델 연결 실패: {e}")

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
        self.gdelt = GDELTSearcher()  # GDELT 검색 엔진 초기화

    # ==================================================================
    # [신규] 임베딩 기반 스마트 필터링 헬퍼 함수
    # ==================================================================
    def _get_embedding(self, text: str):
        """텍스트를 벡터(숫자 배열)로 변환"""
        if not embedding_model or not text:
            return None
        try:
            # 임베딩 모델은 입력 텍스트를 768차원 등의 벡터로 변환함
            embeddings = embedding_model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            print(f"⚠️ 임베딩 생성 실패: {e}")
            return None

    def _calculate_similarity(self, vec1, vec2):
        """두 벡터 간의 코사인 유사도 계산 (-1.0 ~ 1.0)"""
        if vec1 is None or vec2 is None:
            return 0.0
        try:
            return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        except Exception as e:
            print(f"⚠️ 유사도 계산 실패: {e}")
            return 0.0

    def _translate_to_korean(self, text: str) -> str:
        """
        [New] Gemini를 사용하여 기사 제목을 자연스러운 한국어로 번역
        """
        if not text or not gemini:
            return text
        try:
            prompt = f"""
            Translate the following news headline into natural Korean.
            Do not explain, just provide the translation.
            
            Headline: "{text}"
            Korean translation:
            """
            # 빠른 응답을 위해 temperature 낮춤
            response = gemini.generate_content(prompt, generation_config={"temperature": 0.1})
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ 번역 실패: {e}")
            return text

    def _get_extractor(self, input_type: str) -> BaseExtractor:
        extractor = self.extractors.get(input_type)
        if not extractor:
            raise ValueError(f"지원하지 않는 입력 타입: {input_type}")
        return extractor

    # ==================================================================
    # 1️⃣ 1차 분석 (Initial Analysis) - 한국어 사용자 최적화
    # ==================================================================
    def analyze_content(self, url: str, input_type: str):
        # 캐시 확인
        cached = self._get_cache(url)
        if cached:
            return cached, True

        # 콘텐츠 추출
        print(f"📥 콘텐츠 추출 중: {url[:50]}...")
        extractor = self._get_extractor(input_type)
        content = extractor.extract(url)
        
        if not content or len(content) < 50:
            raise Exception("콘텐츠를 추출할 수 없거나 내용이 너무 짧습니다.")
            
        print(f"✅ 추출 완료: {len(content)} 글자")

        # AI 분석
        print("🤖 Gemini로 1차 분석 중 (한글 요약 + 영어 검색어 생성)...")
        result = self._analyze_with_gemini_bridge(content)
        print("✅ 1차 분석 완료")

        # 캐시 저장
        self._set_cache(url, result)
        return result, False

    def _analyze_with_gemini_bridge(self, content: str):
        """
        Gemini 프롬프트: 한국어 입력을 받아 '한국어 요약'과 '영어 검색어'를 동시 생성
        """
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        content = content[:config.MAX_CONTENT_LENGTH_FIRST_ANALYSIS]

        prompt = f"""
        당신은 국제 정세 및 미디어 분석 전문가입니다. 
        주어진 텍스트(영상 자막 또는 기사)를 분석하여 다음 정보를 JSON 형식으로 추출하세요.

        [분석 대상 텍스트]
        {content}

        [필수 요구사항]
        1. **사용자는 한국인입니다.** 모든 설명과 요약은 자연스러운 **한국어**로 작성하세요.
        2. **검색 키워드(search_keywords_en)**는 반드시 **영어(English)**로 작성하세요.
           - ❌ 잘못된 예: "북한 미사일", "경제 위기"
           - ✅ 올바른 예: "North Korea missile", "economic crisis"
           - 이유: 전 세계 뉴스(GDELT, Google) 검색은 영어로만 가능합니다
        3. **관련 국가(target_country_codes)**는 해당 이슈와 이해관계가 있는 국가들의 **2자리 ISO 코드**로 작성하세요.
           (예: 한국='KR', 미국='US', 중국='CN', 북한='KP', 러시아='RU', 일본='JP')

        [출력 예시]
        {{
          "title_kr": "북한 신형 ICBM 발사와 국제사회 반응",
          "summary_kr": "북한이 신형 ICBM 화성-18호를 발사했습니다. 미국과 한국은 강력히 규탄했으며, 유엔 안보리 긴급회의가 소집되었습니다.",
          "topics": ["북한", "미사일", "국제정치"],
          "key_claims": [
            {{
              "claim_kr": "북한의 화성-18호는 사거리 15,000km의 신형 ICBM이다",
              "search_keywords_en": ["North Korea", "Hwasong-18", "ICBM", "intercontinental ballistic missile", "15000km range"],
              "target_country_codes": ["KR", "US", "JP", "CN"]
            }},
            {{
              "claim_kr": "미국은 추가 제재를 검토 중이다",
              "search_keywords_en": ["United States", "North Korea sanctions", "additional sanctions", "UN Security Council"],
              "target_country_codes": ["US", "KR", "CN", "RU"]
            }}
          ]
        }}

        [출력 형식 (JSON Only)]
        반드시 위 예시와 동일한 형식으로 출력하세요.
        search_keywords_en은 절대로 한국어를 포함하지 마세요.
        JSON 외에 다른 말은 하지 마세요.
        """

        try:
            response = gemini.generate_content(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            analysis_result = json.loads(result_text)

            # ✅ 영어 키워드 검증 및 자동 생성
            if 'key_claims' in analysis_result:
                for claim in analysis_result['key_claims']:
                    # search_keywords_en이 없거나 비어있으면 claim_kr로 생성 (폴백)
                    if not claim.get('search_keywords_en') or len(claim.get('search_keywords_en', [])) == 0:
                        print(f"⚠️ 영어 키워드 누락 감지, claim_kr로 대체: {claim.get('claim_kr', '')[:30]}...")
                        claim['search_keywords_en'] = [claim.get('claim_kr', '')]
                    else:
                        # 한글 포함 여부 확인 (간단한 유니코드 범위 체크)
                        keywords = claim.get('search_keywords_en', [])
                        has_korean = any(
                            any('\uac00' <= char <= '\ud7a3' for char in keyword)
                            for keyword in keywords
                        )
                        if has_korean:
                            print(f"⚠️ search_keywords_en에 한글 감지! AI가 프롬프트를 따르지 않았습니다: {keywords}")
                            print(f"   → 이 키워드로 GDELT 검색이 실패할 수 있습니다. claim_kr: {claim.get('claim_kr', '')[:50]}")

                    # target_country_codes가 없으면 빈 배열로 초기화
                    if 'target_country_codes' not in claim:
                        claim['target_country_codes'] = []

            return analysis_result
        except Exception as e:
            print(f"❌ AI 1차 분석 실패: {e}")
            raise Exception(f"AI 분석 중 오류가 발생했습니다: {e}")

    def optimize_search_query(self, user_input: str, context: dict):
        """
        사용자 질문을 분석하여 '검색 키워드'와 '타겟 국가들'을 추출합니다.
        이제 찬성/반대가 아니라 '어느 나라의 시각을 볼 것인가'를 결정합니다.
        """
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        prompt = f"""
        당신은 국제 뉴스 큐레이터입니다. 사용자의 질문을 분석하여 글로벌 시각 비교를 위한 검색 전략을 수립하세요.

        [질문] "{user_input}"

        [분석 목표]
        1. 이 이슈가 **단일 국가 이슈(Case A)**인지 **국가 간/다국적 이슈(Case B)**인지 판단하세요.
           - Case A: 주체가 기업, 개인, 또는 한 국가 내부의 사건 (예: 스페이스X 발사, 한국 의대 파업)
           - Case B: 주체가 국가 정부이거나, 여러 나라가 얽힌 사건 (예: 미중 무역 전쟁, 캄보디아 납치 사건)
        2. **검색할 국가(target_countries)**를 3~5개 선정하세요.
           - Case A: 본국(Home) + 경쟁국/관심국(Interested)
           - Case B: 당사국(Stakeholders) + 인접국/영향받는 국(Neighbors)
           - **반드시 2자리 ISO 국가 코드(예: US, KR, CN, KH, VN)로 출력하세요.**
        3. 검색에 사용할 **영어 키워드**와 **GDELT 테마**를 추출하세요.
           - 범죄 사건의 경우 법률적 용어(Trafficking, Scam 등)를 포함하세요.

        [출력 형식 (JSON Only)]
        {{
            "issue_type": "single" 또는 "multi_country",
            "primary_country": "KR",  // 사건의 중심 국가 (없으면 'Global')
            "topic_en": "Cambodia job scam and kidnapping",
            "gdelt_params": {{
                "keywords": ["human trafficking", "cyber scam", "job fraud", "Cambodia"],
                "themes": ["CRIME_COMMON_ROBBERY", "HUMAN_TRAFFICKING", "MANMADE_DISASTER_IMPLIED"],
                "event_date": "2024-01-01" // 추정 날짜
            }},
            "target_countries": [
                {{"code": "KR", "role": "victim", "reason": "피해자 국적"}},
                {{"code": "KH", "role": "source", "reason": "사건 발생국"}},
                {{"code": "CN", "role": "involved", "reason": "범죄 연루 및 공조"}},
                {{"code": "VN", "role": "neighbor", "reason": "인접국 관점"}}
            ]
        }}
        JSON 외에 다른 말은 하지 마세요.
        """

        try:
            print(f"🤖 이슈 유형 및 타겟 국가 분석 중: '{user_input}'")
            response = gemini.generate_content(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return {"success": True, "data": json.loads(result_text)}
        except Exception as e:
            print(f"⚠️ 쿼리 최적화 실패: {e}")
            # Fallback (기본값: 미국, 한국)
            return {
                "success": False,
                "data": {
                    "issue_type": "multi_country",
                    "target_countries": [{"code": "US"}, {"code": "KR"}],
                    "gdelt_params": {"keywords": [user_input], "themes": []}
                }
            }

    # ==================================================================
    # [Phase 1.5 핵심] 스마트 필터링이 적용된 국가별 검색
    # ==================================================================
    def get_global_perspectives(self, search_params: dict):
        """
        확정된 전략에 따라 국가별로 GDELT를 조회하고(Loop Search),
        임베딩 기반 스마트 필터링을 적용하여 관련성 높은 기사만 선별합니다.
        """
        gdelt_base_params = search_params.get('gdelt_params', {})
        target_countries = search_params.get('target_countries', [])
        topic_en = search_params.get('topic_en', '')

        # 1. [기준점] 주제(Topic)에 대한 임베딩 생성
        print(f"🧠 주제 임베딩 생성 중: '{topic_en}'")
        topic_embedding = self._get_embedding(topic_en)

        # 최종 결과 컨테이너 (프론트엔드 약속 포맷)
        final_response = {
            "status": "success",
            "issue_type": search_params.get('issue_type', 'multi_country'),
            "topic": topic_en,
            "data": {}  # 여기에 국가 코드("US", "KR")가 키(Key)로 들어갑니다.
        }

        all_collected_urls = set()  # 중복 기사 방지용 (URL)

        # 🔄 국가별 루프 실행
        for target in target_countries:
            country_code = target.get('code', 'Unknown')
            role_desc = target.get('reason', '')

            print(f"🌍 [{country_code}] 검색 시작 ({role_desc})...")

            # 1. 해당 국가 전용 파라미터 설정
            current_params = gdelt_base_params.copy()
            current_params['locations'] = [country_code]  # GDELT Location 필터 활용

            # 2. GDELT 검색 (수량을 넉넉하게 가져와서 필터링)
            raw_articles = self.gdelt.search(current_params)

            # 3. [스마트 필터링] 임베딩 유사도 검사
            valid_articles = []
            for article in raw_articles:
                if article['url'] in all_collected_urls:
                    continue

                # 제목이 없는 경우 소스로 대체
                title = article.get('title') or article.get('source') or ''

                # 유사도 계산 (주제 <-> 기사 제목)
                score = 0.0
                if topic_embedding:
                    article_embedding = self._get_embedding(title)
                    score = self._calculate_similarity(topic_embedding, article_embedding)
                else:
                    score = 1.0  # 임베딩 실패 시 통과

                # [필터링] 기준점(config.SIMILARITY_THRESHOLD) 이상만 합격
                if score >= config.SIMILARITY_THRESHOLD:
                    article['relevance_score'] = round(score, 3)
                    valid_articles.append(article)
                    all_collected_urls.add(article['url'])
                    # print(f"   ✅ 합격 (유사도 {score:.3f}): {title[:50]}...")
                else:
                    pass
                    # print(f"   🗑️ 제외 (유사도 {score:.3f}): {title[:50]}...")

            # 관련성 점수 순으로 정렬 (높은 게 위로)
            valid_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

            # 상위 5개만 선택 (쿼터제)
            top_articles = valid_articles[:5]

            # 4. 본문 추출 (병렬) + [New] 제목 번역
            if top_articles:
                print(f"   ↳ {len(top_articles)}개 기사 본문 추출 및 번역")
                full_articles = self._extract_contents_parallel(top_articles)

                # 5. 결과 저장
                final_response['data'][country_code] = {
                    "role": role_desc,
                    "count": len(full_articles),
                    "articles": full_articles
                }
            else:
                # 기사가 없는 경우도 빈 리스트로 명시 (UI 처리를 위해)
                final_response['data'][country_code] = {
                    "role": role_desc,
                    "count": 0,
                    "articles": [],
                    "message": "관련성 높은 기사를 찾지 못했습니다."
                }

        return final_response

    # ==================================================================
    # 2️⃣ 2차 분석 (Find Sources) - AI 추론 없이 검색만 수행
    # ==================================================================
    def find_sources_for_claims(
        self, url: str, input_type: str, claims_data: list
    ):
        """
        [Step 2] 확정된 검색 전략(claims_data)으로 실제 GDELT 5대 요소 검색 수행
        """
        all_results = []
        all_articles = []

        # 각 주장별로 독립적인 검색 수행
        for claim_data in claims_data:
            claim_kr = claim_data.get('claim_kr', '')

            # ✅ NEW: gdelt_params 우선 사용 (5대 요소 검색)
            gdelt_params = claim_data.get('gdelt_params')

            if not gdelt_params:
                # Fallback: 기존 search_keywords_en 방식으로 변환
                search_keywords = claim_data.get('search_keywords_en', [])
                target_countries = claim_data.get('target_country_codes', [])

                if not search_keywords:
                    print(f"⚠️ 검색 파라미터 없음 - 스킵: '{claim_kr[:30]}...'")
                    continue

                gdelt_params = {
                    'keywords': search_keywords,
                    'entities': [],
                    'locations': [],
                    'themes': [],
                    'event_date': datetime.now().strftime('%Y-%m-%d')
                }
                print(f"🔍 '{claim_kr[:15]}...' 검색 (Legacy 모드: keywords={search_keywords})")
            else:
                print(f"🔍 '{claim_kr[:15]}...' 검색 (5대 요소 모드)")

            # GDELT 5대 요소 검색 실행
            articles = self._search_real_articles_with_params(gdelt_params)

            # 결과 구조화
            result_entry = {
                "claim": claim_kr,
                "searched_keywords": gdelt_params.get('keywords', []),
                "articles": articles
            }
            all_results.append(result_entry)
            all_articles.extend(articles)

        # 중복 제거 (URL 기준)
        unique_articles = {v['url']: v for v in all_articles}.values()
        final_articles = list(unique_articles)

        print(f"✅ 검색 완료: {len(final_articles)}개 기사 발견")

        # AI 분석 없이 검색 결과만 반환
        return {"results": all_results}, final_articles

    def _search_real_articles_with_params(self, gdelt_params: dict):
        """
        GDELT 5대 요소 검색 with Google Search Fallback
        """
        if not gdelt_params:
            return []

        # 1️⃣ GDELT 5대 요소 검색 시도 (무료, 빠름, 글로벌)
        print(f"📊 [1/2] GDELT 5대 요소 검색 중...")
        gdelt_results = []
        try:
            gdelt_results = self.gdelt.search(gdelt_params)
        except Exception as e:
            print(f"⚠️ GDELT 검색 실패: {e}")

        # 2️⃣ 병렬 본문 추출 (ThreadPool 10개 워커)
        if gdelt_results:
            print(f"🔄 병렬 본문 추출 중... ({len(gdelt_results)}개 기사)")
            extracted = self._extract_contents_parallel(gdelt_results)
            print(f"✅ 추출 완료: {len(extracted)}개")
            return extracted

        # 3️⃣ GDELT 실패 시 Google Search Grounding 폴백
        print(f"⚠️ GDELT 검색 결과 없음, Google Search 시도...")

        # gdelt_params에서 키워드 추출 (모든 요소 결합)
        all_keywords = []
        all_keywords.extend(gdelt_params.get('keywords', []))
        all_keywords.extend(gdelt_params.get('entities', []))
        all_keywords.extend(gdelt_params.get('locations', []))

        google_results = self._search_google_fallback(all_keywords[:config.MAX_KEYWORDS], [])

        if google_results:
            print(f"✅ Google Search 완료: {len(google_results)}개 발견")
            return google_results

        print(f"⚠️ Google Search도 결과 없음")
        return []

    def _extract_contents_parallel(self, articles_meta: list):
        """
        병렬 처리로 기사 본문 추출 및 [New] 제목 번역 (ThreadPool)
        """
        extracted = []
        extractor = self.extractors['article']

        def fetch_one(meta):
            """단일 기사 추출 (병렬 실행 함수)"""
            try:
                url = meta.get('url', '')
                if not url or url == '#':
                    return None

                # 제목과 본문 추출
                result = extractor.extract_with_title(url)
                title = result.get('title', '')
                content = result.get('content', '')

                # 너무 짧으면 무시
                if not content or len(content) < 100:
                    return None

                # 메타데이터에 제목과 본문 추가
                meta['title'] = title if title else meta.get('source', 'No title')  # 제목이 없으면 출처를 제목으로
                
                # [New] 제목 한국어 번역 수행 (병렬 처리의 이점 활용)
                meta['title_kr'] = self._translate_to_korean(meta['title'])
                
                meta['content'] = content
                meta['snippet'] = content[:500]  # 미리보기

                # 언론사 정보 추가 (국가/출처 기반)
                media_info = get_media_credibility(
                    meta.get('source', ''),
                    meta.get('country', '')
                )

                # 국영/민영 정보만 추가
                if media_info:
                    meta['media_type'] = media_info.get('type', '알 수 없음')
                    meta['media_category'] = media_info.get('category', '알 수 없음')

                print(f"✅ 추출/번역 성공: {meta.get('source', 'Unknown')}")
                return meta

            except Exception as e:
                print(f"⚠️ 추출 실패: {meta.get('url', 'unknown')} - {e}")
                return None

        # ThreadPool 병렬 실행
        with ThreadPoolExecutor(max_workers=config.THREAD_POOL_WORKERS) as executor:
            futures = [executor.submit(fetch_one, item) for item in articles_meta]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    extracted.append(result)

        return extracted

    def _search_google_fallback(self, keywords: list, target_countries: list = None):
        """Google Search 폴백 (GDELT 실패 시)"""
        if not keywords:
            return []

        base_query = " ".join(keywords[:config.MAX_KEYWORDS])
        query = base_query

        if target_countries and len(target_countries) > 0:
            country_query = " OR ".join(target_countries)
            query = f"{base_query} ({country_query})"

        print(f"🔍 Google Search Query: {query}")

        try:
            model = GenerativeModel(config.GEMINI_MODEL_SEARCH)
            prompt = f"""Find recent news articles about: {query}
            Return a JSON list of articles with this structure:
            [ {{"title": "article title", "url": "https://...", "source": "source name"}}, ... ]
            Only return valid JSON."""

            search_tool = Tool(google_search_retrieval=grounding.GoogleSearchRetrieval())
            response = model.generate_content(prompt, tools=[search_tool])

            articles = []
            try:
                import re
                text = response.text
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    for item in parsed[:10]:
                        if isinstance(item, dict) and 'url' in item:
                            item['country'] = target_countries[0] if target_countries else 'Unknown'
                            # 구글 검색 결과도 번역
                            item['title_kr'] = self._translate_to_korean(item.get('title', ''))
                            articles.append(item)
            except Exception:
                pass
            
            if not articles and hasattr(response, 'candidates'):
                 for candidate in response.candidates:
                    if hasattr(candidate, 'grounding_metadata'):
                        for chunk in candidate.grounding_metadata.grounding_chunks[:10]:
                            if hasattr(chunk, 'web'):
                                articles.append({
                                    'title': chunk.web.title,
                                    'title_kr': self._translate_to_korean(chunk.web.title),
                                    'url': chunk.web.uri,
                                    'source': 'Google Search',
                                    'country': target_countries[0] if target_countries else 'Unknown'
                                })

            if articles:
                print(f"✅ Google Search에서 {len(articles)}개 URL 추출 성공")
                # 본문 추출은 별도로 해야 함 (여기서는 URL만 반환하거나 그대로 사용)
                return articles

            return []

        except Exception as e:
            print(f"⚠️ Google Search 실패: {e}")
            return []

    # --- 캐시 및 유틸리티 ---
    def _get_cache(self, url: str):
        if not db: return None
        try:
            cache_key = hashlib.md5(url.encode()).hexdigest()
            doc = db.collection('cache').document(cache_key).get()
            if doc.exists:
                print(f"✅ 캐시 히트: {url[:30]}...")
                return doc.to_dict().get('result')
        except: pass
        return None

    def _set_cache(self, url: str, result):
        if not db: return
        try:
            cache_key = hashlib.md5(url.encode()).hexdigest()
            db.collection('cache').document(cache_key).set({
                'url': url, 'result': result, 'cached_at': datetime.now()
            })
        except: pass