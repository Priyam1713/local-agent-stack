#!/usr/bin/env bash
# Three of the six harnesses have no --model flag: the model is read from a config file.
# This rewrites that file in place and echoes back what it now says, so a run can never
# silently benchmark the previous slot.
#   dsh     ~/.dsh/settings.yaml     agent-default-model.model
#   codex   ~/.codex/config.toml     model =
#   hermes  ~/.hermes/config.yaml    model.default
set -uo pipefail
export HOME=/home/priya
H="${1:?harness}"; M="${2:?model}"

case "$H" in
  dsh)
    sed -i "/^agent-default-model:/,/^[^[:space:]]/ s/^  model: .*/  model: $M/" /home/priya/.dsh/settings.yaml
    echo "dsh    -> $(grep -A2 '^agent-default-model:' /home/priya/.dsh/settings.yaml | grep '  model:')"
    ;;
  codex)
    sed -i "s|^model = .*|model = \"$M\"|" /home/priya/.codex/config.toml
    echo "codex  -> $(grep '^model = ' /home/priya/.codex/config.toml)"
    ;;
  hermes)
    sed -i "/^model:/,/^[^[:space:]]/ s/^  default: .*/  default: $M/" /home/priya/.hermes/config.yaml
    echo "hermes -> $(grep -A3 '^model:' /home/priya/.hermes/config.yaml | grep '  default:')"
    ;;
  *) echo "no config-file model for $H (uses a flag)" ;;
esac
echo "=== SET_MODEL_DONE ==="
