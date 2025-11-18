"""
Content extractors for different media types
"""
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

from app.config import config


class BaseExtractor(ABC):
    """콘텐츠 추출기 기본 클래스"""

    @abstractmethod
    def extract(self, url: str) -> str:
        """URL에서 텍스트 콘텐츠를 추출합니다."""
        pass


class YoutubeExtractor(BaseExtractor):
    """유튜브 자막 추출 전략 (자막 우선, 실패 시 Direct URL Processing)"""

    def __init__(self):
        """YouTube Video Service 초기화"""
        self.video_service = None

        try:
            from app.utils.youtube_video_service import YouTubeVideoService
            self.video_service = YouTubeVideoService()
            print("✅ (YoutubeExtractor) YouTube Video Service 연결 성공")
        except Exception as e:
            print(f"⚠️ (YoutubeExtractor) YouTube Video Service 초기화 실패: {e}")

    def extract(self, url: str) -> str:
        """하이브리드 방식: 자막 우선, 실패 시 Direct URL Processing"""

        # 1단계: 자막 추출 시도
        try:
            print("📝 자막 추출 시도 중...")
            transcript_text = self._extract_transcript(url)
            print(f"✅ 자막 추출 성공: {len(transcript_text)} 글자")
            return transcript_text
        except Exception as transcript_error:
            print(f"⚠️ 자막 추출 실패: {transcript_error}")

            # 2단계: Direct URL Processing으로 영상 분석 (다운로드 불필요)
            if self.video_service:
                print("🎬 Direct URL Processing으로 영상 분석 시도 중...")
                try:
                    result = self.video_service.analyze_video(url, analysis_type="transcript")

                    # transcript 텍스트 추출
                    transcript = result.get('transcript', '')
                    if transcript:
                        print(f"✅ 영상 분석 성공: {len(transcript)} 글자")
                        return transcript
                    else:
                        raise Exception("영상 분석 결과에 transcript가 없습니다")

                except Exception as video_error:
                    print(f"❌ 영상 분석 실패: {video_error}")
                    raise Exception(
                        f"자막 추출과 영상 분석 모두 실패했습니다.\n"
                        f"자막 오류: {transcript_error}\n"
                        f"영상 분석 오류: {video_error}"
                    )
            else:
                raise Exception(
                    f"자막을 가져올 수 없으며, YouTube Video Service를 사용할 수 없습니다.\n"
                    f"자막 오류: {transcript_error}"
                )

    def _extract_transcript(self, url: str) -> str:
        """유튜브 자막 추출 (기존 로직)"""
        if 'v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
        else:
            raise ValueError("유효하지 않은 유튜브 URL")

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        try:
            # 1. 한국어 자막 시도
            transcript = transcript_list.find_transcript(['ko'])
        except:
            # 2. 영어 자막 시도
            transcript = transcript_list.find_transcript(['en'])

        text = ' '.join([item['text'] for item in transcript.fetch()])
        return text


class ArticleExtractor(BaseExtractor):
    """기사 본문 추출 전략"""

    def extract(self, url: str) -> str:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 불필요한 태그 제거
            for tag in soup(
                ['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']
            ):
                tag.decompose()

            # 기사 본문 유력 태그 탐색
            article = (
                soup.find('article')
                or soup.find('main')
                or soup.find(id='content')
                or soup.find(class_='content')
                or soup.body
            )

            if article:
                text = article.get_text(separator=' ', strip=True)
                # 지나치게 긴 공백 제거
                text = ' '.join(text.split())
                return text
            else:
                return ""

        except requests.RequestException as e:
            print(f"⚠️ 기사 요청 실패: {e}")
            raise Exception(f"기사 내용을 가져오는 데 실패했습니다. URL을 확인해주세요.")
        except Exception as e:
            print(f"⚠️ 기사 처리 실패: {e}")
            raise Exception(f"기사 내용을 처리하는 중 오류가 발생했습니다.")
