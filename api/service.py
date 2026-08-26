from pathlib import Path
from uuid import uuid4

from diffusers.utils import export_to_video
from pydantic import BaseModel

from api.config import environment
from api.generation.create import GenerationHandler
from api.generation.model import GenerationParams, Reference


class GenerateVideoRequest(BaseModel):
    model: str
    video_type: str
    fields: dict
    params: GenerationParams
    references: list[Reference] | None = None


def generate_video(request: GenerateVideoRequest) -> str:
    handler = GenerationHandler(request.model)
    frames = handler.generate(
        request.video_type,
        request.fields,
        request.params,
        request.references,
    )

    output_dir = Path(environment.generation.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uuid4()}.mp4"

    return export_to_video(frames, str(output_path), fps=request.params.fps)
