# AI Inference Platform

Two independent FastAPI microservices for AI generation:

- **image-service** — text-to-image (FLUX on the GPU box; a mock backend for local dev)
- **video-service** — text-to-video (LTX on the GPU box; a mock backend for local dev)

Both share the `shared/` package (S3 upload, logging, helpers) and are deployed
independently to their own EC2 instances, but live in one repository.

```
                   Windows Dev PC
                         │
                  VS Code + Git
                         │
                    git push
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
    Image EC2                        Video EC2
   (FLUX + FastAPI)               (LTX + FastAPI)
      /generate                      /generate
```

## Layout

```
ai-inference-platform/
├── image-service/          # FLUX text-to-image API
│   └── app/{main,routes,inference,model,schemas,config,utils}.py
├── video-service/          # LTX text-to-video API
│   └── app/{main,routes,inference,model,schemas,config,utils}.py
├── shared/                 # s3.py, logger.py, helpers.py (used by both)
├── docker-compose.yml
└── README.md
```

## Run locally (Windows, no GPU needed)

Each service ships a **mock** model backend so you can build and test the API
without downloading FLUX/LTX. `MODEL_BACKEND=mock` is the default in
`.env.example`.

```powershell
cd image-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Then open http://localhost:8000/docs and try `POST /generate`.

Video service is identical on port 8001:

```powershell
cd video-service
uvicorn app.main:app --reload --port 8001
```

## On EC2 (real models)

Set `MODEL_BACKEND=flux` (image) / `MODEL_BACKEND=ltx` (video) and point
`MODEL_PATH` at the downloaded weights. See each service's README.

## Quick test

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Luxury jewellery photography, studio lighting"}'
```
