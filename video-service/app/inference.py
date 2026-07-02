"""Inference logic: prompt (+ optional image) -> video -> uploaded -> URL out."""
import base64
import io
import math
import threading

from app.config import settings
from app.model import get_pipeline
from app.schemas import GenerateRequest, GenerateResponse
from app.utils import make_temp_path, upload_and_cleanup
from shared.logger import get_logger

log = get_logger("video.inference")

# Only one generation may touch the GPU at a time. Concurrent requests wait
# here (queue up) instead of running simultaneously and crashing with OOM.
_gpu_lock = threading.Lock()

_DEFAULT_NEGATIVE = (
    "worst quality, inconsistent motion, blurry, jittery, distorted, "
    "low quality, artifacts, warped, overexposed, static"
)


def generate_video(req: GenerateRequest) -> GenerateResponse:
    pipe = get_pipeline()
    log.info("generating video prompt=%r image=%s", req.prompt, bool(req.image))

    tmp_path, filename = make_temp_path()

    with _gpu_lock:
        if settings.model_backend == "mock":
            pipe(
                prompt=req.prompt,
                out_path=tmp_path,
                num_frames=req.num_frames,
                fps=req.fps,
            )
        else:
            import torch
            from diffusers.utils import export_to_video

            generator = None
            if req.seed is not None:
                generator = torch.Generator(device="cuda").manual_seed(req.seed)

            negative = req.negative_prompt or _DEFAULT_NEGATIVE

            if settings.model_backend == "wan":
                result = _run_wan(pipe, req, negative, generator)
            else:  # ltx (text-to-video only)
                result = pipe(
                    prompt=req.prompt,
                    negative_prompt=negative,
                    width=req.width,
                    height=req.height,
                    num_frames=req.num_frames,
                    num_inference_steps=req.steps,
                    guidance_scale=req.guidance_scale,
                    generator=generator,
                    decode_timestep=0.03,
                    decode_noise_scale=0.025,
                )

            export_to_video(result.frames[0], tmp_path, fps=req.fps)

    url = upload_and_cleanup(tmp_path, filename)
    return GenerateResponse(
        video_url=url,
        prompt=req.prompt,
        num_frames=req.num_frames,
        fps=req.fps,
        seed=req.seed,
        backend=settings.model_backend,
    )


def _run_wan(pipes, req, negative, generator):
    """Wan: route to text-to-video or image-to-video (both share one model)."""
    common = dict(
        prompt=req.prompt,
        negative_prompt=negative,
        num_frames=req.num_frames,
        num_inference_steps=req.steps,
        guidance_scale=req.guidance_scale,
        generator=generator,
    )
    if req.image:
        pipe = pipes["i2v"]
        image = _decode_image(req.image)
        height, width = _wan_size(pipe, image, req.width * req.height)
        image = image.resize((width, height))
        log.info("image-to-video at %dx%d", width, height)
        return pipe(image=image, height=height, width=width, **common)

    pipe = pipes["t2v"]
    return pipe(width=req.width, height=req.height, **common)


def _wan_size(pipe, image, max_area):
    """Height/width matching the image aspect ratio, snapped to the model grid."""
    aspect = image.height / image.width
    mod = pipe.vae_scale_factor_spatial * pipe.transformer.config.patch_size[1]
    height = int(round(math.sqrt(max_area * aspect)) // mod * mod)
    width = int(round(math.sqrt(max_area / aspect)) // mod * mod)
    return height, width


def _decode_image(src: str):
    """Load a PIL image from a base64 data URL, raw base64, or an http(s) URL."""
    from PIL import Image

    if src.startswith("http://") or src.startswith("https://"):
        from diffusers.utils import load_image

        return load_image(src).convert("RGB")
    if src.startswith("data:"):
        src = src.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(src))).convert("RGB")
