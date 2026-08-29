#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$MCP_DIR/.venv"

exec "$VENV_DIR/bin/fraime-mcp"
