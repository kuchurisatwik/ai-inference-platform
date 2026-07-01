#!/usr/bin/env bash
#
# Phase 2 + 3 — Server provisioning + AI runtime.
# Run ON an EC2 instance (Ubuntu 22.04/24.04). Idempotent: safe to re-run.
#
#   Image server:  ./provision.sh image
#   Video server:  ./provision.sh video
#
# It updates Ubuntu, installs common packages, verifies the GPU, creates the
# /opt/ai-platform tree, clones/updates the repo, builds the service venv and
# installs Python deps (incl. PyTorch). NVIDIA driver + CUDA install is left to
# you (see the notes it prints) because that depends on your exact AMI.
set -euo pipefail

SERVICE="${1:?usage: provision.sh <image|video>}"
if [[ "$SERVICE" != "image" && "$SERVICE" != "video" ]]; then
  echo "service must be 'image' or 'video'"; exit 1
fi

# ---- Config (override via env) -------------------------------------------
REPO_URL="${REPO_URL:-https://github.com/CHANGE_ME/ai-inference-platform.git}"
BASE="${BASE:-/opt/ai-platform}"
REPO_DIR="${REPO_DIR:-$BASE/ai-inference-platform}"
SVC_DIR="$REPO_DIR/${SERVICE}-service"
# PyTorch CUDA build — match your installed CUDA toolkit (cu121 / cu124 / ...)
TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu124}"

echo "==> Provisioning ${SERVICE} server"

# ---- Step 2: update Ubuntu ------------------------------------------------
sudo apt-get update -y
sudo apt-get upgrade -y

# ---- Step 3: common packages ---------------------------------------------
sudo apt-get install -y \
  build-essential git git-lfs curl wget unzip htop tree vim \
  python3-pip python3-venv python3-dev ffmpeg nginx
git lfs install

# ---- Step 4: verify GPU ---------------------------------------------------
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi || true
else
  echo "!! nvidia-smi not found."
  echo "   Install drivers, then re-run:"
  echo "     ubuntu-drivers devices"
  echo "     sudo ubuntu-drivers autoinstall && sudo reboot"
  echo "   And a CUDA toolkit (nvcc --version) matching \$TORCH_INDEX ($TORCH_INDEX)."
fi

# ---- Step 7: project structure -------------------------------------------
sudo mkdir -p "$BASE"
sudo chown -R "$USER":"$USER" "$BASE"
mkdir -p "$BASE/models" "$BASE/logs" "$BASE/temp"

# ---- Clone or update the repo --------------------------------------------
if [[ -d "$REPO_DIR/.git" ]]; then
  echo "==> Updating existing repo at $REPO_DIR"
  git -C "$REPO_DIR" pull --ff-only
else
  echo "==> Cloning $REPO_URL"
  git clone "$REPO_URL" "$REPO_DIR"
fi

# ---- Step 8-11: venv + Python deps ---------------------------------------
cd "$SVC_DIR"
python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip setuptools wheel

echo "==> Installing PyTorch from $TORCH_INDEX"
pip install torch --index-url "$TORCH_INDEX"

echo "==> Installing service requirements"
pip install -r requirements.txt

# The heavy model libs are commented out in requirements.txt so local Windows
# dev stays light. Install them here on the GPU box.
if [[ "$SERVICE" == "image" ]]; then
  pip install diffusers transformers accelerate safetensors \
              sentencepiece huggingface_hub
else
  pip install diffusers transformers accelerate imageio imageio-ffmpeg \
              sentencepiece huggingface_hub
fi

# ---- .env -----------------------------------------------------------------
if [[ ! -f .env ]]; then
  cp .env.example .env
  # switch the backend from mock -> real model
  BACKEND=$([[ "$SERVICE" == "image" ]] && echo flux || echo ltx)
  sed -i "s/^MODEL_BACKEND=.*/MODEL_BACKEND=$BACKEND/" .env
  echo "==> Wrote $SVC_DIR/.env (MODEL_BACKEND=$BACKEND). Edit S3_BUCKET etc."
fi

echo
echo "==> Verifying PyTorch sees the GPU"
python - <<'PY'
import torch
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY

echo
echo "Done. Next:"
echo "  1) Download the model:   deployment/download_models.sh $SERVICE"
echo "  2) Install the service:  see deployment/RUNBOOK.md (systemd + nginx)"
