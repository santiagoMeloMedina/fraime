from pydantic import BaseModel, Field


class GenerationParams(BaseModel):
    duration_s: float = Field(gt=0, description="Requested clip duration in seconds")
    fps: int = Field(gt=0, description="Frames per second")
    resolution: str = Field(description="Target resolution, e.g. '1024x576'")
    seed: int | None = Field(default=None, description="Seed for reproducible generation")
