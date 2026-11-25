#!/usr/bin/env bash
# slot-guard.sh <slot>  -- run inside WSL. Prints one line: GUARD ok|reloaded|FAILED ...
#
# Why (2026-11-25): during `run-h2h-harness.sh hermes deep`, the APEX llama-server (pinned
# build 85c5522) degenerated mid-run: after 11 good trajectories it began answering every
# request with nothing but '/' characters in reasoning_content, and Hermes reported each as
# "Context length exceeded (57 tokens)". All 13 remaining trajectories failed at ~207s. The
# same process stayed broken; unloading and reloading the model fixed it immediately
# (3/3 clean '42'). This guard probes the slot before every trajectory and reloads it if the
# answer is degenerate, so a runtime fault cannot be scored as a model failure.
set -uo pipefail
SLOT="${1:?usage: slot-guard.sh <slot>}"
probe() {
  curl -s -m 600 http://127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' \
    -d "{\"model\":\"$SLOT\",\"messages\":[{\"role\":\"user\",\"content\":\"What is 17 plus 25? Answer with the number only.\"}],\"max_tokens\":1024}" \
  | python3 -c '
import json, sys
try:
    m = json.load(sys.stdin)["choices"][0]["message"]
except Exception as e:
    print("bad-response"); sys.exit()
txt = (m.get("content") or "") + (m.get("reasoning_content") or "")
slashes = txt.count("/")
ok = "42" in (m.get("content") or "") and slashes < max(20, len(txt) // 4)
content = repr((m.get("content") or "")[:30])
print("ok" if ok else "degenerate content=%s slashes=%d/%d" % (content, slashes, len(txt)))'
}
r=$(probe)
if [ "$r" = ok ]; then echo "GUARD ok $SLOT"; exit 0; fi
echo "GUARD fault on $SLOT: $r -- reloading"
curl -s -m 30 http://127.0.0.1:8080/unload >/dev/null; sleep 5
r=$(probe)
if [ "$r" = ok ]; then echo "GUARD reloaded $SLOT"; exit 0; fi
echo "GUARD FAILED $SLOT after reload: $r"; exit 1
