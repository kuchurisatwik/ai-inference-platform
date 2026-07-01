"""Request/response models for the video service."""
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, examples=["A drone shot over a coastal city at sunset"])
    negative_prompt: str = Field("", examples=["blurry, distorted"])
    width: int = Field(768, ge=256, le=1280)
    height: int = Field(512, ge=256, le=1280)
    num_frames: int = Field(49, ge=1, le=257)
    fps: int = Field(24, ge=1, le=60)
    steps: int = Field(40, ge=1, le=100)
    guidance_scale: float = Field(3.0, ge=1.0, le=10.0,
                                  description="How strongly to follow the prompt; 3-4 is the LTX sweet spot")
    seed: int | None = Field(None, description="Set for reproducible output")


class GenerateResponse(BaseModel):
    video_url: str
    prompt: str
    num_frames: int
    fps: int
    seed: int | None = None
    backend: str


class HealthResponse(BaseModel):
    status: str
    gpu: str
    backend: str
    model_loaded: bool
