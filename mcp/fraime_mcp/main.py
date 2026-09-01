from fraime import (
    PROMPT_FIELDS_BY_VIDEO_TYPE,
    CinematicPromptFields,
    FraimeClient,
    GenerationParams,
    ImageGenerationParams,
    ImagePromptFields,
    MotionGraphicsPromptFields,
    MusicVideoPromptFields,
    PresenterPromptFields,
    PromptFields,
    Reference,
    SocialAdPromptFields,
    UGCPromptFields,
)
from fraime.exceptions import FraimeError
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from fraime_mcp.model import (
    GenerateImageInput,
    GenerateImageOutput,
    GenerateVideoInput,
    GenerateVideoOutput,
    ModelsConfigOutput,
    RulesConfigOutput,
    VideoTypeInfo,
)

server = MCPServer(
    "fraime",
    description="Generate short AI videos and images through a self-hosted Fraime API instance.",
)

# FraimeClient itself already falls back to FRAIME_BASE_URL/FRAIME_API_KEY from
# the environment when these aren't passed explicitly. It's also the entire
# data-access layer this server needs — no separate repository wrapper adds
# anything beyond what calling it directly here does.
_client = FraimeClient()


@server.tool()
def generate_video(input: GenerateVideoInput) -> GenerateVideoOutput:
    """Generate a short AI video from a structured prompt.

    Picks a model automatically based on the API host's detected hardware
    unless `model` is set explicitly. Call list_video_types first if unsure
    which extra fields a given video_type actually uses.
    """
    fields = _build_fields(input)
    params = GenerationParams(
        duration_s=input.duration_s,
        fps=input.fps,
        resolution=input.resolution,
        seed=input.seed,
        num_inference_steps=input.num_inference_steps,
    )
    references = [Reference(url=u) for u in input.reference_urls] if input.reference_urls else None

    try:
        response = _client.generate_video(
            video_type=input.video_type,
            fields=fields,
            params=params,
            model=input.model,
            references=references,
            vram_safety_margin=input.vram_safety_margin,
            low_memory_decode=input.low_memory_decode,
            cpu_offload=input.cpu_offload,
        )
    except FraimeError as e:
        # Anticipated: auth/connection/API failures talking to the Fraime API.
        # Re-raised as ToolError so the agent gets is_error=True with a clear
        # message instead of an opaque crash.
        raise ToolError(str(e)) from e

    return GenerateVideoOutput(
        video_path=response.video_path,
        model=response.model,
        s3_bucket=response.s3_bucket,
        s3_key=response.s3_key,
        s3_url=response.s3_url,
    )


@server.tool()
def generate_image(input: GenerateImageInput) -> GenerateImageOutput:
    """Generate a still AI image from a structured prompt.

    Unlike generate_video, there's no per-type field variation — the same
    fixed field set covers every image request. Picks a model automatically
    based on the API host's detected hardware unless `model` is set
    explicitly.
    """
    fields = ImagePromptFields(
        subject=input.subject,
        scene=input.scene,
        camera=input.camera,
        lighting=input.lighting,
        style=input.style,
        action=input.action,
        color_palette=input.color_palette,
        negative_prompt=input.negative_prompt,
    )
    params = ImageGenerationParams(
        width=input.width,
        height=input.height,
        seed=input.seed,
        num_inference_steps=input.num_inference_steps,
        guidance_scale=input.guidance_scale,
    )
    references = [Reference(url=u) for u in input.reference_urls] if input.reference_urls else None

    try:
        response = _client.generate_image(
            fields=fields,
            params=params,
            model=input.model,
            references=references,
            vram_safety_margin=input.vram_safety_margin,
            cpu_offload=input.cpu_offload,
        )
    except FraimeError as e:
        raise ToolError(str(e)) from e

    return GenerateImageOutput(
        image_path=response.image_path,
        model=response.model,
        s3_bucket=response.s3_bucket,
        s3_key=response.s3_key,
        s3_url=response.s3_url,
    )


@server.tool()
def list_video_types() -> list[VideoTypeInfo]:
    """List every supported video_type and which extra fields each one uses.

    Every video_type shares the base fields (subject, action, scene, camera,
    lighting, style, negative_prompt); this only lists what's on top of that.
    """
    base_fields = set(CinematicPromptFields.model_fields)
    return [
        VideoTypeInfo(
            video_type=video_type,
            fields_class=fields_class.__name__,
            extra_fields=sorted(set(fields_class.model_fields) - base_fields),
        )
        for video_type, fields_class in PROMPT_FIELDS_BY_VIDEO_TYPE.items()
    ]


@server.tool()
def get_models_config() -> ModelsConfigOutput:
    """Get the model catalog the Fraime API auto-selects from.

    Covers both video and image models, distinguished by each entry's
    media_type. Lists every catalog model with its capabilities, VRAM
    requirements, license, and which video_types it's preferred for, plus
    the capability requirements each video_type imposes on that selection.
    """
    try:
        config = _client.get_models_config()
    except FraimeError as e:
        raise ToolError(str(e)) from e
    return ModelsConfigOutput.model_validate(config.model_dump())


@server.tool()
def get_rules_config() -> RulesConfigOutput:
    """Get the prompt-structure rules the Fraime API enforces.

    Covers both media types: for video, field guidance and evaluation
    criteria shared by every video_type, plus each video_type's own style
    guidance, extra fields, and additional evaluation criteria; for image,
    the single fixed field set (image_fields) and its evaluation criteria
    (image_evaluation_criteria). Useful for understanding what makes a
    prompt score well before calling generate_video or generate_image.
    """
    try:
        config = _client.get_rules_config()
    except FraimeError as e:
        raise ToolError(str(e)) from e
    return RulesConfigOutput.model_validate(config.model_dump())


def _build_fields(input: GenerateVideoInput) -> PromptFields:
    fields_class = PROMPT_FIELDS_BY_VIDEO_TYPE[input.video_type]
    shared = {
        "subject": input.subject,
        "action": input.action,
        "scene": input.scene,
        "camera": input.camera,
        "lighting": input.lighting,
        "style": input.style,
        "negative_prompt": input.negative_prompt,
    }

    if fields_class is CinematicPromptFields:
        return CinematicPromptFields(**shared)

    if fields_class is UGCPromptFields:
        return UGCPromptFields(**shared, dialogue=input.dialogue, reference_image=input.reference_image)

    if fields_class is PresenterPromptFields:
        return PresenterPromptFields(
            **shared, dialogue=input.dialogue, reference_image=input.reference_image, voice_tone=input.voice_tone
        )

    if fields_class is SocialAdPromptFields:
        return SocialAdPromptFields(
            **shared,
            dialogue=input.dialogue,
            reference_image=input.reference_image,
            text_overlay=input.text_overlay,
            aspect_ratio=input.aspect_ratio,
        )

    if fields_class is MusicVideoPromptFields:
        if not input.audio_reference:
            raise ToolError("audio_reference is required for video_type='music_video'")
        return MusicVideoPromptFields(**shared, audio_reference=input.audio_reference, tempo_bpm=input.tempo_bpm)

    if fields_class is MotionGraphicsPromptFields:
        if not input.text_content:
            raise ToolError("text_content is required for video_type='motion_graphics'")
        return MotionGraphicsPromptFields(**shared, text_content=input.text_content, transitions=input.transitions)

    raise ToolError(f"Unhandled fields class for video_type={input.video_type!r}: {fields_class}")


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
