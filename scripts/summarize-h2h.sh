#!/usr/bin/env bash
# Per-category matrix across every completed harness/slot run.
#
#   summarize-h2h.sh [slot]
#
# Two things this deliberately does NOT do:
#
# 1. It does not report an aggregate pass rate alone. The whole question is whether a harness
#    owns a particular task category, and 23/24 tells you nothing about which one it missed.
#
# 2. It does not report the median alone. Pi's deep-tiel run has a 28.2s median -- the fastest
#    in the field -- and a 9163.9s worst case, a single trajectory that ran 100x its own
#    median and blew straight through a 500s timeout. A summary line carrying only the median
#    makes the harness with the worst tail risk look like the best choice.
set -uo pipefail
SLOT="${1:-}"

printf "%-34s %-12s %-10s" "run-dir" "harness" "slot"
for t in alias auth median overlay rollback cache dedupe pipeline; do printf " %-9s" "$t"; done
printf " %-7s %-9s %-8s %-9s\n" "TOTAL" "median_s" "p90_s" "max_s"
printf '%s\n' "----------------------------------------------------------------------------------------------------------------------------------------------------"

for d in /d/LocalAI/results/h2h-harness-runs-*/results.tsv; do
  [ -f "$d" ] || continue
  n=$(awk -F'\t' 'NR>1' "$d" | wc -l)
  [ "$n" -ge 8 ] || continue          # skip 1-task smoke runs
  h=$(awk -F'\t' 'NR==2{print $1}' "$d"); m=$(awk -F'\t' 'NR==2{print $2}' "$d")
  [ -z "$SLOT" ] || [ "$m" = "$SLOT" ] || continue
  printf "%-34s %-12s %-10s" "$(basename "$(dirname "$d")" | sed s/h2h-harness-runs-//)" "$h" "$m"
  for t in alias auth median overlay rollback cache dedupe pipeline; do
    printf " %-9s" "$(awk -F'\t' -v t="$t" 'NR>1&&$3==t{s+=$6;n++} END{printf "%d/%d", s+0, n+0}' "$d")"
  done
  awk -F'\t' '
    NR>1 { s+=$6; n++; v[n]=$5 }
    END {
      asort(v)
      mid = (n%2) ? v[(n+1)/2] : (v[n/2] + v[n/2+1]) / 2
      i = int(n*0.9); if (i < 1) i = 1
      printf " %-7s %-9.1f %-8.1f %-9.1f\n", sprintf("%d/%d", s, n), mid, v[i], v[n]
    }' "$d"
done
