# Fraime API

Video generation engine + model detection engine for Fraime. Detects your
hardware, picks the best open source video model it can actually run, and
generates video from a structured prompt.

## Features

0. **Video generation API with customizable models** — a single `/generate`
   endpoint that works with any `diffusers`-compatible Hugging Face model.
   Pass `model` explicitly to pin one, or omit it and let the hardware
   detector pick automatically. Generation itself is tunable per request:
   duration, fps, resolution, seed, denoising steps, and memory/performance
   trade-offs (CPU offload, VAE tiling, VRAM safety margin).
1. **Its own model catalog, with a customization tool** — models ship in
   [`instructions/models.json`](instructions/models.json) (capabilities,
   VRAM requirements, license, style strengths). Extend it — add, edit,
   delete, or wipe entries — with the interactive `define` tool instead of
   hand-editing JSON.
2. **Prompt structure per video type, with the same customization tool** —
   [`instructions/rules.json`](instructions/rules.json) defines the fields,
   style guidance, and evaluation criteria for each video type (`pixar`,
   `action`, `ugc_product_review`, `commercial_product_ad`, ...). Also
   editable through `define`.
3. **Hardware detector for optimal model selection** — detects your
   accelerator (CUDA/MPS/CPU), VRAM, system RAM, and disk space, then matches
   it directly against each model's real capabilities and VRAM figures — no
   coarse hardware "tiers," just exact numbers compared to exact numbers.
4. **Introspection endpoints** — `GET /config/models` and `GET /config/rules`
   return the exact contents of `instructions/models.json` and
   `instructions/rules.json` the running instance is using, so a client never
   has to guess or hardcode what's configured server-side.

## Install

From the repo root:

```bash
make install-api
```

Or from `api/` directly:

```bash
make install
```

This creates a `.venv` inside `api/` and installs `requirements.txt` into it.

## Run

```bash
make run-api        # from repo root
# or
make run            # from api/
```

Starts the API with `uvicorn api.main:app --reload` on
`http://127.0.0.1:8000`.

## Define models and rules

```bash
make define-api      # from repo root
# or
make define           # from api/
```

Launches the interactive catalog editor
([`scripts/instructions/define.py`](scripts/instructions/define.py)). Pick
`models` or `rules`, then a numbered list of existing entries lets you edit
or delete one, or add a new one / erase all. Each instruction type is driven
by its own schema file next to the script
(`scripts/instructions/models_schema.json`,
`scripts/instructions/rules_schema.json`) — the data itself lives in
`instructions/`.

## Docker

A [`Dockerfile`](Dockerfile) is included, built on a CUDA-enabled PyTorch base
image so it can actually use a GPU inside the container:

```bash
cd api
docker build -t fraime-api .
docker run --gpus all -p 8000:8000 --env-file .env fraime-api
```

Optionally, skip building it yourself and pull the published image instead:

```bash
docker pull santsq18/framie-api:latest
docker run --gpus all -p 8000:8000 --env-file .env santsq18/framie-api:latest
```

**This Dockerfile will not work with MPS.** Docker containers can't access
Apple's Metal backend, so running this image on a Mac — even one with a
capable Apple Silicon GPU — always falls back to CPU generation inside the
container, regardless of what the detector reports on the host. This image
is meant for a Linux host with an NVIDIA GPU (e.g. one of the AWS instances
discussed for this project), not for local Mac development; use `make run`
(outside Docker) there instead.

## Environment variables

Copy `api/.env-example` to `api/.env` and configure as needed — every
setting has a sensible default if left unset.

| Variable | Default | What it controls |
|---|---|---|
| `GENERATION_DURATION_S` | `5.0` | Default clip duration in seconds |
| `GENERATION_FPS` | `24` | Default frames per second |
| `GENERATION_RESOLUTION` | `1024x576` | Default target resolution |
| `GENERATION_SEED` | unset | Default seed for reproducible generation |
| `GENERATION_MODEL_CACHE_DIR` | Hugging Face's default cache | **Where downloaded model weights are stored.** Models are several to tens of GB each — point this at a volume with real disk space, especially if you'll pull more than one model from the catalog. |
| `GENERATION_OUTPUT_DIR` | `.generated` | **Where generated `.mp4` files are written.** Created automatically if it doesn't exist; grows with every request, so worth pointing somewhere you're comfortable letting fill up (or cleaning periodically). |
| `DETECTOR_CATALOG_PATH` | `instructions/models.json` | Path to the model catalog the detector matches against |
| `PROMPT_RULES_PATH` | `instructions/rules.json` | Path to the prompt rules the `/config/rules` endpoint serves |
| `AUTH_API_KEY` | unset | If set, every request must send `Authorization: Bearer <key>` matching it. **Unset by default, meaning the API is open with no auth** — set this before exposing the API beyond your own machine. |
| `CLOUD_S3_OUTPUT_BUCKET` | unset | If set, generated videos are uploaded to this S3 bucket instead of being kept on the host — see [S3 output](#s3-output) below. |
| `CLOUD_S3_OUTPUT_PREFIX` | unset (bucket root) | Key prefix to upload under within `CLOUD_S3_OUTPUT_BUCKET`. Only used if that bucket is set. |

## Using the API

Once running, `POST /generate` with a video type, prompt fields, and
generation params. `model` is optional — omit it to let the hardware
detector pick automatically.

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "video_type": "commercial_product_ad",
    "fields": {
      "subject": "a matte black ceramic coffee mug with a minimalist logo",
      "action": "slowly rotates in place as steam rises gently from the coffee inside",
      "scene": "a clean marble kitchen counter with soft blurred greenery in the background",
      "camera": "smooth slow orbit around the product, shallow depth of field",
      "lighting": "controlled studio softbox lighting, warm highlight on the ceramic surface",
      "style": "polished commercial product photography style, crisp reflections, shallow focus",
      "negative_prompt": "blurry, low quality, warped shape, extra objects, morphing, watermark, text overlay"
    },
    "params": {
      "duration_s": 5,
      "fps": 16,
      "resolution": "768x512"
    }
  }'
```

If `AUTH_API_KEY` is set, add
`-H "Authorization: Bearer <your-key>"` to the request.

The response reports which model actually ran, since it may not be the one
you'd expect if it was auto-selected:

```json
{
  "video_path": ".generated/<uuid>.mp4",
  "model": "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
  "s3_bucket": null,
  "s3_key": null,
  "s3_url": null
}
```

### S3 output

Set `CLOUD_S3_OUTPUT_BUCKET` to upload the generated video to S3 instead of
leaving it on the host. `CLOUD_S3_OUTPUT_PREFIX` is optional — leave it unset
to upload at the bucket root. Credentials are resolved the standard boto3
way (environment, `~/.aws/credentials`, instance role, etc.) — there's no
separate credential setting.

When configured:
- Before generation starts, the API does a test write to the destination
  key to confirm it has access — if that fails, the request is rejected
  immediately with **403 Forbidden**, instead of only finding out after
  several minutes of generation.
- On success, the video is uploaded to that key (replacing the test write),
  `video_path` is omitted from the response (`null`), and `s3_bucket`,
  `s3_key`, and a presigned `s3_url` (valid for 1 hour, enough to download
  the video) are populated instead:

```json
{
  "video_path": null,
  "model": "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
  "s3_bucket": "my-fraime-videos",
  "s3_key": "outputs/.<uuid>.mp4",
  "s3_url": "https://my-fraime-videos.s3.amazonaws.com/outputs/.<uuid>.mp4?X-Amz-..."
}
```

### Inspecting the running configuration

`GET /config/models` returns the full contents of
[`instructions/models.json`](instructions/models.json) — the exact catalog
this instance auto-selects from — and `GET /config/rules` returns the full
contents of [`instructions/rules.json`](instructions/rules.json), the prompt
structure/evaluation criteria per video type. Both require the same
`Authorization: Bearer <key>` header as `/generate` if `AUTH_API_KEY` is set.

```bash
curl http://127.0.0.1:8000/config/models
curl http://127.0.0.1:8000/config/rules
```

### Sample output

Generated with the exact request above — the model picked will depend on
your own hardware, so this won't be byte-identical to what you get locally:

![assets/demo.gif](assets/demo.gif)

(If your viewer doesn't render inline video: [`assets/demo.mp4`](assets/demo.mp4).)
