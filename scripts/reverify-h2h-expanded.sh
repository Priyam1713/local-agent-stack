#!/usr/bin/env bash
# Re-verify already-completed h2h-expanded runs: reruns pytest with the correct
# PYTHONPATH (a bug in early runs made every `success` column read 0), and pulls
# tool-call/reasoning stats straight from the JSONL transcript rather than
# trusting the raw run's own accounting.
set -uo pipefail
OUT="${1:?usage: reverify-h2h-expanded.sh <runs-dir>}"

# Locate the fixture's venv relative to the repo root (this script's grandparent dir).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -x "$REPO_ROOT/fixture/.venv/Scripts/python.exe" ]; then
  PYTEST="$REPO_ROOT/fixture/.venv/Scripts/python.exe"   # Windows venv
elif [ -x "$REPO_ROOT/fixture/.venv/bin/python" ]; then
  PYTEST="$REPO_ROOT/fixture/.venv/bin/python"            # Linux/macOS venv
else
  echo "FAILED: no venv found under fixture/.venv -- run 'python -m venv fixture/.venv' first" >&2
  exit 1
fi

RESULTS="$OUT/results-clean.tsv"
echo -e "task\trun\tsec\tsuccess\ttoolcalls\ttoolerrors\treasoning_chars\tcontent_chars" > "$RESULTS"

for task in alias auth median overlay rollback cache dedupe pipeline; do
  for run in 1 2 3; do
    WORK="$OUT/${task}-${run}"
    JSONOUT="$OUT/${task}-${run}.jsonl"
    [ -d "$WORK" ] || { echo "MISSING $WORK"; continue; }

    # cygpath only exists on Windows/Git Bash; fall back to the plain path elsewhere.
    if command -v cygpath >/dev/null 2>&1; then
      PYTHONPATH="$(cygpath -w "$WORK")" "$PYTEST" -m pytest "$WORK/tests/test_${task}.py" -q \
        > "$OUT/${task}-${run}.pytest2" 2>&1
    else
      PYTHONPATH="$WORK" "$PYTEST" -m pytest "$WORK/tests/test_${task}.py" -q \
        > "$OUT/${task}-${run}.pytest2" 2>&1
    fi
    if grep -qE "^[0-9]+ passed" "$OUT/${task}-${run}.pytest2" && ! grep -qE " failed| error" "$OUT/${task}-${run}.pytest2"; then
      SUCCESS=1
    else
      SUCCESS=0
    fi

    TOOLCALLS=$(grep -o '"type":"toolcall_start"' "$JSONOUT" 2>/dev/null | wc -l)
    TOOLERRORS=$(grep -o '"isError":true' "$JSONOUT" 2>/dev/null | wc -l)
    REASON=$(grep -oE '"type":"thinking_delta"[^}]*"delta":"[^"]*"' "$JSONOUT" 2>/dev/null | wc -c)
    CONTENT=$(grep -oE '"type":"text_delta"[^}]*"delta":"[^"]*"' "$JSONOUT" 2>/dev/null | wc -c)

    SEC=$(awk -F'\t' -v t="$task" -v r="$run" '$1==t && $2==r {print $3; exit}' "$OUT/results.tsv")

    echo -e "${task}\t${run}\t${SEC}\t${SUCCESS}\t${TOOLCALLS}\t${TOOLERRORS}\t${REASON}\t${CONTENT}" >> "$RESULTS"
  done
done

echo "=== REVERIFY_EXPANDED_DONE ==="
column -t "$RESULTS"
