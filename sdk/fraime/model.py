from abc import ABC
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class MediaType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    SOUND = "sound"


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


class ImageGenerationParams(BaseModel):
    width: int = Field(gt=0, description="Target image width in pixels")
    height: int = Field(gt=0, description="Target image height in pixels")
    seed: int | None = Field(default=None, description="Seed for reproducible generation")
    num_inference_steps: int | None = Field(
        default=None,
        gt=0,
        description="Denoising steps; lower is faster/lower quality. Defaults to the model's own default when unset.",
    )
    guidance_scale: float | None = Field(
        default=None,
        ge=0,
        description="Classifier-free guidance scale; defaults to the model's own default when unset.",
    )


class SoundVariant(str, Enum):
    """Which chatterbox class the API loads — a fixed set of Python classes, not
    an arbitrary swappable HF repo id the way video/image models are."""

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


class ImagePromptFields(BaseModel):
    """Fields for an image generation request — a single fixed set, unlike video's
    per-video_type variants, since an image prompt doesn't structurally vary the way
    dialogue-driven/music-synced/motion-graphics video types do."""

    subject: str = Field(description="Main focus of the image: who/what")
    scene: str = Field(description="Environment, background, setting, time of day")
    camera: str = Field(description="Shot type, angle, and framing")
    lighting: str = Field(description="Lighting style, direction, and mood")
    style: str = Field(description="Visual/artistic style or medium reference")
    action: str | None = Field(
        default=None, description="Pose or momentary action, if not purely static"
    )
    color_palette: str | None = Field(default=None, description="Dominant tones or color scheme")
    negative_prompt: str | None = Field(default=None, description="What to avoid in the generation")


class GenerateVideoRequest(BaseModel):
    media_type: Literal[MediaType.VIDEO] = MediaType.VIDEO
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


class GenerateImageRequest(BaseModel):
    media_type: Literal[MediaType.IMAGE] = MediaType.IMAGE
    fields: ImagePromptFields
    params: ImageGenerationParams
    model: str | None = Field(
        default=None, description="Explicit Hugging Face model id; omit to auto-select by hardware"
    )
    references: list[Reference] | None = Field(
        default=None, description="A reference image; presence requires image-to-image capability"
    )
    vram_safety_margin: bool = Field(
        default=True, description="Match against 85% of detected VRAM instead of 100%, for headroom"
    )
    cpu_offload: bool = Field(
        default=True, description="Move pipeline components between CPU and accelerator instead of holding all at once"
    )


class GenerateSoundRequest(BaseModel):
    media_type: Literal[MediaType.SOUND] = MediaType.SOUND
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


class ModelCatalogEntry(BaseModel):
    """One entry from the API's model catalog (`GET /config/models`)."""

    media_type: MediaType = Field(description="Whether this model generates video or image output")
    id: str = Field(description="Hugging Face repo id, intended for DiffusionPipeline.from_pretrained")
    variant: str | None = Field(
        default=None, description="Checkpoint/variant label when the repo id alone doesn't disambiguate it"
    )
    org: str = Field(description="Organization or lab that produced the model")
    params: str = Field(description="Parameter count, e.g. '5B', or a MoE breakdown like '27B total / 14B active per step'")
    license: str = Field(description="License identifier, e.g. Apache-2.0")
    min_vram_gb: float | None = Field(description="Minimum VRAM in GB at standard precision; null if not confirmed")
    min_vram_gb_quantized: float | None = Field(
        default=None, description="Minimum VRAM in GB when quantized (only set if meaningfully different from min_vram_gb)"
    )
    min_vram_gb_optimized: float | None = Field(
        default=None,
        description="Minimum VRAM in GB with optimized/offloaded inference (only set if meaningfully different from min_vram_gb)",
    )
    capabilities: list[str] = Field(description="Generation capabilities this model supports")
    preferred_for: list[str] | None = Field(
        default=None, description="video_type ids this model has a genuine style/quality edge for"
    )
    notes: str | None = Field(default=None, description="Caveats, benchmarks, or licensing nuance worth flagging")


class VideoTypeCapabilityRequirement(BaseModel):
    """Capability requirements a video_type imposes on model auto-selection."""

    required: list[str] = Field(description="Capabilities a model must have to serve this video_type")
    notes: str | None = Field(default=None, description="Caveats about this video_type's capability requirements")


class ModelsConfig(BaseModel):
    """The API's model catalog, as returned by `GET /config/models` — video and
    image models together, distinguished by each entry's `media_type`."""

    models: dict[str, ModelCatalogEntry] = Field(description="Catalog models keyed by their unique model key")
    video_type_capabilities: dict[str, VideoTypeCapabilityRequirement] = Field(
        description="Capability requirements per video_type, used to auto-select a matching model"
    )


class EvaluationCriterion(BaseModel):
    """One prompt-quality or structural check from the API's rules config."""

    name: str = Field(description="Unique identifier for the criterion within its scope")
    description: str = Field(description="What is being checked")
    check_type: str = Field(description="'structural' (deterministically computable) or 'semantic' (LLM-as-judge)")
    severity: str = Field(description="'blocking' (gates generation) or 'quality' (contributes to an aggregate score)")
    weight: float | None = Field(
        default=None, description="Relative importance (0-1) among quality criteria in the same scope"
    )
    remediation: str = Field(description="What the improve step should try when this criterion fails")


class SharedPromptRules(BaseModel):
    """Prompt rules applied to every video_type."""

    fields: dict[str, str] = Field(description="Guidance text for each shared prompt field")
    evaluation_criteria: list[EvaluationCriterion] = Field(description="Criteria applied to every video_type")


class VideoTypeRules(BaseModel):
    """Prompt rules specific to one video_type, on top of the shared rules."""

    style_guidance: str = Field(description="How this type's prompt should be steered stylistically")
    extra_fields: dict[str, str] | None = Field(
        default=None, description="Extra prompt fields this type adds beyond the shared set, mapped to guidance text"
    )
    evaluation_criteria: list[EvaluationCriterion] = Field(
        description="Criteria this type's prompts are checked against, on top of the shared criteria"
    )
    caveat: str | None = Field(default=None, description="Known limitation, e.g. no integrated model supports this type well")


class RulesConfig(BaseModel):
    """The API's prompt rules, as returned by `GET /config/rules` — video and image
    rules together, in one file on the API side (video under `shared`/`types`,
    image under `image_fields`/`image_evaluation_criteria`)."""

    criteria_schema: dict[str, str] = Field(description="What each evaluation criterion field means")
    shared: SharedPromptRules = Field(description="Prompt rules shared by every video_type")
    types: dict[str, VideoTypeRules] = Field(description="Prompt rules specific to each video_type")
    image_fields: dict[str, str] = Field(description="Guidance text for each image prompt field")
    image_evaluation_criteria: list[EvaluationCriterion] = Field(
        description="Criteria applied to every image generation prompt"
    )


class GenerateVideoResponse(BaseModel):
    video_path: str | None = Field(
        default=None,
        description="Path to the generated .mp4 on the API server, or null if the API is configured for S3 output instead",
    )
    model: str = Field(description="Hugging Face model id that actually ran")
    s3_bucket: str | None = Field(
        default=None, description="S3 bucket the video was uploaded to, if the API has S3 output configured"
    )
    s3_key: str | None = Field(default=None, description="S3 object key the video was uploaded to")
    s3_url: str | None = Field(
        default=None, description="Presigned GET URL for downloading the video directly from S3, valid for 1 hour"
    )


class GenerateImageResponse(BaseModel):
    image_path: str | None = Field(
        default=None,
        description="Path to the generated .png on the API server, or null if the API is configured for S3 output instead",
    )
    model: str = Field(description="Hugging Face model id that actually ran")
    s3_bucket: str | None = Field(
        default=None, description="S3 bucket the image was uploaded to, if the API has S3 output configured"
    )
    s3_key: str | None = Field(default=None, description="S3 object key the image was uploaded to")
    s3_url: str | None = Field(
        default=None, description="Presigned GET URL for downloading the image directly from S3, valid for 1 hour"
    )


class GenerateSoundResponse(BaseModel):
    sound_path: str | None = Field(
        default=None,
        description="Path to the generated .wav on the API server, or null if the API is configured for S3 output instead",
    )
    model: str = Field(description="Hugging Face model id that actually ran")
    s3_bucket: str | None = Field(
        default=None, description="S3 bucket the sound file was uploaded to, if the API has S3 output configured"
    )
    s3_key: str | None = Field(default=None, description="S3 object key the sound file was uploaded to")
    s3_url: str | None = Field(
        default=None, description="Presigned GET URL for downloading the sound file directly from S3, valid for 1 hour"
    )
