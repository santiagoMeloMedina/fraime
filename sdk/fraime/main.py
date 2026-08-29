import os

from fraime.model import (
    GenerateVideoRequest,
    GenerateVideoResponse,
    GenerationParams,
    PromptFields,
    Reference,
    VideoType,
)
from fraime.repository import GenerationRepository
from fraime.service import GenerationService

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class FraimeClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 600.0,
    ):
        base_url = base_url or os.environ.get("FRAIME_BASE_URL", DEFAULT_BASE_URL)
        api_key = api_key or os.environ.get("FRAIME_API_KEY")

        repository = GenerationRepository(base_url=base_url, api_key=api_key, timeout=timeout)
        self._service = GenerationService(repository)

    def generate(
        self,
        video_type: VideoType,
        fields: PromptFields,
        params: GenerationParams,
        model: str | None = None,
        references: list[Reference] | None = None,
        vram_safety_margin: bool = True,
        low_memory_decode: bool = True,
        cpu_offload: bool = True,
    ) -> GenerateVideoResponse:
        request = GenerateVideoRequest(
            video_type=video_type,
            fields=fields,
            params=params,
            model=model,
            references=references,
            vram_safety_margin=vram_safety_margin,
            low_memory_decode=low_memory_decode,
            cpu_offload=cpu_offload,
        )
        return self._service.generate_video(request)
