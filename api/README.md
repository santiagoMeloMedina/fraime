# Fraime API

Video, image, and sound generation engine + model detection engine for
Fraime. Detects your hardware, picks the best open source model it can
actually run, and generates video, image, or sound output from a prompt.

## Features

- **`POST /generate`** — works with any `diffusers`-compatible Hugging Face
  model for video/image, and with chatterbox TTS for sound. Set `media_type`
  to `"video"`, `"image"`, or `"sound"` to pick the request shape and
  generation handler; pass `model` (video/image) to pin an exact HF repo id,
  or `variant` (sound — `base`/`turbo`/`multilingual`, a fixed set of
  chatterbox classes, not an arbitrary repo) to pin one; omit either to
  auto-select by hardware. Tunable per request: duration/fps/resolution
  (video), width/height (image), or exaggeration/cfg_weight/temperature
  (sound), seed (video/image), CPU offload/VAE tiling (video/image), VRAM
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
  editable with `define`. Sound takes `text` directly (no structured
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
([`scripts/install.sh`](scripts/install.sh)). That last step is load-bearing,
not an oversight: `chatterbox-tts` hard-pins exact (`==`, not a range)
`diffusers`/`transformers`/`torch` versions old enough to predate this
project's video pipelines (FLUX, Wan2.1/2.2) — a normal
`pip install chatterbox-tts` silently downgrades those and breaks video/image
generation. `--no-deps` skips chatterbox's declared pins and keeps this
project's newer versions; chatterbox's own real (non-conflicting)
dependencies are already covered by `requirements.txt`. This combination is
verified working (real inference tested), but it's an unusual install order
worth knowing about if you're changing dependencies later — reinstalling
`chatterbox-tts` normally will reintroduce the conflict.

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

Verified: a real `docker build` + `docker run` (emulated `linux/amd64` on
Apple Silicon) confirms the image builds, all three media types' imports
succeed (including `chatterbox-tts`), the app starts as the intended non-root
user, and `/config/models`/`/config/rules` respond correctly over real HTTP.

## Environment variables

Copy `api/.env-example` to `api/.env` and configure as needed — every
setting has a sensible default if left unset.

| Variable | Default | What it controls |
|---|---|---|
| `GENERATION_DURATION_S` | `5.0` | Default clip duration in seconds |
| `GENERATION_FPS` | `24` | Default frames per second |
| `GENERATION_RESOLUTION` | `1024x576` | Default target resolution |
| `GENERATION_SEED` | unset | Default seed for reproducible generation |
| `GENERATION_MODEL_CACHE_DIR` | Hugging Face's default cache | Where downloaded video/image model weights (several to tens of GB each) are stored. **Not honored for sound** — chatterbox's `from_pretrained()` takes no cache_dir argument and always downloads to Hugging Face's own default cache regardless of this setting. |
| `GENERATION_OUTPUT_DIR` | `.generated` | Where generated `.mp4`/`.png`/`.wav` files are written; created automatically |
| `DETECTOR_CATALOG_PATH` | `instructions/models.json` | Path to the model catalog the detector matches against |
| `PROMPT_RULES_PATH` | `instructions/rules.json` | Path to the prompt rules (both video and image) that `/config/rules` serves |
| `AUTH_API_KEY` | unset (no auth) | If set, requests must send `Authorization: Bearer <key>` matching it |
| `CLOUD_S3_OUTPUT_BUCKET` | unset | If set, generated files upload to this S3 bucket instead of the host — see [S3 output](#s3-output) |
| `CLOUD_S3_OUTPUT_PREFIX` | unset (bucket root) | Key prefix to upload under within `CLOUD_S3_OUTPUT_BUCKET` |

## Using the API

Once running, `POST /generate` with `media_type` set to `"video"` or
`"image"` — this picks which request shape is expected and which handler
generates the output. `model` is optional in both — omit it to let the
hardware detector pick automatically among catalog models of that media
type.

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

Response:

```json
{
  "video_path": ".generated/<uuid>.mp4",
  "model": "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
  "s3_bucket": null,
  "s3_key": null,
  "s3_url": null
}
```

### Image

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "image",
    "fields": {
      "subject": "a matte black ceramic coffee mug with a minimalist logo",
      "scene": "a clean marble kitchen counter with soft blurred greenery in the background",
      "camera": "close-up, straight-on angle, shallow depth of field",
      "lighting": "controlled studio softbox lighting, warm highlight on the ceramic surface",
      "style": "polished commercial product photography, crisp reflections",
      "color_palette": "warm neutrals with a matte black accent",
      "negative_prompt": "blurry, low quality, warped shape, extra objects, watermark, text overlay"
    },
    "params": {
      "width": 1024,
      "height": 1024
    }
  }'
```

Pass `references: [{"url": "https://..."}]` for image-to-image generation
(edits/restyles the first reference image) instead of pure text-to-image.

Response:

```json
{
  "image_path": ".generated/<uuid>.png",
  "model": "black-forest-labs/FLUX.1-schnell",
  "s3_bucket": null,
  "s3_key": null,
  "s3_url": null
}
```

### Sound

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "sound",
    "text": "Hello from Chatterbox. This is a real end to end test of the Fraime sound generation pipeline.",
    "params": {
      "exaggeration": 0.5,
      "cfg_weight": 0.5,
      "temperature": 0.8
    }
  }'
```

Response:

```json
{
  "sound_path": ".generated/<uuid>.wav",
  "model": "ResembleAI/chatterbox-turbo",
  "s3_bucket": null,
  "s3_key": null,
  "s3_url": null
}
```

Unlike video/image, sound has no `fields`/structured prompt — `text` is
spoken as-is (chunked internally at sentence boundaries and stitched back
together, since chatterbox silently truncates any single call past ~30-40s
of audio). It also has no `model` pin the way video/image do — chatterbox
ships three fixed Python classes (`base`/`turbo`/`multilingual`), not
arbitrary swappable HF repos, so pin one explicitly with `variant` instead:

```json
{
  "media_type": "sound",
  "text": "Hola, esto es una prueba en español.",
  "variant": "multilingual",
  "language": "es",
  "voice": {"url": "https://example.com/reference-clip.wav"},
  "params": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8}
}
```

- `variant` — omit to auto-select by hardware (and by `multilingual`
  capability, if `language` is set to anything other than `en`); every
  variant supports zero-shot voice cloning, `turbo` trades some
  expressiveness for much lower VRAM/latency, `multilingual` supports 23
  languages instead of English-only.
- `language` — ISO code (e.g. `es`, `fr`, `ja`); only honored when the
  resolved variant is `multilingual` — `base`/`turbo` ignore it (English
  only).
- `voice` — a single reference clip URL (5-20s clean single-speaker audio)
  to clone; omit for the model's default voice. Unlike video/image's
  `references` (a list), sound clones from exactly one clip.

Verified working end to end on Apple Silicon (MPS), including voice cloning,
for all three variants. One MPS-specific fix was needed and is already
applied: `turbo`'s reference-clip loudness normalization
(`norm_loudness`, on by default in chatterbox) computes an intermediate
value as `float64` via `pyloudnorm`, which MPS can't hold at all — the
handler disables it automatically when `variant="turbo"` and the detected
accelerator is MPS (harmless elsewhere; `base`/`multilingual` never had this
step to begin with). CUDA/CPU hosts are unaffected either way.

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
  `video_path`/`image_path`/`sound_path` is `null`, and `s3_bucket`,
  `s3_key`, and a presigned `s3_url` (valid for 1 hour) are populated
  instead:

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
[`instructions/models.json`](instructions/models.json) (both media types'
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
