# Fraime MCP Server

MCP server exposing the [Fraime API](../api/README.md) to agentic workflows,
built on top of the [Fraime SDK](../sdk/README.md)'s `FraimeClient`.

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

Generates one video.

- Shared prompt fields: `subject`, `action`, `scene`, `camera`, `lighting`,
  `style`, `negative_prompt`
- Video-type-specific extras: `dialogue`, `voice_tone`, `text_overlay`,
  `aspect_ratio`, `audio_reference`, `tempo_bpm`, `text_content`,
  `transitions`
- Generation params: `duration_s`, `fps`, `resolution`, `seed`,
  `num_inference_steps`
- Model/performance knobs: `model`, `reference_urls`, `vram_safety_margin`,
  `low_memory_decode`, `cpu_offload`

Fields that don't apply to the chosen `video_type` are ignored. `audio_reference`
is required for `music_video`; `text_content` is required for
`motion_graphics` — omitting either returns a tool error.

If the API has `CLOUD_S3_OUTPUT_BUCKET` configured (see
[`api/README.md`](../api/README.md#s3-output)), the result's `video_path` is
`null` and `s3_bucket`, `s3_key`, and a presigned `s3_url` are populated
instead; otherwise those three are `null` and `video_path` points to the
file on the API host.

### `list_video_types`

Returns every `video_type` and which extra fields it uses on top of the
shared base fields.

### `get_models_config`

Returns the model catalog the API host auto-selects from when `generate_video`
is called without an explicit `model`: every model's capabilities, VRAM
requirements, license, and `preferred_for` video types, plus the capability
requirements each `video_type` imposes on that selection.

### `get_rules_config`

Returns the prompt-structure rules the API enforces per `video_type`: field
guidance and evaluation criteria shared by every type, plus each type's own
style guidance, extra fields, and additional criteria.

## Configuration reference

| Env var | Default | What it controls |
|---|---|---|
| `FRAIME_BASE_URL` | `http://127.0.0.1:8000` | Base URL of the Fraime API to call |
| `FRAIME_API_KEY` | none | Sent as `Authorization: Bearer <key>` if set |

Both are read by the underlying `FraimeClient` — see
[`sdk/README.md`](../sdk/README.md#configuration-reference) for details.
