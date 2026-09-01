from pydantic import BaseModel, Field


class ImageGenerationParams(BaseModel):
    width: int = Field(gt=0, description="Target image width in pixels")
    height: int = Field(gt=0, description="Target image height in pixels")
    seed: int | None = Field(default=None, description="Seed for reproducible generation")
    num_inference_steps: int | None = Field(
        default=None,
        gt=0,
        description="Denoising steps; lower is faster/lower quality. Defaults to the pipeline's own default when unset.",
    )
    guidance_scale: float | None = Field(
        default=None,
        ge=0,
        description="Classifier-free guidance scale; defaults to the pipeline's own default when unset.",
    )
