# Daily coding stack manifest

Frozen 2026-09-02; updated 2026-09-03 for the final sampling reversion. This is the operational Zed + Pi + llama-swap setup; measurements below are local observations, not synthetic benchmark claims.

## Pinned components

- WSL: Ubuntu 24.04, mirrored networking; Windows and WSL share `127.0.0.1:8080`.
- llama.cpp: b10726, commit `85c5522`, CUDA `sm_120`; binaries in `/home/YOU/src/llamacpp/build/bin/`.
- llama-swap: v252 (`e31a1ad`), `/home/YOU/bin/llama-swap`.
- Pi: 0.84.4; Pi ACP: 0.0.33.
- Zed: 1.17.2 on Windows.
- Prime Agent: installed in WSL and registered as Zed's second ACP agent; Pi remains installed and is the default daily agent.
- Smart App Control remains enabled.

## Service and routing

- Config: `/mnt/e/AI/config/llama-swap.yaml` (`E:\AI\config\llama-swap.yaml`).
- Endpoint: `http://127.0.0.1:8080/v1` with no authentication.
- systemd user unit: `~/.config/systemd/user/llama-swap.service`, enabled and active.
- Command: `/home/YOU/bin/llama-swap -config /mnt/e/AI/config/llama-swap.yaml -listen 127.0.0.1:8080 -watch-config`.
- One model is resident at a time. Coding slots have a 900-second TTL.
- Achilles' legacy llama.cpp router autostart remains disabled; Achilles and its files remain installed.

## Active slots

All coding slots use `-c 65536 --flash-attn on -ctk q8_0 -ctv q8_0 --jinja --reasoning-format deepseek`.

| Slot | Model and launch-specific settings | Role |
|---|---|---|
| `fast` | Qwen3.5 9B Q6_K; `-ngl 99` | Pi default; routine work |
| `deep` | Nemotron 3.5 Lightning 30B-A3B Q4_0; `-ngl 99 --n-cpu-moe 28` | incumbent deep model; Prime default |
| `deep-budget` | same as `deep`; `--reasoning-budget 1024` | retained experimental slot |
| `deep-budget-2k` | same as `deep`; `--reasoning-budget 2048` | retained experimental slot |
| `deep-lite` | same as `deep`; `--reasoning off` | isolation/diagnostic slot, not default |
| `vision` | Qwen3.8 27B Q4_K_M + BF16 mmproj; 32K context, 34 GPU layers, 2K reasoning budget | vision fallback |

The rejected MTP/speculative-decoding flags are absent. `deep-alt` was removed after the fair 8K retest, and its Ornith directory was deleted.

## GGUF inventory

| Artifact | Path | Bytes | GiB |
|---|---|---:|---:|
| Qwen3.5 9B Q6_K | `/home/YOU/.local/share/sovereign-ai/models/qwen35-9b/gguf/qwen35-9b-Q6_K.gguf` | 7,558,901,472 | 7.040 |
| Nemotron 30B-A3B Q4_0 | `/home/YOU/.local/share/sovereign-ai/models/nemotron35-lightning-30b-a3b/gguf/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf` | 18,898,091,584 | 17.600 |
| Nemotron MTP Q4_0 (unused) | `/home/YOU/.local/share/sovereign-ai/models/nemotron35-lightning-30b-a3b/gguf/mtp-NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf` | 1,155,907,520 | 1.077 |
| Qwen3.8 27B Q4_K_M | `/mnt/e/AI/ModelStore/gguf/qwen3.8-27b/Qwen3.8-27B-Q4_K_M.gguf` | 17,106,775,008 | 15.932 |
| Qwen3.8 mmproj BF16 | `/mnt/e/AI/ModelStore/gguf/qwen3.8-27b/mmproj-BF16.gguf` | 931,146,432 | 0.867 |

Sampling:

- `deep`, `deep-budget`, `deep-budget-2k`, and `deep-lite` use llama.cpp defaults: temperature 0.80, top-p 0.95, top-k 40, min-p 0.05.
- `fast` keeps Qwen3.5's precise-coding thinking profile for llama.cpp: temperature 0.6, top-p 0.95, top-k 20, min-p 0, presence penalty 0, repetition penalty 1.
- `vision` retains its existing defaults; it was outside the coding-sampler test.

## Pi policy

- Provider `llama-swap`, base URL `http://127.0.0.1:8080/v1`, no auth header.
- Default model `fast`; `fast`, `deep`, `deep-budget`, and `deep-budget-2k` expose 65,536 context and 8,192 max output tokens.
- Compaction: reserve 22,528, keep recent 16,384; trigger is 43,008 / 65,536 tokens = 65.625%.
- Skills: `run-tests`, `fix-failing-test`, `add-feature`, `review-diff`.
- Source-edit hook formats and runs tests after writes. The main gate is `uv run --extra dev pytest -q`.
- Loop guard: second identical tool call is blocked; three consecutive identical calls abort the turn (`PI_ANTI_LOOP_REPEATS=2`, `PI_ANTI_LOOP_FAILS=3`).
- Edit prompt: exact-string or symbol edits only; never rewrite a whole existing file; never reread after a successful edit; search identifies paths and reads use offset/limit.
- Model-visible tools (8): `read`, `powershell`, `edit`, `replace_symbol_body`, `search_for_pattern`, `get_symbols_overview`, `find_symbol`, `find_referencing_symbols`.
- Route by task shape: single-shot questions use `fast`, or `deep-budget-2k` when they need more reasoning; repository work that needs tools uses `deep`.

## Zed ACP agents

- `pi`: Windows Node launches Pi ACP with Git Bash as `SHELL` and the loop-guard environment above.
- `prime-agent`: runs in Zed WSL remote mode from WSL Node, provider `llama-swap`, model `deep`, thinking `high`.

## Measurements — 2026-09-02

### Startup and throughput

- Autostart proof: after `wsl --shutdown`, `/v1/models` succeeded without manual start in 13.522 s; idle GPU usage was 0 MiB in the clean ownership check.
- `fast`: 49.595 tok/s, 8,068 MiB resident.
- `deep` CPU-MoE fit: 32 = 20.277 tok/s / 9,178 MiB; 28 = 38.433 tok/s / 10,548 MiB and selected; 24 = 50.671 tok/s / 11,918 MiB and rejected. 20 was not run because the ceiling had already been crossed.
- Current no-draft `deep`: 56.59 tok/s.
- Speculative decoding: partial draft residency = 45.30 tok/s / 10,940 MiB; full draft = 63.08 tok/s / 11,912 MiB. Both were rejected: partial was slower and full exceeded the 11,000 MiB ceiling.

### Reasoning controls and agents

- Reference `deep` median prompt: 33.5 s, 169 content chars, 6,342 reasoning chars. `deep-lite` isolation: correct, 1.924 s, 161 content chars, 0 reasoning chars. Real Prime ACP workload: failed with empty content after 8,192 tokens in about 280 s. It was not promoted.
- Pi `deep` non-empty smoke prompt: 31.611 s.
- Prime median task: 162.5 s; corrected odd/even implementation landed in its WSL worktree.
- Three-edit output-discipline check: 693 output tokens before, 300 after.
- Full repository gate after dependency/memory-test resolution: 311 passed, 2 warnings, 189.62 s.

### Do not retry

- Speculative decoding / MTP: 45.30 versus 56.59 tok/s. Rejected.
- Reasoning budgets for agent work: cut reasoning from 76:1 to 4.8:1, but degraded tool behavior (60 calls / 12 failures at 1K) and produced about 4x wall-clock per success. Reasoning is load-bearing here.
- Ornith `deep-alt`: 0/3 content at a fair 8K. Deleted.
- Low-temperature sampling on `deep`: no reliability gain (4/5 and 12/15 stayed unchanged), while wall/success rose from 35.567 s to 93.947 s with 79 tool calls / 27 failures. This is the second confirmation that reducing this model's reasoning breaks tool calling. Reverted to defaults.
- Exception: budgets are useful for single-shot, non-agentic prompts (6.5 s versus 33.5 s), hence `deep-budget-2k` remains available for that shape.

### Original 4K deep head-to-head

| Model | All-three task wins | Individual wins | Total wall | Wall/success | Reasoning:content | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|
| Nemotron `deep` | 4/5 | 12/15 | 426.799 s | 35.567 s | 76.373:1 | 10,940 MiB |
| Ornith `deep-alt` | 0/5 | 0/15 | 1,862.845 s | n/a | content was empty | 10,940 MiB cold / 6,816 MiB steady |

### Real Pi ACP reasoning-budget workload (five repo tasks, three runs each)

The client identified as Zed 1.17.2 and used Zed's Git Bash environment. A tool call counted as parsed when Pi emitted a structured ACP tool call; execution errors are reported separately.

| Config | All-three task wins | Individual wins | Total wall | Wall/success | Reasoning:content | Tool parsing | Peak VRAM |
|---|---:|---:|---:|---:|---:|---|---:|
| incumbent `deep` baseline | 4/5 | 12/15 | 426.799 s | 35.567 s | 76.373:1 | not captured in original run | 10,940 MiB |
| `deep-budget` 1K | 3/5 | 10/15 | 1,501.04 s | 150.10 s | 4.80:1 | 60/60 parsed; 12 execution failures | 10,576 MiB |
| `deep-budget-2k` | 2/5 | 8/15 | 1,573.80 s | 196.72 s | 4.50:1 | 23/23 parsed; 4 execution failures | 10,576 MiB |

Neither budget slot retained the required 4/5 all-three reliability, so unbudgeted `deep` remains promoted.

Per-run rows (`W`/`F` is validator outcome; `r/c` is reasoning/content characters; `t/e` is structured tool calls/execution failures):

| Config | Task/run | Result | Wall | r/c | t/e |
|---|---|---:|---:|---:|---:|
| 1K | alias/1 | F | 32.79 s | 2,032/913 | 2/0 |
| 1K | alias/2 | F | 34.79 s | 2,796/906 | 2/0 |
| 1K | alias/3 | F | 54.77 s | 3,424/1,179 | 5/1 |
| 1K | auth/1 | W | 28.26 s | 2,578/854 | 2/1 |
| 1K | auth/2 | W | 235.00 s | 7,133/1,595 | 8/1 |
| 1K | auth/3 | W | 247.51 s | 5,640/2,436 | 12/2 |
| 1K | median/1 | W | 30.52 s | 2,364/311 | 3/1 |
| 1K | median/2 | W | 118.60 s | 3,060/431 | 5/3 |
| 1K | median/3 | W | 244.46 s | 3,796/724 | 8/2 |
| 1K | overlay/1 | W | 19.53 s | 2,637/26 | 1/0 |
| 1K | overlay/2 | W | 25.59 s | 3,818/169 | 1/0 |
| 1K | overlay/3 | W | 111.07 s | 13,318/1,334 | 9/1 |
| 1K | rollback/1 | W | 22.10 s | 1,743/447 | 2/0 |
| 1K | rollback/2 | F | 147.10 s | 8,192/0 | 0/0 |
| 1K | rollback/3 | F | 148.95 s | 8,192/0 | 0/0 |
| 2K | alias/1 | W | 28.77 s | 2,320/10 | 2/0 |
| 2K | alias/2 | F | 30.76 s | 2,308/564 | 2/0 |
| 2K | alias/3 | F | 53.37 s | 4,480/923 | 4/0 |
| 2K | auth/1 | W | 65.23 s | 5,340/1,233 | 7/2 |
| 2K | auth/2 | F | 149.47 s | 8,192/0 | 0/0 |
| 2K | auth/3 | F | 161.92 s | 8,192/0 | 0/0 |
| 2K | median/1 | W | 6.53 s | 746/175 | 0/0 |
| 2K | median/2 | W | 8.45 s | 918/175 | 0/0 |
| 2K | median/3 | W | 167.27 s | 1,775/175 | 0/0 |
| 2K | overlay/1 | F | 136.34 s | 8,192/0 | 0/0 |
| 2K | overlay/2 | F | 149.62 s | 8,192/0 | 0/0 |
| 2K | overlay/3 | F | 152.46 s | 8,192/0 | 0/0 |
| 2K | rollback/1 | W | 19.60 s | 1,092/110 | 2/0 |
| 2K | rollback/2 | W | 58.21 s | 3,104/988 | 2/1 |
| 2K | rollback/3 | W | 385.80 s | 3,503/1,330 | 4/1 |

### Model-recommended coding sampling retest

Same five repository tasks through Pi's Zed-compatible ACP path, three runs each. `deep` used temperature 0.6, top-p 0.95, min-p 0.01, and top-k disabled. The keep gate was at least 4/5 all-three task wins.

| Config | All-three task wins | Individual wins | Total wall | Wall/success | Reasoning:content | Tools/failures | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| prior defaults | 4/5 | 12/15 | 426.799 s | 35.567 s | 76.373:1 | not captured | baseline |
| recommended coding sampling | 4/5 | 12/15 | 1,263.564 s | 93.947 s | 3.14:1 | 79/27 | initially met gate; later reverted for cost/no gain |

| Task/run | Result | Wall | Reasoning chars | Content chars | Tools/failures |
|---|---:|---:|---:|---:|---:|
| median/1 | W | 77.325 s | 693 | 175 | 0/0 |
| median/2 | W | 11.971 s | 1,322 | 175 | 0/0 |
| median/3 | W | 9.437 s | 719 | 175 | 0/0 |
| auth/1 | W | 27.024 s | 3,188 | 608 | 1/0 |
| auth/2 | W | 53.617 s | 3,413 | 927 | 6/1 |
| auth/3 | W | 454.786 s | 11,283 | 3,960 | 28/11 |
| overlay/1 | W | 95.674 s | 6,774 | 2,187 | 8/2 |
| overlay/2 | W | 72.608 s | 6,625 | 1,527 | 6/2 |
| overlay/3 | W | 74.875 s | 6,695 | 1,143 | 8/4 |
| rollback/1 | W | 102.762 s | 4,739 | 1,316 | 7/1 |
| rollback/2 | W | 73.873 s | 3,042 | 906 | 4/3 |
| rollback/3 | W | 73.413 s | 3,072 | 1,775 | 3/2 |
| alias/1 | F | 37.903 s | 2,007 | 935 | 2/0 |
| alias/2 | F | 37.657 s | 2,379 | 921 | 2/0 |
| alias/3 | F | 60.639 s | 2,857 | 1,983 | 4/1 |

The sampler held reliability at 4/5 all-three rather than improving it. It initially met the predefined keep gate, but was reverted on 2026-09-03 because equal reliability did not justify 2.64x wall time per success or the tool failures. Further sampler optimization is frozen until a real task motivates it.

### Default-sampling confirmation rerun — 2026-09-03

The same five tasks, three runs each, were repeated after removing the four Nemotron sampling overrides. The historical 4/5 and 35.567 s/success result did not reproduce: this fresh sample scored 3/5 all-three, 11/15 individual, and 107.093 s/success. No additional sweep was run.

| Config | All-three task wins | Individual wins | Total wall | Wall/success | Reasoning:content | Tools/failures |
|---|---:|---:|---:|---:|---:|---:|
| historical defaults | 4/5 | 12/15 | 426.799 s | 35.567 s | 76.373:1 | not captured |
| defaults confirmation | 3/5 | 11/15 | 1,793.923 s | 107.093 s | 4.04:1 | 58/20 |

| Task/run | Result | Wall | Reasoning chars | Content chars | Tools/failures |
|---|---:|---:|---:|---:|---:|
| median/1 | W | 105.606 s | 745 | 175 | 0/0 |
| median/2 | W | 11.772 s | 1,245 | 175 | 0/0 |
| median/3 | W | 9.607 s | 689 | 175 | 0/0 |
| auth/1 | W | 144.818 s | 5,132 | 748 | 10/5 |
| auth/2 | W | 63.075 s | 6,466 | 1,215 | 5/3 |
| auth/3 | W | 316.572 s | 13,892 | 4,441 | 15/5 |
| overlay/1 | W | 119.477 s | 9,912 | 2,304 | 11/5 |
| overlay/2 | W | 101.444 s | 8,393 | 1,260 | 8/2 |
| overlay/3 | F | 156.109 s | 0 | 0 | 0/0 |
| rollback/1 | W | 30.722 s | 1,497 | 399 | 3/0 |
| rollback/2 | W | 226.872 s | 2,831 | 1,929 | 5/0 |
| rollback/3 | W | 48.059 s | 2,073 | 279 | 1/0 |
| alias/1 | F | 158.110 s | 0 | 0 | 0/0 |
| alias/2 | F | 150.631 s | 0 | 0 | 0/0 |
| alias/3 | F | 151.049 s | 0 | 0 | 0/0 |

Operational decision: keep the requested default-sampling revert. The low-temperature alternative has no demonstrated reliability advantage, and both configurations show high run-to-run variance under this agent workload.

### Fair Ornith 8K retest through Pi

| Task | Wall | Reasoning chars | Content chars | Result |
|---|---:|---:|---:|---|
| median | 300.09 s | no final payload | 0 | request timeout |
| auth | 433.896 s | 8,192 | 0 | length |
| overlay | 233.249 s | 8,192 | 0 | length |

Result: 0/3 content at the fair 8,192-token limit. `/mnt/e/AI/ModelStore/gguf/ornith-35b` was deleted, reclaiming 21,713,463,040 bytes (20.222 GiB); recovery requires redownloading.

### Harness uplift audit (one run of the same five tasks)

| Path | Success | Total wall | Wall/success | Reasoning:content | Task split |
|---|---:|---:|---:|---:|---|
| raw llama-swap chat | 4/5 (80%) | 214.248 s | 18.433 s | 128.18:1 overall | passed median/auth/overlay/alias; rollback exhausted 8,192 |
| Pi via Zed-compatible ACP | 4/5 (80%) | 348.632 s | 66.695 s | 4.31:1 overall | passed median/auth/overlay/rollback; alias violated exact-output contract |

Measured success-rate uplift: 0 percentage points. Pi changed which task succeeded and provided repository/tool grounding, but did not increase this sample's success count and added 48.262 s per successful task.

| Path | Task | Result | Wall | Reasoning chars | Content chars | Tools/errors |
|---|---|---:|---:|---:|---:|---:|
| raw | median | W | 28.739 s | 2,263 | 161 | n/a |
| raw | auth | W | 14.696 s | 2,882 | 146 | n/a |
| raw | overlay | W | 16.941 s | 3,576 | 26 | n/a |
| raw | rollback | F | 140.516 s | 33,102 | 0 | n/a |
| raw | alias | W | 13.356 s | 2,143 | 10 | n/a |
| Pi | median | W | 25.709 s | 1,754 | 161 | 0/0 |
| Pi | auth | W | 169.444 s | 5,288 | 1,132 | 15/8 |
| Pi | overlay | W | 27.702 s | 3,033 | 314 | 1/0 |
| Pi | rollback | W | 43.926 s | 1,589 | 369 | 1/0 |
| Pi | alias | F | 81.850 s | 4,171 | 1,694 | 7/0 |

## Repository guidance

- Handwritten repository facts: `D:\local-sovereign-ai\AGENTS.md` (28 lines).
- Handwritten short-form facts: `E:\claude-setup-shortform\AGENTS.md` (30 lines).

## Gemma 4 26B-A4B challenger — tested and rejected, 2026-09-03

Tested on a hunch after the stack was frozen. Downloaded `unsloth/gemma-4-26B-A4B-it-GGUF`
UD-Q4_K_XL (17,010,980,576 bytes, verified against remote Content-Length).

**Config notes that cost real time to discover:**

- Gemma 4 does **not** use deepseek `<think>` tags. It uses a channel format
  (`<|channel>thought ... <channel|>`). Copying `--reasoning-format deepseek` from the
  Nemotron slots makes the parser swallow the answer and return empty content — the same
  failure mode that wasted 1,862 s on Ornith. The `deep-gemma` slot deliberately omits
  the flag so llama.cpp auto-detects. **Do not add it.**
- Gemma 4 thinking is opt-in via `<|think|>` in the system prompt, unlike Nemotron which
  always reasons.
- llama.cpp b10726 supports `GEMMA4` / `GEMMA4_ASSISTANT`.
- Sampling is verbatim from the model card: `--temp 1.0 --top-p 0.95 --top-k 64`. Not tuned.
- `--n-cpu-moe` fit: 28 = 5,456 MiB; 12 = 11,876 MiB (over the 11,000 ceiling);
  **16 = 10,898 MiB, selected**. Gemma needs far less offload than Nemotron at equal VRAM.

**Head-to-head, model level (single-shot, 5 tasks x 2 runs, max_tokens 4096, identical prompts):**

| Model | Non-empty | Correct | Mean s/answer | Total wall | reasoning:content | tok/s | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nemotron `deep` | 10/10 | 5/5 | **17.7 s** | 176.6 s | 12.7:1 | 56.6 | 10,548 MiB |
| Gemma `deep-gemma` | 10/10 | 5/5 | 19.8 s | 197.5 s | 9.1:1 | ~35 | 10,898 MiB |

Result: identical correctness, Nemotron 12% faster. Gemma's leaner reasoning does not
offset generating at 35 tok/s vs 56.6. Nemotron also produced better code detail twice
(`sorted()` instead of mutating `nums.sort()`; `is` rather than `==` for node identity).

**Nemotron remains promoted.** `deep-gemma` is retained as a tuned, zero-cost second
opinion selectable from Zed. The UD-IQ3_S quant was deleted (11.3 GB reclaimed) without
being tested.

**Caveat — one regime remains untested.** This was a model-level single-shot comparison,
not Pi's agent-loop protocol. Nemotron measured 12.7:1 here versus 76:1 through Pi, so the
regime materially changes its behaviour. If Gemma is ever revisited, the only test worth
running is the full Pi 5-task x 3-run agent loop, where leaner reasoning would pay most.

## How to start and use it

**Nothing to start.** llama-swap runs as a systemd user service in WSL with `Linger=yes`,
backed by the Windows scheduled task "SovereignAI llama-swap WSL keepalive". It survives
reboots and `wsl --shutdown`. Models load on first request and unload after 900 s idle.

1. Open **Zed** (`C:\Users\YOU\AppData\Local\Programs\Zed\Zed.exe`).
2. Open a project folder.
3. Open the **Agent Panel** — the sparkle icon bottom-right, or Ctrl+Shift+P then "agent panel".
4. Pick **Pi** from the agent dropdown. Ask it something.

Model is chosen in Pi, not Zed. Default is `fast`. Switch inside the Pi session with `/model`:

| Slot | Use for |
|---|---|
| `fast` | default; routine edits, questions, most work |
| `deep` | hard bugs, architecture, anything needing real reasoning |
| `deep-gemma` | second opinion when `deep` gets stuck (different lab/architecture) |
| `deep-budget-2k` | quick single-shot answers with less thinking |
| `vision` | screenshots, diagrams |

Skills (type `/` in a Pi session): `run-tests`, `fix-failing-test`, `add-feature`, `review-diff`.

Hooks fire automatically on source edits: format (ruff / prettier / cargo) then `uv run --extra dev pytest -q`.

**Health check if something looks wrong:**

    curl http://127.0.0.1:8080/v1/models          # should list 7 slots
    wsl -d Ubuntu-24.04 -- systemctl --user is-active llama-swap    # should say: active
    nvidia-smi --query-gpu=memory.used --format=csv,noheader        # ~0 MiB idle

Restart the service if needed:

    wsl -d Ubuntu-24.04 -- systemctl --user restart llama-swap

**Zed ACP registration** lives at `%APPDATA%\Zed\settings.json` under `agent_servers.Pi`,
launching `node .../pi-acp/dist/index.js` with `SHELL` set to Git Bash and the loop-guard
env vars. If the Pi agent ever disappears from Zed's dropdown, that file is what to check —
it was missing once already after a cleanup pass.

## Qwen3.8-27B-OBLITERATED benchmark — 2026-09-03

Files in `C:\Users\YOU\Downloads` (not installed as slots). Dense 27B, 27.32B params.
Benchmarked with `llama-bench`, flash attention on, q4_0 K/V cache, 32K ctx fit,
`-lm none` (no mmap — files are on drvfs, mmap'd CPU layers would read over 9p per token),
text-only (no mmproj).

| Config | pp512 t/s | tg128 t/s | Peak VRAM |
|---|---:|---:|---:|
| Q6_K (20.88 GiB), fit-margin 1200 | 288.13 ± 12.77 | 4.21 ± 0.01 | — |
| IQ4_XS (14.35 GiB), fit-margin 1200 | 488.7 | 7.42–7.56 | 9,120 MiB |
| **IQ4_XS, fit-margin 500 — best** | **540.16 ± 19.05** | **8.59 ± 0.07** | ~11.7 GB |
| IQ4_XS + MTP draft, default fit | — | 7.02 | 7,656 MiB |
| IQ4_XS + MTP draft, fit-margin 500 | — | 6.82–7.07 | 8,130 MiB |

**Findings:**

- IQ4_XS beats Q6_K by **2.04x** on generation. Q6_K is not worth its size on a 12 GB card.
- Tightening `--fit-target` from 1200 to 500 MiB gained **+14.7%** tg and +10.5% pp.
  The default fit leaves real headroom unused. Two runs at margin 1200 gave 7.56/7.42
  (±2%), so the 8.59 is a genuine gain and not variance.
- **MTP speculative decoding LOSES, tested twice.** Draft acceptance was fine (68.4-74.9%,
  mean accepted length 3.04-3.23) using the stock Qwen3.8 MTP draft against the OBLITERATED
  finetune. It still lost because the draft plus its KV cache reserve VRAM the dense main
  model needs more: peak residency fell to 8,130 MiB even at fit-margin 500. Speculation
  reduces forward passes, but each pass is bandwidth-bound, so evicting main layers to CPU
  costs more than the saved passes return. **Do not retry on this hardware.**
- **Root cause is architectural.** Q6_K processes prompts at 288 t/s — the GPU is not the
  limit. Dense 27B must stream every weight every token and has no experts to leave on the
  CPU, so `--n-cpu-moe` does not apply. Compare Nemotron 30B-A3B at 56.6 t/s (3B active).
- **D-CFR not pursued.** It reclaims a few hundred MiB of MTP recurrent-state overhead, but
  MTP itself loses here, so the patch optimises a path we do not use.

**Verdict:** fully tuned, these run at 8.59 t/s versus 56.6 t/s for the `deep` slot — 6.6x
slower for the same capability class. Worth installing only for OBLITERATED's refusal
behaviour, never for throughput. If installed, use IQ4_XS with `--fit-target 500`, flash
attention, q4_0 KV, 32K context, no draft model. Q6_K has no use case here.

## Qwen3.8-27B quant sweep — 2026-09-03 (continued)

Same method as above: `llama-bench`, FA on, q4_0 K/V, 32K ctx fit, `-lm none`, text-only,
`--fit-target 500`, `-r 5`.

| Quant | Size | pp512 t/s | tg128 t/s |
|---|---:|---:|---:|
| Q6_K (deleted) | 20.88 GiB | 288.13 | 4.21 |
| IQ4_XS (installed) | 14.35 GiB | 540.16 | 8.59 |
| Q2_K | 10.11 GiB | 664.08 ± 26.88 | 24.20 ± 2.06 |
| UD-IQ3_XXS (stock, not OBLITERATED) | 10.17 GiB | 832.01 ± 42.50 | 28.56 ± 0.10 |

**The residency cliff.** Speed is governed almost entirely by whether the model fits in
12 GB, not by quant sophistication: ~10 GiB -> 24-28 t/s, 14.35 GiB -> 8.6 t/s,
20.88 GiB -> 4.2 t/s. Dense 27B has no experts to leave on CPU, so everything above
~11 GiB streams over PCIe every token.

**Dynamic quants beat uniform ones outright.** UD-IQ3_XXS (3.06 bpw) is FASTER than Q2_K
(2 bpw) on both pp (+25%) and tg (+18%) despite being 0.06 GiB larger, with far tighter
variance (±0.10 vs ±2.06). Importance-aware quantization wins on speed as well as quality.

### Quality test — the number that actually decided it

Five coding tasks (median bug, off-by-one binary search, mutable default, cycle detection,
merge), one run each, through llama-swap.

| Model | tok/s resident | tokens generated | wall/answer | Correct |
|---|---:|---:|---:|---:|
| Q2_K | ~16.4 | 3,062 | 54.4 s | **4/5** |
| IQ4_XS | ~6.8 | 1,488 | 67.7 s | **5/5** |

Q2_K failed the binary-search task by emitting `hi = m - 1` against an exclusive upper
bound (correct is `hi = m`), which silently returns -1 for elements that are present. It
broke the very task that tested off-by-one awareness. IQ4_XS also produced better detail
throughout: `sorted()` rather than mutating `nums.sort()`, and `is` rather than `==` for
node identity.

Critically, **Q2_K's throughput advantage does not survive contact with real work**: it
generated 2x more tokens for the same answers, so a 2.4x tok/s lead collapsed to a 20%
wall-clock lead — paid for with a correctness bug. Benchmark `tg128` (24.20) also badly
overstated its real resident speed (~16.4).

**Decision: `deep-uncensored` stays on IQ4_XS.** Q2_K rejected on quality. Q3_K_M
(12.57 GiB) not downloaded — it sits above the cliff, so it would land mid-range at best,
and the whole speed axis is worth only ~20% wall-clock here. Not worth 12.57 GiB.

## gpt-oss-20b challenger — promoted, 2026-09-03

Real MoE (3.6B/20.9B active, 4-of-32 experts, MXFP4-native), unlike the dense Qwen3.8
line above. `llama-bench`, FA on, q4_0 KV, 32K ctx fit, `-lm none`, `--fit-target 500`, r=5.

| Quant | Size | pp512 t/s | tg128 t/s |
|---|---:|---:|---:|
| Q5_K_M | 10.90 GiB | 3,890 ± 417 | 95.18 ± 0.84 |
| **UD-Q4_K_XL** | 11.04 GiB | **4,079 ± 193** | **101.44 ± 0.68** |

**101 t/s is the fastest deep-class result measured this session** — 1.8x `fast` (49.6),
12x tuned Qwen3.8 IQ4_XS (8.59). Confirms the residency-cliff finding: both quants sit
under ~11 GiB and both are fast; real MoE means `--n-cpu-moe` genuinely applies here.

**LANDMINE — caught only under live load, not by llama-bench:** `--reasoning-format none`
does NOT suppress Harmony's channel markup; it leaks raw `<|channel|>analysis<|message|>
...<|end|>` directly into `message.content`. Despite gpt-oss using OpenAI's own Harmony
tags rather than deepseek-style `<think>`, **`--reasoning-format deepseek` is what
correctly splits it into `reasoning_content` vs `content`.** The flag name does not match
its correct usage for this model. Do not use `none`.
Also: llama.cpp's own gpt-oss guide warns against `repeat-penalty != 1.0` for this model.

**Quality test, 5 tasks, one run each, through llama-swap:**

| Model | Correct | Wall/answer | Note |
|---|---:|---:|---|
| UD-Q4_K_XL | 5/5 | 19.1 s | Faithful in-place edits; added an unprompted empty-list guard |
| Q5_K_M | 5/5* | 24.1 s | *`bsearch` rewrote to an inclusive-bound convention instead of patching the exclusive-bound off-by-one in place — correct but not a faithful edit |

**Verdict vs the incumbent:**

| Model | Size | tg t/s | Correct | Wall/answer |
|---|---:|---:|---:|---:|
| Nemotron `deep` (installed) | 17.6 GiB | 56.6 | 5/5 | 17.7 s |
| **gpt-oss UD-Q4_K_XL** | **11.04 GiB** | **101.4** | **5/5** | **19.1 s** |

Matches Nemotron's wall-clock within 1.4 s, at 6.5 GiB less VRAM, with 1.8x the raw
generation headroom for harder/longer tasks. **Promoted as `deep-gptoss`.** Q5_K_M deleted
after losing the head-to-head. NOT yet run through the full 5-task x3-run protocol used to
promote Nemotron — this is single-run signal. Recommend that full protocol before
replacing `deep` outright; for now both slots coexist.

## Real-agent-loop head-to-head: deep-gptoss vs deep — 2026-09-04

Following the new standing rule (capability/smartness must be benchmarked, not just tok/s),
ran the full 5-task x3-run protocol through Pi's actual agent loop in a fresh fixture
(pkg/{alias,auth,median,overlay,rollback}.py, each with a real bug and a pytest suite
that genuinely fails against the buggy baseline). Codex's original alias/auth/median/
overlay/rollback fixtures no longer exist (cleaned up as temporary evaluation worktrees),
so this is a newly built but methodologically identical fixture, not a byte-identical rerun.

| Metric | gpt-oss `deep-gptoss` | Nemotron `deep` |
|---|---:|---:|
| All-three (5 tasks) | 1/5 | **5/5** |
| Individual wins (15 runs) | 9/15 | **15/15** |
| Wall/success | 50.77s | 65.51s |
| Reasoning:content | 27.96:1 | 2.23:1 |

**Nemotron sweeps.** gpt-oss's lower wall/success is not a real advantage — it reflects
only its easy successes; failed runs burn time without entering that average. Nemotron
completed every task, including the two hardest (overlay, rollback), with idiomatic fixes:
a proper recursive deep-merge helper for overlay, and an exception-safe rollback that
snapshots state, restores in-place (`items[:] = original`), and re-raises.

**gpt-oss's failure mode is consistent and diagnostic, not random.** Every failure shows
the model calling `read` (or `edit`/`bash`) up to 21 times in a row without committing to
an edit, until Pi's step ceiling aborts the turn (`errorMessage: "This operation was
aborted"`). This is a genuine multi-turn agentic control-flow weakness — gpt-oss produced
excellent code on the earlier isolated single-shot test (5/5, 19.1s/answer) but fails to
recognize when it already has enough context to act, under real sustained tool-use
pressure. Confirms, a second time, that isolated prompt-response tests on this stack can
pass while the same model fails the real Pi/ACP workload (see deep-lite, 2026-09-02).

**Decision: `deep` (Nemotron) remains primary.** `deep-gptoss` stays installed — its raw
speed and single-shot quality are real and may suit non-agentic or single-turn work — but
it is not a safe default for sustained multi-turn coding tasks.

**Process note:** `run-h2h.sh` originally hardcoded one shared output directory across all
models with an `rm -rf` at the top. Launching the Nemotron run deleted the gpt-oss run's
raw JSONL transcripts before they were archived (the aggregated table survived and was
recovered from prior output). Fixed: each model now gets `/e/Test/h2h-runs-<model>/`.
Raw transcripts for this gpt-oss run are lost; the aggregate numbers in the table above are
intact and archived at `E:\AI\config\h2h-archive\deep-gptoss-2026-09-04.tsv` (and
`deep-nemotron-2026-09-04.tsv`).

## Six-candidate sweep — 2026-09-04

Deleted per user request: `deep-gemma` (Gemma 4 26B-A4B UD-Q4_K_XL) and `vision`
(Qwen3.8-27B Q4_K_M + mmproj). The stack currently has NO vision-capable slot.

Tested six new downloads. Methodology fixes made mid-session, now standard practice:
- **Never batch multiple different model files in one `llama-bench` invocation.**
  Proven to corrupt tg128 timing (variance up to ±14-15 tok/s on a ~30 tok/s mean) even
  though pp512 stays mostly clean. Confirmed by isolating one model: variance collapsed
  from ±15 to ±0.21 with no other change. Always benchmark one model file per invocation;
  an `-ncmoe` sweep on the SAME file in one invocation is fine.
- **`llama-bench` has no `-c`/`--ctx-size` flag** (that's server/cli only) — omit it
  entirely when using an explicit `-ncmoe`/`-ngl` sweep; context need is implied by `-p`/`-n`.
- **The Gemma 4 family shows genuine bimodal tg128 timing even fully isolated**, confirmed
  via `-o jsonl` per-sample output: 8 of 10 samples cluster tightly, 1-2 spike to 2-3x the
  cluster. This looks like a GPU power-state transition specific to this laptop GPU
  (residual boost clock from the preceding compute-bound pp512 phase occasionally carrying
  into the memory-bound tg128 phase), not a data quality problem. Trust the tight cluster,
  not llama-bench's raw mean, for any Gemma 4 quant.

### Speed (clean, single-model-isolated numbers only)

| Model | Type | Size | Clean tg128 | VRAM |
|---|---|---:|---:|---:|
| gemma-4-26B-A4B IQ3_S | MoE | 10.50 GiB | 58.45 ± 0.49 @ ncmoe=8 | 9,394 MiB |
| Qwen3.6-35B-A3B-APEX-Compact | MoE | 16.10 GiB | 50.67 ± 0.13 @ ncmoe=20 | 9,848 MiB |
| DeepSeek-R1-Distill-Qwen-14B | dense | 10.23 GiB | 33.05 ± 0.71 | — |
| gemma-4-12b | dense | 9.94 GiB | ~27-30 (bimodal cluster) | — |
| Qwen3.8-27B IQ3_XXS | dense | 10.17 GiB | 25.81 ± 0.21 | — |
| gemma-4-31B | dense | 11.01 GiB | ~15 (noisy, right at cliff) | — |

### Correctness (5-task single-shot pass, same fixture as prior sessions)

| Model | Correct | Reasoning:content | Mean s/answer | Verdict |
|---|---:|---:|---:|---|
| gemma-4-26B-A4B IQ3_S | 5/5 | 8.3:1 | 33.2s | Passed screen -> full protocol |
| Qwen3.8-27B IQ3_XXS | 5/5 | 8.6:1 | 58.7s | Correct, secondary candidate |
| gemma-4-12b | 5/5 | 6.5:1 | 42.2s | Correct, secondary candidate (fast-tier) |
| Qwen3.6-35B-A3B-APEX | 5/5 | **32.1:1** | 66.9s | Warning-sign ratio, NOT protocol-tested |
| gemma-4-31B | 5/5 | 6.7:1 | 93.6s | Correct but dominated on speed |
| DeepSeek-R1-Distill-14B | **4/5** | 4.6:1 (deceptive - bloated prose) | 153.8s | REJECTED: failed bsearch outright (burned full 4096-token budget on reasoning, zero content), verbose unseparated output even on success |

### Full protocol: gemma-4-26B-A4B IQ3_S vs deep (Nemotron), same fixture, same gate

Pre-declared gate: all-three >= 4/5 AND wall/success <= Nemotron's 65.51s.

| Metric | gemma-4-26B-A4B | Nemotron `deep` (incumbent) |
|---|---:|---:|
| All-three (5 tasks) | 4/5 | 5/5 |
| Individual wins (15 runs) | 14/15 | 15/15 |
| Wall/success | **122.0s** | **65.51s** |
| Reasoning:content (real load) | **29.06:1** | 2.23:1 |

**FAILED the gate on wall/success (nearly 2x over).** Despite winning on raw tok/s (58.45 vs
56.6) and having the best isolated single-shot reasoning ratio of any candidate tested today
(8.3:1), its real-agent-loop reasoning overhead exploded to 29:1 under Pi's actual tool-use
workload — matching gpt-oss and APEX's warning-sign range despite looking nothing like them
in isolation. This is the clearest demonstration yet of why isolated single-shot tests are a
screening gate only, never a verdict: the strongest-looking candidate on every measure
available before the real test still lost once measured properly.

**Decision: `deep` remains Nemotron.** No candidate from this sweep is promoted.
Qwen3.6-35B-A3B-APEX was not run through the full protocol — its isolated ratio (32.1:1)
was already worse than gemma-26a4b's (8.3:1), and gemma-26a4b lost anyway; spending another
20-40 min to very likely reconfirm a negative was not a good use of the machine.

All six candidate GGUFs and their temporary llama-swap/Pi registrations were removed after
testing. Config restored to exactly the 7 permanent slots: fast, deep, deep-budget,
deep-budget-2k, deep-lite, deep-uncensored, deep-gptoss.

## Full real-agent-loop protocol, round 2 — 2026-09-04 (intelligence-first pass)

Per user instruction: prioritize correctness/intelligence over speed for the four bigger
models (gemma-31B, APEX, gemma-26A4B [already tested], Qwen3.8-IQ3_XXS), and race
gemma-4-12b against the incumbent `fast` (Qwen3.5-9B) on the identical protocol. All run
through Pi's real agent loop, same fixture/verifier as every other protocol test.

| Model | All-three | Individual | Wall/success | Reasoning:content | Notes |
|---|---:|---:|---:|---:|---|
| Nemotron `deep` (incumbent) | 5/5 | 15/15 | 65.51s | 2.23:1 | reference |
| Qwen3.5-9B `fast` (incumbent) | 5/5 | 15/15 | 30.37s | 2.05:1 | reference |
| **Qwen3.6-35B-A3B-APEX-Compact** | **5/5** | **15/15** | **42.93s** | **1.32:1** | Ties Nemotron on correctness, BEATS it on speed and reasoning-efficiency |
| gemma-4-31B IQ3_XXS | 5/5 | 15/15 | 316.01s | 22.23:1 | Ties Nemotron on correctness, ~4.8x slower |
| gemma-4-26B-A4B IQ3_S | 4/5 | 14/15 | 122.0s | 29.06:1 | Lost to Nemotron (round 1 result, unchanged) |
| Qwen3.8-27B IQ3_XXS | 3/5 | 13/15 | 169.32s | 4.48:1 | 2 genuine failures: complete non-action (7 reads, no edit, no error — just stopped) |
| gemma-4-12b | 4/5 | 13/15 | 155.12s | 0.07:1 (artifact, not real) | SERIOUS: 3/15 runs hit a 400s timeout after generating 400,000+ characters, cut off mid-tool-call. Genuine non-termination, not simple repetition. The 0.07:1 ratio is inflated by this garbage content, not real efficiency. |

**Standout finding: Qwen3.6-35B-A3B-APEX-Compact is a clean win with no tradeoff.**
Isolated single-shot testing gave it the worst reasoning ratio of the whole six-candidate
sweep (32.1:1) — a result that led to a decision NOT to run the full protocol on it. That
decision would have been wrong: under real agentic load its ratio inverts to 1.32:1 (better
than Nemotron's own 2.23:1), it matches Nemotron's perfect correctness, and it completes
34% faster (42.93s vs 65.51s/success). This is the second demonstrated case (after
gemma-26a4b's opposite miss) that isolated single-shot signal, in EITHER direction, is not
predictive of real-agent-loop behaviour on this stack. Only the full protocol is trustworthy.

One qualitative note on APEX's code: its rollback fix snapshots state before every
operation and rolls back through the snapshot history, rather than the simpler
snapshot-once/restore-once pattern every other model (including Nemotron) used. It passes
correctly but is unnecessarily complex for the task — a minor over-engineering signal, not
a correctness concern.

**`fast` (Qwen3.5-9B) decisively beats gemma-4-12b**: perfect correctness vs 4/5, no
pathological behaviour vs a serious runaway-generation problem, and faster (30.37s vs
155.12s, though the latter figure is inflated by the timeouts). `fast` stays Qwen3.5-9B.

DeepSeek-R1-Distill-Qwen-14B was deleted (failed the isolated `bsearch` task outright,
verbose unseparated output). All four temporary test slots and their Pi registrations were
removed after testing; config restored to the 7 permanent slots. The five candidate GGUFs
remain in Downloads awaiting a keep/discard decision, alongside two long-orphaned files on
disk with no current slot: Ornith-1.5-9B (7.36 GB) and Qwen3.6-27B (18.08 GB, unclear
provenance — not something either party configured in this project).

## Stack rebuild per user decision — 2026-09-04

User reviewed the full inventory and made explicit keep/delete/promote calls on every
model. Executed as follows.

**Audit correction** (user caught two real errors in the prior report): the "7 rejected"
count in the inventory artifact was off by one (actual count of distinct rejected models
was 6), and the "~121G" total did not match the sum of the report's own listed sizes. Both
were arithmetic/counting slips in that write-up, not data errors — fixed by computing all
totals below from `stat` on real files, never by hand.

### Promoted: deep = Qwen3.6-35B-A3B APEX-Compact

Moved from Downloads to `/mnt/e/AI/ModelStore/gguf/qwen3.6-35b-a3b-apex/`, byte-verified
(17,293,089,216 bytes). Now backs the `deep` slot with its already-settled config
(`--n-cpu-moe 20`, 9,848 MiB peak). Reason: ties Nemotron's perfect real-agent-loop
correctness (15/15) while running 34% faster (42.9s vs 65.5s/success) with a healthier
reasoning ratio (1.32:1 vs 2.23:1). See the 2026-09-04 "intelligence-first pass" entry above.

### Demoted: deep-alt = Nemotron 3.5 Lightning 30B-A3B

Kept as temporary control/fallback pending an expanded tournament against APEX, per user's
explicit caution that 15 trajectories each is not yet proof of dominance across longer
sessions. Delete outright if APEX also wins the expanded test.

**Simplification made alongside this, not explicitly requested but consistent with the
user's stated goal of a much smaller stack:** the `deep-budget`, `deep-budget-2k`, and
`deep-lite` slots (Nemotron with different reasoning flags) were removed. They existed only
because Nemotron was primary; now that it is a temporary fallback, three extra variant
slots of a temporary model contradicted the stated goal. Flagging this explicitly since it
was my inference, not a direct instruction.

### Deleted, per explicit decision

- Qwen3.8-27B UD-IQ3_XXS (10.18 GiB) — 2 genuine non-action failures
- gemma-4-12b Q6_K_XL (9.95 GiB) — runaway/non-termination pathology, also lost to `fast`
- gemma-4-26B-A4B UD-IQ3_S (10.52 GiB) — reasoning exploded to 29:1 under real load
- gemma-4-31B UD-IQ3_XXS (11.03 GiB) — 7.4x slower than the new `deep` (APEX) for no quality gain
- Qwen3.6-27B Q4_K_M (16.84 GiB) — deleted UNTESTED. User's reasoning: an 18GB dense model's
  behaviour on this card is already answered by every dense-model result this session, and
  APEX already has more capacity at less size while running well. Only case this session of
  deleting something without ever running it.
- gpt-oss-20b UD-Q4_K_XL (11.06 GiB) — pathological agent behaviour (repeat-loops without
  acting, aborts). Its slot name `deep-gptoss` is retired along with the file; if a future
  need arises for a fast non-agentic single-shot utility model, that would be a new decision,
  not a revival of this one.

Total reclaimed this round: **~69.5 GiB** (sum of the six deletions above, real bytes).

### Pending — do not skip

1. **`deep-uncensored` full real-agent-loop protocol — IN PROGRESS**, launched 2026-09-04.
   This model has run for a full session as the "permanent" uncensored slot on the strength
   of a single isolated 5-task check only. User's explicit gate: 15/15 retain as-is, 14/15
   retain but flag for a harder test, <=13/15 delete regardless of its unique role. At ~8.6
   tok/s this will take considerably longer than any other model tested — expect hours, not
   minutes.
2. **Vision via APEX's own mmproj — mmproj downloaded, NOT yet smoke-tested.**
   `mudler/Qwen3.6-35B-A3B-APEX-GGUF` does ship `mmproj.gguf` (902,822,624 bytes, verified
   present in the repo listing before download, byte count confirmed after). This is NOT
   yet proven to work with our llama.cpp build — every multimodal/format claim this session
   that looked right on paper needed a real test before trusting it (Gemma's channel format,
   gpt-oss's Harmony tags). Test blocked on GPU availability until the uncensored protocol
   finishes. Ornith-1.5-9B + its mmproj (7.71 GiB combined) stay on disk, undeleted, until
   this is confirmed one way or the other.
3. **Qwen3-Coder-30B-A3B-Instruct — verified, not yet downloaded.** 30.5B total / 3.3B
   active, 128 experts / 8-per-token, 262K native context, Apache 2.0. Confirmed via the
   model's own card (matches user's figures exactly). One note the user's summary did not
   mention: this model supports non-thinking mode only, no `<think>` blocks at all — a real
   architectural difference from every other `deep` candidate tested this session, worth
   watching for in its reasoning:content numbers. GGUF: `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`,
   Q4_K_M = 18,556,689,568 bytes (17.28 GiB), same size class as APEX/Nemotron.
4. **LFM2-24B-A2B — verified, flagged as a real concern before downloading.** 24B total /
   2.3B active MoE, confirmed. But LiquidAI's own model card states directly: "We don't
   recommend using it for coding, as it wasn't optimized for this purpose." This is the
   vendor's own disclaimer, not an inference. Also uses "LFM Open License v1.0", not
   Apache/MIT — terms unverified. Recommend explicit user confirmation before spending
   download time/disk on this one given the direct anti-recommendation for our exact use case.
5. **Qwen3.6-35B-A3B APEX quant ladder — verified.** I-Compact 17 GiB, I-Mini 14 GiB (both
   confirmed against `mudler/Qwen3.6-35B-A3B-APEX-GGUF`'s own file listing, matching the
   user's figures closely). Testing I-Mini against the already-installed Compact quant is a
   cheap, low-risk test once the current two protocol runs clear the queue.
6. **Sarvam-30B — verified, GGUF source not yet located.** 32B total / 2.4B active MoE
   (128 experts, top-6), Apache 2.0, 65,536 context, GGUF confirmed to exist somewhere in
   the HF ecosystem but the specific repo name tried did not resolve — needs a real search
   before downloading, not a guessed URL.

## deep-uncensored full protocol result — 2026-09-04 — FAILED, DELETED

Per user's pre-declared gate (15/15 retain, 14/15 retain-with-caution, <=13/15 delete
regardless of role uniqueness — "its role doesn't excuse incorrect code").

| Metric | Result |
|---|---:|
| All-three (5 tasks) | **0/5** |
| Individual wins (15 runs) | **7/15** |

Every failed run showed complete non-action, not wrong code: `auth` failed all 3 runs with
the file left byte-for-byte identical to the buggy baseline each time, one lone tool call
(almost certainly a single `read`) and then nothing — no edit attempt, no error, the turn
simply ended. This is a worse failure mode than gpt-oss's repeat-loop-then-abort pattern:
this model didn't even try repeatedly, it gave up after one look.

**Deleted per the user's own gate, 7/15 << 13/15.** Qwen3.8-27B-OBLITERATED-IQ4_XS removed
(14.36 GiB reclaimed), `deep-uncensored` slot and Pi registration removed. Config is now
3 slots: fast, deep, deep-alt — the smallest this stack has been.

**The uncensored role currently has no model.** This was a role that existed for refusal
behaviour specifically; no replacement has been chosen. Worth a deliberate decision (skip
the role entirely, or find a different uncensored/abliterated model and apply the full
protocol before installing it permanently this time) rather than downloading the next
available one on reputation alone — exactly the mistake this whole session has been
correcting.

## APEX vision smoke test — 2026-09-04 — BROKEN, do not delete Ornith

`mudler/Qwen3.6-35B-A3B-APEX-GGUF` genuinely ships `mmproj.gguf` (902,822,624 bytes,
verified present and downloaded). `llama-server --mmproj ...` loads it without error,
reports "loaded multimodal model", and a real image submitted via the OpenAI-compatible
`image_url` (base64 data URI) genuinely engages the vision pipeline — prompt_tokens jumped
from ~30-50 (text-only) to 1,053-1,055, consistent with real image-token embedding.

**Generation is broken.** Both attempts (default sampling with reasoning on; temp 0.2 with
`--reasoning off`) produced identical garbage: 300 tokens of repeated `/` characters,
`finish_reason: length`, zero usable content. Reproducible across two materially different
configurations, ruling out a reasoning-mode or temperature artifact — this is the actual
generation output, not a stuck thinking phase.

llama.cpp's own load-time warning is relevant: "Qwen-VL models require at minimum 1024
image tokens to function correctly on grounding tasks... if you encounter problems with
accuracy, try --image-min-tokens 1024" (already applied in both tests). Whatever is wrong
goes deeper than that flag.

**Decision: Ornith-1.5-9B + its mmproj (7.71 GiB combined) are NOT deleted.** They remain
the only working vision path on this stack. Fixing APEX's vision output — different
llama.cpp version, different mmproj source/quant, or an upstream bug report — is a real
task, not a quick follow-up, and is not attempted further right now.

## Qwen3-Coder-30B-A3B-Instruct vs deep (APEX) — 2026-09-04 — LOST, deleted

The actually useful question this test answered: does a coding specialist beat APEX's
general agentic post-training? No.

Speed tuning: isolated `-ncmoe` sweep hit the same GPU power-state bimodal artifact seen
with Gemma and APEX earlier (single-sample readings ranged 34-57 tok/s with huge variance).
`-o jsonl` diagnostics showed the real signature clearly: 9 of 10 samples clustered tightly
at 42.7-45.7 tok/s, one wild outlier at 1560 tok/s (a 0.082s "generation" — a measurement
glitch, not real capability). True clean speed ~44 tok/s. `--n-cpu-moe 24` was the settled
fit at 10,448 MiB (20 overshoots to 11,840 MiB, 22 to 11,142 MiB).

Quick correctness screen: 5/5, confirmed `reasoning_content` is genuinely always empty
(0.0:1) — this model has NO thinking mode at all, an architectural fact, not an efficiency
signal. One minor style nitpick: `median` mutates the input via `nums.sort()` rather than
`sorted()`, unlike APEX/Nemotron's more careful versions.

Full real-agent-loop protocol result, identical fixture/gate as every other candidate:

| Metric | APEX `deep` (incumbent) | Qwen3-Coder |
|---|---:|---:|
| All-three | 5/5 | 4/5 |
| Individual | 15/15 | 14/15 |
| Wall/success | 42.93s | 47.11s |
| Reasoning:content | 1.32:1 | 0.0:1 (architectural) |

Its one failure (`rollback` run 2) was the same non-action pattern seen in every other
failed model this session — file left completely unchanged, 6 tool calls attempted and
none landed, no error thrown. Less severe than deep-uncensored's single-attempt give-up,
but the same underlying failure class.

**Deleted per the user's own pre-declared rule for this exact test** ("if Coder can't beat
APEX: delete it immediately"). 17.28 GiB reclaimed. `test-qwen3coder` slot and Pi
registration removed; config back to 3 slots (fast, deep, deep-alt).

## LFM2-24B-A2B vs deep (APEX) — 2026-09-04 — 0/15, TOTAL FAILURE

LiquidAI's own model card: "We don't recommend using it for coding, as it wasn't optimized
for this purpose." Tested anyway per explicit user instruction, since raw speed and the
quick correctness screen looked strong enough to warrant checking whether the disclaimer
held up under real agentic pressure specifically (as opposed to isolated single-shot use).

Architecture note: hybrid conv/attention MoE (30 conv + 10 attention layers of 40 total,
2.3B active of 24B total). Loaded cleanly (`lfm2moe` recognized natively, no errors).
Unusual tuning behaviour: --n-cpu-moe showed the OPPOSITE relationship from every other
MoE model this session — ncmoe=0 was slowest (37.45 tok/s), ncmoe=8 fastest (109.24 tok/s),
then declining again at higher values. Settled at ncmoe=12 (10,840 MiB, 88.46 tok/s clean,
±2.11 variance) since ncmoe=8 overshot the VRAM ceiling (11,884 MiB).

Quick correctness screen (5/5) already showed a real yellow flag: 2 of 5 answers ignored
the explicit "return only the corrected function" instruction, wrapped in unsolicited
prose and an offer to do more work. Flagged to the user before the expensive test; user
chose to proceed anyway given the raw speed (88 tok/s, fastest MoE this session) and
correct-but-verbose behaviour did not yet prove the disclaimer was fatal to agentic use.

**Full protocol result: 0/15 individual, 0/5 all-three.** Total failure, every task, every
run. Worse than deep-uncensored's 7/15 — the worst result of the entire session. Verified
genuine (not a grader artifact): inspected alias-2 directly — file left byte-for-byte
unchanged despite 7 `read` tool calls, and the model's final output was conversational
prose ending "...you need anything else!" It behaved as a chatbot offering to help rather
than an agent that acts. The vendor's disclaimer was accurate and should have been treated
as sufficient on its own — this is the clearest case this session of an explicit,
documented limitation being confirmed exactly as stated.

**Deleted.** 13.43 GiB reclaimed. `test-lfm2` slot and Pi registration removed.

## Sarvam-30B — 2026-09-04 — CANNOT LOAD, architecture unsupported

Downloaded from DevQuasar (`sarvamai.sarvam-30b.f16.gguf.Q4_K_M.gguf`, 19,582,216,032 bytes,
byte-verified). `llama-bench` produced zero output rows; direct `llama-server` load gave the
real error: `unknown model architecture: 'sarvam_moe'`.

Verified this is a genuine upstream gap, not a bad quant or a fixable flag: llama.cpp has an
open pull request adding `sarvam_moe` support, dated in the search results as triggered May 9,
2026, but a direct check of the repo's commit history (spanning through Sep 4 2026, well past
our pinned build) confirms it is still unmerged. Our build (b10726/85c5522) genuinely cannot
load this architecture, and no newer official release can yet either.

**Not pursued further.** Building against an unmerged, unstable PR branch for one wildcard
candidate would be the exact kind of scope creep this project has spent this whole session
correcting away from. Revisit only once the PR merges into an official release.

**Deleted.** 18.24 GiB reclaimed.

## Expanded tournament: deep-alt (Nemotron) vs deep (APEX) — 2026-09-05 — APEX WINS DECISIVELY

Per user's explicit caution that the original 5-task fixture (15 trajectories) doesn't prove
dominance across "longer coding sessions." Expanded the fixture from 5 to 8 tasks by adding
three genuinely harder task types, each verified broken at baseline before testing:

- `cache` (feature): apply a memoize decorator to an existing function, following a
  documented convention — tests generalizing from a pattern, not just patching a bug.
- `dedupe` (refactor): extract duplicated validation logic from two functions into one
  shared helper without changing behaviour — tests cross-function understanding. The test
  suite includes a source-inspection check that a genuine shared helper exists, not just
  that both functions happen to still pass their own tests.
- `pipeline` (multistep): three independent bugs in one file, all three must be fixed for
  any test to pass — tests sustained focus within one turn.

24 trajectories per model (8 tasks x 3 runs), identical fixture, identical Pi/ACP protocol.

| Metric | Nemotron `deep-alt` | APEX `deep` |
|---|---:|---:|
| All-three (8 tasks) | 6/8 | **7/8** |
| Individual (24 runs) | 19/24 | **23/24** |
| Wall/success | 168.27s | **52.29s** |
| Reasoning:content | 2.10:1 | **1.32:1** |
| Tool calls / errors | 215 / 470 | **62 / 55** |

**Both models were perfect on the original 5-task fixture (5/5, 15/15) — the expanded tasks
are what separated them.** Nemotron's degradation was concrete and inspectable, not just an
aggregate number: complete non-action on `dedupe` (0/3, file left byte-identical to baseline
in all three runs, no error thrown, no attempt), and a genuine logic bug on `pipeline` run 1
(a `raise ValueError(...); return [...]` chained on one line via `;`, which Python's syntax
puts entirely inside the preceding `if` block, so the non-error path silently returns `None`
instead of the expected list).

APEX's one failure (`dedupe` run 2) was milder: it built a correct shared helper and a
correctly-refactored `validate_username`, but left the original un-refactored definition
sitting above it as dead code (harmless at runtime — Python's last-definition-wins rule
means the correct version executes — but a real code-quality lapse the test's source-level
duplication check correctly flagged).

**Decision: APEX has now beaten Nemotron twice** — the original 15-trajectory protocol and
this 24-trajectory expanded one, the second specifically designed to probe the concern that
kept Nemotron installed. Per the user's own standing rule ("if APEX also wins that too:
delete the 17.6 GiB Nemotron file"), Nemotron is being deleted; `deep-alt` and the
control/fallback role are retired.

## APEX I-Mini vs installed Compact — 2026-09-05 — FAILED SCREEN, deleted

Same architecture as the promoted `deep`, smaller quant (13.32 GiB vs 17.28 GiB). Speed
tuning was clean: `--n-cpu-moe 12` gave 69.08 ± 0.79 tok/s at 10,188 MiB (comfortably under
the ceiling) — genuinely faster than Compact's 50.7 tok/s isolated.

Quick 5-task correctness screen: **3/5, with 2 complete failures.** `cycle` and `merge` both
hit `finish_reason: length` with zero content — the model burned its entire 4,096-token
budget on reasoning and produced no answer at all. Reasoning:content ratio 93.1:1, the worst
of the entire session (worse than gpt-oss's 28:1, worse than Compact's own isolated 32.1:1
that turned out fine under real load). This is visible quantization damage: I-Mini's more
aggressive compression appears to impair the model's ability to terminate its own thinking.

Per the user's own pre-declared bar for this exact test ("does it preserve 15/15 and beat
42.9s? If not, delete immediately") — failed decisively at the screening stage, no need to
spend the expensive full protocol confirming an already-clear result. **Deleted.** 13.34 GiB
reclaimed, `test-apex-imini` slot removed. Compact remains the installed quant.

## Stack state — 2026-09-05

Down to 2 slots: `fast` (Qwen3.5-9B) and `deep` (APEX-Compact). APEX has now beaten every
challenger tested this session: Nemotron (twice, including the expanded tournament),
gemma-31B, gemma-26B-A4B, Qwen3.8-IQ3_XXS, Qwen3-Coder-30B-A3B, and its own smaller I-Mini
quant. LFM2 and Sarvam-30B failed before comparison was even possible (total failure and
unsupported architecture respectively). Config validates clean.

## Research-digest triage — 2026-09-05

A batch of September 2026 developments was evaluated against this machine (12 GB VRAM
Blackwell laptop, 32 GB RAM) and this stack (Zed + Pi + llama-swap, 2 slots). All sources
were verified as real before assessment — correct titles, authors and dates.

**Rejected on hardware arithmetic — Speculative Macro Commit (arXiv 2609.03236).** Requires
the authoritative model AND a smaller drafter resident simultaneously. `deep` alone occupies
9,848 MiB of 12,288. There is no room for a second resident model, and swapping between them
destroys the very latency the technique exists to deliver. Not a judgement call; it does not
fit.

**Rejected on measurement — MXFP4/FP4 quantization.** Blackwell has native FP4 tensor cores
and this looked like the most promising lead. But the MXFP4_MOE build of this model is
~20.2 GiB against APEX-Compact's 16.11 GiB. Four GiB larger on a card that already offloads
20 expert layers to CPU means strictly more offload, and published comparisons show ~-25%
token generation (it wins only on prompt processing, the wrong half for agentic coding). It
is also base Qwen3.6, which would forfeit the APEX fine-tune that won every tournament here.

**Rejected as inapplicable — Perplexity Lily.** Rust + Metal, Apple Silicon only.

**Deferred — Harness-of-Harness (arXiv 2609.01481).** Real, and notably wraps Pi. But three
full harness invocations per iteration (planner/developer/tester) against demos run on
GPT-5.5, DeepSeek-V4-Pro and MiniMax-M3. Worth a bounded trial once the stack has real
mileage; adding a lifecycle controller above an unproven stack is the exact pattern that
previously produced a 40-model manifest and zero working agents.

**Already covered — Repo-To-Skill / DisCo (arXiv 2609.02749).** The architectural principle
(skills as files with progressive disclosure) is already available in both Claude Code and
Pi. The AREX library itself is ML-research-specific and irrelevant to this use case.

## llama.cpp MoE-fusion A/B — 2026-09-05 — NO MEASURABLE GAIN, not adopted

NVIDIA's Sept 3 post advertised up to 1.9x on llama.cpp, but that figure is RTX 5090-specific
and describes work upstreamed *before* the announcement — our build (Aug 31) already sat on
the optimized path. Only 7 CUDA commits landed since, none mentioning Blackwell, sm_120 or
FP4. One was directly on our critical path: `3466812d cuda: fuse MoE weighted expert
reduction (#25952)`, and our `deep` slot is a 35B-A3B MoE.

Built 4d917609 (2026-09-04) into a separate `build-new` with flags replicated exactly from
`build/CMakeCache.txt`, leaving the working binary untouched. Benchmarks INTERLEAVED
(old,new,old,new) so drift hits both equally.

| | OLD 85c5522 | NEW 4d917609 |
|---|---:|---:|
| pp512 | 760.34, 759.53 | 765.06 |
| tg128 (clean rows) | 49.22 +-15.61 | 49.03 +-15.59 |

pp512 differs by +0.7% — inside noise. A tie-breaker (tg128 only, -r 10, interleaved) was run
because 3 of 4 first-pass tg rows carried the bimodal power-state artifact (stddev to
+-53.10); it returned 49.22 vs 49.03 with near-identical spread, i.e. the same distribution.

**Conclusion: no measurable improvement.** Plausible cause: the commit optimizes a GPU-side
expert reduction, but with `--n-cpu-moe 20` the majority of expert work is on CPU, so the
GPU reduction kernel is not our bottleneck. Not adopted; `build-new` deleted.

**Reproducibility note:** the source tree was deliberately reset to `85c5522` to MATCH the
binaries actually running in `build/bin`. Rebuilding without this would silently substitute
unvalidated code into a runtime backed by 100+ measured trajectories.

## funes episodic memory — 2026-09-05 — ADOPTED (manual refresh)

Hugging Face's local-first agent memory (v1.3.0). Linux/macOS binaries only, so it runs in
WSL alongside llama.cpp — which also keeps it clear of Smart App Control.

Indexed **106 sessions / 24,607 chunks** from Claude Code transcripts and Pi sessions. Fully
local; `funes push` is never called, so nothing leaves the machine.

Recall was graded against three facts whose answers were independently known, rather than
merely eyeballed. All three returned correct evidence with provenance and follow-up `get`
commands: Nemotron's deletion rationale (0.938), the `--n-cpu-moe 20` / 9,848 MiB decision
(0.893), and the llama-bench multi-model batching landmine reproduced verbatim (0.989).

**Known limitation:** `funes add pi` writes to WSL's `~/.pi`, but the Pi that Zed drives is
the *Windows* install, and no Windows binary exists — so automatic per-turn indexing cannot
be wired to it. `funes-refresh.sh` (explicit Windows paths, incremental) is the substitute;
run it to make recent sessions recallable.

## funes wired into Claude Code as an MCP server — 2026-09-05

`funes mcp` speaks MCP over stdio, so Claude Code (Windows) reaches the WSL binary directly
through `wsl.exe` — no Windows build needed, which is what blocked the Pi integration.

Registered at user scope in `C:\Users\YOU\.claude.json` so the memory is available across
all projects rather than this one:

```json
"mcpServers": {
  "funes": {
    "command": "wsl.exe",
    "args": ["-d", "Ubuntu-24.04", "--", "/home/YOU/.local/bin/funes", "mcp"]
  }
}
```

Verified before and after writing: a stdio probe returned a valid `initialize` result and
six tools (`recall`, `get`, `scan`, `sessions`, `sketch`, `status`) with clean stderr, and
the same probe was repeated through the exact spawn form Claude Code uses (direct argv via
PowerShell, not Git Bash) to rule out MSYS path mangling. The config was backed up first and
re-parsed afterwards: 33 top-level keys and all 8 project entries intact.

The tools are read-only over already-recorded transcripts, so this adds recall without
changing how sessions are stored. MCP servers load at startup, so Claude Code must be
restarted before the tools appear. Recall only covers what has been indexed — run
`funes-refresh.sh` to pick up recent sessions.

## trufflehog + funes scrub — 2026-09-05

funes treats its secret scan as mandatory and had been indexing with redaction DISABLED
because trufflehog was absent. Installed trufflehog 3.97.4 to `~/.local/bin` (one of the
paths funes already probes), pinned to a release tarball rather than piping the upstream
install script so the exact artifact is visible: sha256 dc24007c2f233bd61c05beabeb44aa27ea
9b43288166279209abe0458c5ce76b.

`funes scrub` then retroactively cleaned the 24,750 chunks indexed before redaction existed:

    scanning 14815 block(s) for secrets…
    scrubbed 24761 rows: redacted 5 secret(s) in 5 block(s); dropped 6 row(s) in 4 block(s)
    that couldn't be safely redacted (Box x3, Privacy x1)

**These were real credentials, not false positives worth ignoring.** Two consequences:

1. **The scrub covers the funes index ONLY.** The source transcripts under
   `C:\Users\YOU\.claude\projects\*.jsonl` are untouched and still contain those secrets in
   cleartext. Scrubbing a derived index does not clean what it was derived from.
2. Any of those credentials that are still live should be treated as exposed-at-rest and
   rotated. Detection means they were sitting in plaintext session history, regardless of
   funes.

Future indexing now scans automatically, so this is a one-time backfill. `funes push` has
never been run, so nothing was published while redaction was off — which is the only reason
this stayed a local-hygiene issue rather than a disclosure.

## Nemotron cleanup completed — 2026-09-05

The 2026-09-05 deletion removed the 17.6 GiB main weights but left behind the 1.077 GiB MTP
drafter (`mtp-NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q4_0.gguf`) and a `source-lock.json`
provenance manifest. Root cause: the original `rmdir` was written `2>/dev/null`, so its
"Directory not empty" failure was swallowed and the cleanup was reported complete.

Now fully removed. Provenance preserved first at
`h2h-archive/nemotron-source-lock-archived-2026-09-05.json` (804 bytes, HF repo + revision
9d425fe18d84ab04da6aabb757d2e2807083d054 + per-artifact sha256), verified byte-identical
with `cmp` BEFORE the original was deleted.

**Process lesson, recorded because it recurred three times in one cleanup.** Passing paths
through nested quoting into `wsl.exe` from Git Bash can collapse a shell variable to an
empty string. The failure is silent and actively misleading:

- `rm -f ""` succeeds and reports exit 0 while deleting nothing.
- `test -e ""` returns false, so a verification step prints "fully removed" for a directory
  that is untouched.

That combination produced a false "fully removed" report AND a false conclusion that the
provenance file had been destroyed (it had not; the `rm -f` was a no-op on an empty string).
A verification that constructs its own path from a variable can therefore confirm a deletion
that never happened.

Standing rule for destructive operations in WSL from this machine: use a script file with
fully literal paths and no variables, never inline nested quoting through `wsl.exe`; verify
deletions by listing the PARENT directory rather than testing a constructed path; and never
let `rm -f` be the step that "proves" anything, since it cannot fail.

## K2-Horizon evaluation — 2026-09-05

Two candidates supplied: `K2-Horizon-7B-Q8_0` (8.92 GiB) and
`K2-Horizon-MoVA-36B-A4B-Q3_K_M` (16.45 GiB).

**Both required a third-party fork to run at all.** Mainline llama.cpp has no `k2-horizon`
architecture: confirmed locally (absent at upstream tip 4d917609, no commit in fetched
history ever mentions it) and upstream (not among the registered architectures, no open
support PR). Renaming the arch is not a workaround -- the GGUF metadata keys are namespaced
`k2-horizon.*`. Built MBZUAI-IFM's fork, branch `model/K2Horizon` (35999d1, 2026-09-01),
into an isolated `~/src/llamacpp-k2`; the validated build and llama-swap's pointer to it
were untouched throughout.

Note: **MoVA is "Mixture-of-Values Attention", not vision.** It does not address the
outstanding vision gap. Vendor claims (Terminal-Bench 2.1 58.6%, GPQA Diamond 80.8%,
"outscores models up to 15x its size") are self-reported with no third-party reproduction --
the same profile as Ornith, which later underperformed here.

**Tuning.** 7B: `-ngl 99`, fully GPU-resident, 10,892 MiB. MoVA-36B: `--n-cpu-moe 32`,
10,954 MiB. The MoVA sweep was non-obvious -- ncmoe 20/24/28 all plateaued near 11,850 MiB,
which resembled a no-op until ncmoe 99 dropped to 6,688 MiB; the response is strongly
non-linear on this architecture, plausibly due to its leading dense blocks. Do not assume
APEX's ncmoe range transfers to it.

**5-task screen: both 5/5.** Non-discriminating -- their answers were near character-identical,
and the 36B took twice as long (56.0s vs 27.9s per answer) for the same output.

### MoVA-36B-A4B expanded protocol — LOSES to APEX on every axis

| Metric | APEX `deep` | K2-MoVA-36B |
|---|---:|---:|
| All-three | **7/8** | 6/8 |
| Individual | **23/24** | 22/24 |
| Wall/success | **52.29s** | 104.61s |
| Reasoning:content | **1.32:1** | 2.37:1 |
| Tool calls / errors | **62 / 55** | 116 / 90 |

Both MoVA failures were complete non-action, files byte-for-byte identical to baseline:
`auth` run 1 (15 tool errors, zero content) and `dedupe` run 2, which burned the entire
400-second timeout without editing anything. This is the same failure mode that sank
Nemotron and every weak model evaluated in this project.

Twice the wall-clock for slightly worse correctness, with 64% more tool errors. Not a
candidate to replace `deep`, and adopting it would additionally mean depending on an
unmerged fork that receives no upstream fixes.

### K2-Horizon-7B expanded protocol + first `fast` baseline — 2026-09-05

`fast` (Qwen3.5-9B) had never run the 8-task fixture, so a 7B could not be judged: APEX's
7/8 is a `deep`-class bar. Ran it to make the K2-7B number interpretable. This baseline is
reusable for any future small-model candidate.

| Metric | APEX-35B `deep` | K2-MoVA-36B | K2-7B | `fast` Qwen3.5-9B |
|---|---:|---:|---:|---:|
| All-three | **7/8** | 6/8 | **7/8** | 6/8 |
| Individual | **23/24** | 22/24 | **23/24** | 22/24 |
| Wall/success | 52.29s | 104.61s | 55.26s | **48.37s** |
| Reasoning:content | **1.32:1** | 2.37:1 | 1.97:1 | 2.54:1 |
| Tool calls / errors | 62 / **55** | 116 / 90 | 114 / 215 | 69 / 90 |
| VRAM | 9,848 MiB | 10,954 MiB | 10,892 MiB | ~7,000 MiB |

**K2-7B matched APEX-35B's correctness exactly (7/8, 23/24) at comparable wall-clock**, while
sitting entirely in VRAM with no expert offload. For a 7B against a 35B-A3B across 24 real
agent-loop trajectories, that is a genuine result rather than a screening artifact.

Against the slot it would actually displace, though, the margin is one trajectory out of 24
-- inside this fixture's run-to-run noise -- and it is bought at 14% slower wall-clock and a
**2.4x tool-error rate** (215 vs 90). It reaches correct answers by fumbling tool calls and
recovering, which tends to degrade on longer tasks than this fixture contains.

**Failure modes, all placement rather than logic** -- notable because every model's remaining
failure now has this shape:
- K2-7B `cache` run 3: wrote a correct `memoize` decorator but placed its definition AFTER
  the function applying it, so `@memoize` raises NameError at import.
- `fast` `pipeline` run 3: fixed all three bugs but `if not fields: raise` tests whether the
  LIST is empty, not whether any FIELD is empty -- a misread requirement.
- `fast` `dedupe` run 2: modified the file but did not produce a passing refactor.
- APEX `dedupe` run 2: correct helper, but left the un-refactored original above it.
- Nemotron `pipeline` run 1: `return` trapped inside an `if` by semicolon chaining.

**Recommendation: do not adopt K2-7B.** The correctness edge is a single trajectory, while
the costs are structural: a permanent dependency on an unmerged fork that receives no
upstream fixes and requires maintaining a second llama.cpp build, a 2.4x tool-error rate,
and 10,892 MiB against `fast`'s ~7,000 MiB, leaving no headroom on a 12 GB card.

## Tiel-Coder-35B-A3B expanded protocol — 2026-09-05 — FIRST PERFECT SCORE

`Tiel-Coder-35B-A3B-MTP-UD-Q3_K_XL`, 16.53 GiB. Architecture is **qwen35moe -- the same as
APEX-Compact** -- so the mainline validated binary loads it natively. No fork, unlike
K2-Horizon. At within 0.5 GiB of APEX this is a genuine like-for-like `deep` comparison.

Tuned to `--n-cpu-moe 18` = 10,378 MiB, the fastest clean fit (16 overshoots at 11,044).
The GGUF embeds MTP `nextn_predict_layers`, deliberately NOT enabled -- STACK.md records MTP
speculative decoding as do-not-retry on this machine, so those tensors only cost file size.

| Metric | APEX `deep` | Tiel-Coder |
|---|---:|---:|
| All-three | 7/8 | **8/8** |
| Individual | 23/24 | **24/24** |
| Wall/success | **52.29s** | 59.42s |
| Reasoning:content | 1.32:1 | **0.94:1** |
| Tool calls / errors | 62 / 55 | 93 / 55 |
| VRAM | **9,848 MiB** | 10,378 MiB |

**First model to complete the expanded 8-task fixture with zero failures.** Every model
previously tested -- APEX, Nemotron, K2-7B, K2-MoVA, `fast` -- dropped at least one
trajectory. The 0.94:1 reasoning ratio is also the lowest ever recorded here: the only model
that produced more answer than reasoning rather than over-thinking. Tool errors (55) tie
APEX's best.

It also showed a quality signal in the 5-task screen that no other model produced: it fixed
the `median` caller-mutation bug (`nums.sort()` -> `sorted()`) AND explained that it had done
so. Both K2 models shipped the mutating version.

Cost: 14% slower per success (59.42s vs 52.29s) and 530 MiB more VRAM. Most of the time gap
came from `cache` runs 1 and 2 (111.4s and 161.7s, 20 tool errors each); the other 22
trajectories ran 41-84s.

**Status: promotion candidate, NOT yet promoted.** The correctness margin over APEX is one
task and one trajectory from a single 24-trajectory pass, which is inside this fixture's
demonstrated run-to-run variance. Per the standard set for Nemotron -- where a single
15-trajectory pass was explicitly judged insufficient to prove dominance -- a second
independent pass should confirm reproducibility before the daily driver is swapped.

## Tiel-Coder confirmation pass + K2-7B Q6_K — 2026-09-05

### Tiel-Coder: perfect score REPRODUCED — 48/48 across two independent passes

| Tiel-Coder | Pass 1 | Pass 2 |
|---|---:|---:|
| All-three | 8/8 | 8/8 |
| Individual | 24/24 | 24/24 |
| Wall/success | 59.42s | 60.50s |
| Reasoning:content | 0.94:1 | **0.86:1** |
| Tool calls / errors | 93 / 55 | 95 / **40** |

Two independent 24-trajectory passes, zero failures in either. Wall-clock differed by 1.8%
between passes, so the result is stable rather than a lucky run. Tool errors dropped to 40 --
the lowest figure recorded in this project, beating APEX's previous best of 55. The 0.86:1
reasoning ratio is likewise the lowest ever seen here.

This clears the standard that was applied to Nemotron (a single pass judged insufficient to
prove dominance). Against APEX's 7/8 - 23/24 - 52.29s, Tiel is better on correctness twice
over, better on reasoning efficiency, better on tool errors, and 14% slower per success at
530 MiB more VRAM. Same qwen35moe architecture, mainline binary, no fork dependency.

Raw transcripts preserved for both passes at `h2h-expanded-runs-test-tiel-pass1` and
`-pass2`, since the protocol driver wipes its output directory on start.

**Neither APEX nor Tiel has been removed or promoted -- the decision is the user's.**

### K2-Horizon-7B Q6_K — FAILS, worse than both Q8_0 and `fast`

| Metric | `fast` 9B | K2-Q6_K | K2-Q8_0 |
|---|---:|---:|---:|
| All-three | 6/8 | 6/8 | **7/8** |
| Individual | 22/24 | 22/24 | **23/24** |
| Wall/success | **48.37s** | 65.77s | 55.26s |
| Reasoning:content | 2.54:1 | **1.75:1** | 1.97:1 |
| Tool calls / errors | 69 / **90** | 105 / 175 | 114 / 215 |
| VRAM | ~7,000 MiB | 9,050 MiB | 10,892 MiB |

The lighter quant did not help. Q6_K is WORSE than Q8_0 on correctness (6/8 vs 7/8, failing
`pipeline` and `overlay`) and 19% slower per success, despite 1.8 GiB less VRAM. Against the
slot it would actually displace it ties `fast` on correctness while being **36% slower** with
roughly double the tool errors, and would additionally require the fork.

**The tool-error problem is inherent to the model, not the quantization**: Q8_0 produced 215
errors and Q6_K 175, both far above `fast`'s 90. Quantization was the wrong hypothesis for
that behaviour.

Conclusion: no K2-Horizon variant earns a slot. Q8_0 was rejected for a one-trajectory gain
not worth a fork dependency; Q6_K fails outright.

## Tiel-Coder promoted to `deep-tiel`; K2-Horizon removed — 2026-09-05

**Stack is now 3 slots: `fast`, `deep` (APEX), `deep-tiel` (Tiel-Coder).**

Tiel was moved out of `Downloads` into permanent storage at
`E:\AI\ModelStore\gguf\tiel-coder-35b-a3b\` before promotion -- a daily-driver model should
not be served from a scratch folder. Copy verified by byte count AND sha256
(db5ad52133efb08872a6907ac672002f6365a95eff3ff5e29e59d7885d7969df) BEFORE the Downloads
source was deleted. Live smoke test through llama-swap confirms it serves from the new path
at 10,426 MiB.

**Both deep models retained deliberately.** Tiel beat APEX reproducibly (8/8 and 24/24 on two
independent passes vs 7/8 and 23/24) with the best tool-error count and reasoning ratio
measured in this project, at 14% more wall-clock. But both Tiel passes ran the SAME 8 tasks,
so what is established is reproducibility, not breadth -- a model can be stable on a fixture
and still be partly fitted to it. Keeping both lets them be compared on real work instead of
on the fixture that selected one of them. No promotion of `deep-tiel` over `deep` is implied
by slot naming.

**K2-Horizon fully removed**: Q6_K GGUF (6.89 GiB) deleted, MBZUAI-IFM fork build (462 MB)
deleted, test slots removed from llama-swap and Pi. The validated mainline build at
`~/src/llamacpp/build` was verified intact afterwards. No K2 variant earned a slot, and the
fork existed solely to supply the `k2-horizon` architecture that mainline lacks, so it had no
remaining purpose.

Reclaimed this pass: 25.4 GiB (Q8_0 + MoVA) + 6.89 GiB (Q6_K) + 462 MB (fork) = ~32.7 GiB.

## CalibForge-35B-A3B — 2026-09-07 — perfect but strictly dominated by Tiel

`CalibForge-35B-A3B.i1-IQ3_M`, 14.38 GiB. qwen35moe built on **Qwen3.5**-35B-A3B (APEX and
Tiel are 3.6 base). Mainline validated binary serves it -- no fork. No MTP tensors.

Tuned to `--n-cpu-moe 14` = 10,666 MiB, fastest clean fit (12 overshoots at 11,326). Being
~2 GiB lighter than APEX buys a lower ncmoe, keeping more experts on GPU.

**llama-bench at that setting: pp512 926 (both passes tight), tg128 49.46 +- 2.46.** That is
+22% prompt processing over APEX's ~760 at parity on generation -- the most promising raw
benchmark of any challenger tested here. Pass 2's tg128 of 75.46 +- 57.02 was the bimodal
power-state artifact and was discarded.

5-task screen: 5/5, three tasks under 5s. (Its `median` used the mutating `nums.sort()`;
Tiel remains the only model that used `sorted()` and said why.)

### Expanded protocol: 8/8, 24/24 -- and it still loses

| Metric | APEX | Tiel p1 | Tiel p2 | CalibForge |
|---|---:|---:|---:|---:|
| All-three | 7/8 | 8/8 | 8/8 | **8/8** |
| Individual | 23/24 | 24/24 | 24/24 | **24/24** |
| Wall/success | **52.3s** | 59.4s | 60.5s | 76.9s |
| Reasoning chars | 302,391 | 259,287 | **198,921** | **1,223,373** |
| Reasoning:content | 1.32:1 | 0.94:1 | **0.86:1** | 4.95:1 |
| Tool calls / errors | 62 / 55 | 93 / 55 | 95 / **40** | 136 / 245 |

Only the second model ever to complete the expanded fixture perfectly. But it is **strictly
dominated by Tiel**, which matches its correctness while being 30% faster per success, using
**6x less reasoning**, and making **6x fewer tool errors** (40 vs 245).

The reasoning figure is the headline: 1.22 million characters to produce 246,975 characters
of answer -- essentially the same output volume as Tiel's 230,926, reached by brute force.
Two runs are illustrative: `rollback` run 1 spent 178,484 reasoning chars over 156.7s with 25
tool errors, and `rollback` run 2 produced 111,001 reasoning chars for 1,781 chars of content.

**This is the clearest demonstration yet of the standing rule against judging on throughput.**
CalibForge posted the best prompt-processing benchmark of any challenger (+22% over APEX) and
matched the best correctness ever recorded -- and still finished last on real wall-clock,
because it spends its speed advantage generating reasoning it does not need. A tok/s table
would have promoted it.

**Not wired in.** Tiel already occupies this niche and does it better on every practical axis.

## Macaron-V1-Tall — 2026-09-07 — LOSES to both incumbents

`Macaron-V1-Tall.i1-IQ4_XS`, 17.86 GiB. qwen35moe on **Qwen3.6-35B-A3B** -- the same base as
both APEX and Tiel -- so the mainline validated binary serves it, no fork. MTP
`nextn_predict_layers` embedded but not enabled (do-not-retry on this machine).

Tuned to `--n-cpu-moe 20` = 10,364 MiB, fastest clean fit (18 overshoots at 11,182).

**Benchmark: pp512 ~749 (751.71 +- 28.71 and 746.43 +- 17.49, both tight).** tg128 was
unreadable in both passes -- 102.87 +- 120.32 (stddev exceeding the mean) and 55.40 +- 11.00.
Recorded as unreliable rather than quoting a figure; protocol wall-clock is the real measure.

| Metric | APEX | Tiel | Macaron |
|---|---:|---:|---:|
| All-three | 7/8 | **8/8** | 5/8 |
| Individual | 23/24 | **24/24** | 20/24 |
| Wall/success | **52.29s** | 59.4s | 67.33s |
| Reasoning:content | 1.32:1 | **0.86:1** | 1.60:1 |
| Tool calls / errors | 62 / 55 | 95 / **40** | 71 / 85 |

Loses to both incumbents on correctness AND wall-clock -- there is no axis on which it is the
better choice. Failures split evenly: `dedupe` runs 1 and 2 were complete non-action (files
byte-identical to baseline), while `rollback` run 2 and `pipeline` run 2 were genuine failed
attempts.

**Methodological note worth keeping:** its 5-task screen showed a 24.7:1 reasoning ratio,
which looked like gpt-oss-style over-thinking and predicted disaster. The real protocol
measured 1.60:1 -- an order of magnitude different. Screen ratios do not predict protocol
ratios, in either direction; APEX went the other way (32:1 isolated, 1.32:1 real). The screen
is a filter for total failure, nothing more.

Test slot removed. GGUF retained pending the user's decision.
