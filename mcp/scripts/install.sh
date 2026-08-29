#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"
SDK_DIR="$(dirname "$MCP_DIR")/sdk"
VENV_DIR="$MCP_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip
# fraime-sdk isn't published to PyPI yet — install it locally first so mcp's
# own dependency on it resolves against this checkout instead of the network.
pip install -e "$SDK_DIR"
pip install -e "$MCP_DIR[dev]"
