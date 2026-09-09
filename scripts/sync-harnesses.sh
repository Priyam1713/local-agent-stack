#!/usr/bin/env bash
# Regenerate every harness's model/provider config FROM the live llama-swap config.
#
# Why this exists: harness configs drift. prime-agent's models.json still described `deep`
# as "Nemotron 3.5 Lightning" days after Nemotron was deleted and `deep` became APEX, and
# still listed a `deep-lite` slot that no longer existed. Hand-maintaining N harness configs
# against a changing model roster guarantees that kind of rot.
#
# The rule this enforces: llama-swap.yaml is the single source of truth for what models
# exist. Every harness's roster is DERIVED from it. Re-run this after any slot change.
#
# Idempotent and safe to re-run. Literal paths, no variables through nested quoting.
set -uo pipefail

SWAP_CONFIG=/mnt/d/LocalAI/config/llama-swap.yaml
ENDPOINT="http://127.0.0.1:8080/v1"
CTX=65536      # fallback only; the real value is read per slot from llama-swap.yaml
MAXTOK=8192

# --- discover live slots from the source of truth -------------------------------------
SLOTS=$(grep -E "^  [a-z][a-z0-9-]*:" "$SWAP_CONFIG" | sed 's/://; s/^  //')
[ -n "$SLOTS" ] || { echo "FAILED: no slots parsed from $SWAP_CONFIG"; exit 1; }
echo "=== live slots from llama-swap.yaml ==="
echo "$SLOTS"

# Pull each slot's human-readable name straight from its `name:` field so harness UIs show
# the real model, not a stale label.
slot_label() {
  awk -v slot="  $1:" '
    $0 == slot { found=1; next }
    found && /^[[:space:]]*name:/ {
      sub(/^[[:space:]]*name:[[:space:]]*"?/, ""); sub(/"$/, ""); print; exit
    }
    found && /^  [a-z]/ { exit }
  ' "$SWAP_CONFIG"
}

# Each slot is served with its OWN context size (-c / --ctx-size in llama-swap.yaml).
# Declaring one number for all of them is how harness configs come to promise a 65536-token
# window on a slot the server only opens at 32768 -- the client then packs a request the
# server cannot accept. Read it per slot.
slot_ctx() {
  awk -v slot="  $1:" '
    $0 == slot { found=1; next }
    found && match($0, /(^|[[:space:]])(-c|--ctx-size)[[:space:]]+[0-9]+/) {
      s = substr($0, RSTART, RLENGTH); gsub(/[^0-9]/, "", s); print s; exit
    }
    found && /^  [a-z]/ { exit }
  ' "$SWAP_CONFIG"
}

# --- 1. prime-agent (Mario Zechner / pi-family) ---------------------------------------
PA_DIR=/home/priya/.prime/agent
if [ -d "$PA_DIR" ]; then
  echo "=== regenerating prime-agent models.json ==="
  {
    printf '{\n  "providers": {\n    "llama-swap": {\n'
    printf '      "baseUrl": "%s",\n' "$ENDPOINT"
    printf '      "api": "openai-completions",\n'
    printf '      "apiKey": "local-no-auth",\n'
    printf '      "authHeader": false,\n'
    printf '      "compat": {\n'
    printf '        "supportsDeveloperRole": false,\n'
    printf '        "supportsReasoningEffort": false,\n'
    printf '        "maxTokensField": "max_tokens"\n'
    printf '      },\n'
    printf '      "models": [\n'
    first=1
    for s in $SLOTS; do
      label=$(slot_label "$s"); [ -n "$label" ] || label="$s"
      ctx=$(slot_ctx "$s"); [ -n "$ctx" ] || ctx=$CTX
      [ $first -eq 1 ] || printf ',\n'
      first=0
      printf '        {\n'
      printf '          "id": "%s",\n' "$s"
      printf '          "name": "%s",\n' "$label"
      printf '          "reasoning": true,\n'
      printf '          "input": ["text"],\n'
      printf '          "contextWindow": %s,\n' "$ctx"
      printf '          "maxTokens": %s,\n' "$MAXTOK"
      printf '          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }\n'
      printf '        }'
    done
    printf '\n      ]\n    }\n  }\n}\n'
  } > "$PA_DIR/models.json"
  echo "wrote $PA_DIR/models.json"
else
  echo "prime-agent config dir absent, skipping"
fi

# --- 2. OpenCode CLI -------------------------------------------------------------------
OC_DIR=/mnt/c/Users/priya/.config/opencode
mkdir -p "$OC_DIR"
echo "=== regenerating opencode.json ==="
{
  printf '{\n'
  printf '  "$schema": "https://opencode.ai/config.json",\n'
  printf '  "provider": {\n'
  printf '    "llama-swap": {\n'
  printf '      "npm": "@ai-sdk/openai-compatible",\n'
  printf '      "name": "llama-swap (local)",\n'
  printf '      "options": { "baseURL": "%s" },\n' "$ENDPOINT"
  printf '      "models": {\n'
  first=1
  for s in $SLOTS; do
    label=$(slot_label "$s"); [ -n "$label" ] || label="$s"
    ctx=$(slot_ctx "$s"); [ -n "$ctx" ] || ctx=$CTX
    [ $first -eq 1 ] || printf ',\n'
    first=0
    printf '        "%s": {\n' "$s"
    printf '          "name": "%s",\n' "$label"
    printf '          "limit": { "context": %s, "output": %s }\n' "$ctx" "$MAXTOK"
    printf '        }'
  done
  printf '\n      }\n    }\n  }\n}\n'
} > "$OC_DIR/opencode.json"
echo "wrote $OC_DIR/opencode.json"

# --- 3. Pi ------------------------------------------------------------------------------
# Pi's models.json is NOT regenerated wholesale: its per-model "reasoning" flags are
# hand-tuned (fast is marked reasoning:false, the deep slots true) and nothing in
# llama-swap.yaml can derive that. Only contextWindow is asserted, because that IS derivable
# and was wrong -- every slot claimed 65536 while the server opens the deep slots at 32768.
PI_JSON=/mnt/c/Users/priya/.pi/agent/models.json
if [ -f "$PI_JSON" ]; then
  echo "=== asserting Pi contextWindow per slot ==="
  PI_CTX=""
  for s in $SLOTS; do
    c=$(slot_ctx "$s"); [ -n "$c" ] || c=$CTX
    PI_CTX="$PI_CTX $s=$c"
  done
  PI_CTX="$PI_CTX" node -e "
const fs=require('fs');
const p='/mnt/c/Users/priya/.pi/agent/models.json';
const want=Object.fromEntries(process.env.PI_CTX.trim().split(/\s+/).map(x=>x.split('=')));
const d=JSON.parse(fs.readFileSync(p,'utf8'));
let changed=0;
for(const m of d.providers['llama-swap'].models){
  const w=Number(want[m.id]);
  if(w && m.contextWindow!==w){ console.log('  '+m.id+': '+m.contextWindow+' -> '+w); m.contextWindow=w; changed++; }
}
if(changed) fs.writeFileSync(p, JSON.stringify(d,null,2)+String.fromCharCode(10));
console.log('  '+(changed?('rewrote '+changed+' model(s)'):'already correct'));
" 2>&1 || echo "  (node unavailable -- Pi contextWindow NOT verified)"
else
  echo "Pi config absent, skipping"
fi

# --- 4. OpenClaw -----------------------------------------------------------------------
OCLAW=/home/priya/.openclaw/openclaw.json
if [ -d /home/priya/.openclaw ]; then
  echo "=== regenerating openclaw.json ==="
  {
    printf '{\n  "models": {\n'
    printf '    "mode": "merge",\n'
    printf '    "providers": {\n'
    printf '      "llama-swap": {\n'
    printf '        "baseUrl": "%s",\n' "$ENDPOINT"
    printf '        "apiKey": "local-no-auth",\n'
    printf '        "models": [\n'
    first=1
    for s in $SLOTS; do
      label=$(slot_label "$s"); [ -n "$label" ] || label="$s"
      ctx=$(slot_ctx "$s"); [ -n "$ctx" ] || ctx=$CTX
      [ $first -eq 1 ] || printf ',\n'
      first=0
      printf '          {\n'
      printf '            "id": "%s",\n' "$s"
      printf '            "name": "%s",\n' "$label"
      printf '            "api": "openai-completions",\n'
      printf '            "baseUrl": "%s",\n' "$ENDPOINT"
      printf '            "reasoning": true,\n'
      printf '            "input": ["text"],\n'
      printf '            "contextWindow": %s,\n' "$ctx"
      printf '            "maxTokens": %s\n' "$MAXTOK"
      printf '          }'
    done
    printf '\n        ]\n      }\n    }\n  }\n}\n'
  } > "$OCLAW"
  echo "wrote $OCLAW"
else
  echo "openclaw config dir absent, skipping"
fi

# --- 5. dsh (DeepSeek Harness) ----------------------------------------------------------
# dsh has no --model flag, so agent-default-model IS the model selection. Preserve whatever
# slot is currently selected rather than silently resetting a benchmark run's choice; fall
# back to the first live slot when the file does not exist yet.
DSH=/home/priya/.dsh/settings.yaml
if [ -d /home/priya/.dsh ]; then
  echo "=== regenerating dsh settings.yaml ==="
  CUR=$(awk '/^agent-default-model:/{f=1;next} f&&/^  model:/{print $2; exit} f&&/^[^ ]/{exit}' "$DSH" 2>/dev/null)
  echo "$SLOTS" | grep -qx "${CUR:-}" || CUR=$(echo "$SLOTS" | head -1)
  {
    printf '# GENERATED by sync-harnesses.sh from llama-swap.yaml -- do not hand-edit.\n'
    printf '# apiKeyEnv points at a dummy var because the local server takes no auth, but the\n'
    printf '# provider schema still expects a credential reference.\n'
    printf 'llm-pi-ai:\n  providers:\n    llama-swap:\n'
    printf '      apiKeyEnv: LLAMA_SWAP_KEY\n'
    printf '      api: openai-completions\n'
    printf '      baseURL: %s\n' "$ENDPOINT"
    printf '      models:\n'
    for s in $SLOTS; do
      label=$(slot_label "$s"); [ -n "$label" ] || label="$s"
      printf '        - id: %s\n' "$s"
      printf '          name: %s\n' "$label"
      printf '          input: [text]\n'
    done
    printf '\n# Override the shipped default (deepseek-official / deepseek-v4-flash).\n'
    printf '# set-harness-model.sh rewrites the model line for each benchmark run.\n'
    printf 'agent-default-model:\n  provider: llama-swap\n  model: %s\n' "$CUR"
  } > "$DSH"
  echo "wrote $DSH (model: $CUR)"
else
  echo "dsh config dir absent, skipping"
fi

# --- 6. Codex ---------------------------------------------------------------------------
# Not regenerated: the file accumulates [projects."..."] trust entries that must survive.
# Only the endpoint is asserted. wire_api MUST stay "responses" -- Codex 0.153 removed
# "chat", and the `model` line is owned by set-harness-model.sh.
CODEX=/home/priya/.codex/config.toml
if [ -f "$CODEX" ]; then
  echo "=== checking codex config.toml ==="
  sed -i "s|^base_url = .*|base_url = \"$ENDPOINT\"|" "$CODEX"
  grep -E '^(model|model_provider|base_url|wire_api) ' "$CODEX" | sed 's/^/  /'
else
  echo "codex config absent, skipping"
fi

# --- 7. Hermes --------------------------------------------------------------------------
# Not regenerated either: config.yaml is Hermes's own heavily-commented example file and
# most of it is unrelated to models. Only the endpoint is asserted; the slot is chosen per
# invocation with -m.
HERMES=/home/priya/.hermes/config.yaml
if [ -f "$HERMES" ]; then
  echo "=== checking hermes config.yaml ==="
  sed -i "s|^  base_url: .*|  base_url: \"$ENDPOINT\"|" "$HERMES"
  awk '/^model:/{f=1} f&&/^[a-z_]+:/&&!/^model:/{exit} f' "$HERMES" \
    | grep -vE '^\s*#|^\s*$' | sed 's/^/  /' | head -6
else
  echo "hermes config absent, skipping"
fi

echo "=== SYNC_HARNESSES_DONE ==="
