#!/usr/bin/env bash
# Full six-harness campaign. Grouped by model slot so llama-swap loads each model once
# instead of thrashing between them.
#
# codex/fast is deliberately absent: the `fast` slot's Qwen3.5 chat template rejects Codex's
# `instructions` field ("System message must be at the beginning"), which surfaces on the
# client as a retry storm and a misleading "high demand" message. Re-verified 2026-09-09.
set -uo pipefail
cd /d/LocalAI/config/harnesses || exit 1
LOG=/d/LocalAI/results/campaign.log
: > "$LOG"

run() {
  echo "######## $1 / $2  $(date +%H:%M:%S) ########" | tee -a "$LOG"
  bash run-h2h-harness.sh "$1" "$2" 2>&1 | grep -E "^\[|H2H_HARNESS_DONE" | tee -a "$LOG"
}

for h in dsh openclaw hermes; do run "$h" fast; done
for h in hermes dsh openclaw codex pi prime opencode; do run "$h" deep-tiel; done

echo "=== CAMPAIGN_DONE $(date +%H:%M:%S) ===" | tee -a "$LOG"
