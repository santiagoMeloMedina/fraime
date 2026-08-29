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
    output_dir: str = ".generated"


class DetectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DETECTOR_", env_file=ENV_FILE, extra="ignore")

    catalog_path: str = str(Path(__file__).resolve().parent / "instructions" / "models.json")


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=ENV_FILE, extra="ignore")

    api_key: str | None = None


class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    generation: GenerationSettings = GenerationSettings()
    detector: DetectorSettings = DetectorSettings()
    auth: AuthSettings = AuthSettings()


environment = Environment()

app = FastAPI(title="Fraime API")
