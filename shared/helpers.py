"""Small, dependency-free helpers shared by both services."""
import uuid
from datetime import datetime, timezone


def timestamp() -> str:
    """UTC timestamp string, safe for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def generate_filename(prefix: str, extension: str) -> str:
    """Build a collision-resistant output filename.

    e.g. generate_filename("flux", "png") -> "flux-20260701-142600-a1b2c3d4.png"
    """
    ext = extension.lstrip(".")
    short_id = uuid.uuid4().hex[:8]
    return f"{prefix}-{timestamp()}-{short_id}.{ext}"
