"""Configuration for the image service, loaded from environment / .env."""
import os
import sys
from pathlib import Path

# Reduce CUDA memory fragmentation (must be set before torch initialises CUDA).
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

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
    # 4-bit (nf4) quantize the FLUX transformer so it fits a 24GB GPU (L4).
    # Set false on a big GPU to run full bf16.
    flux_quantize: bool = True
    # Offload to CPU during denoise. Slow (per-request transfers) — only turn on
    # if quantized FLUX still won't fit VRAM. Off keeps it all on the GPU (fast).
    flux_cpu_offload: bool = False

    # Storage — leave s3_bucket empty for local ./outputs fallback
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_public_base_url: str = ""
    s3_presign: bool = False       # return time-limited pre-signed URLs (Phase 6)
    s3_url_expiry: int = 3600      # seconds

    output_folder: str = "outputs"
    log_level: str = "INFO"


settings = Settings()
