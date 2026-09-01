import io
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx
import torch
from diffusers import DiffusionPipeline
from huggingface_hub import snapshot_download
from PIL import Image

from api.config import environment
from api.detector import Accelerator, detect_hardware
from api.generation.media_type import MediaType
from api.generation.model import GenerationParams, Reference
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


class GenerationHandler:
    def __init__(
        self,
        model: str,
        on_progress: Callable[[float], None] | None = None,
        low_memory_decode: bool = True,
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
        self.pipeline = DiffusionPipeline.from_pretrained(
            model,
            cache_dir=environment.generation.model_cache_dir,
            torch_dtype=_DTYPE_BY_ACCELERATOR[hardware.accelerator],
        )
        if self.device == "mps":
            self._downcast_float64_buffers()
        if cpu_offload and hardware.accelerator != Accelerator.CPU:
            # Keeps only the component currently running (text encoder, then
            # transformer, then VAE) on the accelerator, moving the rest to system
            # RAM. This is what actually shrinks peak accelerator memory — dtype and
            # VAE tiling alone don't stop the whole pipeline sitting resident at once.
            self.pipeline.enable_model_cpu_offload(device=self.device)
        else:
            self.pipeline.to(self.device)
        if low_memory_decode:
            self._enable_low_memory_vae_decoding()

    def _downcast_float64_buffers(self) -> None:
        # Some model implementations (e.g. CogVideoX's sinusoidal positional
        # embedding) register a buffer as float64 at construction time, independent
        # of torch_dtype. MPS can't hold float64 tensors at all — not a missing-op
        # case PYTORCH_ENABLE_MPS_FALLBACK would catch, a hard framework limit — so
        # this has to be downcast before anything moves to an MPS device.
        for component in getattr(self.pipeline, "components", {}).values():
            if not isinstance(component, torch.nn.Module):
                continue
            for buf in component.buffers():
                if buf.dtype == torch.float64:
                    buf.data = buf.data.to(torch.float32)

    def _enable_low_memory_vae_decoding(self) -> None:
        # Decodes the VAE output in slices/tiles instead of all at once. This is the
        # single biggest memory spike in video pipelines (bigger than the denoising
        # loop itself). Costs a little speed for a lot of headroom, so it defaults on;
        # disable it on hardware with VRAM to spare via low_memory_decode=False.
        for target in (self.pipeline, getattr(self.pipeline, "vae", None)):
            if target is None:
                continue
            if hasattr(target, "enable_slicing"):
                target.enable_slicing()
            elif hasattr(target, "enable_vae_slicing"):
                target.enable_vae_slicing()
            if hasattr(target, "enable_tiling"):
                target.enable_tiling()
            elif hasattr(target, "enable_vae_tiling"):
                target.enable_vae_tiling()

    def generate(
        self,
        video_type: str,
        fields: dict,
        params: GenerationParams,
        references: list[Reference] | None = None,
    ):
        compiled_prompt = PromptHandler.compile(MediaType.VIDEO, fields, video_type=video_type)
        width, height = (int(value) for value in params.resolution.split("x"))
        generator = (
            torch.Generator(device=self.device).manual_seed(params.seed)
            if params.seed is not None
            else None
        )

        pipeline_kwargs = {
            "prompt": compiled_prompt,
            "negative_prompt": fields.get("negative_prompt"),
            "num_frames": round(params.duration_s * params.fps),
            "width": width,
            "height": height,
            "generator": generator,
        }
        if params.num_inference_steps is not None:
            pipeline_kwargs["num_inference_steps"] = params.num_inference_steps

        fetched = self._fetch_references(references or [])
        if len(fetched.images) >= 1:
            pipeline_kwargs["image"] = fetched.images[0]
        if len(fetched.images) >= 2:
            pipeline_kwargs["last_image"] = fetched.images[1]

        return self.pipeline(**pipeline_kwargs).frames[0]

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
