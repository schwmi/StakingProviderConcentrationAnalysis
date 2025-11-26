#!/bin/bash

set -a
source .env
set +a

docker build -t jupyter-image-ml0 .
docker run -p 8888:8888 -e X_API_KEY="${X_API_KEY}" -v .:/home/jovyan/work jupyter-image-ml0
