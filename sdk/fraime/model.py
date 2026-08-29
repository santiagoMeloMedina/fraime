from abc import ABC
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class VideoType(str, Enum):
    PIXAR = "pixar"
    ACTION = "action"
    ANIMATION = "animation"
    ANIME = "anime"
    DOCUMENTARY = "documentary"
    FASHION = "fashion"
    UGC_PRODUCT_REVIEW = "ugc_product_review"
    COMMERCIAL_PRODUCT_AD = "commercial_product_ad"
    EXPLAINER_TESTIMONIAL = "explainer_testimonial"
    PRESENTER_AVATAR = "presenter_avatar"
    SOCIAL_SHORT_FORM_AD = "social_short_form_ad"
    MUSIC_VIDEO = "music_video"
    MOTION_GRAPHICS = "motion_graphics"


class AspectRatio(str, Enum):
    VERTICAL_9_16 = "9:16"
    VERTICAL_4_5 = "4:5"


class Reference(BaseModel):
    url: HttpUrl = Field(description="Publicly accessible URL the file is downloaded from")


class GenerationParams(BaseModel):
    duration_s: float = Field(gt=0, description="Requested clip duration in seconds")
    fps: int = Field(gt=0, description="Frames per second")
    resolution: str = Field(description="Target resolution, e.g. '1024x576'")
    seed: int | None = Field(default=None, description="Seed for reproducible generation")
    num_inference_steps: int | None = Field(
        default=None,
        gt=0,
        description="Denoising steps; lower is faster/lower quality. Defaults to the model's own default (usually 50) when unset.",
    )


class PromptFields(BaseModel, ABC):
    """Fields shared by every video type."""

    subject: str = Field(description="Main focus of the video: who/what")
    action: str = Field(description="What happens over time; the motion")
    scene: str = Field(description="Environment, background, time of day")
    camera: str = Field(description="Shot type and camera movement")
    lighting: str = Field(description="Lighting style and mood")
    style: str = Field(description="Visual/cinematic style reference")
    negative_prompt: str | None = Field(default=None, description="What to avoid in the generation")


class CinematicPromptFields(PromptFields):
    """pixar, action, animation, anime, documentary, fashion — no extra fields."""


class UGCPromptFields(PromptFields):
    """ugc_product_review, commercial_product_ad, explainer_testimonial."""

    dialogue: str | None = Field(
        default=None, description="Spoken script/dialogue delivered by the subject"
    )
    reference_image: str | None = Field(
        default=None, description="Reference image URL for product/subject fidelity"
    )


class PresenterPromptFields(UGCPromptFields):
    """presenter_avatar."""

    voice_tone: str | None = Field(
        default=None, description="Directive for how the voice should sound, e.g. 'warm, confident, corporate'"
    )


class SocialAdPromptFields(UGCPromptFields):
    """social_short_form_ad."""

    text_overlay: str | None = Field(default=None, description="On-screen text/captions overlaid on the video")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.VERTICAL_9_16, description="Target aspect ratio")


class MusicVideoPromptFields(PromptFields):
    """music_video. No catalog model currently supports this — expect no viable model today."""

    audio_reference: str = Field(description="Reference audio track/URL the visuals should sync to")
    tempo_bpm: int | None = Field(default=None, description="Beats per minute to sync visual cuts to")


class MotionGraphicsPromptFields(PromptFields):
    """motion_graphics."""

    text_content: str = Field(description="On-screen text/copy driving the animation")
    transitions: str | None = Field(
        default=None, description="Transition style between graphic elements, e.g. 'fade, slide, zoom'"
    )


PROMPT_FIELDS_BY_VIDEO_TYPE: dict[VideoType, type[PromptFields]] = {
    VideoType.PIXAR: CinematicPromptFields,
    VideoType.ACTION: CinematicPromptFields,
    VideoType.ANIMATION: CinematicPromptFields,
    VideoType.ANIME: CinematicPromptFields,
    VideoType.DOCUMENTARY: CinematicPromptFields,
    VideoType.FASHION: CinematicPromptFields,
    VideoType.UGC_PRODUCT_REVIEW: UGCPromptFields,
    VideoType.COMMERCIAL_PRODUCT_AD: UGCPromptFields,
    VideoType.EXPLAINER_TESTIMONIAL: UGCPromptFields,
    VideoType.PRESENTER_AVATAR: PresenterPromptFields,
    VideoType.SOCIAL_SHORT_FORM_AD: SocialAdPromptFields,
    VideoType.MUSIC_VIDEO: MusicVideoPromptFields,
    VideoType.MOTION_GRAPHICS: MotionGraphicsPromptFields,
}


class GenerateVideoRequest(BaseModel):
    video_type: VideoType
    fields: PromptFields
    params: GenerationParams
    model: str | None = Field(
        default=None, description="Explicit Hugging Face model id; omit to auto-select by hardware"
    )
    references: list[Reference] | None = Field(
        default=None, description="Reference images; presence requires image-to-video capability"
    )
    vram_safety_margin: bool = Field(
        default=True, description="Match against 85% of detected VRAM instead of 100%, for headroom"
    )
    low_memory_decode: bool = Field(
        default=True, description="Decode the VAE output in slices/tiles instead of all at once"
    )
    cpu_offload: bool = Field(
        default=True, description="Move pipeline components between CPU and accelerator instead of holding all at once"
    )


class GenerateVideoResponse(BaseModel):
    video_path: str = Field(description="Path to the generated .mp4 on the API server")
    model: str = Field(description="Hugging Face model id that actually ran")
