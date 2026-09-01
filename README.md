<p align="center">
  <img src="assets/logo.png" alt="Fraime logo" width="160">
</p>

# Fraime

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-ffdd00.svg)](https://buymeacoffee.com/smelomedina)

Open source AI media generation platform. Generates video, image, and voice
output from a single self-hosted API.

## The problem

AI media generation today is either hidden behind paywalls that get more
expensive the more you use them, or "free" in name only — the open source
models exist, but actually running one yourself means figuring out which
model fits your hardware, wiring up prompt structure, and managing the whole
generation pipeline by hand. Creating video, image, or voice content without
AI, meanwhile, is still a slow, manual process. The gap isn't a lack of
capable open models — it's the friction and hardware guesswork standing
between you and using them.

## The vision

Nobody should need to be a systems engineer to use an open source
generation model, and nobody should have to pay a token-metered paywall for
something their own hardware can already do. Fraime's bet is that
automatically matching hardware to the right model — instead of making a
human do that matching by hand — is what actually makes self-hosted AI
media generation practical, not just theoretically free.

## The solution

Fraime detects what hardware it's running on (accelerator type, VRAM,
system RAM, disk space) and automatically picks the best open-weight model
it can actually run from a curated catalog — matching exact capabilities
and VRAM figures against exact hardware numbers, not coarse hardware
"tiers." No model fits, no problem: it tells you why instead of guessing.

## What's in this repo

Three self-contained components, each with its own setup and docs:

| Component | What it is |
|---|---|
| [`api/`](api/README.md) | The actual generation engine: hardware detection, model catalog, prompt-structure rules, and the `/generate` endpoint. Start here. |
| [`sdk/`](sdk/README.md) | A typed Python client for the API — `pip install fraime-sdk` (or install from this repo), get enums/models for every video type instead of hand-writing request JSON. |
| [`mcp/`](mcp/README.md) | An MCP server exposing the API to agentic workflows (Claude Code, Claude Desktop, etc.) built directly on the SDK. |

Each component's own README covers its prerequisites, install/run steps,
and environment variables in full — this file is the map, not a
substitute for them. Each component also has its own `PUBLISHING.md` for
maintainers publishing new versions (Docker Hub for `api/`, PyPI for
`sdk/`/`mcp/`).

See [`idea.md`](idea.md) for the original product framing this project
started from.

## License

[MIT](LICENSE) — permissive, no obligations on forks or commercial reuse
beyond keeping the copyright notice. Each of `api/`, `sdk/`, and `mcp/`
bundles its own copy of the license, since each is also distributed
independently (Docker image, PyPI packages) rather than only as part of
this git repo.

## Support this project

If Fraime saved you from a token-metered paywall or a weekend of hardware
wrangling, consider [buying me a coffee](https://buymeacoffee.com/smelomedina) —
it genuinely helps keep this maintained.
