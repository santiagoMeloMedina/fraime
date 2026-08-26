#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$API_DIR")"
VENV_DIR="$API_DIR/.venv"

source "$VENV_DIR/bin/activate"

cd "$REPO_ROOT"
uvicorn api.main:app --reload
