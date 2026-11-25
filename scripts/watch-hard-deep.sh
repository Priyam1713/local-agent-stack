#!/usr/bin/env bash
# Watches the `deep` hard run (Git Bash). Exits with a one-line verdict when either:
#   LOST  -- deep has more failed trajectories than Inkling's total (it can no longer tie), or
#   DONE  -- the deep run finished.
# User rule 2026-11-25: stop deep as soon as it loses to Inkling; no reruns for slowness.
R=/d/LocalAI/results
INK_FAILS=$(awk -F'\t' 'NR>1 && $6==0{n++} END{print n+0}' $R/h2h-hard-hermes-test-inkling-iq3/results.tsv)
while true; do
  F=$R/h2h-hard-hermes-deep/results.tsv
  if [ -f "$F" ]; then
    read -r N FAILS < <(awk -F'\t' 'NR>1{n++; if($6==0) f++} END{print n+0, f+0}' "$F")
    if [ "$FAILS" -gt "$INK_FAILS" ]; then echo "LOST deep fails=$FAILS > inkling fails=$INK_FAILS after $N trajectories"; exit 0; fi
  fi
  if grep -q "H2H_HARD_DONE (deep)" $R/protocol-hard-deep.log 2>/dev/null; then echo "DONE deep fails=$FAILS after $N"; exit 0; fi
  sleep 60
done
