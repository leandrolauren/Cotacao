import logging

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.core.auth import Auth
from backend.core.youtube import DwmYoutube
from backend.models import DownloadRequest

auth = Auth()

logger = logging.getLogger(__name__)

youtube_router = APIRouter()


@youtube_router.post("/download", tags=["Downloads"])
async def download_media(
    request: DownloadRequest,
    authorization: str = Header(..., alias="Authorization"),
) -> dict:
    """
    Endpoint for downloading media from a YouTube URL.

    Download video or audio as specified in the request body.
    The user can define the path where the file will be saved.

    Args:
        request (DownloadRequest): Object containing the download parameters:
            - url (str): YouTube URL.
            - download_type (str): Download type ('video' or 'audio').
            - download_path (str): Directory to save the file.
            - resolution (Optional[str]): Video resolution, if the type is 'video'.

    Returns:
        dict: Dictionary with download result data and media metadata.

    Raises:
        HTTPException: If the download_type is not recognized or an error occurs during the download.
    """
    if not auth.verify_token(authorization):
        logger.warning("Invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        yt = DwmYoutube(request.url)
        if request.download_type.lower() == "video":
            result = yt.download_video(
                resolution=request.resolution, download_path=request.download_path
            )
        elif request.download_type.lower() == "audio":
            result = yt.download_audio(download_path=request.download_path)
        else:
            raise HTTPException(
                status_code=400, detail="download_type must be 'video' or 'audio'."
            )
        return result
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))
