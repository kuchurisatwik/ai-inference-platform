"""Service-specific helpers: save a video and push it to storage."""
import os
from pathlib import Path

from app.config import settings
from shared.helpers import generate_filename
from shared.s3 import upload_file


def make_temp_path(prefix: str = "ltx") -> tuple[str, str]:
    """Return (temp_path, filename) for the encoder to write into."""
    filename = generate_filename(prefix, "mp4")
    tmp_dir = Path(settings.output_folder) / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return str(tmp_dir / filename), filename


def upload_and_cleanup(tmp_path: str, filename: str) -> str:
    """Upload the finished video, delete the temp file, return the URL."""
    try:
        url = upload_file(
            local_path=tmp_path,
            key=filename,
            bucket=settings.s3_bucket,
            region=settings.aws_region,
            public_base_url=settings.s3_public_base_url,
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return url
