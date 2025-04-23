import logging

from fastapi import HTTPException
from pytubefix import YouTube
from pytubefix.cli import on_progress

logger = logging.getLogger(__name__)


class DwmYoutube:
    """A class to handle YouTube video and audio downloads."""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(DwmYoutube, cls).__new__(cls)
        return cls._instance

    def __init__(self, url: str):
        if not url:
            raise HTTPException(status_code=400, detail="URL cannot be empty.")
        if not url.startswith("https://www.youtube.com/watch?v="):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL.")
        self.url = url
        self.video = None
        self._initialize_video()

    def _initialize_video(self):
        try:
            self.video = YouTube(self.url, on_progress_callback=on_progress)
            if not self.video:
                raise HTTPException(status_code=404, detail="Video not found.")
        except Exception as e:
            logger.error(f"Error initializing video: {e}")
            raise HTTPException(
                status_code=500, detail="Error initializing video."
            ) from e

    def _get_video_metadata(self) -> dict:
        """Retrieve metadata of the video."""
        return {
            "title": self.video.title,
            "thumbnail": self.video.thumbnail_url,
            "description": self.video.description,
            "channel_url": self.video.channel_url,
            "duration": self.video.length,
            "views": self.video.views,
            "likes": self.video.likes,
        }

    def download_video(
        self, resolution: str = "highest", download_path: str = "videos_downloads"
    ) -> dict:
        """Download the video with the specified resolution."""
        try:
            logger.info(
                f"Downloading video from {self.url} at resolution {resolution}."
            )
            stream = (
                self.video.streams.get_highest_resolution()
                if resolution == "highest"
                else self.video.streams.filter(res=resolution, progressive=True).first()
            )

            if not stream:
                raise HTTPException(
                    status_code=400, detail="Requested resolution not available."
                )

            stream.download(output_path=download_path)
            return {
                "success": True,
                "message": f"Downloaded video '{self.video.title}' successfully.",
                "video_data": self._get_video_metadata(),
            }
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise HTTPException(
                status_code=500, detail="Error downloading video."
            ) from e

    def download_audio(self, download_path: str = "audio_downloads") -> dict:
        """Download the audio of the video.

        Args:
            download_path (str, optional): Directory path where the audio will be saved. Defaults to "audio_downloads".

        Raises:
            HTTPException: If the audio stream is not available.
            HTTPException: If an error occurs during the download process.

        Returns:
            dict: A dictionary containing the success status, a message, and video metadata.
        """
        try:
            logger.info(f"Downloading audio from {self.url}.")
            audio_stream = self.video.streams.filter(only_audio=True).first()

            if not audio_stream:
                raise HTTPException(
                    status_code=400, detail="Audio stream not available."
                )

            audio_stream.download(output_path=download_path)
            return {
                "success": True,
                "message": f"Downloaded audio '{self.video.title}' successfully.",
                "video_data": self._get_video_metadata(),
            }
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            raise HTTPException(
                status_code=500, detail="Error downloading audio."
            ) from e
