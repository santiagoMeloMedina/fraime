from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from diffusers.utils import export_to_video
from pydantic import BaseModel

from api.config import environment
from api.detector import select_best_model
from api.generation.create import GenerationHandler
from api.generation.model import GenerationParams, Reference
from api.storage.s3 import generate_presigned_url, probe_write_access, upload_file


class GenerateVideoRequest(BaseModel):
    model: str | None = None
    video_type: str
    fields: dict
    params: GenerationParams
    references: list[Reference] | None = None
    vram_safety_margin: bool = True
    low_memory_decode: bool = True
    cpu_offload: bool = True


@dataclass
class GenerateVideoResult:
    video_path: str | None
    model: str
    s3_bucket: str | None = None
    s3_key: str | None = None
    s3_url: str | None = None


def generate_video(request: GenerateVideoRequest) -> GenerateVideoResult:
    video_name = f"{uuid4()}.mp4"

    s3_bucket = environment.cloud.s3_output_bucket
    s3_key = None
    if s3_bucket:
        prefix = environment.cloud.s3_output_prefix
        s3_key = f"{prefix.strip('/')}/.{video_name}" if prefix else f".{video_name}"
        probe_write_access(s3_bucket, s3_key)

    model = request.model
    if model is None:
        capabilities = ["image-to-video"] if request.references else None
        model = select_best_model(
            video_type=request.video_type,
            capabilities=capabilities,
            safety_margin=request.vram_safety_margin,
        ).model_id

    handler = GenerationHandler(
        model, low_memory_decode=request.low_memory_decode, cpu_offload=request.cpu_offload
    )
    frames = handler.generate(
        request.video_type,
        request.fields,
        request.params,
        request.references,
    )

    output_dir = Path(environment.generation.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / video_name
    local_path = export_to_video(frames, str(output_path), fps=request.params.fps)

    if s3_bucket:
        upload_file(s3_bucket, s3_key, local_path)
        s3_url = generate_presigned_url(s3_bucket, s3_key)
        Path(local_path).unlink(missing_ok=True)
        return GenerateVideoResult(
            video_path=None, model=model, s3_bucket=s3_bucket, s3_key=s3_key, s3_url=s3_url
        )

    return GenerateVideoResult(video_path=local_path, model=model)
