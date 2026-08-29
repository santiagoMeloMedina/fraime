#!/usr/bin/env bash
set -euo pipefail

# Builds and publishes the Fraime API Docker image to Docker Hub.
#
# GPU hosts (the AWS instances this image targets) are linux/amd64 — building
# on Apple Silicon (or any arm64 machine) without specifying the platform
# would produce an arm64 image nobody running this on a GPU server could use,
# so this always cross-builds for linux/amd64 explicitly via buildx.
#
# Auth: run `docker login` yourself first. This script doesn't try to detect
# whether you're logged in — Docker Desktop routes real credentials through
# an OS credential store that isn't reliably visible from a script, so a
# pre-check here would be more misleading than useful. If you're not logged
# in, `docker buildx build --push` will fail with its own clear auth error.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")"

IMAGE="santsq18/framie-api"
TAG="latest"

echo "About to build and push $IMAGE:$TAG for linux/amd64."
echo "This is a public push, visible to anyone who pulls $IMAGE."
read -r -p "Type the image name ($IMAGE) to confirm: " CONFIRM
if [ "$CONFIRM" != "$IMAGE" ]; then
    echo "Mismatch, aborting." >&2
    exit 1
fi

docker buildx build \
    --platform linux/amd64 \
    -t "$IMAGE:$TAG" \
    --push \
    "$API_DIR"

echo "Pushed $IMAGE:$TAG"
