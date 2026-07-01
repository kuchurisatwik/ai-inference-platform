"""Service-specific helpers: save an image and push it to storage."""
import os
from pathlib import Path

from app.config import settings
from shared.helpers import generate_filename
from shared.s3 import upload_file


def save_and_upload(image, prefix: str = "flux") -> str:
    """Persist a PIL image to a temp file, upload it, delete the temp, return the URL."""
    filename = generate_filename(prefix, "png")
    tmp_dir = Path(settings.output_folder) / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / filename

    image.save(tmp_path, format="PNG")
    try:
        url = upload_file(
            local_path=str(tmp_path),
            key=filename,
            bucket=settings.s3_bucket,
            region=settings.aws_region,
            public_base_url=settings.s3_public_base_url,
        )
    finally:
        # Always clean up the temp file, even if upload fails.
        if tmp_path.exists():
            os.remove(tmp_path)

    return url
