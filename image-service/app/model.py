"""Model loading. The model is loaded ONCE at startup and kept in memory.

Two backends:
  - "mock": generates a placeholder image on CPU (for local dev on Windows)
  - "flux": loads the real FLUX pipeline onto the GPU (on EC2)
"""
from __future__ import annotations

from app.config import settings
from shared.logger import get_logger

log = get_logger("image.model")

_pipeline = None  # module-level singleton — never reloaded per request


def load_model():
    """Load the model into memory. Called once on FastAPI startup."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    if settings.model_backend == "mock":
        log.info("loading MOCK image backend (no GPU)")
        _pipeline = _MockPipeline()
    else:
        log.info("loading FLUX from %s", settings.model_path)
        _pipeline = _load_flux()

    return _pipeline


def get_pipeline():
    """Return the loaded pipeline, loading it lazily if needed."""
    return _pipeline if _pipeline is not None else load_model()


def is_loaded() -> bool:
    return _pipeline is not None


def _load_flux():
    """Load FLUX. On a small GPU (e.g. L4 24GB) the 12B transformer is loaded
    in 4-bit (nf4) so it fits; on a big GPU set FLUX_QUANTIZE=false for full
    bf16. CPU offload keeps the T5 encoder off the GPU during denoise.
    """
    import torch
    from diffusers import FluxPipeline

    if settings.flux_quantize:
        from diffusers import FluxTransformer2DModel, BitsAndBytesConfig

        nf4 = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        log.info("loading FLUX transformer in 4-bit (nf4)")
        transformer = FluxTransformer2DModel.from_pretrained(
            settings.model_path,
            subfolder="transformer",
            quantization_config=nf4,
            torch_dtype=torch.bfloat16,
        )
        pipe = FluxPipeline.from_pretrained(
            settings.model_path,
            transformer=transformer,
            torch_dtype=torch.bfloat16,
        )
        if settings.flux_cpu_offload:
            # Only for very tight VRAM: slow (per-request CPU<->GPU transfers).
            pipe.enable_model_cpu_offload()
        else:
            # nf4 transformer (~7GB) is already on the GPU; put the rest there
            # too (~20GB total, fits a 24GB card) so there are NO slow per-
            # request transfers. This is the fast path.
            pipe.text_encoder.to("cuda")
            pipe.text_encoder_2.to("cuda")
            pipe.vae.to("cuda")
        pipe.vae.enable_tiling()
        return pipe

    pipe = FluxPipeline.from_pretrained(
        settings.model_path, torch_dtype=torch.bfloat16
    )
    pipe = pipe.to("cuda")
    return pipe


class _MockPipeline:
    """Tiny stand-in that returns a solid-colour PIL image derived from the prompt."""

    def __call__(self, prompt: str, width: int, height: int, seed: int | None = None, **_):
        from PIL import Image

        # Deterministic colour from the prompt + seed so output is reproducible.
        base = sum(ord(c) for c in prompt) + (seed or 0)
        colour = (base * 53 % 256, base * 97 % 256, base * 151 % 256)
        return Image.new("RGB", (width, height), colour)
