#!/usr/bin/env bash
# ctx-probe.sh <slot> <ctx> -- start a llama-swap slot's llama-server by hand on :9091 with a
# different --ctx-size, fill ~FILL tokens of prompt, and report peak VRAM and prefill speed.
# Reads the slot's cmd from llama-swap.yaml so it tests exactly what would be served.
# llama-swap must have nothing loaded (it would share the GPU). Never run with ComfyUI busy.
set -uo pipefail
SLOT=$1; CTX=$2; FILL=${FILL:-40000}
CFG=/mnt/d/LocalAI/config/llama-swap.yaml
CMD=$(awk -v slot="  $SLOT:" '
  $0 == slot { f=1; next }
  f && /cmd: \|/ { c=1; next }
  f && c && /^      / { sub(/^      /, ""); printf "%s ", $0; next }
  f && c { exit }' "$CFG")
CMD=$(echo "$CMD" | sed -E "s/\\$\\{PORT\\}/9091/; s/(--ctx-size|-c) [0-9]+/--ctx-size $CTX/")
echo "cmd: $CMD"
LOG=/tmp/ctx-probe-$SLOT.log
$CMD > "$LOG" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null; wait $PID 2>/dev/null' EXIT
peak=0
for i in $(seq 1 240); do
  sleep 2
  curl -s -m 2 http://127.0.0.1:9091/health | grep -q '"ok"' && break
  kill -0 $PID 2>/dev/null || { echo "server died"; tail -20 "$LOG"; exit 1; }
done
idle=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
echo "loaded: ${idle} MiB"
python3 - "$FILL" > /tmp/ctx-probe-req.json <<'EOF'
import json, sys
n = int(sys.argv[1])
words = ("alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike "
         "november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu ").split()
body = " ".join(words[i % len(words)] + str(i % 97) for i in range(int(n / 2.2)))
print(json.dumps({"messages": [{"role": "user", "content": body + "\n\nReply with the single word OK."}],
                  "max_tokens": 16, "temperature": 0}))
EOF
( while kill -0 $PID 2>/dev/null; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1; sleep 1; done ) > /tmp/ctx-probe-vram.txt &
MON=$!
t0=$(date +%s)
R=$(curl -s -m 1200 http://127.0.0.1:9091/v1/chat/completions -H 'Content-Type: application/json' -d @/tmp/ctx-probe-req.json)
t1=$(date +%s)
kill $MON 2>/dev/null
peak=$(sort -n /tmp/ctx-probe-vram.txt | tail -1)
echo "$R" | python3 -c 'import json,sys; d=json.load(sys.stdin); u=d.get("usage",{}); t=d.get("timings",{}); print("prompt_tokens", u.get("prompt_tokens"), "| prefill tok/s", round(t.get("prompt_per_second",0),1), "| error", d.get("error"))' 2>/dev/null || echo "raw: ${R:0:300}"
echo "$SLOT ctx=$CTX: loaded ${idle} MiB, peak ${peak} MiB, request $((t1-t0))s"
grep -E "CUDA error|out of memory|failed" "$LOG" | head -3
