# Image Service (FLUX)

Text-to-image FastAPI service.

## Local dev (Windows, mock backend)

```powershell
cd image-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs

## Endpoints

| Method | Path        | Description                        |
| ------ | ----------- | ---------------------------------- |
| GET    | `/health`   | Service + GPU status               |
| POST   | `/generate` | Generate an image, return its URL  |

`POST /generate` body:

```json
{ "prompt": "Luxury jewellery photography", "width": 1024, "height": 1024 }
```

Response:

```json
{ "image_url": "...", "prompt": "...", "seed": null, "backend": "mock" }
```

## On EC2 with the real model

```bash
git clone <repo> && cd ai-inference-platform/image-service
pip install -r requirements.txt
# install torch (matching CUDA) + uncomment the FLUX deps in requirements.txt
# download FLUX weights to /opt/models/flux
export MODEL_BACKEND=flux
export S3_BUCKET=your-bucket
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8000 --timeout 300
```
