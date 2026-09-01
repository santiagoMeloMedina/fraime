from dataclasses import dataclass
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from api.generation.image.model import ImageGenerationParams
from api.generation.media_type import MediaType
from api.generation.model import GenerationParams, Reference
from api.generation.sound.model import SoundGenerationParams, SoundVariant


class GenerateRequestBase(BaseModel):
    model: str | None = None
    references: list[Reference] | None = None
    vram_safety_margin: bool = True
    cpu_offload: bool = True


class GenerateVideoRequest(GenerateRequestBase):
    media_type: Literal[MediaType.VIDEO]
    video_type: str
    fields: dict
    params: GenerationParams
    low_memory_decode: bool = True


class GenerateImageRequest(GenerateRequestBase):
    media_type: Literal[MediaType.IMAGE]
    fields: dict
    params: ImageGenerationParams


class GenerateSoundRequest(BaseModel):
    # Doesn't inherit GenerateRequestBase: chatterbox variants are fixed Python
    # classes (no arbitrary HF repo pin the way DiffusionPipeline.from_pretrained
    # allows) and have no cpu_offload-style API, so `model`/`cpu_offload` don't
    # apply here the way they do for video/image. `references` becomes a single
    # `voice` instead, since chatterbox clones from exactly one reference clip.
    media_type: Literal[MediaType.SOUND]
    text: str = Field(description="The text to speak")
    variant: SoundVariant | None = Field(
        default=None,
        description="Explicit variant to use; omit to auto-select by hardware and, if language requires it, multilingual capability",
    )
    language: str | None = Field(
        default=None,
        description="ISO language code (e.g. 'es', 'fr', 'ja'); only honored when the resolved variant is multilingual",
    )
    voice: Reference | None = Field(
        default=None,
        description="Reference audio clip URL to clone the voice from (5-20s of clean, single-speaker audio); omit for the model's default voice",
    )
    params: SoundGenerationParams
    vram_safety_margin: bool = Field(
        default=True, description="Match against 85% of detected VRAM instead of 100%, for headroom"
    )


GenerateRequest = Annotated[
    Union[GenerateVideoRequest, GenerateImageRequest, GenerateSoundRequest],
    Field(discriminator="media_type"),
]


@dataclass
class GenerateVideoResult:
    video_path: str | None
    model: str
    s3_bucket: str | None = None
    s3_key: str | None = None
    s3_url: str | None = None


@dataclass
class GenerateImageResult:
    image_path: str | None
    model: str
    s3_bucket: str | None = None
    s3_key: str | None = None
    s3_url: str | None = None


@dataclass
class GenerateSoundResult:
    sound_path: str | None
    model: str
    s3_bucket: str | None = None
    s3_key: str | None = None
    s3_url: str | None = None
