# Build from the REPO ROOT so the shared/ package is in the build context:
#   docker build -f image-service/Dockerfile -t image-service .
FROM python:3.11-slim

WORKDIR /app

COPY image-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code + shared package
COPY image-service/app ./app
COPY shared ./shared

ENV MODEL_BACKEND=mock
EXPOSE 8000

# Production: gunicorn managing uvicorn workers.
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "1", "-b", "0.0.0.0:8000", "--timeout", "300"]
