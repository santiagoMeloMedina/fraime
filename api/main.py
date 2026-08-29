from fastapi import Depends

from api.auth import require_api_key
from api.config import app
from api.service import GenerateVideoRequest, generate_video

__all__ = ["app"]


@app.post("/generate", dependencies=[Depends(require_api_key)])
def generate(request: GenerateVideoRequest) -> dict:
    result = generate_video(request)
    return {
        "video_path": result.video_path,
        "model": result.model,
        "s3_bucket": result.s3_bucket,
        "s3_key": result.s3_key,
        "s3_url": result.s3_url,
    }
