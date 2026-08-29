#!/usr/bin/env bash
set -euo pipefail

# Builds and publishes fraime-sdk.
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
# Usage:
#   scripts/publish.sh            # build + upload to TestPyPI (safe default, a sandbox)
#   scripts/publish.sh pypi       # build + upload to the real, public PyPI (irreversible per version)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SDK_DIR/.venv"
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
rm -rf "$SDK_DIR/dist" "$SDK_DIR/build"
python -m build "$SDK_DIR"

echo "Validating package metadata..."
twine check "$SDK_DIR"/dist/*

if [ "$TARGET" = "pypi" ]; then
    VERSION="$(python -c "import tomllib; print(tomllib.load(open('$SDK_DIR/pyproject.toml', 'rb'))['project']['version'])")"
    echo "About to upload to the REAL public PyPI as fraime-sdk==$VERSION."
    echo "This is IRREVERSIBLE — this version number can never be reused, even if deleted."
    read -r -p "Type the version ($VERSION) to confirm: " CONFIRM
    if [ "$CONFIRM" != "$VERSION" ]; then
        echo "Version mismatch, aborting." >&2
        exit 1
    fi
    twine upload "$SDK_DIR"/dist/*
else
    echo "Uploading to TestPyPI..."
    twine upload --repository testpypi "$SDK_DIR"/dist/*
fi
