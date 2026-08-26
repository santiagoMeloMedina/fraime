from pathlib import Path

from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent / ".env"


class GenerationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GENERATION_", env_file=ENV_FILE)

    duration_s: float = 5.0
    fps: int = 24
    resolution: str = "1024x576"
    seed: int | None = None
    model_cache_dir: str | None = None
    output_dir: str = "generated"


class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    generation: GenerationSettings = GenerationSettings()


environment = Environment()

app = FastAPI(title="Fraime API")
