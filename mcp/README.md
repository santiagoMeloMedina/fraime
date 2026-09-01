# Fraime MCP Server

MCP server exposing the [Fraime API](../api/README.md)'s video, image, and
voice generation to agentic workflows, built on top of the
[Fraime SDK](../sdk/README.md)'s `FraimeClient`.

## Prerequisites

- Python 3.11+
- A running Fraime API instance (see [`api/README.md`](../api/README.md))
- An MCP client to talk to this server (Claude Code, Claude Desktop, or
  anything else that speaks MCP over stdio)

## Install

### Option 1 — pip / uvx

```bash
pip install fraime-mcp
# or, to run it without installing into any project env:
uvx fraime-mcp
```

Pulls in `fraime-sdk` from PyPI automatically as a dependency.

### Option 2 — from a local clone (development)

```bash
make install-mcp   # from repo root
# or
make install       # from mcp/
```

Creates `.venv` inside `mcp/`, installs `fraime-sdk` from the local `../sdk`
checkout, then installs this package.

## Run

```bash
make run-mcp   # from repo root
# or
make run       # from mcp/
```

Runs the server over stdio. It prints nothing and waits for a client to
connect.

## Configuring an MCP client

Point your client at the installed console script. For Claude Code /
Claude Desktop style config:

```json
{
  "mcpServers": {
    "fraime": {
      "command": "/absolute/path/to/fraime/mcp/.venv/bin/fraime-mcp",
      "env": {
        "FRAIME_BASE_URL": "http://127.0.0.1:8000",
        "FRAIME_API_KEY": "your-api-key"
      }
    }
  }
}
```

`command` depends on how you installed it: the path above is for the local-clone
install (Option 2). For a `pip install fraime-mcp` into your own venv, point
`command` at that venv's `bin/fraime-mcp` instead; for `uvx`, use `"command": "uvx", "args": ["fraime-mcp"]`.

`FRAIME_API_KEY` is only needed if the API has `AUTH_API_KEY` set — see
[`api/README.md`](../api/README.md).

## Tools

### `generate_video`

Generates one video from shared prompt fields (`subject`, `action`, `scene`,
`camera`, `lighting`, `style`, `negative_prompt`), video-type-specific extras
(`dialogue`, `voice_tone`, `text_overlay`, `aspect_ratio`,
`audio_reference`, `tempo_bpm`, `text_content`, `transitions`), generation
params (`duration_s`, `fps`, `resolution`, `seed`, `num_inference_steps`),
and model/performance knobs (`model`, `reference_urls`,
`vram_safety_margin`, `low_memory_decode`, `cpu_offload`).

Fields that don't apply to the chosen `video_type` are ignored.
`audio_reference` is required for `music_video`; `text_content` is required
for `motion_graphics`.

Result includes `video_path` and `model`; if `CLOUD_S3_OUTPUT_BUCKET` is
configured on the API (see [`api/README.md`](../api/README.md#s3-output)),
`video_path` is `null` and `s3_bucket`/`s3_key`/`s3_url` are populated
instead.

### `generate_image`

Generates one still image. Unlike `generate_video`, there's no per-type
field variation: prompt fields (`subject`, `scene`, `camera`, `lighting`,
`style`, `action`, `color_palette`, `negative_prompt`), generation params
(`width`, `height`, `seed`, `num_inference_steps`, `guidance_scale`), and
model/performance knobs (`model`, `reference_urls`, `vram_safety_margin`,
`cpu_offload`).

Same S3-output behavior as `generate_video`, with `image_path` in place of
`video_path`.

### `generate_voice`

Generates one spoken-audio clip from raw `text` — no structured prompt.
Chatterbox ships three fixed classes rather than arbitrary swappable HF
repos, so `variant` (`base`/`turbo`/`multilingual`) pins one instead of
`model`; omit it to auto-select by hardware (and by multilingual capability,
if `language` requires it). `voice_url` clones a voice from a single 5-20s
reference clip; `language` (ISO code) is only honored when the resolved
variant is multilingual. Generation params: `exaggeration`, `cfg_weight`,
`temperature`.

Long `text` is chunked internally at sentence boundaries and stitched back
together, since the underlying model truncates past ~30-40 seconds per call.

Same S3-output behavior as the other tools, with `voice_path` in place of
`video_path`.

### `list_video_types`

Returns every `video_type` and which extra fields it uses on top of the
shared base fields. No image or voice equivalent exists: image has a single
fixed field set (see `get_rules_config`'s `image_fields`), and voice has no
structured fields at all.

### `get_models_config`

Returns the model catalog the API host auto-selects from when `generate_video`,
`generate_image`, or `generate_voice` is called without an explicit `model`/
`variant`: every model's `media_type` (video, image, or voice), capabilities,
VRAM requirements, license, and `preferred_for` video types, plus the
capability requirements each `video_type` imposes on that selection.

### `get_rules_config`

Returns the prompt-structure rules the API enforces, for video and image:
for video, field guidance and evaluation criteria shared by every
`video_type`, plus each type's own style guidance, extra fields, and
additional criteria; for image, the fixed field set (`image_fields`) and its
evaluation criteria (`image_evaluation_criteria`). Voice has no equivalent —
call `generate_voice` directly, it just takes text.

## Configuration reference

| Env var | Default | What it controls |
|---|---|---|
| `FRAIME_BASE_URL` | `http://127.0.0.1:8000` | Base URL of the Fraime API to call |
| `FRAIME_API_KEY` | none | Sent as `Authorization: Bearer <key>` if set |

Both are read by the underlying `FraimeClient` — see
[`sdk/README.md`](../sdk/README.md#configuration-reference) for details.
