"""Configuration for the video service, loaded from environment / .env."""
import os
import sys
from pathlib import Path

# Reduce CUDA memory fragmentation (must be set before torch initialises CUDA).
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "mock" (default, no GPU) or "ltx" (real model on the GPU box)
    model_backend: str = "mock"
    model_path: str = "/opt/models/ltx"
    # Wan: offload to CPU during denoise (slower). Off = all on GPU (needs ~48GB).
    wan_cpu_offload: bool = False
    # Build the image-to-video pipeline. True for the 5B TI2V model; set false
    # for the 14B T2V-A14B model (text-to-video only, no i2v components).
    wan_i2v: bool = True

    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_public_base_url: str = ""
    s3_presign: bool = False       # return time-limited pre-signed URLs (Phase 6)
    s3_url_expiry: int = 3600      # seconds

    output_folder: str = "outputs"
    log_level: str = "INFO"

    # Comma-separated API keys required in the X-API-Key header. Empty = no auth.
    api_keys: str = ""

    @property
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}


settings = Settings()
