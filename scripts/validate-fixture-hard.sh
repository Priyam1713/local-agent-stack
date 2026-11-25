#!/usr/bin/env bash
# Validate the hard fixture (2026-11-25). RUN FROM GIT BASH.
# Every hidden test file must FAIL against the shipped starting code and PASS against the
# reference solution -- otherwise the task measures nothing (or is unsolvable as specified).
set -uo pipefail
SRC=/d/LocalAI/fixture-hard
REF=/d/LocalAI/fixture-hard-ref
TESTS=/d/LocalAI/fixture-hard-tests/tests
PY=/d/LocalAI/fixture/.venv/Scripts/python.exe
TMP=$(mktemp -d)
bad=0
declare -A res
for t in lru intervals calc csvparse rename toposort ratelimit semver money envsubst pagination trie; do
  for variant in start ref; do
    W="$TMP/$t-$variant"
    cp -r "$SRC" "$W"
    [ "$variant" = ref ] && cp -r "$REF/pkg/." "$W/pkg/"
    mkdir -p "$W/tests" && cp "$TESTS/test_$t.py" "$W/tests/"
    out=$(cd "$W" && PYTHONPATH="$(cygpath -w "$W")" "$PY" -m pytest "tests/test_$t.py" -q -p no:cacheprovider 2>&1 | tail -1)
    res[$variant]="$out"
  done
  ok_start=1; ok_ref=1
  echo "${res[start]}" | grep -qE "failed|error" || ok_start=0
  echo "${res[ref]}" | grep -qE "^[0-9]+ passed" && ! echo "${res[ref]}" | grep -qE "failed|error" || ok_ref=0
  verdict=OK; [ $ok_start = 1 ] && [ $ok_ref = 1 ] || { verdict=BAD; bad=1; }
  printf '%-11s %-4s start: %-38s ref: %s\n' "$t" "$verdict" "${res[start]}" "${res[ref]}"
done
rm -rf "$TMP"
[ $bad = 0 ] && echo "=== FIXTURE_VALID ===" || echo "=== FIXTURE_INVALID ==="
