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
        [Step 1] 사용자 입력을 GDELT 5대 요소 검색 전략으로 변환 (Gemini 사용)

        Args:
            user_input: 사용자의 자연어 질문
            context: 분석 컨텍스트 {'title_kr', 'key_claims'}

        Returns:
            {
                "success": True/False,
                "data": {
                    "interpreted_intent": "...",
                    "gdelt_params": {
                        "keywords": [...],
                        "entities": [...],
                        "locations": [...],
                        "themes": [...],
                        "event_date": "YYYY-MM-DD"
                    },
                    "search_keywords_en": [...],  # 하위 호환성
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

            # 5대 요소 추출 프롬프트
            prompt = f"""
            당신은 데이터 저널리즘 및 GDELT 검색 전문가입니다.
            사용자의 질문을 분석하여 글로벌 뉴스 검색에 필요한 5대 요소를 추출하세요.

            [질문] "{user_input}"

            [문맥 정보]
            제목: {context_title}
            관련 주장: {str(context_claims)[:500]}

            [필수 지시사항]
            1. **모든 검색 요소는 반드시 영어(English)**로 작성하세요.
            2. **event_date**: 사건이 발생한 날짜 (YYYY-MM-DD 형식). 정확한 날짜를 모르면 최근 날짜 추정.
            3. **entities**: 핵심 인물/조직 영문명 (예: ["Kim Jong Un", "NATO"])
            4. **locations**: 관련 도시/국가 영문명 (예: ["Seoul", "Ukraine", "Middle East"])
            5. **themes**: GDELT 테마 코드 (예: ["ARMEDCONFLICT", "SCANDAL", "ECON_INFLATION"])
               - 주요 테마: ARMEDCONFLICT, SCANDAL, HEALTH_PANDEMIC, ECON_INFLATION, TERROR, ENV_CLIMATECHANGE
            6. **keywords**: 일반 검색 키워드 (위에 포함되지 않은 추가 단어)

            [출력 형식 (JSON Only)]
            {{
                "interpreted_intent": "질문 의도를 한국어로 요약",
                "gdelt_params": {{
                    "event_date": "2024-01-15",
                    "keywords": ["missile", "test"],
                    "entities": ["Kim Jong Un", "US Defense Department"],
                    "locations": ["North Korea", "Pacific Ocean"],
                    "themes": ["ARMEDCONFLICT", "WB_1678_SECURITY_THREAT"]
                }},
                "search_keywords_en": ["North Korea", "missile", "test"],
                "target_country_codes": ["KP", "US", "KR"],
                "confidence": 0.9
            }}

            [예시]
            질문: "북한의 최근 미사일 발사에 대한 미국의 반응은?"
            출력:
            {{
                "interpreted_intent": "북한 미사일 발사에 대한 미국의 공식 입장 및 대응 조치",
                "gdelt_params": {{
                    "event_date": "2024-11-20",
                    "keywords": ["missile", "launch", "response"],
                    "entities": ["North Korea", "United States", "Pentagon"],
                    "locations": ["North Korea", "Washington"],
                    "themes": ["ARMEDCONFLICT", "WB_1678_SECURITY_THREAT"]
                }},
                "search_keywords_en": ["North Korea", "missile", "US response"],
                "target_country_codes": ["KP", "US", "KR"],
                "confidence": 0.95
            }}

            JSON만 출력하세요. 다른 말은 하지 마세요.
            """

            print(f"🤖 5대 요소 검색 쿼리 최적화 중: '{user_input[:50]}...'")

            # Gemini 호출
            response = gemini.generate_content(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '').strip()

            # JSON 파싱
            optimized_data = json.loads(result_text)

            # 하위 호환성: search_keywords_en이 없으면 keywords에서 생성
            if 'search_keywords_en' not in optimized_data and 'gdelt_params' in optimized_data:
                gdelt_params = optimized_data['gdelt_params']
                all_keywords = gdelt_params.get('keywords', []) + gdelt_params.get('entities', [])
                optimized_data['search_keywords_en'] = all_keywords[:config.MAX_KEYWORDS]

            print(f"✅ 5대 요소 추출 완료 (confidence: {optimized_data.get('confidence', 0)})")

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
                    "gdelt_params": {
                        "keywords": [user_input],
                        "entities": [],
                        "locations": [],
                        "themes": [],
                        "event_date": datetime.now().strftime('%Y-%m-%d')
                    },
                    "search_keywords_en": [user_input],
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
        [Step 2] 확정된 검색 전략(claims_data)으로 실제 GDELT 5대 요소 검색 수행
        * 이제 이 함수는 AI 추론을 하지 않고, 전달받은 파라미터로 검색 수행에만 집중합니다.

        Args:
            url: 원본 콘텐츠 URL (현재는 사용하지 않음)
            input_type: 콘텐츠 타입 (현재는 사용하지 않음)
            claims_data: 주장 정보 리스트
                [
                    {
                        "claim_kr": "한국어 주장",
                        "gdelt_params": {  # 5대 요소 (신규)
                            "keywords": [...],
                            "entities": [...],
                            "locations": [...],
                            "themes": [...],
                            "event_date": "YYYY-MM-DD"
                        },
                        "search_keywords_en": [...],  # 하위 호환성
                        "target_country_codes": [...]
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
                print(f"   entities={gdelt_params.get('entities', [])} locations={gdelt_params.get('locations', [])}")
                print(f"   themes={gdelt_params.get('themes', [])} keywords={gdelt_params.get('keywords', [])}")

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

    def _search_real_articles_with_params(self, gdelt_params: dict):
        """
        GDELT 5대 요소 검색 with Google Search Fallback

        Args:
            gdelt_params: {
                'keywords': [...],
                'entities': [...],
                'locations': [...],
                'themes': [...],
                'event_date': 'YYYY-MM-DD'
            }

        Returns:
            검색 결과 리스트
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

    def _search_real_articles(self, keywords: list, target_countries: list = None):
        """
        GDELT Hybrid 검색 (Legacy Wrapper)

        이 함수는 하위 호환성을 위해 유지됩니다.
        내부적으로 _search_real_articles_with_params()를 호출합니다.

        Args:
            keywords: 영어 검색 키워드 리스트
            target_countries: 타겟 국가 코드 리스트 (예: ["US", "CN"])

        Returns:
            검색 결과 리스트
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

        # Legacy 파라미터를 5대 요소 형식으로 변환
        gdelt_params = {
            'keywords': flat_keywords[:config.MAX_KEYWORDS],
            'entities': [],
            'locations': [],
            'themes': [],
            'event_date': datetime.now().strftime('%Y-%m-%d')
        }

        # 새로운 5대 요소 검색 함수 호출
        return self._search_real_articles_with_params(gdelt_params)

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

                # 언론사 정보 추가 (국가/출처 기반)
                media_info = get_media_credibility(
                    meta.get('source', ''),
                    meta.get('country', '')
                )

                # 국영/민영 정보만 추가
                if media_info:
                    meta['media_type'] = media_info.get('type', '알 수 없음')
                    meta['media_category'] = media_info.get('category', '알 수 없음')

                print(f"✅ 추출 성공: {meta.get('source', 'Unknown')} ({meta.get('country', 'Unknown')}) - {meta.get('media_type', 'Unknown')}")
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
        base_query = " ".join(keywords[:config.MAX_KEYWORDS])
        query = base_query

        # 타겟 국가가 있으면 쿼리에 추가
        if target_countries and len(target_countries) > 0:
            country_query = " OR ".join(target_countries)
            query = f"{base_query} ({country_query})"

        print(f"🔍 Google Search Query: {query}")

        try:
            # Google Search Grounding 시도 (Tool 객체 없이 직접 grounding 사용)
            model = GenerativeModel('gemini-2.0-flash')

            # tools 파라미터는 generate_content에 직접 전달

            prompt = f"""Find recent news articles about: {query}

            Return a JSON list of articles with this structure:
            [
              {{"title": "article title", "url": "https://...", "source": "source name"}},
              ...
            ]

            Only return valid JSON, no other text."""

            # Google Search Grounding을 tools로 전달
            response = model.generate_content(
                prompt,
                tools=[grounding.GoogleSearchRetrieval()]
            )

            # Grounding Metadata에서 URL 추출 시도
            articles = []

            # 1. 응답 텍스트에서 JSON 파싱 시도
            try:
                import re
                text = response.text
                # JSON 추출
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    import json
                    parsed = json.loads(json_match.group())
                    for item in parsed[:10]:  # 최대 10개
                        if isinstance(item, dict) and 'url' in item:
                            articles.append({
                                'title': item.get('title', 'No title'),
                                'url': item.get('url', '#'),
                                'source': item.get('source', 'Unknown'),
                                'snippet': item.get('snippet', '')[:500],
                                'country': target_countries[0] if target_countries else 'Unknown',
                                'content': ''
                            })
            except Exception as parse_error:
                print(f"⚠️ JSON 파싱 실패: {parse_error}")

            # 2. Grounding Metadata 확인 (있다면)
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'grounding_metadata'):
                        metadata = candidate.grounding_metadata
                        if hasattr(metadata, 'grounding_chunks'):
                            for chunk in metadata.grounding_chunks[:10]:
                                if hasattr(chunk, 'web') and hasattr(chunk.web, 'uri'):
                                    articles.append({
                                        'title': getattr(chunk.web, 'title', 'No title'),
                                        'url': chunk.web.uri,
                                        'source': 'Google Search',
                                        'snippet': '',
                                        'country': target_countries[0] if target_countries else 'Unknown',
                                        'content': ''
                                    })

            if articles:
                print(f"✅ Google Search에서 {len(articles)}개 URL 추출 성공")
                return articles

            # 3. 실패 시 샘플 데이터 반환 (완전 실패 방지)
            print("⚠️ Google Search URL 추출 실패, 샘플 데이터 반환")
            return []  # 샘플 데이터 대신 빈 배열 반환

        except Exception as e:
            print(f"⚠️ Google Search 실패: {e}")
            return []

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