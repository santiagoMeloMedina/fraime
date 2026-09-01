from pydantic import BaseModel, Field

from fraime import AspectRatio, MediaType, VideoType


class GenerateVideoInput(BaseModel):
    """Everything needed to generate one video via the Fraime API."""

    video_type: VideoType = Field(
        description=(
            "The kind of video to generate; determines which of the fields below are "
            "actually used, and the style guidance applied server-side. Call "
            "list_video_types first if unsure which extra fields a type needs."
        )
    )

    # Shared prompt fields — used by every video_type.
    subject: str = Field(
        description="Main focus of the video: who/what, concrete and visually groundable — avoid vague adjectives"
    )
    action: str = Field(
        description="What happens over the clip: a single continuous motion achievable in a short clip, not a multi-beat sequence"
    )
    scene: str = Field(
        description="Environment, background, and time of day, specific enough to anchor lighting/mood"
    )
    camera: str = Field(
        description="Shot type and camera movement; must be physically compatible with the described action"
    )
    lighting: str = Field(
        description="Lighting style/mood; must not contradict the scene's implied conditions"
    )
    style: str = Field(
        description="A concrete visual/style reference (rendering style, film stock, animation technique) — never a vague quality adjective like 'high quality'"
    )
    negative_prompt: str | None = Field(
        default=None, description="Concrete failure modes to avoid for this content type, not generic boilerplate"
    )

    # Used by ugc_product_review / commercial_product_ad / explainer_testimonial /
    # presenter_avatar / social_short_form_ad. Ignored otherwise.
    dialogue: str | None = Field(
        default=None, description="Spoken script/dialogue delivered by the subject. Ignored for video types that don't use it."
    )
    reference_image: str | None = Field(
        default=None,
        description=(
            "A short text note anchoring product/subject visual fidelity for the prompt "
            "(this is prompt guidance text, NOT an actual image — for real image "
            "conditioning use reference_urls instead). Ignored for video types that don't use it."
        ),
    )

    # presenter_avatar only.
    voice_tone: str | None = Field(
        default=None,
        description="Directive for how the voice should sound, e.g. 'warm, confident, corporate'. Only used for video_type='presenter_avatar'.",
    )

    # social_short_form_ad only.
    text_overlay: str | None = Field(
        default=None, description="On-screen text/captions overlaid on the video. Only used for video_type='social_short_form_ad'."
    )
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.VERTICAL_9_16, description="Target aspect ratio. Only used for video_type='social_short_form_ad'."
    )

    # music_video only.
    audio_reference: str | None = Field(
        default=None, description="Reference audio track URL the visuals should sync to. Required when video_type='music_video'."
    )
    tempo_bpm: int | None = Field(
        default=None, description="Beats per minute, to sync visual cuts. Only used for video_type='music_video'."
    )

    # motion_graphics only.
    text_content: str | None = Field(
        default=None, description="On-screen text/copy driving the animation. Required when video_type='motion_graphics'."
    )
    transitions: str | None = Field(
        default=None,
        description="Transition style between graphic elements, e.g. 'fade, slide, zoom'. Only used for video_type='motion_graphics'.",
    )

    # Generation parameters.
    duration_s: float = Field(gt=0, description="Requested clip duration in seconds")
    fps: int = Field(gt=0, description="Frames per second")
    resolution: str = Field(
        description="Target resolution, e.g. '768x512'. Match the picked model's documented shape when possible — an unfamiliar aspect ratio can noticeably degrade output."
    )
    seed: int | None = Field(default=None, description="Seed for reproducible generation")
    num_inference_steps: int | None = Field(
        default=None,
        gt=0,
        description="Denoising steps; lower is faster/lower quality. Omit to use the model's own default (usually 50).",
    )

    # Model selection / real image conditioning / performance knobs.
    model: str | None = Field(
        default=None, description="Explicit Hugging Face model id to use. Omit to auto-select the best model the API's hardware can run."
    )
    reference_urls: list[str] | None = Field(
        default=None,
        description=(
            "Publicly accessible image URLs for real image-to-video conditioning — the "
            "actual images fed to the model, distinct from reference_image above. Presence "
            "requires image-to-video capability on whichever model gets used."
        ),
    )
    vram_safety_margin: bool = Field(
        default=True,
        description="Match auto-selection against 85% of detected VRAM instead of 100%, for headroom against real-world usage spikes. Recommended on.",
    )
    low_memory_decode: bool = Field(
        default=True,
        description="Decode the VAE output in slices/tiles instead of all at once — trades a little speed for much lower peak memory. Recommended on unless the host has VRAM to spare.",
    )
    cpu_offload: bool = Field(
        default=True,
        description="Move pipeline components between CPU and the accelerator instead of holding all of them resident at once — trades speed for headroom. Recommended on unless the host has VRAM to spare.",
    )


class GenerateVideoOutput(BaseModel):
    video_path: str | None = Field(
        default=None,
        description="Path to the generated .mp4 on the API server, or null if the API is configured for S3 output instead",
    )
    model: str = Field(description="The Hugging Face model id that actually ran")
    s3_bucket: str | None = Field(
        default=None, description="S3 bucket the video was uploaded to, if the API has S3 output configured"
    )
    s3_key: str | None = Field(default=None, description="S3 object key the video was uploaded to")
    s3_url: str | None = Field(
        default=None, description="Presigned GET URL for downloading the video directly from S3, valid for 1 hour"
    )


class GenerateImageInput(BaseModel):
    """Everything needed to generate one image via the Fraime API.

    Unlike video, there's no per-type variation — this fixed field set covers
    every image generation request.
    """

    subject: str = Field(
        description="Main focus of the image: who/what, concrete and visually groundable — avoid vague adjectives"
    )
    scene: str = Field(
        description="Environment, background, and time of day, specific enough to anchor lighting/mood"
    )
    camera: str = Field(
        description="Shot type, angle, and framing; must be physically compatible with what the subject/scene can show"
    )
    lighting: str = Field(
        description="Lighting style, direction, and mood; must not contradict the scene's implied conditions"
    )
    style: str = Field(
        description="A concrete visual/artistic style or medium reference — never a vague quality adjective like 'high quality'"
    )
    action: str | None = Field(
        default=None,
        description="The subject's pose or momentary action, as a single plausible instant — omit for a purely static subject",
    )
    color_palette: str | None = Field(
        default=None, description="Dominant tones/color scheme; must not contradict lighting or scene"
    )
    negative_prompt: str | None = Field(
        default=None, description="Concrete failure modes to avoid, not generic boilerplate"
    )

    # Generation parameters.
    width: int = Field(gt=0, description="Target image width in pixels")
    height: int = Field(gt=0, description="Target image height in pixels")
    seed: int | None = Field(default=None, description="Seed for reproducible generation")
    num_inference_steps: int | None = Field(
        default=None,
        gt=0,
        description="Denoising steps; lower is faster/lower quality. Omit to use the model's own default.",
    )
    guidance_scale: float | None = Field(
        default=None, ge=0, description="Classifier-free guidance scale. Omit to use the model's own default."
    )

    # Model selection / real image conditioning / performance knobs.
    model: str | None = Field(
        default=None, description="Explicit Hugging Face model id to use. Omit to auto-select the best model the API's hardware can run."
    )
    reference_urls: list[str] | None = Field(
        default=None,
        description=(
            "Publicly accessible image URLs for real image-to-image conditioning. Presence "
            "requires image-to-image capability on whichever model gets used."
        ),
    )
    vram_safety_margin: bool = Field(
        default=True,
        description="Match auto-selection against 85% of detected VRAM instead of 100%, for headroom against real-world usage spikes. Recommended on.",
    )
    cpu_offload: bool = Field(
        default=True,
        description="Move pipeline components between CPU and the accelerator instead of holding all of them resident at once — trades speed for headroom. Recommended on unless the host has VRAM to spare.",
    )


class GenerateImageOutput(BaseModel):
    image_path: str | None = Field(
        default=None,
        description="Path to the generated .png on the API server, or null if the API is configured for S3 output instead",
    )
    model: str = Field(description="The Hugging Face model id that actually ran")
    s3_bucket: str | None = Field(
        default=None, description="S3 bucket the image was uploaded to, if the API has S3 output configured"
    )
    s3_key: str | None = Field(default=None, description="S3 object key the image was uploaded to")
    s3_url: str | None = Field(
        default=None, description="Presigned GET URL for downloading the image directly from S3, valid for 1 hour"
    )


class VideoTypeInfo(BaseModel):
    video_type: VideoType
    fields_class: str = Field(description="Name of the underlying SDK PromptFields class this type uses")
    extra_fields: list[str] = Field(
        description="Field names beyond the shared base (subject/action/scene/camera/lighting/style/negative_prompt) that this video type actually uses"
    )


class ModelCatalogEntryOutput(BaseModel):
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


class VideoTypeCapabilityRequirementOutput(BaseModel):
    required: list[str] = Field(description="Capabilities a model must have to serve this video_type")
    notes: str | None = Field(default=None, description="Caveats about this video_type's capability requirements")


class ModelsConfigOutput(BaseModel):
    """The Fraime API's model catalog — what `generate_video` auto-selects from when `model` is omitted."""

    models: dict[str, ModelCatalogEntryOutput] = Field(description="Catalog models keyed by their unique model key")
    video_type_capabilities: dict[str, VideoTypeCapabilityRequirementOutput] = Field(
        description="Capability requirements per video_type, used to auto-select a matching model"
    )


class EvaluationCriterionOutput(BaseModel):
    name: str = Field(description="Unique identifier for the criterion within its scope")
    description: str = Field(description="What is being checked")
    check_type: str = Field(description="'structural' (deterministically computable) or 'semantic' (LLM-as-judge)")
    severity: str = Field(description="'blocking' (gates generation) or 'quality' (contributes to an aggregate score)")
    weight: float | None = Field(
        default=None, description="Relative importance (0-1) among quality criteria in the same scope"
    )
    remediation: str = Field(description="What the improve step should try when this criterion fails")


class SharedPromptRulesOutput(BaseModel):
    fields: dict[str, str] = Field(description="Guidance text for each shared prompt field")
    evaluation_criteria: list[EvaluationCriterionOutput] = Field(description="Criteria applied to every video_type")


class VideoTypeRulesOutput(BaseModel):
    style_guidance: str = Field(description="How this type's prompt should be steered stylistically")
    extra_fields: dict[str, str] | None = Field(
        default=None, description="Extra prompt fields this type adds beyond the shared set, mapped to guidance text"
    )
    evaluation_criteria: list[EvaluationCriterionOutput] = Field(
        description="Criteria this type's prompts are checked against, on top of the shared criteria"
    )
    caveat: str | None = Field(default=None, description="Known limitation, e.g. no integrated model supports this type well")


class RulesConfigOutput(BaseModel):
    """The Fraime API's prompt structure/evaluation rules, for both video (per
    video_type) and image (a single fixed field set)."""

    criteria_schema: dict[str, str] = Field(description="What each evaluation criterion field means")
    shared: SharedPromptRulesOutput = Field(description="Prompt rules shared by every video_type")
    types: dict[str, VideoTypeRulesOutput] = Field(description="Prompt rules specific to each video_type")
    image_fields: dict[str, str] = Field(description="Guidance text for each image prompt field")
    image_evaluation_criteria: list[EvaluationCriterionOutput] = Field(
        description="Criteria applied to every image generation prompt"
    )
