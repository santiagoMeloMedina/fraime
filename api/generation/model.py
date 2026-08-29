from abc import ABC

from pydantic import BaseModel, Field, HttpUrl


class GenerationParams(BaseModel):
    duration_s: float = Field(gt=0, description="Requested clip duration in seconds")
    fps: int = Field(gt=0, description="Frames per second")
    resolution: str = Field(description="Target resolution, e.g. '1024x576'")
    seed: int | None = Field(default=None, description="Seed for reproducible generation")
    num_inference_steps: int | None = Field(
        default=None,
        gt=0,
        description="Denoising steps; lower is faster/lower quality. Defaults to the pipeline's own default (usually 50) when unset.",
    )


class Reference(BaseModel, ABC):
    url: HttpUrl = Field(description="Publicly accessible URL the file is downloaded from")
