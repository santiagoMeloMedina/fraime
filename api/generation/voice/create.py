import os
import re
import tempfile
from collections.abc import Callable
from pathlib import Path

import httpx
import torch
from huggingface_hub import snapshot_download

from api.config import environment
from api.detector import detect_hardware
from api.generation.model import Reference
from api.generation.voice.model import VoiceGenerationParams, VoiceVariant
from api.utils.progress import make_progress_reporter

MAX_CHUNK_CHARS = 300


def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current.strip())
    return chunks


class VoiceGeneratorHandler:
    def __init__(
        self,
        variant: VoiceVariant,
        model_id: str,
        on_progress: Callable[[float], None] | None = None,
    ):
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        from chatterbox.tts import ChatterboxTTS
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        variant_classes = {
            VoiceVariant.BASE: ChatterboxTTS,
            VoiceVariant.TURBO: ChatterboxTurboTTS,
            VoiceVariant.MULTILINGUAL: ChatterboxMultilingualTTS,
        }

        self.variant = variant
        self.model_id = model_id
        if on_progress is not None:
            snapshot_download(
                repo_id=model_id,
                cache_dir=environment.generation.model_cache_dir,
                tqdm_class=make_progress_reporter(on_progress),
            )

        hardware = detect_hardware()
        self.device = hardware.accelerator.value
        self.model = variant_classes[variant].from_pretrained(device=self.device)

    def generate(
        self,
        text: str,
        params: VoiceGenerationParams,
        language: str | None = None,
        voice: Reference | None = None,
    ) -> tuple[torch.Tensor, int]:
        audio_prompt_path = self._fetch_voice(voice) if voice is not None else None
        try:
            wavs = [
                self._generate_chunk(chunk, params, language, audio_prompt_path)
                for chunk in _chunk_text(text)
            ]
        finally:
            if audio_prompt_path:
                Path(audio_prompt_path).unlink(missing_ok=True)

        silence = torch.zeros(1, int(0.2 * self.model.sr))
        pieces: list[torch.Tensor] = []
        for i, wav in enumerate(wavs):
            pieces.append(wav)
            if i < len(wavs) - 1:
                pieces.append(silence)

        return torch.cat(pieces, dim=-1), self.model.sr

    def _generate_chunk(
        self,
        chunk: str,
        params: VoiceGenerationParams,
        language: str | None,
        audio_prompt_path: str | None,
    ) -> torch.Tensor:
        kwargs = {
            "audio_prompt_path": audio_prompt_path,
            "exaggeration": params.exaggeration,
            "cfg_weight": params.cfg_weight,
            "temperature": params.temperature,
        }
        if self.variant == VoiceVariant.MULTILINGUAL:
            kwargs["language_id"] = language or "en"
        if self.variant == VoiceVariant.TURBO and self.device == "mps":
            kwargs["norm_loudness"] = False
        return self.model.generate(chunk, **kwargs)

    @staticmethod
    def _fetch_voice(voice: Reference) -> str:
        response = httpx.get(
            str(voice.url),
            follow_redirects=True,
            headers={"User-Agent": "fraime/1.0"},
        )
        response.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".wav")
        with os.fdopen(fd, "wb") as f:
            f.write(response.content)
        return path
