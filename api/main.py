from fastapi import Depends

from api.auth import require_api_key
from api.config import app
from api.detector.catalog import load_catalog
from api.generation.prompt.rules import load_rules
from api.model import GenerateImageResult, GenerateRequest, GenerateVoiceResult
from api.service import generate_media

__all__ = ["app"]


@app.post("/generate", dependencies=[Depends(require_api_key)])
def generate(request: GenerateRequest) -> dict:
    result = generate_media(request)
    if isinstance(result, GenerateImageResult):
        return {
            "image_path": result.image_path,
            "model": result.model,
            "s3_bucket": result.s3_bucket,
            "s3_key": result.s3_key,
            "s3_url": result.s3_url,
        }
    if isinstance(result, GenerateVoiceResult):
        return {
            "voice_path": result.voice_path,
            "model": result.model,
            "s3_bucket": result.s3_bucket,
            "s3_key": result.s3_key,
            "s3_url": result.s3_url,
        }
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
