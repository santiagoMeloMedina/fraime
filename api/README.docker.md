# Fraime API — Docker image

Video generation engine + hardware model detector for
[Fraime](https://github.com/santiagoMeloMedina/fraime), an open source AI
video generation platform. Detects the accelerator available inside the
container, picks the best open source video model it can run, and serves
generation over HTTP.

## Pull

```bash
docker pull santsq18/framie-api:latest
```

## Run

Requires an NVIDIA GPU and the NVIDIA Container Toolkit on the host.

```bash
docker run --gpus all -p 8000:8000 --env-file .env santsq18/framie-api:latest
```

The API is then available at `http://localhost:8000`.

**GPU only — no MPS support.** Docker containers cannot access Apple's
Metal backend, so running this image on a Mac (even Apple Silicon) always
falls back to CPU generation inside the container regardless of host
hardware. CPU generation is impractically slow for these models. This image
targets a Linux host with an NVIDIA GPU.

## Volumes

Model weights and generated videos are large and should live on mounted
volumes rather than the container's writable layer:

```bash
docker run --gpus all -p 8000:8000 --env-file .env \
  -v fraime-models:/data/models \
  -v fraime-output:/data/generated \
  santsq18/framie-api:latest
```

| Path | Contents |
|---|---|
| `/data/models` | Downloaded model weights (several to tens of GB per model) |
| `/data/generated` | Generated `.mp4` output files |

## Environment variables

Pass with `--env-file .env` or individual `-e` flags. Every setting has a
sensible default if left unset.

| Variable | Default | What it controls |
|---|---|---|
| `GENERATION_DURATION_S` | `5.0` | Default clip duration in seconds |
| `GENERATION_FPS` | `24` | Default frames per second |
| `GENERATION_RESOLUTION` | `1024x576` | Default target resolution |
| `GENERATION_SEED` | unset | Default seed for reproducible generation |
| `GENERATION_MODEL_CACHE_DIR` | `/data/models` | Where downloaded model weights are stored — mount a volume here |
| `GENERATION_OUTPUT_DIR` | `/data/generated` | Where generated `.mp4` files are written — mount a volume here |
| `DETECTOR_CATALOG_PATH` | `instructions/models.json` | Path to the model catalog the detector matches against |
| `PROMPT_RULES_PATH` | `instructions/rules.json` | Path to the prompt rules the `/config/rules` endpoint serves |
| `AUTH_API_KEY` | unset | If set, every request must send `Authorization: Bearer <key>` matching it. **Unset by default — the API is open with no auth.** Set this before exposing the container beyond your own machine. |
| `CLOUD_S3_OUTPUT_BUCKET` | unset | If set, generated videos are uploaded to this S3 bucket instead of staying in `/data/generated` |
| `CLOUD_S3_OUTPUT_PREFIX` | unset (bucket root) | Key prefix to upload under within `CLOUD_S3_OUTPUT_BUCKET` |

## Port

`8000` — the `uvicorn` server (single worker; one GPU-resident model per
process is the intended shape, so don't scale workers per container without
also scaling GPUs).

## Build it yourself

```bash
git clone https://github.com/santiagoMeloMedina/fraime.git
cd fraime/api
docker build -t fraime-api .
docker run --gpus all -p 8000:8000 --env-file .env fraime-api
```

Base image is `pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime` (CUDA 12.1,
cuDNN 9). If your GPU driver needs a different CUDA version, edit the `FROM`
line in the `Dockerfile` to match a tag from
[hub.docker.com/r/pytorch/pytorch/tags](https://hub.docker.com/r/pytorch/pytorch/tags)
before building.

## Full documentation

See the [project README](https://github.com/santiagoMeloMedina/fraime/blob/main/api/README.md)
for the generation API, model catalog, and prompt rules.
