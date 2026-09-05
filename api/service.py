from api.utils.quiet import suppress_library_noise

suppress_library_noise()

import gc
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import torch
from diffusers.utils import export_to_video

from api.config import environment
from api.detector import NoModelFitsError, select_best_model
from api.detector.catalog import load_catalog
from api.generation.create import GenerationHandler
from api.generation.image.create import ImageGeneratorHandler
from api.generation.media_type import MediaType
from api.generation.voice.create import VoiceGeneratorHandler
from api.generation.voice.model import VoiceVariant
from api.model import (
    GenerateImageRequest,
    GenerateImageResult,
    GenerateRequest,
    GenerateVideoRequest,
    GenerateVideoResult,
    GenerateVoiceRequest,
    GenerateVoiceResult,
)
from api.utils.aws.s3 import generate_presigned_url, probe_write_access, upload_file
from api.utils.log import log_event


def generate_media(
    request: GenerateRequest,
) -> GenerateVideoResult | GenerateImageResult | GenerateVoiceResult:
    if request.media_type == MediaType.IMAGE:
        return generate_image(request)
    if request.media_type == MediaType.VOICE:
        return generate_voice(request)
    return generate_video(request)


def _release_accelerator_memory() -> None:
    """Drops any cached-but-now-unreferenced pipeline before the next one loads.
    Without this, a model switch can transiently hold two pipelines' weights at
    once — the previous one hasn't actually freed VRAM yet when the next
    from_pretrained call starts allocating."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    elif torch.backends.mps.is_available():
        torch.mps.empty_cache()


# Each holds at most one loaded pipeline — matches this process being pinned to a
# single GPU-resident model at a time (see api/Dockerfile). Keyed on whatever the
# handler's constructor args are, since those (not just the model id) determine
# what's actually resident.
_cached_image_key: tuple[str, bool] | None = None
_cached_image_handler: ImageGeneratorHandler | None = None

_cached_video_key: tuple[str, bool, bool] | None = None
_cached_video_handler: GenerationHandler | None = None

_cached_voice_key: tuple[str, VoiceVariant] | None = None
_cached_voice_handler: VoiceGeneratorHandler | None = None


def _get_image_handler(model: str, cpu_offload: bool) -> ImageGeneratorHandler:
    global _cached_image_key, _cached_image_handler
    key = (model, cpu_offload)
    if key != _cached_image_key:
        _cached_image_handler = None
        _release_accelerator_memory()
        log_event(f"started download of model {model}")
        _cached_image_handler = ImageGeneratorHandler(model, cpu_offload=cpu_offload)
        _cached_image_key = key
    return _cached_image_handler


def _get_video_handler(model: str, low_memory_decode: bool, cpu_offload: bool) -> GenerationHandler:
    global _cached_video_key, _cached_video_handler
    key = (model, low_memory_decode, cpu_offload)
    if key != _cached_video_key:
        _cached_video_handler = None
        _release_accelerator_memory()
        log_event(f"started download of model {model}")
        _cached_video_handler = GenerationHandler(
            model, low_memory_decode=low_memory_decode, cpu_offload=cpu_offload
        )
        _cached_video_key = key
    return _cached_video_handler


def _get_voice_handler(variant: VoiceVariant, model_id: str) -> VoiceGeneratorHandler:
    global _cached_voice_key, _cached_voice_handler
    key = (model_id, variant)
    if key != _cached_voice_key:
        _cached_voice_handler = None
        _release_accelerator_memory()
        log_event(f"started download of model {model_id}")
        _cached_voice_handler = VoiceGeneratorHandler(variant=variant, model_id=model_id)
        _cached_voice_key = key
    return _cached_voice_handler


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

    log_event(f"started video generation with model={model} params={request.params.model_dump()}")
    handler = _get_video_handler(
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

    log_event(f"started image generation with model={model} params={request.params.model_dump()}")
    handler = _get_image_handler(model, cpu_offload=request.cpu_offload)
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


def _resolve_pinned_voice_variant(variant: VoiceVariant) -> str:
    """Chatterbox variants are fixed classes, not arbitrary HF repo pins, so an
    explicit `variant` resolves through the catalog to its documented model id
    rather than being passed to a loader directly."""
    catalog = load_catalog()
    for candidate in catalog["models"].values():
        if candidate.get("media_type") == MediaType.VOICE.value and candidate.get("variant") == variant.value:
            return candidate["id"]
    raise NoModelFitsError(f"No voice catalog model has variant={variant.value!r}")


def generate_voice(request: GenerateVoiceRequest) -> GenerateVoiceResult:
    import soundfile

    output_path, s3_bucket, s3_key = _reserve_output_path(".wav")

    if request.variant is not None:
        variant = request.variant
        model = _resolve_pinned_voice_variant(variant)
    else:
        capabilities = ["multilingual"] if request.language and request.language.lower() != "en" else None
        match = select_best_model(
            media_type=MediaType.VOICE,
            capabilities=capabilities,
            safety_margin=request.vram_safety_margin,
        )
        variant = VoiceVariant(match.variant)
        model = match.model_id

    log_event(
        f"started voice generation with model={model} variant={variant.value} params={request.params.model_dump()}"
    )
    handler = _get_voice_handler(variant=variant, model_id=model)
    wav, sample_rate = handler.generate(request.text, request.params, request.language, request.voice)
    wav_array = wav.numpy()
    if wav_array.ndim == 2:
        wav_array = wav_array.T
    soundfile.write(str(output_path), wav_array, sample_rate)

    stored = _store_output(str(output_path), s3_bucket, s3_key)
    return GenerateVoiceResult(
        voice_path=stored.local_path,
        model=model,
        s3_bucket=stored.s3_bucket,
        s3_key=stored.s3_key,
        s3_url=stored.s3_url,
    )
