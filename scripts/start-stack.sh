#!/usr/bin/env bash
# Starts the inference layer inside WSL2.
#
# llama-swap listens on 127.0.0.1:8080 and lazily starts/stops llama-server
# processes per requested model. Because .wslconfig sets networkingMode=mirrored,
# this port is directly reachable from Windows at the same address.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec "$HOME/bin/llama-swap" \
  -config "$REPO_ROOT/llama-swap.yaml" \
  -listen 127.0.0.1:8080 \
  -watch-config
