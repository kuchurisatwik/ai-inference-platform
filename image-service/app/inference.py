"""Inference logic: prompt in -> image generated -> uploaded -> URL out."""
from app.config import settings
from app.model import get_pipeline
from app.schemas import GenerateRequest, GenerateResponse
from app.utils import save_and_upload
from shared.logger import get_logger

log = get_logger("image.inference")


def generate_image(req: GenerateRequest) -> GenerateResponse:
    pipe = get_pipeline()
    log.info("generating image for prompt=%r", req.prompt)

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
            guidance_scale=0.0,  # FLUX.1 Schnell is distilled; no CFG
            generator=generator,
        )
        image = result.images[0]

    url = save_and_upload(image)
    return GenerateResponse(
        image_url=url,
        prompt=req.prompt,
        seed=req.seed,
        backend=settings.model_backend,
    )
