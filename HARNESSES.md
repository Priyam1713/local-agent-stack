# Harnesses: seven agent loops, one model backend

*Campaign run 2026-09-09. 336 recorded trajectories, 312 analysed, 8.9 hours of measured
agent wall-clock.*

[`STACK.md`](./STACK.md) answers "which local model?". This document answers the other half:
**given a fixed model, how much does the harness driving it matter?**

The answer turns out to be: not much for correctness, a great deal for speed and
operational safety — and the ranking **inverts between model slots**, so there is no single
best harness to standardise on.

## Method

Identical to the model protocol in [`README.md`](./README.md), with one variable changed.
Every harness drives the **same** llama-swap instance at `http://127.0.0.1:8080/v1` and sees
the **same** slots, so swapping harness changes only the harness.

- Same fixture ([`fixture/`](./fixture)), same 8 tasks, 3 runs each = 24 trajectories per
  harness/slot cell.
- **Grading is pytest against the resulting files.** This is the only metric comparable
  across seven harnesses whose event schemas share nothing, and it is immune to a harness
  narrating a fix it did not make — which happened, see *"It answered" is not "it edited"*
  below.
- Runner: [`scripts/run-h2h-harness.sh`](./scripts/run-h2h-harness.sh) `<harness> <slot>`.
- Summary: [`scripts/summarize-h2h.sh`](./scripts/summarize-h2h.sh).
- Raw per-trajectory data: [`harnesses/results/`](./harnesses/results).

Two slots were measured: `fast` (Qwen3.5-9B, dense, 65536 ctx) and `deep-tiel`
(Tiel-Coder-35B-A3B, MoE, 32768 ctx).

## The harnesses

| Harness | Runs on | Notes |
|---|---|---|
| [Pi](https://github.com/badlogic/pi-mono) | Windows | The project's original daily driver; the 8-task protocol was built around it. |
| [Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent) | WSL | PrimeIntellect's. Persistent IPython REPL, recursive subagents, Continual Harness. |
| [OpenCode](https://opencode.ai) | Windows | Persistent client/server sessions, SQLite-backed. |
| [Codex CLI](https://github.com/openai/codex) | WSL | Commercial harness pointed at local weights — the control. |
| [dsh](https://www.npmjs.com/package/@deepseek-ai/dsh) | WSL | DeepSeek Harness. Verbose interleaved reasoning on stdout. |
| [OpenClaw](https://docs.openclaw.ai) | WSL | Chat-platform-first agent with an isolated headless `agent exec`. |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | WSL | Nous Research. Standing daemon with persistent cross-session memory. |

## Results

### `fast` slot — Qwen3.5-9B

| harness | alias | auth | median | overlay | rollback | cache | dedupe | pipeline | **total** | med s | p90 s | max s |
|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|
| **OpenClaw** | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 18.2 | 36.2 | 86.8 |
| **Hermes** | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 37.9 | 46.4 | 143.9 |
| dsh | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 23/24 | 23.0 | 34.7 | **43.6** |
| Prime Agent | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 23/24 | 25.8 | 52.1 | 64.1 |
| OpenCode | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 2/3 | 3/3 | 3/3 | 22/24 | 20.8 | 26.5 | 47.0 |
| Pi | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | **1/3** | 3/3 | 21/24 | 33.0 | 45.2 | 78.5 |

Codex cannot use this slot at all — see *Blockers* below.

### `deep-tiel` slot — Tiel-Coder-35B-A3B

| harness | alias | auth | median | overlay | rollback | cache | dedupe | pipeline | **total** | med s | p90 s | max s |
|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|
| **Prime Agent** | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 35.5 | 71.2 | **137.1** |
| **Hermes** | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 35.5 | 65.0 | 231.2 |
| dsh | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 52.0 | 83.0 | 174.6 |
| Codex | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 60.2 | 95.4 | 501.5 |
| OpenClaw | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 79.1 | 223.9 | 383.5 |
| Pi | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **24/24** | 28.2 | 49.2 | **9163.9** |
| OpenCode | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 23/24 | 339.4 | 437.7 | 500.3 |

OpenCode's `deep-tiel` **timings are not comparable** — a defect that appeared partway
through the campaign adds a fixed ~300s hang to every run. Its correctness is unaffected.
Detail below.

## What the numbers say

### The ranking inverts between slots

| harness | `fast` median | `deep-tiel` median | ratio |
|---|---:|---:|---:|
| OpenClaw | 18.2 (fastest) | 79.1 (slowest bar OpenCode) | 4.3× |
| Hermes | 37.9 (slowest) | 35.5 (fastest bar Pi) | 0.9× |
| dsh | 23.0 | 52.0 | 2.3× |

**OpenClaw is the fastest harness on `fast` and nearly the slowest on `deep-tiel`. Hermes is
the exact reverse.** A harness choice made on `fast` numbers is actively wrong for the deep
slot. This is the single most useful result in the campaign: there is no "best harness",
only a best harness *per slot*.

Hermes being flat across a 9B dense model and a 35B MoE (0.9×) says its wall-clock is
dominated by fixed per-turn overhead, not token generation. dsh more than doubling says the
opposite — it streams verbose interleaved reasoning, so its clock tracks the model.

### The median lies; report the tail

Pi on `deep-tiel` posts the **fastest median in the field (28.2s) and the worst maximum by a
factor of 67 (9163.9s)** — a single `pipeline` trajectory that ran 2h33m and then succeeded.
Not a hang: its log shows 18 turns, 43 messages, 14 tool executions and 3 auto-retries of
genuine work.

Any summary carrying only the median makes the harness with the worst tail risk in the
campaign look like the outright winner. `summarize-h2h.sh` reports p90 and max for exactly
this reason.

### Harness contributes ~nothing to correctness at the deep tier

Six of seven harnesses scored a perfect 24/24 on `deep-tiel`, **including Codex** — a
mainstream commercial harness scoring identically to four open ones on the same local
weights. On these tasks at this model tier the harness contributes only wall-clock.

The corollary is a limitation, stated plainly: **the fixture is saturated on `deep-tiel` and
cannot rank capability there.** `fast` still discriminates (21/24 → 24/24 across six
harnesses), so that half of the conclusion rests on real spread. Ranking "which harness is
smartest on the deep slot" needs harder tasks than these.

### Category ownership

Only `fast` separates the field, so this is where per-category signal lives:

- **`pipeline`** (three independent bugs in one file) is the hard task — dsh and Prime each
  lost their single failure there. OpenClaw and Hermes took it 3/3.
- **`dedupe`** is Pi's structural weakness at **1/3**. Two-thirds failure on one category
  while scoring 3/3 on six others is a different shape from a scattered miss. It is the only
  pure refactor and the only task with no `BUG:` comment to anchor on.
- **`rollback` + `cache`** are OpenCode's two misses — the only harness failing in two
  distinct categories.

## Recommendations

**`fast` slot — routine edits, subagents, high call volume → OpenClaw.**
24/24 at an 18.2s median; fastest in the field and one of two perfect scores. If
predictability matters more than speed, **dsh** has the tightest ceiling measured anywhere in
the campaign (43.6s max).

**`deep-tiel` slot — hard reasoning → Prime Agent.**
24/24, 35.5s median, 137.1s max — the only harness that is both fast and bounded. Hermes ties
the median and beats the p90 (65.0 vs 71.2) but carries a 231.2s tail, making it the
alternative rather than the default.

**Avoid on `deep-tiel`:** Pi (9163.9s tail), OpenCode (defective, see below), OpenClaw (its
p90 of 223.9s is worse than Prime's *maximum*).

**Pi should be demoted.** It is this project's original daily driver and the harness the
entire 8-task protocol was built around — and it finished **last on `fast` at 21/24** while
owning the worst tail on `deep-tiel` by a factor of 67.

### How much of this is noise

Every cell is 24 trajectories, so one- and two-trajectory gaps on `fast` are not
distinguishable from chance. The claims above rest on the gaps larger than that (Pi's
`dedupe` 1/3; the two-category spread) and on the timing distributions, which are far better
resolved than the pass counts.

## Blockers and traps

Each of these cost real time and none is visible from documentation.

**Codex cannot use the `fast` slot.** Qwen3.5's chat template rejects Codex's `instructions`
field with *"System message must be at the beginning"*. The client surfaces this as a retry
storm and *"We're currently experiencing high demand"* — which looks like a server problem
and is not. Diagnosed by proxying the wire on port 8099. Separately, the Windows build is
unusable: `pwsh.exe` resolves to the WindowsApps alias and is blocked by execution policy,
hence WSL.

**dsh must be installed from npm, not from source.** `@deepseek-ai/cordis` declares
`FiberState` as `export const enum`, which TypeScript erases at compile time, leaving no
runtime export for tsx's isolated transpilation to import. `pnpm run build` only builds
`apps/web`; `build:lib` does not fix it; `rescope-vendor` runs dry-only; and
`node_modules/@deepseek-ai/cordis` never existed. The published `@deepseek-ai/dsh` build has
those const enums inlined.

**OpenClaw ignores `cwd` unless you use `agent exec --cwd`.** Plain `openclaw agent --local`
edits `~/.openclaw/workspace` no matter where it is invoked. Staging into that shared
workspace is not a workaround: OpenClaw attests it in `state/openclaw.sqlite` and refuses to
run once `BOOTSTRAP.md` has gone missing from an already-initialised workspace.

**Hermes resolves relative paths against `$HOME`** — not the process working directory, and
not `--in`, which it accepts and then ignores. Left alone it finds and edits some *other*
copy of the file elsewhere under `$HOME`; in this campaign it "fixed"
`~/.openclaw/workspace/pkg/alias.py`, another harness's leftover copy of the same fixture.
Run it as `HOME=<workdir> HERMES_HOME=~/.hermes hermes -z "<prompt>" -m <slot> --yolo`.
Without `--yolo`, approval prompts block a headless run.

**"It answered" is not "it edited".** Every harness here can produce a fluent description of
a fix while changing nothing on disk. OpenClaw went further and reported *"Fixed and
committed"* for an edit it had made to a different copy of the file. This is why grading runs
pytest against the resulting files and never reads the transcript.

**`timeout` does not bound Pi's Windows launcher.** GNU `timeout` sends SIGTERM and then
*waits* for the child; reached through Pi's launcher that signal never lands and `timeout`
blocks indefinitely — which is how one trajectory ran 18× its own 500s bound. `timeout -k 30`
adds a SIGKILL that maps to a real `TerminateProcess`. The bound held correctly for OpenCode
(also Windows) and Codex (WSL), so this is specific to Pi's launcher, not to Windows.

**Harness configs overstate context unless generated.** Every generated config declared
65536 tokens for all three slots while llama-swap serves the deep slots at 32768.
[`scripts/sync-harnesses.sh`](./scripts/sync-harnesses.sh) now parses `-c` / `--ctx-size` out
of each slot's own block in `llama-swap.yaml`, which is the single source of truth for the
roster.

### OpenCode's `~300s` hang

OpenCode acquired a fixed ~300s hang partway through the campaign. It reaches `init` in
~100ms and then emits nothing — it never issues a provider request, so llama-swap never sees
it. This exactly reconstructs the observed timings: `alias` at 317-323s is 300s of hang plus
~20s of work; `pipeline` at 443-500s is the same 300s plus real effort.

Ruled out by test, not by argument:

| Suspected cause | Test | Result |
|---|---|---|
| Working-directory size (62,883 files) | clean 39-file dir | still hangs |
| Session DB (79.8 MB + 4.2 MB WAL) | fresh `XDG_DATA_HOME` | still hangs |
| Missing `--format json` | both invocations | both hang |
| Model slot | `fast` and `deep-tiel` | both hang |
| Provider config | `opencode models` | lists `llama-swap/*` in 2.6s |
| Backend unhealthy | direct warm API call | 1.7s |
| Stale server process | process list | none running |

Root cause not identified. Its `fast` numbers predate the onset and stand; its `deep-tiel`
timings do not.

## A harness is not eliminated until it has been run

Hermes was recorded in this project's registry as *"deliberately not wired"*, with reasoning
taken entirely from its documentation: no ACP, daemon-shaped, and its persistent-memory
headline already covered by another tool. That verdict was reached without ever installing
it. The registry also asserted OpenClaw could not run `deep-tiel` at all — measured, but
measured on a default configuration, when the harness ships `--local-model-lean` as its own
answer to exactly that problem.

**Both verdicts were wrong, and those two harnesses are the only ones that scored 24/24 on
`fast`.** Install it, run it on the fixture, and let the result decide — in both directions.


## Epilogue: what the stack looks like now

The campaign above is a record and is not rewritten -- every number, including those for the
harnesses since removed, stands as measured.

On **2026-09-09**, three harnesses were uninstalled. The criterion was *more than one failed
task category, or an inability to run a whole model slot*; single-trajectory misses were
treated as noise, since at three runs per category one miss is not distinguishable from
chance.

| Removed | Why |
|---|---|
| **Pi** | `rollback` 2/3 and `dedupe` 1/3 on `fast` (21/24, last in the field), plus the worst tail measured anywhere -- one trajectory at 9163.9s, 67x the next worst maximum. This was the project's original daily driver and the harness the entire 8-task protocol was built around. |
| **OpenCode** | The only harness to fail two categories on one slot (`rollback`, `cache`) *and* a third on the other (`pipeline`); additionally acquired a reproducible ~300s startup hang that was never root-caused. |
| **Codex** | Cannot use the `fast` slot at all. A perfect 24/24 on `deep-tiel`, but a harness covering only half the roster is not worth maintaining when four others cover both. |

Removal was a full uninstall -- npm packages, config and state directories (~1.9 GB), and Zed
`agent_servers` entries. `verify-harnesses.sh` passes **4/4** afterwards, and
`sync-harnesses.sh` regenerates cleanly for the four that remain:

| Kept | Role |
|---|---|
| **OpenClaw** | `fast`-slot default -- 24/24 at an 18.2s median, the quickest measured. |
| **Prime Agent** | `deep-tiel` default -- 24/24, 35.5s median, 137.1s ceiling; the only harness both fast and bounded. |
| **Hermes** | The only harness perfect on both slots, and flat across model tiers. |
| **dsh** | The most predictable: a 43.6s maximum on `fast`, the tightest ceiling in the campaign. |

Note what this leaves: **both slots keep a strong primary and a real fallback**, which the
strict reading of the criterion would not have -- it would have removed dsh and Prime Agent
over a single `pipeline` trajectory each, and with Prime Agent gone the deep slot's best
remaining option has a p90 worse than Prime's maximum.
