#!/usr/bin/env bash
# End-to-end verification of the multi-harness setup. RUN FROM GIT BASH (Windows side).
#
# For every registered harness, run the SAME real task against the SAME llama-swap slot and
# check the answer is actually correct. "Integrated" should mean proven, not "the binary
# exists and the config looks plausible".
#
# Each harness is invoked WHERE IT ACTUALLY LIVES -- this matters and was a real bug:
# running Pi from inside WSL resolved a different HOME and it reported
# 'Unknown provider "llama-swap"' despite being correctly configured on the Windows side.
#   Pi          -> Windows (config at C:\Users\priya\.pi\agent)
#   OpenCode    -> Windows (config at C:\Users\priya\.config\opencode)
#   Prime Agent -> WSL     (config at ~/.prime/agent)
#   Codex       -> WSL     (~/.codex/config.toml)      the Windows build is policy-blocked
#   dsh         -> WSL     (~/.dsh/settings.yaml)
#   OpenClaw    -> WSL     (~/.openclaw/openclaw.json)
#   Hermes      -> WSL     (~/.hermes/config.yaml)
# All WSL invocations wrap the path inside bash -c: passing /home/... or /mnt/d/... bare to
# wsl.exe from Git Bash gets MSYS-mangled into C:/Program Files/Git/home/... , which fails
# with "No such file or directory" AND STILL EXITS 0.
#
# Sequential by design: llama-swap holds one model at a time.
set -uo pipefail

# Deep slots need the longer timeout: OpenCode's client/server startup plus a slower
# model exceeded 240s on deep-tiel while still answering correctly at 400s.
SLOT="${1:-fast}"
PROMPT='Reply with exactly one word, nothing else: the result of 17 plus 25.'
EXPECT="42"
NVM=/home/priya/.nvm/versions/node/v24.18.0/bin
WORK=/mnt/d/LocalAI/results/verify-scratch

echo "########## verifying against slot: $SLOT ##########"
echo

PASS=0; FAIL=0; SKIP=0
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

echo "=== 1/7 Pi (Windows) ==="
OUT=$(timeout 420 pi --provider llama-swap --model "$SLOT" --no-session --print "$PROMPT" 2>&1)
check "Pi" "$OUT"
echo

echo "=== 2/7 Prime Agent (WSL) ==="
OUT=$(timeout 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "$NVM/prime-agent --provider llama-swap --model '$SLOT' --print '$PROMPT'" 2>&1)
check "Prime Agent" "$OUT"
echo

echo "=== 3/7 OpenCode (Windows) ==="
OUT=$(timeout 420 opencode run --model "llama-swap/$SLOT" "$PROMPT" 2>&1)
check "OpenCode" "$OUT"
echo

echo "=== 4/7 Codex (WSL) ==="
if [ "$SLOT" = "fast" ]; then
  # Not a defect in the wiring: Qwen3.5's chat template rejects Codex's `instructions`
  # field ("System message must be at the beginning"), which the client reports as a retry
  # storm and "experiencing high demand". Re-verified 2026-09-09; still failing.
  echo "  [SKIP] Codex -- the fast slot's chat template rejects Codex's instructions field"
  SKIP=$((SKIP+1))
else
  wsl.exe -d Ubuntu-24.04 -- bash -c \
    "bash /mnt/d/LocalAI/config/harnesses/set-harness-model.sh codex '$SLOT'" >/dev/null 2>&1
  OUT=$(timeout 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
          "mkdir -p $WORK; cd $WORK; $NVM/codex exec --skip-git-repo-check -s workspace-write '$PROMPT'" 2>&1)
  check "Codex" "$OUT"
fi
echo

echo "=== 5/7 dsh (WSL) ==="
wsl.exe -d Ubuntu-24.04 -- bash -c \
  "bash /mnt/d/LocalAI/config/harnesses/set-harness-model.sh dsh '$SLOT'" >/dev/null 2>&1
OUT=$(timeout 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "export LLAMA_SWAP_KEY=local-no-auth; mkdir -p $WORK; cd $WORK; $NVM/dsh --profile headless '$PROMPT'" 2>&1)
check "dsh" "$OUT"
echo

echo "=== 6/7 OpenClaw (WSL) ==="
# agent exec --cwd, never `agent --local`: the latter ignores cwd and works on
# ~/.openclaw/workspace. --local-model-lean is its reduced tool surface for local models and
# is what makes the deep slots fit at all (the full surface builds a 33,635-token prompt).
OUT=$(timeout 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "mkdir -p $WORK; $NVM/openclaw agent exec --cwd $WORK --local-model-lean --timeout 400 --model llama-swap/'$SLOT' '$PROMPT'" 2>&1)
check "OpenClaw" "$OUT"
echo

echo "=== 7/7 Hermes (WSL) ==="
# HOME is overridden to the scratch dir because Hermes resolves relative paths against $HOME
# rather than the working directory; HERMES_HOME keeps its config and session store in place.
OUT=$(timeout 420 wsl.exe -d Ubuntu-24.04 -- bash -c \
        "mkdir -p $WORK; cd $WORK; HOME=$WORK HERMES_HOME=/home/priya/.hermes /home/priya/.local/bin/hermes -z '$PROMPT' -m '$SLOT' --yolo" 2>&1)
check "Hermes" "$OUT"
echo

echo "########## $PASS passed, $FAIL failed, $SKIP skipped ##########"
echo "=== VERIFY_HARNESSES_DONE ==="
