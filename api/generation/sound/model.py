from enum import Enum

from pydantic import BaseModel, Field


class SoundVariant(str, Enum):
    """Which chatterbox class to load — a code-level choice (each variant is its
    own Python class with its own from_pretrained), not a swappable HF repo id the
    way video/image models are."""

    BASE = "base"
    TURBO = "turbo"
    MULTILINGUAL = "multilingual"


class SoundGenerationParams(BaseModel):
    exaggeration: float = Field(default=0.5, ge=0, description="Emotional intensity/exaggeration of the delivery")
    cfg_weight: float = Field(
        default=0.5, ge=0, description="Classifier-free guidance weight; controls pacing/adherence to the reference voice"
    )
    temperature: float = Field(
        default=0.8, ge=0, description="Sampling temperature; higher is more varied/expressive, lower is more monotone/stable"
    )
