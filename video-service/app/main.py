"""Video service entrypoint. Run: uvicorn app.main:app --port 8001"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.model import load_model
from app.routes import router
from shared.logger import get_logger

log = get_logger("video.main", settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting video-service (backend=%s)", settings.model_backend)
    load_model()
    log.info("model ready")
    yield
    log.info("shutting down video-service")


app = FastAPI(title="Video Service (LTX)", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def root():
    return {"service": "video", "docs": "/docs", "generate": "POST /generate"}
