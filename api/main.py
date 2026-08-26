from api.config import app
from api.service import GenerateVideoRequest, generate_video

__all__ = ["app"]


@app.post("/generate")
def generate(request: GenerateVideoRequest) -> dict:
    video_path = generate_video(request)
    return {"video_path": video_path}
