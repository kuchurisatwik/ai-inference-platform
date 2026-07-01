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

    image = pipe(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        width=req.width,
        height=req.height,
        num_inference_steps=req.steps,
        seed=req.seed,
    )
    # Real diffusers pipelines return an object with `.images`; the mock returns
    # a PIL image directly. Normalise both.
    if hasattr(image, "images"):
        image = image.images[0]

    url = save_and_upload(image)
    return GenerateResponse(
        image_url=url,
        prompt=req.prompt,
        seed=req.seed,
        backend=settings.model_backend,
    )
