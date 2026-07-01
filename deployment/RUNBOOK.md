# Deployment Runbook

End-to-end steps to turn a fresh Ubuntu GPU EC2 instance into a running
inference API. Do the **image server** first, then repeat for **video**.

All scripts live in `deployment/` and are idempotent (safe to re-run).

Paths used throughout:

| Thing        | Path                                              |
| ------------ | ------------------------------------------------- |
| Base         | `/opt/ai-platform`                                |
| Repo         | `/opt/ai-platform/ai-inference-platform`          |
| Image venv   | `.../image-service/venv`                          |
| Video venv   | `.../video-service/venv`                          |
| Models       | `/opt/models/flux`, `/opt/models/ltx`             |

---

## Phase 2 + 3 — Provision + AI runtime

SSH in, then:

```bash
# one-time: get the repo so you have the scripts
sudo mkdir -p /opt/ai-platform && sudo chown -R $USER:$USER /opt/ai-platform
git clone https://github.com/CHANGE_ME/ai-inference-platform.git /opt/ai-platform/ai-inference-platform
cd /opt/ai-platform/ai-inference-platform

# image server:
REPO_URL=https://github.com/CHANGE_ME/ai-inference-platform.git \
  bash deployment/provision.sh image
```

If `nvidia-smi` fails, the script tells you to install drivers:

```bash
ubuntu-drivers devices
sudo ubuntu-drivers autoinstall
sudo reboot            # reconnect afterwards, then re-run provision.sh
```

Set `TORCH_INDEX` to match your CUDA (`nvcc --version`), e.g.
`TORCH_INDEX=https://download.pytorch.org/whl/cu121 bash deployment/provision.sh image`.

**Checkpoint:** the script prints `cuda available: True` and the GPU name.

---

## Phase 4 — Download the model

```bash
# image server (FLUX.1 Schnell -> /opt/models/flux)
bash deployment/download_models.sh image
# huggingface-cli login   # first, if the repo is gated
```

Confirm `.env` points at it: `MODEL_PATH=/opt/models/flux`.

---

## Phase 5 — Run the API

Quick manual check (foreground):

```bash
cd /opt/ai-platform/ai-inference-platform/image-service
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
# in another shell:
curl -s localhost:8000/health
```

Then install it as a managed service (Phase 8, do it now):

```bash
sudo cp deployment/systemd/image-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now image-service
systemctl status image-service --no-pager
```

---

## Phase 6 — S3 uploads / pre-signed URLs

Give the instance an **IAM role** with `s3:PutObject` (+ `s3:GetObject` for
pre-signing) on your bucket — no keys on disk. Then in the service `.env`:

```env
S3_BUCKET=your-bucket
AWS_REGION=us-east-1
S3_PRESIGN=true        # return time-limited URLs
S3_URL_EXPIRY=3600
```

`sudo systemctl restart image-service` to apply.

---

## Phase 7 — HTTPS + domain

```bash
sudo cp deployment/nginx/image-service.conf /etc/nginx/sites-available/image-service
sudo ln -sf /etc/nginx/sites-available/image-service /etc/nginx/sites-enabled/
# edit server_name to your domain, then:
sudo nginx -t && sudo systemctl reload nginx

# point an A record at the Elastic IP, then:
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d image.yourdomain.com
```

Security group: allow 80/443 from the internet; 8000/8001 stay bound to
127.0.0.1 (nginx proxies to them) — do **not** open them publicly.

---

## Phase 8 — Verify in production

```bash
curl -s https://image.yourdomain.com/health
curl -s -X POST https://image.yourdomain.com/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Luxury jewellery photography, studio lighting"}'
```

Logs & health:

```bash
journalctl -u image-service -f
nvidia-smi              # GPU utilisation while generating
htop
```

---

## Repeat for the video server

Identical, swapping `image` -> `video`, port `8000` -> `8001`,
FLUX -> LTX, `/generate` returns `video_url`:

```bash
REPO_URL=... bash deployment/provision.sh video
bash deployment/download_models.sh video
sudo cp deployment/systemd/video-service.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now video-service
sudo cp deployment/nginx/video-service.conf /etc/nginx/sites-available/video-service
sudo ln -sf /etc/nginx/sites-available/video-service /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d video.yourdomain.com
```

---

## Redeploying after a code change

```bash
cd /opt/ai-platform/ai-inference-platform && git pull
sudo systemctl restart image-service    # or video-service
```

## Phase 2 checklist

| Task                        | Where |
| --------------------------- | ----- |
| Ubuntu updated              | provision.sh |
| Common packages installed   | provision.sh |
| GPU detected (`nvidia-smi`) | provision.sh (Step 4) |
| CUDA / driver               | manual if missing |
| Project directories created | provision.sh (Step 7) |
| venv + pip                  | provision.sh (Step 8-9) |
| PyTorch + GPU visible       | provision.sh (verify block) |
| AI libraries installed      | provision.sh (Step 11) |
