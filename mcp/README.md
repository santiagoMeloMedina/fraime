# Fraime MCP Server

MCP server exposing the [Fraime API](../api/README.md) to agentic workflows,
built directly on top of the [Fraime SDK](../sdk/README.md)'s `FraimeClient`
— which already is this server's entire data-access layer, so there's no
separate repository/service indirection here: `model.py` holds the MCP tool
schema, `main.py` holds the routing logic and the server itself.

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

Runs the server over stdio (the standard MCP transport for locally-launched
servers) — it won't print anything and will just wait for a client to
connect; that's normal, not a hang.

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

Generates one video. Every parameter the API's `/generate` endpoint accepts
is exposed, with rich field descriptions so an agent can fill it in without
prior knowledge of the schema — shared prompt fields (`subject`, `action`,
`scene`, `camera`, `lighting`, `style`, `negative_prompt`), the video-type-specific
extras (`dialogue`, `voice_tone`, `text_overlay`, `aspect_ratio`,
`audio_reference`, `tempo_bpm`, `text_content`, `transitions`), generation
params (`duration_s`, `fps`, `resolution`, `seed`, `num_inference_steps`),
and the model/performance knobs (`model`, `reference_urls`,
`vram_safety_margin`, `low_memory_decode`, `cpu_offload`).

Fields that don't apply to the chosen `video_type` are simply ignored; two
fields that are actually required for specific types
(`audio_reference` for `music_video`, `text_content` for `motion_graphics`)
return a clear tool error if missing, rather than a confusing failure
downstream.

### `list_video_types`

Returns every `video_type` and which extra fields it uses on top of the
shared base — derived directly from the SDK's own typed field classes, so it
can't drift out of sync with what `generate_video` actually accepts. Meant
to be called first when an agent isn't sure which fields a given type needs.

## Configuration reference

| Env var | Default | What it controls |
|---|---|---|
| `FRAIME_BASE_URL` | `http://127.0.0.1:8000` | Base URL of the Fraime API to call |
| `FRAIME_API_KEY` | none | Sent as `Authorization: Bearer <key>` if set |

Both are read by the underlying `FraimeClient` — see
[`sdk/README.md`](../sdk/README.md#configuration-reference) for details.
