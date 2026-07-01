# Build from the REPO ROOT so the shared/ package is in the build context:
#   docker build -f video-service/Dockerfile -t video-service .
FROM python:3.11-slim

WORKDIR /app

COPY video-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY video-service/app ./app
COPY shared ./shared

ENV MODEL_BACKEND=mock
EXPOSE 8001

CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "1", "-b", "0.0.0.0:8001", "--timeout", "600"]
