#!/usr/bin/env bash
set -euo pipefail

# Builds and publishes fraime-mcp.
#
# Auth: PyPI uses API tokens, not passwords. Generate one at
# https://pypi.org/manage/account/token/ (or https://test.pypi.org/manage/account/token/
# for TestPyPI) and export it before running this script:
#
#   export TWINE_USERNAME=__token__
#   export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...
#
# (Or configure the same pair in ~/.pypirc instead — twine reads either.)
#
# Note: fraime-mcp depends on fraime-sdk>=1.0,<2.0 — that needs to already be
# published (see ../sdk/scripts/publish.sh) before this package is genuinely
# installable by anyone else, even though this script doesn't check that.
#
# Usage:
#   scripts/publish.sh            # build + upload to TestPyPI (safe default, a sandbox)
#   scripts/publish.sh pypi       # build + upload to the real, public PyPI (irreversible per version)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$MCP_DIR/.venv"
TARGET="${1:-testpypi}"

if [ "$TARGET" != "testpypi" ] && [ "$TARGET" != "pypi" ]; then
    echo "Usage: $0 [testpypi|pypi]" >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "No .venv found — run scripts/install.sh first." >&2
    exit 1
fi

source "$VENV_DIR/bin/activate"

if [ -z "${TWINE_PASSWORD:-}" ] && [ ! -f "$HOME/.pypirc" ]; then
    echo "No credentials found — set TWINE_USERNAME/TWINE_PASSWORD, or configure ~/.pypirc, first." >&2
    exit 1
fi

echo "Building distribution..."
rm -rf "$MCP_DIR/dist" "$MCP_DIR/build"
python -m build "$MCP_DIR"

echo "Validating package metadata..."
twine check "$MCP_DIR"/dist/*

if [ "$TARGET" = "pypi" ]; then
    VERSION="$(python -c "import tomllib; print(tomllib.load(open('$MCP_DIR/pyproject.toml', 'rb'))['project']['version'])")"
    echo "About to upload to the REAL public PyPI as fraime-mcp==$VERSION."
    echo "This is IRREVERSIBLE — this version number can never be reused, even if deleted."
    read -r -p "Type the version ($VERSION) to confirm: " CONFIRM
    if [ "$CONFIRM" != "$VERSION" ]; then
        echo "Version mismatch, aborting." >&2
        exit 1
    fi
    twine upload "$MCP_DIR"/dist/*
else
    echo "Uploading to TestPyPI..."
    twine upload --repository testpypi "$MCP_DIR"/dist/*
fi
