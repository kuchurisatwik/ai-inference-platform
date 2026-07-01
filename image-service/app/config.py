"""Configuration for the image service, loaded from environment / .env."""
import sys
from pathlib import Path

# Make the repo root importable so `from shared import ...` works both locally
# (uvicorn app.main:app) and inside Docker.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "mock" (default, no GPU) or "flux" (real model on the GPU box)
    model_backend: str = "mock"
    model_path: str = "/opt/models/flux"

    # Storage — leave s3_bucket empty for local ./outputs fallback
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_public_base_url: str = ""

    output_folder: str = "outputs"
    log_level: str = "INFO"


settings = Settings()
