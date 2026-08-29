from fastapi import Depends

from api.auth import require_api_key
from api.config import app
from api.detector.catalog import load_catalog
from api.generation.prompt.rules import load_rules
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


@app.get("/config/models", dependencies=[Depends(require_api_key)])
def get_models_config() -> dict:
    return load_catalog()


@app.get("/config/rules", dependencies=[Depends(require_api_key)])
def get_rules_config() -> dict:
    return load_rules()
