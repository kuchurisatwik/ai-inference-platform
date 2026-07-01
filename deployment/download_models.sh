#!/usr/bin/env bash
#
# Phase 4 — Download model weights into /opt/models via the Hugging Face CLI.
#
#   Image server:  ./download_models.sh image   # FLUX.1 Schnell -> /opt/models/flux
#   Video server:  ./download_models.sh video   # LTX-Video      -> /opt/models/ltx
#
# Gated/large repos may need a token:  huggingface-cli login   (or export HF_TOKEN)
set -euo pipefail

SERVICE="${1:?usage: download_models.sh <image|video>}"
MODELS_DIR="${MODELS_DIR:-/opt/models}"

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

# Use the CLI from the active venv if present, else pip-install it.
if ! command -v huggingface-cli >/dev/null 2>&1; then
  pip install huggingface_hub
fi

echo "==> Downloading $MODEL_REPO -> $TARGET"
huggingface-cli download "$MODEL_REPO" --local-dir "$TARGET"

echo "==> Done. Point MODEL_PATH at $TARGET in the service .env"
du -sh "$TARGET" || true
