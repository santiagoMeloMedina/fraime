from dataclasses import dataclass
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from api.generation.image.model import ImageGenerationParams
from api.generation.media_type import MediaType
from api.generation.model import GenerationParams, Reference


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


GenerateRequest = Annotated[
    Union[GenerateVideoRequest, GenerateImageRequest], Field(discriminator="media_type")
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
