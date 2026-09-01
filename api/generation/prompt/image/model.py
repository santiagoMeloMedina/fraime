from pydantic import BaseModel, ConfigDict, Field


class ImagePromptComponents(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    subject: str = Field(description="Main focus of the image: who/what")
    scene: str = Field(description="Environment, background, setting, time of day")
    camera: str = Field(description="Shot type, angle, and framing")
    lighting: str = Field(description="Lighting style, direction, and mood")
    style: str = Field(description="Visual/artistic style or medium reference")
    action: str | None = Field(
        default=None, description="Pose or what the subject is doing, if not purely static"
    )
    color_palette: str | None = Field(
        default=None, description="Dominant tones or color scheme"
    )
    negative_prompt: str | None = Field(default=None, description="What to avoid in the generation")
