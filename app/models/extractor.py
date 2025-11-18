"""
Content extractors for different media types
"""
from abc import ABC, abstractmethod
import os
import uuid
import tempfile
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
from google.cloud import storage

from app.config import config


class BaseExtractor(ABC):
    """콘텐츠 추출기 기본 클래스"""

    @abstractmethod
    def extract(self, url: str) -> str:
        """URL에서 텍스트 콘텐츠를 추출합니다."""
        pass


class YoutubeExtractor(BaseExtractor):
    """유튜브 자막 추출 전략 (3단계 하이브리드 방식)"""

    def __init__(self):
        """GCS, Gemini, YouTube Video Service 초기화"""
        # GCS 및 Gemini 모델 초기화 (yt-dlp 방식용)
        self.storage_client = None
        self.bucket = None
        self.gemini_model = None

        if config.GCS_BUCKET_NAME:
            try:
                self.storage_client = storage.Client(project=config.GCP_PROJECT)
                self.bucket = self.storage_client.bucket(config.GCS_BUCKET_NAME)

                # Gemini 2.0 모델 초기화
                vertexai.init(project=config.GCP_PROJECT, location=config.GCP_REGION)
                self.gemini_model = GenerativeModel('gemini-2.0-flash-exp')
                print("✅ (YoutubeExtractor) GCS 및 Gemini 연결 성공")
            except Exception as e:
                print(f"⚠️ (YoutubeExtractor) GCS/Gemini 초기화 실패: {e}")

        # Direct URL Processing 서비스 초기화 (폴백용)
        self.video_service = None
        try:
            from app.utils.youtube_video_service import YouTubeVideoService
            self.video_service = YouTubeVideoService()
            print("✅ (YoutubeExtractor) YouTube Video Service 연결 성공")
        except Exception as e:
            print(f"⚠️ (YoutubeExtractor) YouTube Video Service 초기화 실패: {e}")

    def extract(self, url: str) -> str:
        """3단계 하이브리드 방식: 자막 → yt-dlp+GCS → Direct URL Processing"""

        errors = []

        # 1단계: 자막 추출 시도 (가장 빠름)
        try:
            print("📝 [1/3] 자막 추출 시도 중...")
            transcript_text = self._extract_transcript(url)
            print(f"✅ 자막 추출 성공: {len(transcript_text)} 글자")
            return transcript_text
        except Exception as transcript_error:
            error_msg = f"자막 추출 실패: {transcript_error}"
            print(f"⚠️ {error_msg}")
            errors.append(error_msg)

        # 2단계: yt-dlp + GCS 방식 시도 (이전 작동 방식)
        if self.gemini_model and self.bucket:
            try:
                print("🎬 [2/3] yt-dlp + GCS 방식 시도 중...")
                video_analysis = self._analyze_video_with_ytdlp_gcs(url)
                print(f"✅ yt-dlp 분석 성공: {len(video_analysis)} 글자")
                return video_analysis
            except Exception as ytdlp_error:
                error_msg = f"yt-dlp 방식 실패: {ytdlp_error}"
                print(f"⚠️ {error_msg}")
                errors.append(error_msg)

        # 3단계: Direct URL Processing 시도 (최후 수단)
        if self.video_service:
            try:
                print("🌐 [3/3] Direct URL Processing 시도 중...")
                result = self.video_service.analyze_video(url, analysis_type="transcript")

                transcript = result.get('transcript', '')
                if transcript:
                    print(f"✅ Direct URL 분석 성공: {len(transcript)} 글자")
                    return transcript
                else:
                    raise Exception("영상 분석 결과에 transcript가 없습니다")

            except Exception as direct_error:
                error_msg = f"Direct URL 방식 실패: {direct_error}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)

        # 모든 방법 실패
        raise Exception(
            f"모든 영상 분석 방법이 실패했습니다:\n" + "\n".join(f"- {e}" for e in errors)
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

    def _analyze_video_with_ytdlp_gcs(self, url: str) -> str:
        """yt-dlp + GCS 방식으로 영상 분석 (이전 작동 방식)"""
        local_video_path = None
        gcs_blob_name = None

        try:
            # 1. 영상 다운로드 (progressive=True로 병합된 스트림만 선택)
            temp_dir = tempfile.gettempdir()
            unique_filename = f"{uuid.uuid4()}.mp4"
            local_video_path = os.path.join(temp_dir, unique_filename)

            ydl_opts = {
                'format': 'bestvideo[ext=mp4][progressive=True][height<=720]/best[ext=mp4][progressive=True]/best[ext=mp4]',
                'outtmpl': local_video_path,
                'quiet': False,  # 디버깅용
            }

            print(f"📥 yt-dlp로 영상 다운로드 중...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if not os.path.exists(local_video_path):
                raise Exception("yt-dlp 다운로드 실패 (파일이 생성되지 않음)")

            print(f"✅ 다운로드 완료: {local_video_path}")

            # 2. GCS 업로드
            gcs_blob_name = f"video-analysis/{unique_filename}"
            blob = self.bucket.blob(gcs_blob_name)

            print(f"☁️ GCS 업로드 중...")
            blob.upload_from_filename(local_video_path)
            gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{gcs_blob_name}"
            print(f"✅ GCS 업로드 완료: {gcs_uri}")

            # 3. Gemini API 호출
            print(f"🤖 Gemini로 영상 분석 중...")
            video_part = Part.from_uri(uri=gcs_uri, mime_type="video/mp4")

            prompt = """
            이 영상의 내용을 상세히 분석하여 텍스트로 변환해주세요.

            다음 정보를 포함해주세요:
            1. 영상의 주요 주제와 핵심 메시지
            2. 언급된 구체적인 사실, 통계, 주장
            3. 화자의 주요 논점과 근거
            4. 중요한 맥락이나 배경 정보

            가능한 한 상세하고 정확하게 작성해주세요.
            """

            response = self.gemini_model.generate_content([prompt, video_part])
            return response.text

        finally:
            # 4. 정리 (로컬 파일 및 GCS 파일 삭제)
            try:
                if local_video_path and os.path.exists(local_video_path):
                    os.remove(local_video_path)
                    print(f"🗑️ 로컬 파일 삭제 완료")

                if gcs_blob_name and self.bucket:
                    blob = self.bucket.blob(gcs_blob_name)
                    if blob.exists():
                        blob.delete()
                        print(f"🗑️ GCS 파일 삭제 완료")
            except Exception as cleanup_error:
                print(f"⚠️ 정리 작업 실패: {cleanup_error}")


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
