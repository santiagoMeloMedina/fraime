import io
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx
import torch
from diffusers import DiffusionPipeline
from huggingface_hub import snapshot_download
from PIL import Image

from api.config import environment
from api.generation.model import GenerationParams, Reference
from api.generation.prompt.handler import PromptHandler
from api.utils.progress import make_progress_reporter


@dataclass
class FetchedReferences:
    images: list[Image.Image] = field(default_factory=list)


class GenerationHandler:
    def __init__(self, model: str, on_progress: Callable[[float], None] | None = None):
        self.model = model
        if on_progress is not None:
            snapshot_download(
                repo_id=model,
                cache_dir=environment.generation.model_cache_dir,
                tqdm_class=make_progress_reporter(on_progress),
            )
        self.pipeline = DiffusionPipeline.from_pretrained(
            model, cache_dir=environment.generation.model_cache_dir
        )

    def generate(
        self,
        video_type: str,
        fields: dict,
        params: GenerationParams,
        references: list[Reference] | None = None,
    ):
        compiled_prompt = PromptHandler.compile(video_type, fields)
        width, height = (int(value) for value in params.resolution.split("x"))
        generator = (
            torch.Generator().manual_seed(params.seed) if params.seed is not None else None
        )

        pipeline_kwargs = {
            "prompt": compiled_prompt,
            "negative_prompt": fields.get("negative_prompt"),
            "num_frames": round(params.duration_s * params.fps),
            "width": width,
            "height": height,
            "generator": generator,
        }

        fetched = self._fetch_references(references or [])
        if len(fetched.images) >= 1:
            pipeline_kwargs["image"] = fetched.images[0]
        if len(fetched.images) >= 2:
            pipeline_kwargs["last_image"] = fetched.images[1]

        return self.pipeline(**pipeline_kwargs).frames

    @staticmethod
    def _fetch_references(references: list[Reference]) -> FetchedReferences:
        fetched = FetchedReferences()
        for reference in references:
            response = httpx.get(
                str(reference.url),
                follow_redirects=True,
                headers={"User-Agent": "fraime/1.0"},
            )
            response.raise_for_status()
            fetched.images.append(Image.open(io.BytesIO(response.content)))

        return fetched
