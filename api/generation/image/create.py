import io
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx
import torch
from diffusers import AutoPipelineForImage2Image, AutoPipelineForText2Image
from huggingface_hub import snapshot_download
from PIL import Image

from api.config import environment
from api.detector import Accelerator, detect_hardware
from api.generation.image.model import ImageGenerationParams
from api.generation.media_type import MediaType
from api.generation.model import Reference
from api.generation.prompt.handler import PromptHandler
from api.utils.progress import make_progress_reporter

_DTYPE_BY_ACCELERATOR = {
    Accelerator.CUDA: torch.float16,
    Accelerator.MPS: torch.bfloat16,
    Accelerator.CPU: torch.float32,
}


@dataclass
class FetchedReferences:
    images: list[Image.Image] = field(default_factory=list)


class ImageGeneratorHandler:
    def __init__(
        self,
        model: str,
        on_progress: Callable[[float], None] | None = None,
        cpu_offload: bool = True,
    ):
        self.model = model
        if on_progress is not None:
            snapshot_download(
                repo_id=model,
                cache_dir=environment.generation.model_cache_dir,
                tqdm_class=make_progress_reporter(on_progress),
            )

        hardware = detect_hardware()
        self.device = hardware.accelerator.value
        self.pipeline = AutoPipelineForText2Image.from_pretrained(
            model,
            cache_dir=environment.generation.model_cache_dir,
            torch_dtype=_DTYPE_BY_ACCELERATOR[hardware.accelerator],
        )
        if cpu_offload and hardware.accelerator != Accelerator.CPU:
            self.pipeline.enable_model_cpu_offload(device=self.device)
        else:
            self.pipeline.to(self.device)
        self._img2img_pipeline: AutoPipelineForImage2Image | None = None

    def generate(
        self,
        fields: dict,
        params: ImageGenerationParams,
        references: list[Reference] | None = None,
    ):
        compiled_prompt = PromptHandler.compile(MediaType.IMAGE, fields)
        generator = (
            torch.Generator(device=self.device).manual_seed(params.seed)
            if params.seed is not None
            else None
        )

        pipeline_kwargs = {
            "prompt": compiled_prompt,
            "negative_prompt": fields.get("negative_prompt"),
            "width": params.width,
            "height": params.height,
            "generator": generator,
        }
        if params.num_inference_steps is not None:
            pipeline_kwargs["num_inference_steps"] = params.num_inference_steps
        if params.guidance_scale is not None:
            pipeline_kwargs["guidance_scale"] = params.guidance_scale

        fetched = self._fetch_references(references or [])
        if fetched.images:
            pipeline_kwargs["image"] = fetched.images[0]
            if params.strength is not None:
                pipeline_kwargs["strength"] = params.strength
            pipeline = self._get_img2img_pipeline()
        else:
            pipeline = self.pipeline

        return pipeline(**pipeline_kwargs).images[0]

    def _get_img2img_pipeline(self) -> AutoPipelineForImage2Image:
        # Built lazily from the loaded text2img pipeline's components, so switching
        # between text- and image-conditioned generation doesn't load the model twice.
        if self._img2img_pipeline is None:
            self._img2img_pipeline = AutoPipelineForImage2Image.from_pipe(self.pipeline)
        return self._img2img_pipeline

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
            fetched.images.append(Image.open(io.BytesIO(response.content)).convert("RGB"))

        return fetched
