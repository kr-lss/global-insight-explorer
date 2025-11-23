"""
분석 비즈니스 로직을 처리하는 서비스 (Global Insight Explorer v2)
- 한국어 사용자 최적화 (입력/출력: 한국어, 내부검색: 영어)
- Google Search Grounding 오류 수정 및 최적화
"""
import os
import json
import hashlib
from datetime import datetime

import vertexai
from vertexai.generative_models import GenerativeModel, Tool, grounding
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
try:
    vertexai.init(project=config.GCP_PROJECT, location=config.GCP_REGION)
    # 1차/2차 분석용 일반 모델 (비용 효율적인 Flash 모델 권장)
    gemini = GenerativeModel('gemini-2.0-flash') 
    print("✅ (Service) Gemini API 연결 성공")
except Exception as e:
    print(f"⚠️ (Service) Gemini API 연결 실패: {e}")

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
           (이유: 전 세계 뉴스(GDELT, Google) 검색 정확도를 높이기 위함)
        3. **관련 국가(target_country_codes)**는 해당 이슈와 이해관계가 있는 국가들의 **2자리 ISO 코드**로 작성하세요.
           (예: 한국='KR', 미국='US', 중국='CN', 북한='KP', 러시아='RU', 일본='JP')

        [출력 형식 (JSON Only)]
        {{
          "title_kr": "콘텐츠 제목 또는 주제 (한국어)",
          "summary_kr": "전체 내용 요약 (한국어 3문장 내외)",
          "topics": ["주제1", "주제2"], 
          "key_claims": [
            {{
              "claim_kr": "핵심 주장 1 (한국어)",
              "search_keywords_en": ["keyword1", "keyword2", "specific term"],
              "target_country_codes": ["CN", "US"] // 이 주장에 대해 입장을 확인해봐야 할 국가들
            }},
            {{
              "claim_kr": "핵심 주장 2 (한국어)",
              "search_keywords_en": ["keyword3", "keyword4"],
              "target_country_codes": ["RU", "UA"]
            }}
          ]
        }}

        JSON 외에 다른 말은 하지 마세요.
        """

        try:
            response = gemini.generate_content(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(result_text)
        except Exception as e:
            print(f"❌ AI 1차 분석 실패: {e}")
            raise Exception(f"AI 분석 중 오류가 발생했습니다: {e}")

    def optimize_search_query(self, user_input: str, context: dict):
        """
        [Step 1] 사용자 입력을 GDELT 검색 전략으로 변환 (Gemini 사용)

        Args:
            user_input: 사용자의 자연어 질문
            context: 분석 컨텍스트 {'title_kr', 'key_claims'}

        Returns:
            {
                "success": True/False,
                "data": {
                    "interpreted_intent": "...",
                    "search_keywords_en": [...],
                    "search_keywords_kr": [...],
                    "target_country_codes": [...],
                    "confidence": 0.95
                },
                "error": "..." (실패 시)
            }
        """
        try:
            if not gemini:
                raise Exception("Gemini API를 사용할 수 없습니다.")

            # 문맥 정보 추출 (없으면 기본값)
            context_title = context.get('title_kr', '')
            context_claims = context.get('key_claims', [])

            # 프롬프트 생성
            prompt = QUERY_OPTIMIZATION_PROMPT.format(
                user_input=user_input,
                context_title=context_title,
                context_claims=str(context_claims)[:1000]  # 길이 제한
            )

            print(f"🤖 검색 쿼리 최적화 중: '{user_input[:50]}...'")

            # Gemini 호출
            response = gemini.generate_content(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '').strip()

            # JSON 파싱
            optimized_data = json.loads(result_text)

            print(f"✅ 쿼리 최적화 완료 (confidence: {optimized_data.get('confidence', 0)})")

            return {
                "success": True,
                "data": optimized_data
            }

        except Exception as e:
            print(f"⚠️ 쿼리 최적화 실패: {e}")

            # Fallback: 입력 텍스트를 그대로 키워드로 사용
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "interpreted_intent": "Fallback raw search",
                    "search_keywords_en": [user_input],
                    "search_keywords_kr": [user_input],
                    "target_country_codes": [],
                    "confidence": 0.1
                }
            }

    # ==================================================================
    # 2️⃣ 2차 분석 (Find Sources) - AI 추론 없이 검색만 수행
    # ==================================================================
    def find_sources_for_claims(
        self, url: str, input_type: str, claims_data: list
    ):
        """
        [Step 2] 확정된 검색 전략(claims_data)으로 실제 GDELT 검색 수행
        * 이제 이 함수는 AI 추론을 하지 않고, 전달받은 키워드로 검색 수행에만 집중합니다.

        Args:
            url: 원본 콘텐츠 URL (현재는 사용하지 않음)
            input_type: 콘텐츠 타입 (현재는 사용하지 않음)
            claims_data: 주장 정보 리스트
                [
                    {
                        "claim_kr": "한국어 주장",
                        "search_keywords_en": ["keyword1", "keyword2"],
                        "target_country_codes": ["US", "CN"]
                    },
                    ...
                ]

        Returns:
            (result, articles) tuple
            - result: 각 주장별 검색 결과 리스트
            - articles: 모든 기사를 평탄화한 리스트
        """
        all_results = []
        all_articles = []

        # 각 주장별로 독립적인 검색 수행
        for claim_data in claims_data:
            claim_kr = claim_data.get('claim_kr', '')
            search_keywords = claim_data.get('search_keywords_en', [])
            target_countries = claim_data.get('target_country_codes', [])

            # 키워드가 없으면 스킵 (AI 생성하지 않음)
            if not search_keywords:
                print(f"⚠️ 키워드 없음 - 스킵: '{claim_kr[:30]}...'")
                continue

            # GDELT 검색 실행 (영어 키워드 + 타겟 국가)
            print(f"🔍 '{claim_kr[:15]}...' 검색 시작 (키워드: {search_keywords}, 국가: {target_countries})")
            articles = self._search_real_articles(search_keywords, target_countries)

            # 결과 구조화
            result_entry = {
                "claim": claim_kr,
                "searched_keywords": search_keywords,
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

    def _generate_keywords_on_the_fly(self, claim_kr: str):
        """사용자 입력 주장을 위한 영어 키워드 및 타겟 국가 생성"""
        if not gemini:
            return {"keywords": [claim_kr], "countries": []}

        try:
            prompt = f"""
            Translate this Korean claim into 2-3 English search keywords for news verification.
            Also suggest 2 relevant country codes (ISO 3166-1 alpha-2).
            Claim: "{claim_kr}"
            Output JSON: {{"keywords": ["kw1", "kw2"], "countries": ["US", "KR"]}}
            """
            response = gemini.generate_content(prompt)
            text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"⚠️ 키워드 생성 실패: {e}")
            return {"keywords": [claim_kr], "countries": []}

    def _search_real_articles(self, keywords: list, target_countries: list = None):
        """
        GDELT Hybrid 검색: GDELT (무료) → Google Search (유료 폴백)

        Args:
            keywords: 영어 검색 키워드 리스트
            target_countries: 타겟 국가 코드 리스트 (예: ["US", "CN"])
        """
        if not keywords:
            return []

        # 키워드 리스트 평탄화
        flat_keywords = []
        for k in keywords:
            if isinstance(k, list):
                flat_keywords.extend(k)
            else:
                flat_keywords.append(k)

        # 1️⃣ GDELT 검색 시도 (무료, 빠름, 글로벌)
        print(f"📊 [1/2] GDELT 검색 중... (키워드: {flat_keywords[:3]}, 국가: {target_countries})")
        gdelt_results = []
        try:
            gdelt_results = self.gdelt.search(
                keywords=flat_keywords[:5],  # 최대 5개 키워드
                target_countries=target_countries,
                days=7,  # 최근 7일
                limit=30  # 최대 30개
            )
        except Exception as e:
            print(f"⚠️ GDELT 검색 실패: {e}")

        # 2️⃣ 병렬 본문 추출 (ThreadPool 10개 워커)
        if gdelt_results:
            print(f"🔄 병렬 본문 추출 중... ({len(gdelt_results)}개 기사)")
            extracted = self._extract_contents_parallel(gdelt_results)
            print(f"✅ 추출 완료: {len(extracted)}개")
            return extracted

        # GDELT 결과가 없으면 빈 배열 반환
        print(f"⚠️ GDELT 검색 결과 없음")
        return []

    def _extract_contents_parallel(self, articles_meta: list):
        """
        병렬 처리로 기사 본문 추출 (ThreadPool)

        Args:
            articles_meta: GDELT 검색 결과 [{url, source, title, date, tone, country}, ...]

        Returns:
            본문이 추출된 기사 리스트
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
                meta['content'] = content
                meta['snippet'] = content[:500]  # 미리보기

                # 신뢰도 추가 (국가/출처 기반)
                if 'credibility' not in meta:
                    meta['credibility'] = get_media_credibility(
                        meta.get('source', ''),
                        meta.get('country', '')
                    )

                print(f"✅ 추출 성공: {meta.get('source', 'Unknown')} ({meta.get('country', 'Unknown')})")
                return meta

            except Exception as e:
                print(f"⚠️ 추출 실패: {meta.get('url', 'unknown')} - {e}")
                return None

        # ThreadPool 병렬 실행 (max_workers=10)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_one, item) for item in articles_meta]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    extracted.append(result)

        return extracted

    def _search_google_fallback(self, keywords: list, target_countries: list = None):
        """
        Google Search 폴백 (GDELT 실패 시)

        Args:
            keywords: 영어 검색 키워드 리스트
            target_countries: 타겟 국가 코드 리스트

        Returns:
            검색 결과 리스트
        """
        if not keywords:
            return []

        # 기본 쿼리
        base_query = " ".join(keywords[:7])  # 최대 7단어
        query = base_query

        # 타겟 국가가 있으면 쿼리에 추가
        if target_countries and len(target_countries) > 0:
            country_query = " OR ".join(target_countries)
            query = f"{base_query} ({country_query})"

        print(f"🔍 Google Search Query: {query}")

        try:
            # Google Search Grounding 시도
            search_tool = Tool(
                google_search=grounding.GoogleSearchRetrieval()
            )

            model = GenerativeModel(
                'gemini-2.0-flash',
                tools=[search_tool]
            )

            prompt = f"Search for latest news articles about: {query}. Provide details."
            response = model.generate_content(prompt)

            # TODO: Grounding Metadata에서 실제 URL 추출
            # 현재는 구조적 URL 추출이 어려우므로 샘플 반환
            print("⚠️ Google Search 완료 (URL 추출 로직 보완 필요)")
            return self._get_sample_articles(keywords, target_countries)

        except Exception as e:
            print(f"⚠️ Google Search 실패: {e}")
            return self._get_sample_articles(keywords, target_countries)

    def _compare_perspectives_with_gemini(
        self, original_content: str, claims: list, articles: list
    ):
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        original_content = original_content[:config.MAX_CONTENT_LENGTH_SECOND_ANALYSIS]
        
        # 기사 목록 텍스트화
        articles_text = "\n".join([
            f"- [{a['source']} ({a['country']})] {a['title']}: {a['snippet']}"
            for a in articles
        ])

        prompt = f"""
        당신은 중립적인 '국제 뉴스 분석가'입니다.
        사용자가 선택한 주장에 대해, 세계 각국의 언론이 어떻게 보도하고 있는지 객관적으로 비교 분석해주세요.
        **반드시 한국어로 답변하세요.**

        **절대로 특정 주장이 사실인지 거짓인지 단정 짓지 마세요.**
        오직 'A 언론사는 이렇게 보도했고, B 언론사는 저렇게 보도했다'는 차이점과 맥락을 보여주는 데 집중하세요.

        [분석 대상 주장]
        {chr(10).join([f'- {c}' for c in claims])}

        [수집된 기사 데이터]
        {articles_text}

        [지시사항]
        1. 각 주장에 대해 수집된 기사들이 **지지(Supporting)**하는지, **반박(Opposing)**하는지, 또는 **중립/관련없음**인지 분석하세요.
        2. 국가별 언론의 시각 차이가 있다면 지적해주세요 (예: 미국 언론은 경제적 측면을, 중국 언론은 정치적 측면을 강조).
        3. **판단은 사용자에게 맡기고**, 다양한 관점이 있다는 것만 보여주세요.

        [응답 형식 (JSON)]
        {{
          "results": [
            {{
              "claim": "주장 내용",
              "perspectives": [
                 {{
                   "country": "US",
                   "media": "CNN",
                   "stance": "Supporting",
                   "viewpoint": "이 기사는 ~~한 근거를 들어 해당 주장을 지지하는 논조입니다."
                 }},
                 {{
                   "country": "CN",
                   "media": "Global Times",
                   "stance": "Opposing",
                   "viewpoint": "반면 이 기사는 ~~라며 다른 관점을 제시합니다."
                 }}
              ],
              "summary_kr": "종합해보면 미국 언론은 경제적 측면을, 중국 언론은 정치적 측면을 강조하고 있습니다. (판단은 사용자 몫)"
            }}
          ]
        }}
        """
        
        try:
            response = gemini.generate_content(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(result_text)
        except Exception as e:
            print(f"❌ AI 2차 분석 실패: {e}")
            # 빈 결과 반환하여 프론트엔드 에러 방지
            return {"results": []}

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

    def _get_sample_articles(self, keywords: list, target_countries: list = None):
        """검색 실패 시 테스트용 샘플 데이터"""
        k = keywords[0] if keywords else "이슈"

        # 타겟 국가에 맞는 샘플 데이터 생성
        sample_sources = []
        if target_countries and len(target_countries) > 0:
            # 타겟 국가별 대표 언론사 매핑
            country_media = {
                'US': {'source': 'CNN', 'credibility': 80},
                'UK': {'source': 'BBC', 'credibility': 85},
                'CN': {'source': 'Xinhua', 'credibility': 60},
                'RU': {'source': 'RT', 'credibility': 55},
                'JP': {'source': 'NHK', 'credibility': 75},
                'KR': {'source': 'Yonhap', 'credibility': 75},
                'FR': {'source': 'France 24', 'credibility': 80},
                'DE': {'source': 'DW', 'credibility': 80},
            }
            for country in target_countries[:3]:  # 최대 3개국
                media = country_media.get(country, {'source': f'{country} News', 'credibility': 70})
                sample_sources.append({
                    'title': f'{media["source"]}: {k} coverage',
                    'snippet': f'{country} perspective on {k}...',
                    'url': '#',
                    'source': media['source'],
                    'country': country,
                    'credibility': media['credibility']
                })
        else:
            # 기본 샘플 (타겟 국가 없을 때)
            sample_sources = [
                {'title': f'Global view on {k}', 'snippet': 'Western media perspective...', 'url': '#', 'source': 'CNN', 'country': 'US', 'credibility': 80},
                {'title': f'Alternative view on {k}', 'snippet': 'Eastern media perspective...', 'url': '#', 'source': 'Xinhua', 'country': 'CN', 'credibility': 60},
            ]

        return sample_sources