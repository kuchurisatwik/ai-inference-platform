"""Image service entrypoint. Run: uvicorn app.main:app --port 8000"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.model import load_model
from app.routes import router
from shared.logger import get_logger

log = get_logger("image.main", settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once, at startup — never per request.
    log.info("starting image-service (backend=%s)", settings.model_backend)
    load_model()
    log.info("model ready")
    yield
    log.info("shutting down image-service")


app = FastAPI(title="Image Service (FLUX)", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def root():
    return {"service": "image", "docs": "/docs", "generate": "POST /generate"}
