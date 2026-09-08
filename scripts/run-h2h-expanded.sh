#!/usr/bin/env bash
# Expanded 8-task x 3-run real-agent-loop protocol. Adds feature/refactor/
# multistep tasks beyond the original 5 single-function bug-fixes, per user
# request to validate behaviour beyond quick isolated patches.
set -uo pipefail

MODEL="${1:?usage: run-h2h-expanded.sh <pi-model-id>}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/fixture"
OUT="./results/h2h-expanded-runs-${MODEL}"
if [ -x "$REPO_ROOT/fixture/.venv/Scripts/python.exe" ]; then
  PYTEST="$REPO_ROOT/fixture/.venv/Scripts/python.exe"
elif [ -x "$REPO_ROOT/fixture/.venv/bin/python" ]; then
  PYTEST="$REPO_ROOT/fixture/.venv/bin/python"
else
  echo "FAILED: no venv found under fixture/.venv -- run 'python -m venv fixture/.venv' first" >&2
  exit 1
fi
rm -rf "$OUT"
mkdir -p "$OUT"

declare -A PROMPTS=(
  [alias]="Fix the bug described in the comment in pkg/alias.py. Make a targeted edit, not a full rewrite."
  [auth]="Fix the bug described in the comment in pkg/auth.py. Make a targeted edit, not a full rewrite."
  [median]="Fix the bug described in the comment in pkg/median.py. Make a targeted edit, not a full rewrite."
  [overlay]="Fix the bug described in the comment in pkg/overlay.py. Make a targeted edit, not a full rewrite. The overlay must be deep-merged, not shallow-replaced."
  [rollback]="Fix the bug described in the comment in pkg/rollback.py. Make a targeted edit, not a full rewrite. On failure, items must be restored to its original state."
  [cache]="Read pkg/cache.py and follow the TASK comment at the bottom: add a memoize decorator (caching by positional args) and apply it to expensive_square."
  [dedupe]="Read pkg/dedupe.py and follow the TASK docstring: extract the duplicated length/whitespace check in validate_username and validate_email into one shared helper, without changing either function's behaviour."
  [pipeline]="Fix all three bugs described in the comments in pkg/pipeline.py (parse_stage, validate_stage, transform_stage). All three must be fixed for the pipeline to work correctly end-to-end."
)

RESULTS="$OUT/results.tsv"
echo -e "task\trun\tsec\tsuccess\ttoolcalls\ttoolerrors\treasoning_chars\tcontent_chars" > "$RESULTS"

for task in alias auth median overlay rollback cache dedupe pipeline; do
  for run in 1 2 3; do
    WORK="$OUT/${task}-${run}"
    rm -rf "$WORK"
    cp -r "$SRC" "$WORK"
    rm -rf "$WORK/.venv" "$WORK/.git/hooks"
    JSONOUT="$OUT/${task}-${run}.jsonl"

    START=$(date +%s.%N)
    ( cd "$WORK" && timeout 400 pi --provider llama-swap --model "$MODEL" --no-session \
        --tools read,edit,bash --mode json --print "${PROMPTS[$task]}" \
        > "$JSONOUT" 2>"$OUT/${task}-${run}.err" )
    END=$(date +%s.%N)
    SEC=$(awk -v a="$START" -v b="$END" 'BEGIN{printf "%.1f", b-a}')

    "$PYTEST" -m pytest "$WORK/tests/test_${task}.py" -q > "$OUT/${task}-${run}.pytest" 2>&1
    if grep -qE "^[0-9]+ passed" "$OUT/${task}-${run}.pytest" && ! grep -qE "failed|error" "$OUT/${task}-${run}.pytest"; then
      SUCCESS=1
    else
      SUCCESS=0
    fi

    TOOLCALLS=$(grep -o '"type":"toolcall_start"' "$JSONOUT" 2>/dev/null | wc -l)
    TOOLERRORS=$(grep -o '"isError":true' "$JSONOUT" 2>/dev/null | wc -l)
    REASON=$(grep -oE '"type":"thinking_delta"[^}]*"delta":"[^"]*"' "$JSONOUT" 2>/dev/null | wc -c)
    CONTENT=$(grep -oE '"type":"text_delta"[^}]*"delta":"[^"]*"' "$JSONOUT" 2>/dev/null | wc -c)

    echo -e "${task}\t${run}\t${SEC}\t${SUCCESS}\t${TOOLCALLS}\t${TOOLERRORS}\t${REASON}\t${CONTENT}" >> "$RESULTS"
    echo "[$task run $run] ${SEC}s success=$SUCCESS toolcalls=$TOOLCALLS errors=$TOOLERRORS"
  done
done

echo "=== H2H_EXPANDED_DONE ($MODEL) ==="
cat "$RESULTS"
