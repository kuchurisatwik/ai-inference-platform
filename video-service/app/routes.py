"""HTTP routes only — no AI logic lives here."""
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.inference import generate_video
from app.model import is_loaded
from app.schemas import GenerateRequest, GenerateResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    gpu = "unavailable"
    if settings.model_backend != "mock":
        try:
            import torch

            gpu = "available" if torch.cuda.is_available() else "unavailable"
        except ImportError:
            gpu = "unavailable"

    return HealthResponse(
        status="healthy",
        gpu=gpu,
        backend=settings.model_backend,
        model_loaded=is_loaded(),
    )


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    try:
        return generate_video(req)
    except Exception as exc:  # noqa: BLE001 - surface a clean 500 to the client
        raise HTTPException(status_code=500, detail=str(exc)) from exc
