from abc import ABC
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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


class PromptComponents(BaseModel, ABC):
    model_config = ConfigDict(validate_assignment=True)

    subject: str = Field(description="Main focus of the video: who/what")
    action: str = Field(description="What happens over time; the motion")
    scene: str = Field(description="Environment, background, time of day")
    camera: str = Field(description="Shot type and camera movement")
    lighting: str = Field(description="Lighting style and mood")
    style: str = Field(description="Visual/cinematic style reference")
    negative_prompt: str | None = Field(default=None, description="What to avoid in the generation")

    @classmethod
    def create(cls, video_type: VideoType, **fields) -> "PromptComponents":
        return _VIDEO_TYPE_COMPONENTS[video_type](**fields)


class CinematicPromptComponents(PromptComponents):
    """Pixar, action, generic animation, anime, documentary, fashion — same shape, different vocabulary."""


class UGCPromptComponents(PromptComponents):
    dialogue: str | None = Field(default=None, description="Spoken script/dialogue delivered by the subject")
    reference_image: str | None = Field(default=None, description="Reference image for product/subject fidelity")


class PresenterPromptComponents(UGCPromptComponents):
    voice_tone: str | None = Field(
        default=None, description="Directive for how the TTS/voice should sound, e.g. 'warm, confident, corporate'"
    )


class SocialAdPromptComponents(UGCPromptComponents):
    text_overlay: str | None = Field(default=None, description="On-screen text/captions overlaid on the video")
    aspect_ratio: str = Field(default="9:16", description="Target aspect ratio, e.g. '9:16' for vertical short-form")


class MusicVideoPromptComponents(PromptComponents):
    audio_reference: str = Field(description="Reference audio track/URL the visuals should sync to")
    tempo_bpm: int | None = Field(default=None, description="Beats per minute to sync visual cuts/transformations to")


class MotionGraphicsPromptComponents(PromptComponents):
    text_content: str = Field(description="On-screen text/copy driving the animation")
    transitions: str | None = Field(default=None, description="Transition style between graphic elements, e.g. 'fade, slide, zoom'")


_VIDEO_TYPE_COMPONENTS: dict[VideoType, type[PromptComponents]] = {
    VideoType.PIXAR: CinematicPromptComponents,
    VideoType.ACTION: CinematicPromptComponents,
    VideoType.ANIMATION: CinematicPromptComponents,
    VideoType.ANIME: CinematicPromptComponents,
    VideoType.DOCUMENTARY: CinematicPromptComponents,
    VideoType.FASHION: CinematicPromptComponents,
    VideoType.UGC_PRODUCT_REVIEW: UGCPromptComponents,
    VideoType.COMMERCIAL_PRODUCT_AD: UGCPromptComponents,
    VideoType.EXPLAINER_TESTIMONIAL: UGCPromptComponents,
    VideoType.PRESENTER_AVATAR: PresenterPromptComponents,
    VideoType.SOCIAL_SHORT_FORM_AD: SocialAdPromptComponents,
    VideoType.MUSIC_VIDEO: MusicVideoPromptComponents,
    VideoType.MOTION_GRAPHICS: MotionGraphicsPromptComponents,
}
