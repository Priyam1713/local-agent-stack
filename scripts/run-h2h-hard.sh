#!/usr/bin/env bash
# HARD fixture protocol (2026-11-25): 12 tasks x 3 runs = 36 trajectories, Hermes. RUN FROM GIT BASH.
#
#   run-h2h-hard.sh <model-slot>          (TASKS=... RUNS=... to narrow for a smoke test)
#
# Built because the 8-task fixture saturated: fast, deep-tiel and Inkling 2 Mini all scored 24/24.
# What makes it harder than the 8-task fixture:
#   - HIDDEN tests. The model gets only a docstring specification; the pytest file is copied
#     into the trajectory AFTER the harness exits, so it cannot be read or gamed. 245 test
#     cases across 12 tasks, every edge case stated in the docstring.
#   - Prompts describe symptoms or the spec, never the location of each bug, and most tasks
#     carry several independent bugs or a full implementation (semver ranges, envsubst
#     defaults, csv quoting, a precedence-climbing parser).
#   - Two tasks span files: `rename` (package + caller + deprecated alias) and `pagination`
#     (api.py and store.py both broken).
# Validated by config/validate-fixture-hard.sh: every test file fails on the starting code
# and passes on the reference solution in /d/LocalAI/fixture-hard-ref (never shown to models).
#
# Timing is recorded but is NOT the criterion for this fixture (user's instruction). The
# 900s bound exists only so a genuinely stuck trajectory ends.
# Harness invocation is identical to run-h2h-harness.sh's hermes branch -- see the comments
# there for why HOME is overridden to the trajectory directory.
set -uo pipefail

MODEL="${1:?usage: run-h2h-hard.sh <model-slot>}"
SRC=/d/LocalAI/fixture-hard
TESTS=/d/LocalAI/fixture-hard-tests/tests
OUT="/d/LocalAI/results/h2h-hard-hermes-${MODEL}"
PYTEST=/d/LocalAI/fixture/.venv/Scripts/python.exe
TIMEOUT=900

rm -rf "$OUT"; mkdir -p "$OUT"
wsl.exe -d Ubuntu-24.04 -- bash -c "bash /mnt/d/LocalAI/config/harnesses/set-harness-model.sh hermes $MODEL"

SPEC=" The docstring is the complete specification: hidden tests will check every rule in it, so read it carefully and handle every case it lists. You may run Python to check your work."
declare -A PROMPTS=(
  [lru]="pkg/lru.py does not behave like the LRUCache its docstring describes: users report recently read keys being evicted and the wrong entry being dropped on overflow. Fix it.$SPEC"
  [intervals]="pkg/intervals.py: merge() gives wrong results on several inputs and insert() is not implemented. Make the module match its docstring.$SPEC"
  [calc]="pkg/calc.py's evaluate() gets operator precedence, associativity and division wrong, and accepts malformed input it should reject. Fix it.$SPEC"
  [csvparse]="pkg/csvparse.py's parse_csv is a naive split that breaks on quoted fields. Rewrite parse_csv so it satisfies its docstring.$SPEC"
  [rename]="Follow the TASK in the docstring of pkg/textutil/core.py: rename normalise to normalize across the package and all of its callers, keeping a deprecated alias.$SPEC"
  [toposort]="pkg/toposort.py's order() ignores its tie-breaking rule and never detects dependency cycles. Make it match its docstring.$SPEC"
  [ratelimit]="pkg/ratelimit.py's TokenBucket loses fractional tokens, can exceed its capacity, and consumes tokens even when it refuses a request. Fix it.$SPEC"
  [semver]="pkg/semver.py: compare() orders versions incorrectly and satisfies() is not implemented. Make the module match its docstring.$SPEC"
  [money]="pkg/money.py uses floats, so split() loses or invents cents and round_half_even() rounds wrongly. Fix both functions.$SPEC"
  [envsubst]="pkg/envsubst.py's expand() only handles bare \$NAME. Implement everything its docstring specifies.$SPEC"
  [pagination]="Clients paging through list_page in pkg/api.py lose items, get an extra empty final page, and bad cursors crash instead of being rejected. The bugs may be in more than one file. Fix them.$SPEC"
  [trie]="pkg/trie.py's Trie is case-sensitive, overwrites weights instead of adding them, ranks results only alphabetically, and delete() neither prunes nodes nor updates len(). Fix it.$SPEC"
)

RESULTS="$OUT/results.tsv"
echo -e "harness\tmodel\ttask\trun\tsec\tsuccess\tpassed\tfailed" > "$RESULTS"
TASKS="${TASKS:-lru intervals calc csvparse rename toposort ratelimit semver money envsubst pagination trie}"
RUNS="${RUNS:-1 2 3}"

for task in $TASKS; do
  for run in $RUNS; do
    WORK="$OUT/${task}-${run}"
    rm -rf "$WORK"; cp -r "$SRC" "$WORK"
    PROMPT="${PROMPTS[$task]}"
    WWSL=$(echo "$WORK" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
    printf '%s' "$PROMPT" > "$OUT/${task}-${run}.prompt"
    PWSL=$(echo "$OUT/${task}-${run}.prompt" | sed 's|^/\([a-z]\)/|/mnt/\1/|')
    RUNNER="$OUT/run-${task}-${run}.sh"
    {
      echo '#!/usr/bin/env bash'
      echo 'set -uo pipefail'
      echo 'export PATH="/home/YOU/.nvm/versions/node/v24.18.0/bin:/home/YOU/.local/bin:/usr/local/bin:/usr/bin:/bin"'
      echo "P=\$(cat $PWSL)"
      echo "W=$WWSL"
      echo 'cd "$W" || exit 1'
      echo 'export HERMES_HOME=/home/YOU/.hermes'
      echo 'export HOME="$W"'
      echo "exec hermes -z \"\$P\" -m $MODEL --yolo"
    } > "$RUNNER"
    RWSL=$(echo "$RUNNER" | sed 's|^/\([a-z]\)/|/mnt/\1/|')

    # Always guarded: probe the slot and reload a degenerate server first (see slot-guard.sh).
    wsl.exe -d Ubuntu-24.04 -- bash -c "bash /mnt/d/LocalAI/config/harnesses/slot-guard.sh $MODEL" \
      | tee -a "$OUT/guard.log"

    START=$(date +%s.%N)
    timeout -k 30 $TIMEOUT wsl.exe -d Ubuntu-24.04 -- bash -c "sed -i 's/\r$//' $RWSL; bash $RWSL" \
      > "$OUT/${task}-${run}.out" 2> "$OUT/${task}-${run}.err"
    END=$(date +%s.%N)
    SEC=$(awk -v a="$START" -v b="$END" 'BEGIN{printf "%.1f", b-a}')

    # Hidden tests go in only now. Overwrite anything the model may have written there.
    mkdir -p "$WORK/tests"
    cp "$TESTS/test_${task}.py" "$WORK/tests/test_${task}.py"
    (cd "$WORK" && PYTHONPATH="$(cygpath -w "$WORK")" "$PYTEST" -m pytest "tests/test_${task}.py" -q -p no:cacheprovider) \
      > "$OUT/${task}-${run}.pytest" 2>&1
    LAST=$(tail -1 "$OUT/${task}-${run}.pytest")
    PASSED=$(echo "$LAST" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+')
    FAILED=$(echo "$LAST" | grep -oE '[0-9]+ (failed|errors?)' | awk '{s+=$1} END {print s+0}')
    if [ "${PASSED:-0}" -gt 0 ] && [ "$FAILED" -eq 0 ]; then SUCCESS=1; else SUCCESS=0; fi

    echo -e "hermes\t${MODEL}\t${task}\t${run}\t${SEC}\t${SUCCESS}\t${PASSED:-0}\t${FAILED}" >> "$RESULTS"
    echo "[hard/$MODEL $task run $run] ${SEC}s success=$SUCCESS (${PASSED:-0} passed, ${FAILED} failed)"
  done
done
echo "=== H2H_HARD_DONE ($MODEL) ==="
