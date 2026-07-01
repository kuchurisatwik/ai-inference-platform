# Video Service (LTX)

Text-to-video FastAPI service.

## Local dev (Windows, mock backend)

```powershell
cd video-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8001
```

Open http://localhost:8001/docs

## Endpoints

| Method | Path        | Description                       |
| ------ | ----------- | --------------------------------- |
| GET    | `/health`   | Service + GPU status              |
| POST   | `/generate` | Generate a video, return its URL  |

`POST /generate` body:

```json
{ "prompt": "A drone shot over a coastal city at sunset", "num_frames": 49, "fps": 24 }
```

Response:

```json
{ "video_url": "...", "prompt": "...", "num_frames": 49, "fps": 24, "backend": "mock" }
```

## On EC2 with the real model

```bash
git clone <repo> && cd ai-inference-platform/video-service
pip install -r requirements.txt
# install torch (matching CUDA) + uncomment the LTX deps in requirements.txt
# download LTX weights to /opt/models/ltx
export MODEL_BACKEND=ltx
export S3_BUCKET=your-bucket
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8001 --timeout 600
```
