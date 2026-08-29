from fastapi import Depends

from api.auth import require_api_key
from api.config import app
from api.service import GenerateVideoRequest, generate_video

__all__ = ["app"]


@app.post("/generate", dependencies=[Depends(require_api_key)])
def generate(request: GenerateVideoRequest) -> dict:
    video_path, model = generate_video(request)
    return {"video_path": video_path, "model": model}
