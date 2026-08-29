from fraime import (
    PROMPT_FIELDS_BY_VIDEO_TYPE,
    CinematicPromptFields,
    FraimeClient,
    GenerationParams,
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

from fraime_mcp.model import GenerateVideoInput, GenerateVideoOutput, VideoTypeInfo

server = MCPServer(
    "fraime",
    description="Generate short AI videos through a self-hosted Fraime API instance.",
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
        response = _client.generate(
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

    return GenerateVideoOutput(video_path=response.video_path, model=response.model)


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
