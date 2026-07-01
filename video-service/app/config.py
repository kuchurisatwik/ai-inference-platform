"""Configuration for the video service, loaded from environment / .env."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "mock" (default, no GPU) or "ltx" (real model on the GPU box)
    model_backend: str = "mock"
    model_path: str = "/opt/models/ltx"

    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_public_base_url: str = ""
    s3_presign: bool = False       # return time-limited pre-signed URLs (Phase 6)
    s3_url_expiry: int = 3600      # seconds

    output_folder: str = "outputs"
    log_level: str = "INFO"


settings = Settings()
