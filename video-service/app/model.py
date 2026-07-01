"""Model loading. Loaded ONCE at startup and kept in GPU memory.

Two backends:
  - "mock": writes a tiny placeholder .mp4 (for local dev on Windows)
  - "ltx":  loads the real LTX video pipeline onto the GPU (on EC2)
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings
from shared.logger import get_logger

log = get_logger("video.model")

_pipeline = None  # module-level singleton — never reloaded per request


def load_model():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    if settings.model_backend == "mock":
        log.info("loading MOCK video backend (no GPU)")
        _pipeline = _MockPipeline()
    else:
        log.info("loading LTX from %s", settings.model_path)
        _pipeline = _load_ltx()

    return _pipeline


def get_pipeline():
    return _pipeline if _pipeline is not None else load_model()


def is_loaded() -> bool:
    return _pipeline is not None


def _load_ltx():
    """Load the real LTX pipeline. Requires torch + diffusers + a GPU."""
    import torch
    from diffusers import LTXPipeline

    pipe = LTXPipeline.from_pretrained(
        settings.model_path, torch_dtype=torch.bfloat16
    )
    pipe = pipe.to("cuda")
    return pipe


class _MockPipeline:
    """Writes a minimal placeholder file so the upload path is exercised locally."""

    def __call__(self, prompt: str, out_path: str, num_frames: int, fps: int, **_):
        # Not a real encoded video — just a deterministic placeholder payload so
        # the save/upload/return-URL flow works without ffmpeg or a GPU.
        Path(out_path).write_bytes(
            f"MOCK-VIDEO\nprompt={prompt}\nframes={num_frames}\nfps={fps}\n".encode()
        )
        return out_path
