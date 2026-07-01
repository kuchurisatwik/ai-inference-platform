"""Request/response models for the image service."""
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, examples=["Luxury jewellery photography"])
    negative_prompt: str = Field("", examples=["blurry, low quality"])
    width: int = Field(1024, ge=256, le=2048)
    height: int = Field(1024, ge=256, le=2048)
    steps: int = Field(4, ge=1, le=100)  # FLUX.1-schnell is distilled to ~4 steps
    seed: int | None = Field(None, description="Set for reproducible output")


class GenerateResponse(BaseModel):
    image_url: str
    prompt: str
    seed: int | None = None
    backend: str


class HealthResponse(BaseModel):
    status: str
    gpu: str
    backend: str
    model_loaded: bool
