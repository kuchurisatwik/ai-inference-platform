"""Storage helper: upload a file to S3, or save locally when S3 is not configured.

Keeping this in one place means both services get identical upload behaviour and
the same local-dev fallback (so you can test on Windows without AWS credentials).
"""
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
    presign: bool = False,
    expiry: int = 3600,
) -> str:
    """Upload ``local_path`` and return a URL to the stored object.

    - No ``bucket``: copy into ./outputs and return a local file:// URL (dev).
    - ``presign=True``: return a time-limited pre-signed GET URL (Phase 6).
    - ``public_base_url``: return that CDN/base joined with the key.
    - otherwise: return the plain virtual-hosted S3 URL.
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

    if presign:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiry,
        )
        return url
    if public_base_url:
        return f"{public_base_url.rstrip('/')}/{key}"
    region_part = f"s3.{region}." if region else "s3."
    return f"https://{bucket}.{region_part}amazonaws.com/{key}"


def _save_local(local_path: str, key: str) -> str:
    """Copy the file into ./outputs/<key> and return an HTTP path served by the
    app at /outputs/<key> (the web UI turns this into a full URL). Falls back to
    a plain relative path so callers behind nginx get a browser-loadable link.
    """
    dest = Path("outputs") / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(local_path, dest)
    url = f"/outputs/{key}"
    log.info("saved locally, served at %s", url)
    return url
