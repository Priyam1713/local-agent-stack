#!/usr/bin/env bash
# Harness-parameterized 8-task x 3-run protocol. RUN FROM GIT BASH.
#
#   run-h2h-harness.sh <prime|dsh|openclaw|hermes> <model-slot>
#
# Same fixture, same tasks, same pytest grading as run-h2h-expanded.sh -- only the harness
# driving the model changes. That isolates harness effect from model effect.
#
# Pi, OpenCode and Codex were removed from the stack on 2026-09-09 for failing more than one
# task category (or, for Codex, a whole model slot); their branches are gone with them. The
# recorded results stay in harnesses/results/ -- see registry.json's `removed` block.
#
# `success` is graded by pytest against the resulting files, which is completely
# harness-agnostic and therefore the one metric comparable across all three. Raw JSONL is
# kept per trajectory so per-harness token/tool metrics can be extracted afterward; their
# event schemas differ and are NOT directly comparable:
#   Prime Agent message_update with usage{input,output,totalTokens}      (native tokens)
#   dsh         plain prose on stdout -- no structured events at all
#   OpenClaw    provider-transport-fetch lines + a final agent-command summary
#   Hermes      final response text only under -z
#
# Timeout is deliberately generous (500s): a tighter 400s window produced a FALSE NEGATIVE
# during pre-flight when a run overlapped a llama-swap model load.
#
# -k 30 is not optional. GNU timeout sends SIGTERM and then WAITS for the child; when the
# child is Pi reached through its Windows launcher, that signal never lands and timeout blocks
# indefinitely. One pi/deep-tiel trajectory ran 9163.9s -- 18x its own 500s bound and 100x its
# median -- before finishing on its own. The follow-up SIGKILL maps to a real TerminateProcess
# and actually bounds the run. Note the bound DID hold for opencode (also Windows) and for
# codex (WSL), so this is specific to Pi's launcher, not to Windows generally.
set -uo pipefail

HARNESS="${1:?usage: run-h2h-harness.sh <prime|dsh|openclaw|hermes> <model-slot>}"
MODEL="${2:?usage: run-h2h-harness.sh <prime|dsh|openclaw|hermes> <model-slot>}"

SRC=/d/LocalAI/fixture
OUT="/d/LocalAI/results/h2h-harness-runs-${HARNESS}-${MODEL}"
PYTEST="$SRC/.venv/Scripts/python.exe"
TIMEOUT=500

rm -rf "$OUT"; mkdir -p "$OUT"

# --- shared WSL launcher ------------------------------------------------------------------
# Four of the six harnesses (prime, codex, dsh, openclaw, hermes) run inside WSL. Each gets
# its prompt through a FILE and its command through a generated script FILE that WSL executes
# by literal path. Nothing is interpolated through a nested shell string: the dedupe prompt
# contains an apostrophe ("either function's behaviour") which terminated quoted strings and
# killed every dedupe run in ~0.5s -- scoring 0/3 and looking exactly like a model capability
# gap when it was purely a quoting bug. The `bash -c` wrapper around the runner path defeats
# MSYS's rewriting of /mnt/... into C:/Program Files/Git/mnt/... , which otherwise fails with
# "No such file or directory" while still exiting 0.
wsl_run() {
  local work="$1" out="$2" task="$3" run="$4" cmd="$5"
  local wwsl pwsl runner rwsl
  wwsl=$(echo "$work" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
  printf '%s' "$PROMPT" > "$out/${task}-${run}.prompt"
  pwsl=$(echo "$out/${task}-${run}.prompt" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
  runner="$out/run-${task}-${run}.sh"
  {
    echo '#!/usr/bin/env bash'
    echo 'set -uo pipefail'
    echo 'export HOME=/home/priya'
    echo 'export PATH="/home/priya/.nvm/versions/node/v24.18.0/bin:/home/priya/.local/bin:/usr/local/bin:/usr/bin:/bin"'
    echo 'export LLAMA_SWAP_KEY=local-no-auth'
    echo "P=\$(cat $pwsl)"
    echo "W=$wwsl"
    echo 'cd "$W" || exit 1'
    echo "$cmd"
  } > "$runner"
  rwsl=$(echo "$runner" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
  timeout -k 30 $TIMEOUT wsl.exe -d Ubuntu-24.04 -- bash -c "sed -i 's/\r$//' $rwsl; bash $rwsl"
}

# --- model plumbing -----------------------------------------------------------------------
# codex, dsh and hermes expose no --model flag; the slot is read from a config file. Rewrite
# it once per protocol run and echo it back, so a run can never silently benchmark the
# previous slot.
case "$HARNESS" in
  codex|dsh|hermes)
    wsl.exe -d Ubuntu-24.04 -- bash -c "bash /mnt/d/LocalAI/config/harnesses/set-harness-model.sh $HARNESS $MODEL"
    ;;
esac

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
echo -e "harness\tmodel\ttask\trun\tsec\tsuccess" > "$RESULTS"

# Overridable for smoke tests before committing to a full 24-trajectory run, e.g.
#   TASKS=alias RUNS=1 bash run-h2h-harness.sh dsh fast
TASKS="${TASKS:-alias auth median overlay rollback cache dedupe pipeline}"
RUNS="${RUNS:-1 2 3}"

for task in $TASKS; do
  for run in $RUNS; do
    WORK="$OUT/${task}-${run}"
    rm -rf "$WORK"
    cp -r "$SRC" "$WORK"
    rm -rf "$WORK/.venv" "$WORK/.git"
    JSONOUT="$OUT/${task}-${run}.jsonl"
    PROMPT="${PROMPTS[$task]}"

    START=$(date +%s.%N)
    case "$HARNESS" in
      prime)
        # Prime Agent runs in WSL: convert /d/... to /mnt/d/... . Its only built-in tool is
        # `ipython` -- it edits by writing Python into a persistent REPL, so passing
        # --tools read,edit,bash errors out with "Unknown built-in tool(s)".
        # Generate a runner script and have WSL execute the FILE. Nothing is interpolated
        # through a nested shell string, because that repeatedly broke: the dedupe prompt
        # contains an apostrophe ("either function's behaviour") which terminated the quoted
        # string and killed every dedupe run in ~0.5s with "unexpected EOF" -- scoring 0/3
        # and looking exactly like a model capability gap. It was a quoting bug; with this
        # fix the same harness/model scores 3/3 on that task.
        WWSL=$(echo "$WORK" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
        printf '%s' "$PROMPT" > "$OUT/${task}-${run}.prompt"
        PWSL=$(echo "$OUT/${task}-${run}.prompt" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
        RUNNER="$OUT/run-${task}-${run}.sh"
        {
          echo '#!/usr/bin/env bash'
          echo 'set -uo pipefail'
          echo "P=\$(cat $PWSL)"
          echo "exec /home/priya/.nvm/versions/node/v24.18.0/bin/prime-agent \\"
          echo "  --provider llama-swap --model $MODEL --cwd $WWSL --no-session --mode json --print \"\$P\""
        } > "$RUNNER"
        RWSL=$(echo "$RUNNER" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
        timeout -k 30 $TIMEOUT wsl.exe -d Ubuntu-24.04 -- bash -c "sed -i 's/\r$//' $RWSL; bash $RWSL" \
          > "$JSONOUT" 2>"$OUT/${task}-${run}.err"
        ;;
      dsh)
        # DeepSeek Harness, from the PUBLISHED npm package (@deepseek-ai/dsh). Running the
        # repo from source is a dead end: @deepseek-ai/cordis declares FiberState as
        # `export const enum`, which TypeScript erases at compile time, so tsx's isolated
        # transpilation has no runtime export to import.
        wsl_run "$WORK" "$OUT" "$task" "$run" \
          'exec dsh --profile headless "$P"'
        ;;
      openclaw)
        # `agent exec` is OpenClaw's isolated headless turn, and its --cwd sets BOTH the
        # agent workspace and the tool working directory -- which matters because plain
        # `openclaw agent --local` ignores cwd entirely and edits ~/.openclaw/workspace.
        # That is not hypothetical: a run configured that way reported "Fixed and committed"
        # while the trajectory's file was untouched, because it had edited the shared
        # workspace copy instead.
        # --local-model-lean is OpenClaw's own reduced tool surface for local models. It is
        # used on both slots so the two are comparable, and it is what makes deep-tiel
        # reachable at all -- the full surface builds a 33,635-token system prompt that does
        # not fit that slot's 32,768 context.
        wsl_run "$WORK" "$OUT" "$task" "$run"           'exec openclaw agent exec --cwd "$W" --local-model-lean --timeout 470              --model llama-swap/'"$MODEL"' "$P"'
        ;;
      hermes)
        # Hermes Agent (NousResearch). `-z` is its one-shot headless entry point.
        # Its tools resolve relative paths against $HOME -- not the process working
        # directory and not --in, both of which it accepts and then ignores. Four pre-flight
        # variants pinned this down: from /mnt/d it "fixed" ~/.openclaw/workspace/pkg/alias.py
        # (another harness's leftover copy of the same fixture); with --no-restore-cwd it
        # looked for /home/priya/pkg/alias.py and created the directory; from /tmp it edited
        # a stale copy still sitting under $HOME; and once that copy was deleted it found
        # nothing at all. Overriding HOME to the trajectory directory -- with HERMES_HOME
        # pinned so its own config and session store stay put -- makes it edit the right
        # file every time, on drvfs included.
        # --yolo bypasses the approval prompts, which would otherwise block a headless run.
        wsl_run "$WORK" "$OUT" "$task" "$run"           'export HERMES_HOME=/home/priya/.hermes
export HOME="$W"
exec hermes -z "$P" -m '"$MODEL"' --yolo'
        ;;
      *)
        echo "unknown harness: $HARNESS"; exit 1 ;;
    esac
    END=$(date +%s.%N)
    SEC=$(awk -v a="$START" -v b="$END" 'BEGIN{printf "%.1f", b-a}')

    # Harness-agnostic grading: pytest against the resulting files.
    PYTHONPATH="$(cygpath -w "$WORK")" "$PYTEST" -m pytest "$WORK/tests/test_${task}.py" -q \
      > "$OUT/${task}-${run}.pytest" 2>&1
    if grep -qE "^[0-9]+ passed" "$OUT/${task}-${run}.pytest" && ! grep -qE " failed| error" "$OUT/${task}-${run}.pytest"; then
      SUCCESS=1
    else
      SUCCESS=0
    fi

    echo -e "${HARNESS}\t${MODEL}\t${task}\t${run}\t${SEC}\t${SUCCESS}" >> "$RESULTS"
    echo "[$HARNESS/$MODEL $task run $run] ${SEC}s success=$SUCCESS"
  done
done

echo "=== H2H_HARNESS_DONE ($HARNESS/$MODEL) ==="
