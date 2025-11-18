"""
분석 비즈니스 로직을 처리하는 서비스 (Facade 패턴)
"""
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any

import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import firestore

from app.models.extractor import BaseExtractor, YoutubeExtractor, ArticleExtractor
from app.models.media import get_media_credibility
from app.config import config
from app.prompts import (
    get_first_analysis_prompt,
    get_stance_analysis_prompt,
    get_article_search_prompt,
)

# Gemini 모델 로드
gemini = None
try:
    vertexai.init(project=config.GCP_PROJECT, location=config.GCP_REGION)
    gemini = GenerativeModel(config.GEMINI_MODEL_ANALYSIS)
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

    def _analyze_with_gemini(self, content: str) -> Dict[str, Any]:
        """1차 분석: 핵심 주장 추출"""
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        # 컨텍스트 길이 조절
        truncated_content = content[:config.MAX_CONTENT_LENGTH_FIRST_ANALYSIS]
        prompt = get_first_analysis_prompt(truncated_content)

        try:
            response = gemini.generate_content(prompt)
            return self._parse_json_response(response.text)
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

    def _search_real_articles(self, keywords: List[str]) -> List[Dict[str, Any]]:
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
                config.GEMINI_MODEL_SEARCH, tools=[search_tool]
            )

            # 검색 쿼리 실행
            search_prompt = get_article_search_prompt(query)
            response = search_model.generate_content(search_prompt)

            # JSON 파싱
            search_data = self._parse_json_response(response.text)
            articles = self._process_search_results(
                search_data.get('articles', [])
            )

            print(f"✅ {len(articles)}개 기사 검색 완료")
            return articles

        except Exception as e:
            print(f"⚠️ 기사 검색 실패: {e}")
            return []  # 빈 배열 반환 (샘플 데이터 대신)

    def _process_search_results(
        self, raw_articles: List[Dict]
    ) -> List[Dict[str, Any]]:
        """검색 결과를 처리하고 신뢰도 정보 추가"""
        articles = []
        max_articles = config.MAX_ARTICLES_PER_SEARCH

        for result in raw_articles[:max_articles]:
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

        return articles

    def _find_related_articles_with_gemini(
        self, original_content: str, claims: List[str], articles: List[Dict]
    ) -> Dict[str, Any]:
        """입장 기반 분석 - 국내/국제 이슈 모두 적용 가능"""
        if not gemini:
            raise Exception("Gemini API를 사용할 수 없습니다.")

        # 컨텍스트 길이 조절
        truncated_content = original_content[:config.MAX_CONTENT_LENGTH_SECOND_ANALYSIS]
        articles_text = self._format_articles_for_ai(
            articles[:config.MAX_ARTICLES_FOR_AI_ANALYSIS]
        )

        # 프롬프트 생성
        prompt = get_stance_analysis_prompt(truncated_content, claims, articles_text)

        try:
            response = gemini.generate_content(prompt)
            parsed_result = self._parse_json_response(response.text)

            # 유효성 검증
            self._validate_stance_analysis_result(parsed_result)

            # 결과를 사용자 친화적으로 재구조화
            return self._restructure_by_stance(parsed_result, articles)

        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            raise Exception(f"AI 응답을 파싱할 수 없습니다. 다시 시도해주세요.")
        except Exception as e:
            print(f"❌ AI 2차 분석 실패: {e}")
            raise Exception(f"입장 분석 중 오류가 발생했습니다: {e}")

    def _restructure_by_stance(
        self, analysis_result: Dict, articles: List[Dict]
    ) -> Dict[str, Any]:
        """AI 분석 결과를 입장별로 그룹화 (국내/국제 구분 없음)"""
        restructured = []

        for claim_result in analysis_result.get('results', []):
            grouped_articles = self._group_articles_by_stance(
                claim_result.get('article_analyses', []), articles
            )

            restructured.append({
                'claim': claim_result.get('claim'),
                'supporting_evidence': self._create_evidence_section(
                    grouped_articles['supporting'],
                    claim_result.get('stance_summary', {}).get(
                        'common_supporting_arguments', []
                    ),
                ),
                'opposing_evidence': self._create_evidence_section(
                    grouped_articles['opposing'],
                    claim_result.get('stance_summary', {}).get(
                        'common_opposing_arguments', []
                    ),
                ),
                'neutral_coverage': {
                    'count': len(grouped_articles['neutral']),
                    'articles': grouped_articles['neutral'],
                },
                'diversity_metrics': self._calculate_diversity_metrics(
                    grouped_articles
                ),
            })

        return {'results': restructured}

    def _group_articles_by_stance(
        self, article_analyses: List[Dict], articles: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """기사들을 입장별로 분류하고 확신도 순으로 정렬"""
        grouped = {'supporting': [], 'opposing': [], 'neutral': []}

        for analysis in article_analyses:
            article_idx = analysis.get('article_index') - 1
            if article_idx < 0 or article_idx >= len(articles):
                continue

            article = articles[article_idx].copy()
            article['analysis'] = {
                'stance': analysis.get('stance'),
                'confidence': analysis.get('confidence'),
                'key_evidence': analysis.get('key_evidence', []),
                'framing': analysis.get('framing', ''),
            }

            stance = analysis.get('stance')
            if stance in grouped:
                grouped[stance].append(article)

        # 확신도 순으로 정렬
        for stance_list in grouped.values():
            self._sort_by_confidence(stance_list)

        return grouped

    def _create_evidence_section(
        self, articles: List[Dict], common_arguments: List[str]
    ) -> Dict[str, Any]:
        """입장별 증거 섹션 생성"""
        return {
            'count': len(articles),
            'articles': articles,
            'common_arguments': common_arguments,
        }

    def _calculate_diversity_metrics(
        self, grouped_articles: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """다양성 지표 계산"""
        total = sum(len(articles) for articles in grouped_articles.values())
        return {
            'total_sources': total,
            'stance_distribution': {
                stance: len(articles)
                for stance, articles in grouped_articles.items()
            },
        }

    # --- 공통 헬퍼 함수 ---
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """AI 응답에서 JSON 파싱"""
        cleaned_text = (
            response_text.strip()
            .replace('```json', '')
            .replace('```', '')
            .strip()
        )
        return json.loads(cleaned_text)

    def _format_articles_for_ai(self, articles: List[Dict]) -> str:
        """기사 목록을 AI가 읽을 수 있는 텍스트로 변환"""
        return "\n\n".join(
            [
                f"[기사 {i+1}]\n"
                f"제목: {article.get('title', '')}\n"
                f"출처: {article.get('source', '')}\n"
                f"내용: {article.get('snippet', '')}"
                for i, article in enumerate(articles)
            ]
        )

    def _validate_stance_analysis_result(self, result: Dict) -> None:
        """입장 분석 결과 유효성 검증"""
        if 'results' not in result:
            raise ValueError("AI 응답에 'results' 키가 없습니다.")

        if not isinstance(result['results'], list):
            raise ValueError("AI 응답의 'results'가 배열이 아닙니다.")

    def _sort_by_confidence(self, articles: List[Dict]) -> None:
        """기사 목록을 확신도 순으로 정렬 (in-place)"""
        articles.sort(
            key=lambda x: x.get('analysis', {}).get('confidence', 0),
            reverse=True,
        )

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
