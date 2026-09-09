#!/usr/bin/env bash
# End-to-end verification of the multi-harness setup. RUN FROM GIT BASH (Windows side).
#
# For every registered harness, run the SAME real task against the SAME llama-swap slot and
# check the answer is actually correct. "Integrated" should mean proven, not "the binary
# exists and the config looks plausible".
#
# All four survivors run in WSL, so every invocation wraps its path inside bash -c: passing
# /home/... or /mnt/d/... bare to wsl.exe from Git Bash gets MSYS-mangled into
# C:/Program Files/Git/home/... , which fails with "No such file or directory" AND STILL
# EXITS 0. (The two Windows-side harnesses, Pi and OpenCode, were removed on 2026-09-09 --
# see registry.json's `removed` block. The rule that each harness must be invoked where it
# lives is kept in the comments because it cost real debugging time: running Pi from inside
# WSL resolved a different HOME and it reported 'Unknown provider "llama-swap"'.)
#
#   prime-agent -> WSL  (~/.prime/agent/models.json)
#   dsh         -> WSL  (~/.dsh/settings.yaml)     no --model flag
#   openclaw    -> WSL  (~/.openclaw/openclaw.json)
#   hermes      -> WSL  (~/.hermes/config.yaml)
#
# Sequential by design: llama-swap holds one model at a time.
set -uo pipefail

# Deep slots need the longer timeout: a slower model plus harness startup exceeded 240s on
# deep-tiel while still answering correctly at 400s.
SLOT="${1:-fast}"
PROMPT='Reply with exactly one word, nothing else: the result of 17 plus 25.'
EXPECT="42"
NVM=/home/priya/.nvm/versions/node/v24.18.0/bin
WORK=/mnt/d/LocalAI/results/verify-scratch

echo "########## verifying against slot: $SLOT ##########"
echo

PASS=0; FAIL=0
check() {
  local name="$1" out="$2"
  if printf '%s' "$out" | grep -q "$EXPECT"; then
    echo "  [PASS] $name -- got expected '$EXPECT'"
    PASS=$((PASS+1))
  else
    echo "  [FAIL] $name -- '$EXPECT' not found"
    printf '         output: %s\n' "$(printf '%s' "$out" | tr '\n' ' ' | cut -c1-220)"
    FAIL=$((FAIL+1))
  fi
}

echo "=== 1/4 Prime Agent (WSL) ==="
OUT=$(timeout -k 30 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "$NVM/prime-agent --provider llama-swap --model '$SLOT' --print '$PROMPT'" 2>&1)
check "Prime Agent" "$OUT"
echo

echo "=== 2/4 dsh (WSL) ==="
# No --model flag: the slot lives in ~/.dsh/settings.yaml and must be rewritten first, or
# this silently verifies whichever slot was last benchmarked.
wsl.exe -d Ubuntu-24.04 -- bash -c \
  "bash /mnt/d/LocalAI/config/harnesses/set-harness-model.sh dsh '$SLOT'" >/dev/null 2>&1
OUT=$(timeout -k 30 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "export LLAMA_SWAP_KEY=local-no-auth; mkdir -p $WORK; cd $WORK; $NVM/dsh --profile headless '$PROMPT'" 2>&1)
check "dsh" "$OUT"
echo

echo "=== 3/4 OpenClaw (WSL) ==="
# agent exec --cwd, never `agent --local`: the latter ignores cwd and works on
# ~/.openclaw/workspace. --local-model-lean is its reduced tool surface for local models and
# is what makes the deep slots fit at all (the full surface builds a 33,635-token prompt).
OUT=$(timeout -k 30 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "mkdir -p $WORK; $NVM/openclaw agent exec --cwd $WORK --local-model-lean --timeout 400 --model llama-swap/'$SLOT' '$PROMPT'" 2>&1)
check "OpenClaw" "$OUT"
echo

echo "=== 4/4 Hermes (WSL) ==="
# HOME is overridden to the scratch dir because Hermes resolves relative paths against $HOME
# rather than the working directory; HERMES_HOME keeps its config and session store in place.
OUT=$(timeout -k 30 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "mkdir -p $WORK; cd $WORK; HOME=$WORK HERMES_HOME=/home/priya/.hermes /home/priya/.local/bin/hermes -z '$PROMPT' -m '$SLOT' --yolo" 2>&1)
check "Hermes" "$OUT"
echo

echo "########## $PASS passed, $FAIL failed ##########"
echo "=== VERIFY_HARNESSES_DONE ==="
