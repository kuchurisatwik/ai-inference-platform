"""Inference logic: prompt in -> image generated -> uploaded -> URL out."""
import threading

from app.config import settings
from app.model import get_pipeline
from app.schemas import GenerateRequest, GenerateResponse
from app.utils import save_and_upload
from shared.logger import get_logger

log = get_logger("image.inference")

# Only one generation may touch the GPU at a time. Concurrent requests wait
# here (queue up) instead of running simultaneously and crashing with OOM.
_gpu_lock = threading.Lock()


def generate_image(req: GenerateRequest) -> GenerateResponse:
    pipe = get_pipeline()
    log.info("generating image for prompt=%r", req.prompt)

    with _gpu_lock:
        if settings.model_backend == "mock":
            image = pipe(prompt=req.prompt, width=req.width, height=req.height, seed=req.seed)
        else:
            import torch

            # FLUX uses a torch.Generator for reproducibility, not a `seed` kwarg.
            generator = None
            if req.seed is not None:
                generator = torch.Generator(device="cuda").manual_seed(req.seed)

            result = pipe(
                prompt=req.prompt,
                width=req.width,
                height=req.height,
                num_inference_steps=req.steps,
                guidance_scale=req.guidance_scale,  # schnell: 0.0 (no CFG); dev: ~3.5
                generator=generator,
            )
            image = result.images[0]

    # Upload happens outside the lock so the next request's GPU work can start
    # while this one is uploading.
    url = save_and_upload(image)
    return GenerateResponse(
        image_url=url,
        prompt=req.prompt,
        seed=req.seed,
        backend=settings.model_backend,
    )
