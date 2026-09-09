#!/usr/bin/env bash
# An ACP agent speaks newline-delimited JSON-RPC on stdio. Feed it an initialize request and
# keep the pipe open long enough for the reply -- closing stdin immediately makes a healthy
# agent exit silently, which is indistinguishable from a broken one.
export HOME=/home/priya
export PATH="/home/priya/.nvm/versions/node/v24.18.0/bin:/home/priya/.local/bin:/usr/local/bin:/usr/bin:/bin"
REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1,"clientCapabilities":{"fs":{"readTextFile":true,"writeTextFile":true}}}}'

probe() {
  local name="$1"; shift
  echo "=== $name ==="
  { printf '%s\n' "$REQ"; sleep 25; } | timeout 40 "$@" 2>/tmp/acp-$name.err | head -c 500
  echo
  echo "  --- stderr ---"
  head -4 /tmp/acp-$name.err | sed 's/^/    /'
  echo
}

probe hermes   /home/priya/.local/bin/hermes acp
probe openclaw bash /mnt/d/LocalAI/config/harnesses/zed-openclaw-acp.sh
echo "=== TEST_ACP_DONE ==="
