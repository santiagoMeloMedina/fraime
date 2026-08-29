# Fraime SDK

Python client for the [Fraime API](../api/README.md) — build a request with
typed models/enums instead of hand-writing JSON, point it at a running
Fraime instance, get a generated video back.

## Prerequisites

- Python 3.11+
- A running Fraime API instance to talk to (see [`api/README.md`](../api/README.md)
  for how to run one) — you'll need its base URL, and its API key if one is
  configured (`AUTH_API_KEY` on the API side).

## Install

### Option 1 — pip

```bash
pip install fraime-sdk
```

### Option 2 — from a local clone

Step by step, from scratch:

```bash
# 1. Clone the repo (skip if you already have it)
git clone <this-repo-url>
cd fraime

# 2. (Recommended) create a virtualenv for your own project
python3 -m venv .venv
source .venv/bin/activate

# 3. Install the SDK from the sdk/ folder
pip install ./sdk
#   or, for local development on the SDK itself (editable install):
pip install -e ./sdk
```

That's it — `import fraime` is now available in that environment.

### Option 3 — straight from git, no local clone needed

```bash
pip install "git+ssh://git@santiago/santiagoMeloMedina/fraime.git#subdirectory=sdk"
```

(Adjust the URL to whatever remote you actually have push/pull access to —
this is this repo's own `origin` in SSH form.)

## Usage

```python
from fraime import FraimeClient, VideoType, GenerationParams, CinematicPromptFields

client = FraimeClient(
    base_url="http://127.0.0.1:8000",  # or set FRAIME_BASE_URL instead
    api_key="your-api-key",             # or set FRAIME_API_KEY instead; omit both if the API has none configured
)

response = client.generate(
    video_type=VideoType.PIXAR,
    fields=CinematicPromptFields(
        subject="a small orange fox with oversized ears",
        action="hops between rocks, pauses, and looks up curiously",
        scene="a sunlit forest clearing at golden hour",
        camera="medium shot, slow dolly-in",
        lighting="warm rim lighting from the low sun",
        style="3D animated feature style, stylized proportions, warm rim lighting",
    ),
    params=GenerationParams(duration_s=3, fps=16, resolution="768x512"),
    # model=...              # optional: pin an exact model instead of auto-selecting
    # references=[...]       # optional: Reference(url=...) list, for image-to-video
)

print(response.video_path, response.model)
```

`model` is optional on `client.generate()` — omit it and the API auto-selects
by hardware, same as calling it directly.

### Picking the right fields class per video type

Every `video_type` has its own field set — some add fields the base six
(`subject`, `action`, `scene`, `camera`, `lighting`, `style`,
`negative_prompt`) don't cover:

| `VideoType` | Fields class | Extra fields |
|---|---|---|
| `PIXAR`, `ACTION`, `ANIMATION`, `ANIME`, `DOCUMENTARY`, `FASHION` | `CinematicPromptFields` | — |
| `UGC_PRODUCT_REVIEW`, `COMMERCIAL_PRODUCT_AD`, `EXPLAINER_TESTIMONIAL` | `UGCPromptFields` | `dialogue`, `reference_image` |
| `PRESENTER_AVATAR` | `PresenterPromptFields` | + `voice_tone` |
| `SOCIAL_SHORT_FORM_AD` | `SocialAdPromptFields` | + `text_overlay`, `aspect_ratio` |
| `MUSIC_VIDEO` | `MusicVideoPromptFields` | `audio_reference`, `tempo_bpm` |
| `MOTION_GRAPHICS` | `MotionGraphicsPromptFields` | `text_content`, `transitions` |

Not sure which class a given `VideoType` needs? Look it up instead of
guessing:

```python
from fraime import PROMPT_FIELDS_BY_VIDEO_TYPE, VideoType

fields_class = PROMPT_FIELDS_BY_VIDEO_TYPE[VideoType.SOCIAL_SHORT_FORM_AD]
# -> SocialAdPromptFields
```

### Reference images (image-to-video)

```python
from fraime import Reference

response = client.generate(
    video_type=VideoType.UGC_PRODUCT_REVIEW,
    fields=ugc_fields,
    params=params,
    references=[Reference(url="https://example.com/product-photo.jpg")],
)
```

### Error handling

```python
from fraime import FraimeAuthError, FraimeAPIError, FraimeConnectionError

try:
    response = client.generate(video_type=VideoType.PIXAR, fields=fields, params=params)
except FraimeAuthError:
    ...  # missing/invalid API key
except FraimeAPIError as e:
    ...  # e.status_code, e.detail — the API reached but returned an error
except FraimeConnectionError:
    ...  # couldn't reach the API at all
```

## Configuration reference

| `FraimeClient(...)` argument | Env var fallback | Default |
|---|---|---|
| `base_url` | `FRAIME_BASE_URL` | `http://127.0.0.1:8000` |
| `api_key` | `FRAIME_API_KEY` | none (open API) |
| `timeout` | — | `600.0` seconds |

`timeout` defaults high on purpose — real generation runs can take several
minutes; see [`api/README.md`](../api/README.md) for why.
