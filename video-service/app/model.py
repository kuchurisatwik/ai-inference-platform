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
    elif settings.model_backend == "wan":
        log.info("loading Wan 2.2 from %s", settings.model_path)
        _pipeline = _load_wan()
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


def _load_wan():
    """Load Wan 2.2 TI2V-5B for BOTH text-to-video and image-to-video.

    One set of weights serves both: the image-to-video pipeline is built from
    the text-to-video one via `from_pipe`, so it costs no extra VRAM. Returns a
    dict {"t2v": WanPipeline, "i2v": WanImageToVideoPipeline}.

    The VAE is loaded in float32 (Wan's recommendation); the rest in bfloat16.
    """
    import torch
    from diffusers import WanPipeline, WanImageToVideoPipeline, AutoencoderKLWan

    vae = AutoencoderKLWan.from_pretrained(
        settings.model_path, subfolder="vae", torch_dtype=torch.float32
    )
    t2v = WanPipeline.from_pretrained(
        settings.model_path, vae=vae, torch_dtype=torch.bfloat16
    )
    # Force the big components to bf16. Some Wan checkpoints otherwise load the
    # transformer/text-encoder in fp32, which nearly fills a 48GB GPU by itself
    # (~44GB) and leaves no room to generate. bf16 halves that to ~24GB.
    t2v.transformer.to(torch.bfloat16)
    t2v.text_encoder.to(torch.bfloat16)

    if settings.wan_cpu_offload:
        # Fallback for tight VRAM: offload idle components to CPU (slower).
        t2v.enable_model_cpu_offload()
    else:
        t2v.to("cuda")
    # Tile/slice the VAE decode so it doesn't spike on many frames.
    t2v.vae.enable_tiling()
    t2v.vae.enable_slicing()

    # Image-to-video must reuse the SAME weight objects (no extra VRAM).
    # Constructing from t2v.components shares them; from_pipe was duplicating
    # the transformer + text encoder (~21GB extra). Skipped for the 14B T2V
    # model, which has no image-to-video components.
    i2v = None
    if settings.wan_i2v:
        try:
            i2v = WanImageToVideoPipeline(**t2v.components)
        except Exception as exc:  # noqa: BLE001
            log.warning("i2v via components failed (%s); falling back to from_pipe", exc)
            i2v = WanImageToVideoPipeline.from_pipe(t2v)

    if torch.cuda.is_available():
        log.info("Wan loaded; GPU memory ~%.1f GB",
                 torch.cuda.memory_allocated() / 1e9)
    return {"t2v": t2v, "i2v": i2v}


class _MockPipeline:
    """Writes a minimal placeholder file so the upload path is exercised locally."""

    def __call__(self, prompt: str, out_path: str, num_frames: int, fps: int, **_):
        # Not a real encoded video — just a deterministic placeholder payload so
        # the save/upload/return-URL flow works without ffmpeg or a GPU.
        Path(out_path).write_bytes(
            f"MOCK-VIDEO\nprompt={prompt}\nframes={num_frames}\nfps={fps}\n".encode()
        )
        return out_path
