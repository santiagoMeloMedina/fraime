import io

import httpx
import torch
from diffusers import DiffusionPipeline
from PIL import Image

from api.generation.model import GenerationParams
from api.generation.prompt.handler import PromptHandler


class GenerationHandler:
    def __init__(self, model: str):
        self.model = model
        self.pipeline = DiffusionPipeline.from_pretrained(model)

    def generate(
        self,
        video_type: str,
        fields: dict,
        params: GenerationParams,
        references: list[str] | None = None,
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
        if fetched["images"]:
            pipeline_kwargs["reference_images"] = fetched["images"]
        if fetched["audio"]:
            pipeline_kwargs["reference_audio"] = fetched["audio"]
        if fetched["video"]:
            pipeline_kwargs["reference_videos"] = fetched["video"]

        return self.pipeline(**pipeline_kwargs).frames

    @staticmethod
    def _fetch_references(urls: list[str]) -> dict[str, list]:
        references: dict[str, list] = {"images": [], "audio": [], "video": []}
        for url in urls:
            response = httpx.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": "fraime/1.0"},
            )
            response.raise_for_status()
            buffer = io.BytesIO(response.content)
            content_type = response.headers.get("content-type", "")

            if content_type.startswith("image/"):
                references["images"].append(Image.open(buffer))
            elif content_type.startswith("audio/"):
                references["audio"].append(buffer)
            elif content_type.startswith("video/"):
                references["video"].append(buffer)
            else:
                raise ValueError(f"Unsupported reference content type '{content_type}' for {url}")

        return references
