"""
Content extractors for different media types
"""
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi


class BaseExtractor(ABC):
    """콘텐츠 추출기 기본 클래스"""

    @abstractmethod
    def extract(self, url: str) -> str:
        """URL에서 텍스트 콘텐츠를 추출합니다."""
        pass


class YoutubeExtractor(BaseExtractor):
    """유튜브 자막 추출 전략"""

    def extract(self, url: str) -> str:
        try:
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

        except Exception as e:
            print(f"⚠️ 유튜브 자막 추출 실패: {e}")
            raise Exception(
                f"자막을 가져올 수 없습니다. 자동 생성된 자막이 없거나 지원하지 않는 영상일 수 있습니다."
            )


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
