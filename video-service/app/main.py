"""Video service entrypoint. Run: uvicorn app.main:app --port 8001"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.model import load_model
from app.routes import router
from shared.logger import get_logger

log = get_logger("video.main", settings.log_level)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEBUI_DIR = _REPO_ROOT / "shared" / "webui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting video-service (backend=%s)", settings.model_backend)
    load_model()
    log.info("model ready")
    yield
    log.info("shutting down video-service")


app = FastAPI(title="Video Service (LTX / Wan)", version="0.1.0", lifespan=lifespan)

# Let the web UI (served from either server) call this API cross-origin.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.include_router(router)

# Serve generated files over HTTP so the browser can preview/download them.
Path(settings.output_folder).mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=settings.output_folder), name="outputs")

# Serve the web console at /ui (and redirect / to it).
app.mount("/ui", StaticFiles(directory=str(_WEBUI_DIR), html=True), name="ui")


@app.get("/")
def root():
    return RedirectResponse(url="/ui/")
