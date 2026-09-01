from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from diffusers.utils import export_to_video

from api.config import environment
from api.detector import select_best_model
from api.generation.create import GenerationHandler
from api.generation.image.create import ImageGeneratorHandler
from api.generation.media_type import MediaType
from api.model import (
    GenerateImageRequest,
    GenerateImageResult,
    GenerateRequest,
    GenerateVideoRequest,
    GenerateVideoResult,
)
from api.utils.aws.s3 import generate_presigned_url, probe_write_access, upload_file


def generate_media(request: GenerateRequest) -> GenerateVideoResult | GenerateImageResult:
    if request.media_type == MediaType.IMAGE:
        return generate_image(request)
    return generate_video(request)


@dataclass
class _StoredOutput:
    local_path: str | None
    s3_bucket: str | None
    s3_key: str | None
    s3_url: str | None


def _reserve_output_path(extension: str) -> tuple[Path, str | None, str | None]:
    """Picks a local output path and, if S3 output is configured, probes write
    access to the destination key upfront so a permissions problem fails fast
    instead of after several minutes of generation."""
    name = f"{uuid4()}{extension}"
    output_dir = Path(environment.generation.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / name

    s3_bucket = environment.cloud.s3_output_bucket
    s3_key = None
    if s3_bucket:
        prefix = environment.cloud.s3_output_prefix
        s3_key = f"{prefix.strip('/')}/.{name}" if prefix else f".{name}"
        probe_write_access(s3_bucket, s3_key)

    return output_path, s3_bucket, s3_key


def _store_output(local_path: str, s3_bucket: str | None, s3_key: str | None) -> _StoredOutput:
    """Uploads the generated file to S3 and removes the local copy when S3 output is
    configured; otherwise keeps it on the local filesystem."""
    if s3_bucket:
        upload_file(s3_bucket, s3_key, local_path)
        s3_url = generate_presigned_url(s3_bucket, s3_key)
        Path(local_path).unlink(missing_ok=True)
        return _StoredOutput(local_path=None, s3_bucket=s3_bucket, s3_key=s3_key, s3_url=s3_url)

    return _StoredOutput(local_path=local_path, s3_bucket=None, s3_key=None, s3_url=None)


def generate_video(request: GenerateVideoRequest) -> GenerateVideoResult:
    output_path, s3_bucket, s3_key = _reserve_output_path(".mp4")

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
    local_path = export_to_video(frames, str(output_path), fps=request.params.fps)

    stored = _store_output(local_path, s3_bucket, s3_key)
    return GenerateVideoResult(
        video_path=stored.local_path,
        model=model,
        s3_bucket=stored.s3_bucket,
        s3_key=stored.s3_key,
        s3_url=stored.s3_url,
    )


def generate_image(request: GenerateImageRequest) -> GenerateImageResult:
    output_path, s3_bucket, s3_key = _reserve_output_path(".png")

    model = request.model
    if model is None:
        capabilities = ["image-to-image"] if request.references else None
        model = select_best_model(
            media_type=MediaType.IMAGE,
            capabilities=capabilities,
            safety_margin=request.vram_safety_margin,
        ).model_id

    handler = ImageGeneratorHandler(model, cpu_offload=request.cpu_offload)
    image = handler.generate(request.fields, request.params, request.references)
    image.save(output_path)

    stored = _store_output(str(output_path), s3_bucket, s3_key)
    return GenerateImageResult(
        image_path=stored.local_path,
        model=model,
        s3_bucket=stored.s3_bucket,
        s3_key=stored.s3_key,
        s3_url=stored.s3_url,
    )
