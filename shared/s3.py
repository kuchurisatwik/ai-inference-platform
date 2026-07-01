"""Storage helper: upload a file to S3, or save locally when S3 is not configured.

Keeping this in one place means both services get identical upload behaviour and
the same local-dev fallback (so you can test on Windows without AWS credentials).
"""
import os
import shutil
from pathlib import Path
from typing import Optional

from shared.logger import get_logger

log = get_logger("shared.s3")


def upload_file(
    local_path: str,
    key: str,
    bucket: Optional[str] = None,
    region: Optional[str] = None,
    public_base_url: Optional[str] = None,
) -> str:
    """Upload ``local_path`` and return a URL to the stored object.

    If ``bucket`` is falsy, falls back to copying the file into ./outputs and
    returns a local file URL — handy for local development without AWS.
    """
    if not bucket:
        return _save_local(local_path, key)

    try:
        import boto3  # imported lazily so local dev doesn't require boto3
    except ImportError:
        log.warning("boto3 not installed; falling back to local storage")
        return _save_local(local_path, key)

    s3 = boto3.client("s3", region_name=region)
    s3.upload_file(local_path, bucket, key)
    log.info("uploaded s3://%s/%s", bucket, key)

    if public_base_url:
        return f"{public_base_url.rstrip('/')}/{key}"
    region_part = f"s3.{region}." if region else "s3."
    return f"https://{bucket}.{region_part}amazonaws.com/{key}"


def _save_local(local_path: str, key: str) -> str:
    """Copy the file into ./outputs/<key> and return a file:// URL."""
    out_dir = Path("outputs")
    dest = out_dir / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(local_path, dest)
    url = dest.resolve().as_uri()
    log.info("saved locally at %s", url)
    return url
