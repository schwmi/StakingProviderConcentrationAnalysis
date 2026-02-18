#!/usr/bin/env bash

set -euo pipefail

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ -z "${X_API_KEY:-}" ]; then
  echo "Missing X_API_KEY."
  echo "Create .env from .env.example or export X_API_KEY in your shell."
  exit 1
fi

IMAGE_NAME="crypto-staking-jupyter"

docker build -t "${IMAGE_NAME}" .
docker run --rm -it \
  -p 8888:8888 \
  -e X_API_KEY="${X_API_KEY}" \
  -v "$(pwd)":/home/jovyan/work \
  "${IMAGE_NAME}"
