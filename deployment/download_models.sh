#!/usr/bin/env bash
#
# Phase 4 — Download ONLY the diffusers-format model files into /opt/models.
#
#   Image server:  ./download_models.sh image   # FLUX.1 Schnell -> /opt/models/flux
#   Video server:  ./download_models.sh video   # LTX-Video      -> /opt/models/ltx
#
# These HF repos also ship huge standalone .safetensors checkpoints (LTX has
# 13B files at ~28 GB each) that our diffusers pipeline does NOT use. We match
# only files inside subfolders ("*/*" -> transformer/, vae/, text_encoder/,
# tokenizer/, scheduler/) plus model_index.json, and skip the rest.
#
# Gated repos need a token first:  hf auth login   (or export HF_TOKEN)
set -euo pipefail

SERVICE="${1:?usage: download_models.sh <image|video>}"
BASE="${BASE:-/opt/ai-platform}"
REPO_DIR="${REPO_DIR:-$BASE/ai-inference-platform}"
MODELS_DIR="${MODELS_DIR:-/opt/models}"
PY="$REPO_DIR/${SERVICE}-service/venv/bin/python"   # use the service's venv

# repo id -> local dir (override MODEL_REPO to pin a different checkpoint)
if [[ "$SERVICE" == "image" ]]; then
  MODEL_REPO="${MODEL_REPO:-black-forest-labs/FLUX.1-schnell}"
  TARGET="$MODELS_DIR/flux"
elif [[ "$SERVICE" == "video" ]]; then
  MODEL_REPO="${MODEL_REPO:-Lightricks/LTX-Video}"
  TARGET="$MODELS_DIR/ltx"
else
  echo "service must be 'image' or 'video'"; exit 1
fi

sudo mkdir -p "$MODELS_DIR"
sudo chown -R "$USER":"$USER" "$MODELS_DIR"

echo "==> Downloading diffusers files of $MODEL_REPO -> $TARGET"
"$PY" - "$MODEL_REPO" "$TARGET" <<'PY'
import sys
from huggingface_hub import snapshot_download
repo, target = sys.argv[1], sys.argv[2]
path = snapshot_download(
    repo,
    local_dir=target,
    allow_patterns=["model_index.json", "*/*"],
)
print("downloaded to", path)
PY

echo "==> Done. Point MODEL_PATH at $TARGET in the service .env"
du -sh "$TARGET" || true
