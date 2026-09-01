# Fraime API

Video, image, and voice generation engine + model detection engine for
Fraime. Detects your hardware, picks the best open source model it can
actually run, and generates video, image, or voice output from a prompt.

## Features

- **`POST /generate`** — works with any `diffusers`-compatible Hugging Face
  model for video/image, and with chatterbox TTS for voice. Set `media_type`
  to `"video"`, `"image"`, or `"voice"` to pick the request shape and
  generation handler; pass `model` (video/image) to pin an exact HF repo id,
  or `variant` (voice — `base`/`turbo`/`multilingual`, a fixed set of
  chatterbox classes, not an arbitrary repo) to pin one; omit either to
  auto-select by hardware. Tunable per request: duration/fps/resolution
  (video), width/height (image), or exaggeration/cfg_weight/temperature
  (voice), seed (video/image), CPU offload/VAE tiling (video/image), VRAM
  safety margin.
- **Model catalog** — [`instructions/models.json`](instructions/models.json)
  (media type, capabilities, VRAM requirements, license, style strengths),
  editable with the `define` tool.
- **Structured prompts** (video/image only) — `fields` (subject, scene,
  camera, lighting, style, ...) instead of a raw prompt string, compiled
  server-side into the actual model prompt. Video fields are per-video-type
  (`pixar`, `action`, `ugc_product_review`, `commercial_product_ad`, ...);
  image fields are a single fixed set (subject, scene, camera, lighting,
  style, action, color_palette, negative_prompt). Both are documented and
  scored against evaluation criteria in the same
  [`instructions/rules.json`](instructions/rules.json) — video under
  `shared`/`types`, image under `image_fields`/`image_evaluation_criteria` —
  editable with `define`. Voice takes `text` directly (no structured
  fields/rules — chatterbox's input is literal spoken text, not a compiled
  scene description).
- **Hardware detector** — reads accelerator (CUDA/MPS/CPU), VRAM, system RAM,
  and disk space, and matches those exact figures against each catalog
  model's requirements.
- **`GET /config/models`, `GET /config/rules`** — return the running
  instance's `instructions/models.json` and `instructions/rules.json` in
  full (all media types together; the caller picks out what it needs).

## Install

From the repo root:

```bash
make install-api
```

Or from `api/` directly:

```bash
make install
```

This creates a `.venv` inside `api/`, installs `requirements.txt`, then
installs `chatterbox-tts` separately with `--no-deps`
([`scripts/install.sh`](scripts/install.sh)) — `chatterbox-tts` hard-pins
older `diffusers`/`transformers`/`torch` versions that would otherwise
downgrade and break video/image generation. Reinstalling `chatterbox-tts`
normally will reintroduce that conflict.

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
`models` or `rules`; `rules` opens a sub-menu since `instructions/rules.json`
holds two independent collections — video types (`types`) and image
evaluation criteria (`image_evaluation_criteria`) — then edit, delete, add,
or wipe entries within whichever you pick. Schemas:
`scripts/instructions/models_schema.json`,
`scripts/instructions/rules_schema.json`. Data: `instructions/`.

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
Apple's Metal backend, so this image falls back to CPU generation on a Mac
regardless of the host's GPU. Use it on a Linux host with an NVIDIA GPU; on
Mac use `make run` outside Docker instead.

## Environment variables

Copy `api/.env-example` to `api/.env` and configure as needed — every
setting has a sensible default if left unset.

| Variable | Default | What it controls |
|---|---|---|
| `GENERATION_DURATION_S` | `5.0` | Default clip duration in seconds |
| `GENERATION_FPS` | `24` | Default frames per second |
| `GENERATION_RESOLUTION` | `1024x576` | Default target resolution |
| `GENERATION_SEED` | unset | Default seed for reproducible generation |
| `GENERATION_MODEL_CACHE_DIR` | Hugging Face's default cache | Where downloaded video/image model weights are stored. Not honored for voice — chatterbox always uses Hugging Face's default cache. |
| `GENERATION_OUTPUT_DIR` | `.generated` | Where generated `.mp4`/`.png`/`.wav` files are written; created automatically |
| `DETECTOR_CATALOG_PATH` | `instructions/models.json` | Path to the model catalog the detector matches against |
| `PROMPT_RULES_PATH` | `instructions/rules.json` | Path to the prompt rules (both video and image) that `/config/rules` serves |
| `AUTH_API_KEY` | unset (no auth) | If set, requests must send `Authorization: Bearer <key>` matching it |
| `CLOUD_S3_OUTPUT_BUCKET` | unset | If set, generated files upload to this S3 bucket instead of the host — see [S3 output](#s3-output) |
| `CLOUD_S3_OUTPUT_PREFIX` | unset (bucket root) | Key prefix to upload under within `CLOUD_S3_OUTPUT_BUCKET` |

## Using the API

Once running, `POST /generate` with `media_type` set to `"video"`,
`"image"`, or `"voice"` — this picks which request shape is expected and
which handler generates the output. `model` (video/image) or `variant`
(voice) is optional — omit it to let the hardware detector pick
automatically among catalog models of that media type.

### Video

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "video",
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

Response includes `video_path`, the `model` that ran, and (if S3 output is
configured) `s3_bucket`/`s3_key`/`s3_url`.

### Image

Same shape, with `media_type: "image"` and image-specific `fields`
(`subject`, `scene`, `camera`, `lighting`, `style`, `color_palette`,
`negative_prompt`) and `params` (`width`, `height`). Pass
`references: [{"url": "https://..."}]` for image-to-image instead of
text-to-image. Response uses `image_path` in place of `video_path`.

### Voice

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "voice",
    "text": "Hello from Chatterbox. This is a test of the Fraime voice generation pipeline.",
    "variant": "multilingual",
    "language": "es",
    "voice": {"url": "https://example.com/reference-clip.wav"},
    "params": {
      "exaggeration": 0.5,
      "cfg_weight": 0.5,
      "temperature": 0.8
    }
  }'
```

Unlike video/image, voice has no `fields`/structured prompt — `text` is
spoken as-is, and there's no `model` pin: chatterbox ships three fixed
classes (`base`/`turbo`/`multilingual`), pinned via `variant` instead.

- `variant` — omit to auto-select by hardware (and by `multilingual`
  capability if `language` isn't English); every variant supports zero-shot
  voice cloning, `turbo` trades some expressiveness for much lower
  VRAM/latency, `multilingual` covers 23 languages.
- `language` — ISO code (e.g. `es`, `fr`, `ja`); only honored when the
  resolved variant is `multilingual`.
- `voice` — a single reference clip URL (5-20s clean single-speaker audio)
  to clone; omit for the model's default voice.

Response uses `voice_path` in place of `video_path`.

If `AUTH_API_KEY` is set, add
`-H "Authorization: Bearer <your-key>"` to any request.

### S3 output

Set `CLOUD_S3_OUTPUT_BUCKET` to upload the generated file to S3 instead of
the host. `CLOUD_S3_OUTPUT_PREFIX` is optional (default: bucket root).
Credentials resolve the standard boto3 way (environment,
`~/.aws/credentials`, instance role, etc.).

When configured:
- Before generation starts, the API does a test write to the destination
  key; failure returns **403 Forbidden** immediately.
- On success, the file is uploaded to that key,
  `video_path`/`image_path`/`voice_path` is `null`, and `s3_bucket`,
  `s3_key`, and a presigned `s3_url` (valid for 1 hour) are populated
  instead.

### Inspecting the running configuration

`GET /config/models` returns the full contents of
[`instructions/models.json`](instructions/models.json) (all media types'
models together, distinguished by each entry's `media_type` field);
`GET /config/rules` returns the full contents of
[`instructions/rules.json`](instructions/rules.json) (both video's
`shared`/`types` and image's `image_fields`/`image_evaluation_criteria`
together). Both require the same `Authorization: Bearer <key>` header as
`/generate` if `AUTH_API_KEY` is set.

```bash
curl http://127.0.0.1:8000/config/models
curl http://127.0.0.1:8000/config/rules
```

### Sample output

Generated with the request above:

![assets/demo.gif](assets/demo.gif)

(If your viewer doesn't render inline video: [`assets/demo.mp4`](assets/demo.mp4).)
