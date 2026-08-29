from pathlib import Path
from uuid import uuid4

from diffusers.utils import export_to_video
from pydantic import BaseModel

from api.config import environment
from api.detector import select_best_model
from api.generation.create import GenerationHandler
from api.generation.model import GenerationParams, Reference


class GenerateVideoRequest(BaseModel):
    model: str | None = None
    video_type: str
    fields: dict
    params: GenerationParams
    references: list[Reference] | None = None
    vram_safety_margin: bool = True
    low_memory_decode: bool = True
    cpu_offload: bool = True


def generate_video(request: GenerateVideoRequest) -> tuple[str, str]:
    model = request.model
    if model is None:
        capabilities = ["image-to-video"] if request.references else None
        model = select_best_model(
            video_type=request.video_type,
            capabilities=capabilities,
            safety_margin=request.vram_safety_margin,
        ).model_id

    handler = GenerationHandler(
        model, low_memory_decode=request.low_memory_decode, cpu_offload=request.cpu_offload
    )
    frames = handler.generate(
        request.video_type,
        request.fields,
        request.params,
        request.references,
    )

    output_dir = Path(environment.generation.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uuid4()}.mp4"

    return export_to_video(frames, str(output_path), fps=request.params.fps), model
