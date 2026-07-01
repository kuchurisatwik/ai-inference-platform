"""Inference logic: prompt in -> video generated -> uploaded -> URL out."""
from app.config import settings
from app.model import get_pipeline
from app.schemas import GenerateRequest, GenerateResponse
from app.utils import make_temp_path, upload_and_cleanup
from shared.logger import get_logger

log = get_logger("video.inference")


def generate_video(req: GenerateRequest) -> GenerateResponse:
    pipe = get_pipeline()
    log.info("generating video for prompt=%r", req.prompt)

    tmp_path, filename = make_temp_path()

    if settings.model_backend == "mock":
        pipe(
            prompt=req.prompt,
            out_path=tmp_path,
            num_frames=req.num_frames,
            fps=req.fps,
        )
    else:
        # Real LTX pipeline: produce frames, then encode to mp4.
        import torch
        from diffusers.utils import export_to_video

        generator = None
        if req.seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(req.seed)

        # A default negative prompt noticeably cleans up LTX output.
        negative = req.negative_prompt or (
            "worst quality, inconsistent motion, blurry, jittery, distorted, "
            "low quality, artifacts, warped"
        )

        result = pipe(
            prompt=req.prompt,
            negative_prompt=negative,
            width=req.width,
            height=req.height,
            num_frames=req.num_frames,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance_scale,
            # These two control the VAE decode and remove the coloured
            # streak/shimmer artifacts. LTX-recommended values.
            decode_timestep=0.03,
            decode_noise_scale=0.025,
            generator=generator,
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
