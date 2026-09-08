# Model Ledger

Every GGUF that has passed through this stack. Sizes are from `stat`, isolated speed from
`llama-bench`, correctness and reasoning:content from Pi's real agent loop. Totals here are
computed from source data, never hand arithmetic.

**Two fixtures — do not compare scores across them.** Work up to 2026-09-04 used a
`5-task × 3-run` fixture (15 trajectories); it stopped discriminating once several models
reached a perfect 15/15, so it was replaced by an `8-task × 3-run` fixture (24 trajectories)
adding a feature-extension, a cross-function refactor, and a three-bug multi-step task. Both
Nemotron and APEX scored 15/15 on the old fixture and then separated cleanly on the new one.
Every row below is tagged with the fixture that produced it.

## Live in the stack (3 slots)

| Model | Fixture | All-three | Individual | Wall/success | Reasoning:content | Tool errors | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| Tiel-Coder-35B-A3B MTP UD-Q3_K_XL (`deep-tiel`) | 8-task ×2 | 8/8, 8/8 | 24/24, 24/24 | 59.4s / 60.5s | 0.94:1 / 0.86:1 | 55 / 40 | Only model to complete the fixture with zero failures, on two independent passes. Best tool-error count and reasoning ratio recorded. Kept *alongside* APEX rather than replacing it — both passes ran the same 8 tasks, so what's proven is reproducibility, not breadth. |
| Qwen3.6-35B-A3B APEX-Compact (`deep`) | 8-task | 7/8 | 23/24 | 52.29s | 1.32:1 | 55 | Fastest deep-class model per success; the reference challenger for everything tested after it. Beat Nemotron twice, then Qwen3-Coder, K2-MoVA, and CalibForge. |
| Qwen3.5-9B Q6_K (`fast`) | 8-task | 6/8 | 22/24 | 48.37s | 2.54:1 | 90 | Fastest of anything in the stack; the baseline any small-model candidate has to clear. Both K2-Horizon 7B quants were measured against it and neither justified displacing it. |

## Rejected on the 8-task protocol

| Model | All-three | Individual | Wall/success | Reasoning:content | Tool errors | Why rejected |
|---|---:|---:|---:|---:|---:|---|
| CalibForge-35B-A3B i1-IQ3_M | 8/8 | 24/24 | 76.90s | 4.95:1 | 245 | **Perfect correctness, still lost.** Best prompt-processing benchmark of any challenger (+22% over APEX) and matched the best correctness ever recorded — then finished last on wall-clock because it burned 1.22M reasoning characters to produce the same answer volume as Tiel's 231K (6× more). Strictly dominated by Tiel on every practical axis. |
| Nemotron 3.5 Lightning 30B-A3B Q4_0 | 6/8 | 19/24 | 168.27s | 2.10:1 | 470 | Held `deep` until APEX matched its correctness at 34% faster. Kept as a control on the reasoning that 15 trajectories couldn't prove dominance over longer sessions — then fell from a perfect 15/15 (old fixture) to 19/24 on the harder one, vindicating that caution exactly. |
| K2-Horizon-MoVA-36B-A4B Q3_K_M | 6/8 | 22/24 | 104.61s | 2.37:1 | 90 | Required a third-party fork (`k2-horizon` isn't in mainline llama.cpp). Vendor claims ("outscores models up to 15× its size") didn't survive a real agent loop — twice APEX's wall-clock for worse correctness. *"MoVA" means Mixture-of-Values Attention, not vision.* |
| K2-Horizon-7B Q8_0 | 7/8 | 23/24 | 55.26s | 1.97:1 | 215 | Matched APEX-35B's correctness exactly from a fully GPU-resident 7B — a genuine result. Rejected anyway: against `fast` (the slot it would take), the margin was one trajectory out of 24, bought at 2.4× the tool errors and a permanent fork dependency. |
| K2-Horizon-7B Q6_K | 6/8 | 22/24 | 65.77s | 1.75:1 | 175 | Tested to see if a lighter quant would cut Q8_0's tool-error rate. It didn't (175 vs `fast`'s 90) — the fumbling is inherent to the model, not the quantization. Also worse than Q8_0 on correctness. |
| Macaron-V1-Tall i1-IQ4_XS | 5/8 | 20/24 | 67.33s | 1.60:1 | 85 | Loses to both incumbents on correctness *and* wall-clock. Its 5-task screen showed a 24.7:1 reasoning ratio that looked like disaster; the real protocol measured 1.60:1 — screen ratios don't predict protocol ratios in either direction. |

## Rejected on the 5-task protocol (not comparable to the section above)

| Model | All-three | Individual | Wall/success | Reasoning:content | Why rejected |
|---|---:|---:|---:|---:|---|
| gpt-oss-20b UD-Q4_K_XL | 1/5 | 9/15 | 50.8s | 28.0:1 | The reversal that established the whole methodology: 5/5 on an isolated screen at 101 tok/s (fastest raw throughput ever measured here), then 9/15 under real multi-turn tool use — repeatedly re-reading context up to 21× without acting, then aborting. |
| Qwen3-Coder-30B-A3B-Instruct | 4/5 | 14/15 | 47.11s | 0.0:1 | 0.0:1 because the architecture emits no reasoning channel at all — not efficiency, an absence. Lost to APEX on both correctness and wall-clock. |
| Qwen3.8-27B OBLITERATED IQ4_XS | 0/5 | 7/15 | n/a | — | Held the uncensored role against a pre-declared gate (≤13/15 = delete). Every failure was complete non-action — one file read, then the turn ended with no edit attempt, three times running. The uncensored role currently has no model. |
| LFM2-24B-A2B | 0/5 | 0/15 | n/a | — | The only model to score zero. Not one of 15 trajectories produced a passing edit. |

## Rejected earlier, or without a full protocol run

| Model | Size | How far it got | Why rejected |
|---|---:|---|---|
| Qwen3.6-35B-A3B APEX I-Mini | 13.32 GiB | Screen: 3/5 | Two answers came back completely empty — full 4,096-token budget spent on reasoning, zero output. 93.1:1 ratio, the worst measured. |
| gemma-4-31B-it UD-IQ3_XXS | 11.01 GiB | 5-task: 5/5, 15/15 | Matched incumbents on correctness at 316.0s/success — 4.8× slower, no compensating quality edge. |
| gemma-4-26B-A4B-it UD-IQ3_S | 10.50 GiB | 5-task: 4/5, 14/15 | Best raw speed and best isolated correctness of its sweep, then reasoning overhead exploded to 29.1:1 under real load, ~2× the incumbent wall-clock. |
| gemma-4-12b-it UD-Q6_K_XL | 9.94 GiB | 5-task: 4/5, 13/15 | Genuine non-termination: 3 of 15 runs hit a hard 400s timeout after generating 400,000+ characters, cut off mid-tool-call. |
| Qwen3.8-27B UD-IQ3_XXS | 10.17 GiB | 5-task: 3/5, 13/15 | Healthy 4.5:1 ratio but failed 2 of 15 outright — complete non-action, read the file up to 7 times, never edited. |
| Gemma 4 26B-A4B UD-Q4_K_XL | 17.01 GiB | Isolated single-shot only | Same correctness as the then-incumbent but 12% slower; superseded before the real-loop protocol existed. |
| DeepSeek-R1-Distill-Qwen-14B Q5_K_L | 10.23 GiB | Screen: 4/5 | Burned its entire token budget reasoning about binary search and returned zero code. |
| Qwen3.8-27B-OBLITERATED Q2_K | 10.11 GiB | Screen: 4/5 | Looked 2.8× faster than IQ4_XS on paper, then introduced a binary-search off-by-one (`hi = m - 1` against an exclusive bound) that silently drops present elements. The near-miss that established this project's capability-first testing rule. |
| Qwen3.8-27B-OBLITERATED Q6_K | 20.88 GiB | Benchmark only: 4.2 tok/s | 2× slower than IQ4_XS of the same model, for quantization quality no coding task could perceive. |
| Ornith-1.5-35B-A3B | ~21.7 GiB | 0/3 on a fair retest | Self-reported SWE-bench 79 / Terminal-Bench 67.8 with no third-party reproduction. Delivered zero usable content three separate times at 8,192 tokens. |
| Qwen3.6-27B Q4_K_M | 18.08 GiB | Deleted untested | Dense, above the residency cliff, in a class where every dense model tested had already lost on wall-clock. |
| Sarvam-30B Q4_K_M | 18.24 GiB | Cannot load | Architecture unsupported by llama.cpp — rejected before comparison was possible. |

## What's still on disk, unused

| Item | Size | Status |
|---|---:|---|
| Ornith-1.5-9B Q6_K + mmproj | 7.72 GiB | Retained pending a working vision path — the only intact vision projector on disk. Its 35B sibling scored 0/3, so its own prospects are unproven. |
| APEX mmproj | 0.84 GiB | Loads without error, produces garbage output. The stack currently has **no working vision path**. |

## Key numbers

- **VRAM ceiling on this hardware:** 11,000 MiB. Below it, MoE models run 24-100+ tok/s;
  above it, performance collapses to single digits.
- **`--n-cpu-moe`** (llama.cpp): offloads routed MoE experts to system RAM. Only applies to
  genuine MoE architectures, not dense models. The right value is architecture- and
  quant-specific and does not transfer between models — it must be swept per model.
- **240 trajectories** run through the 8-task protocol across 10 protocol runs, as of the
  last update to this file.
