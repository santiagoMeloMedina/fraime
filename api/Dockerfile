# Build from inside api/:  docker build -t fraime-api .
# Run with GPU access:      docker run --gpus all -p 8000:8000 --env-file .env fraime-api
#
# This base image ships Python + a CUDA-enabled torch build already installed, so
# `pip install -r requirements.txt` below only adds the rest — torch is already
# satisfied (unpinned in requirements.txt) and won't be reinstalled with a
# CPU-only wheel. Pick a tag matching your target GPU driver/CUDA version:
# https://hub.docker.com/r/pytorch/pytorch/tags
#
# For CPU-only use (dev/testing — real generation on CPU is impractically slow
# for these models, see api/README.md), swap the FROM line for `python:3.11-slim`.
FROM pytorch/pytorch:2.13.0-cuda12.6-cudnn9-runtime

WORKDIR /app

# Copied separately so this layer only rebuilds when dependencies actually change.
COPY requirements.txt api/requirements.txt
RUN pip install --no-cache-dir --break-system-packages --upgrade pip \
    && pip install --no-cache-dir --break-system-packages -r api/requirements.txt \
    && pip install --no-cache-dir --break-system-packages --no-deps chatterbox-tts

COPY . api/

# Model weights and generated videos are large and should live on a mounted
# volume, not baked into (or lost with) the container's writable layer.
ENV GENERATION_MODEL_CACHE_DIR=/data/models \
    GENERATION_OUTPUT_DIR=/data/generated
RUN mkdir -p /data/models /data/generated \
    && useradd --create-home fraime \
    && chown -R fraime:fraime /app /data
VOLUME ["/data/models", "/data/generated"]
USER fraime

EXPOSE 8000

# No --reload here (that's uvicorn's dev-mode file watcher); single worker
# since one GPU-resident model per process is the right shape for this app —
# multiple workers would each try to load their own copy into VRAM.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
