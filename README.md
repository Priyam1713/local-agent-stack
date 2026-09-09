# Local Agent Stack: A Testing Journal

A record of picking, tuning, and rejecting local LLMs as the daily driver for an
agentic coding stack on a 12 GB laptop GPU — every number measured, every rejection
kept, nothing hand-waved.

## Hardware

RTX 5070 Ti Laptop (12 GB VRAM, Blackwell / `sm_120`), 32 GB system RAM, Ryzen AI 9 HX 375.
Inference via [llama.cpp](https://github.com/ggml-org/llama.cpp) + [llama-swap](https://github.com/mostlygeek/llama-swap)
(model residency/routing), harness is [Pi](https://github.com/badlogic/pi-mono) driven
through Zed's Agent Client Protocol.

## Why this exists

Most "I ran model X locally" posts report one number: tokens/sec, or a single-prompt vibe
check. Neither predicts whether a model is usable as a coding agent. Twice in this project,
a model that looked great in isolation collapsed under real multi-turn tool use — and once,
a model that looked *risky* in isolation turned out to be the best challenger tested. See
[`STACK.md`](./STACK.md) for the full, dated log of every measurement and every reversal.

**The rule that survived all of it:** never judge a local model on throughput alone, and
never trust a single-prompt screen as a verdict — only a full multi-turn agent-loop protocol,
against a fixture with real bugs and a real test suite, is trustworthy.

The same rule turned out to apply to *harnesses*, and cost two wrong verdicts before it was
learned there too: one harness was written off from its documentation without ever being
installed, and another was declared incompatible with a model slot on the strength of a
default configuration. Both went on to score perfectly. See [`HARNESSES.md`](./HARNESSES.md).

## The protocol

Every serious candidate runs through [`scripts/run-h2h-expanded.sh`](./scripts/run-h2h-expanded.sh):
8 tasks × 3 runs = 24 real trajectories, driven through Pi's actual agent loop (not raw HTTP
chat) against the fixture in [`fixture/`](./fixture). The fixture is a small Python package
with a real, verifiable bug (or missing feature, or multi-bug interaction) in each module and
a pytest suite that only passes on a correct fix:

| Task | Kind | What it tests |
|---|---|---|
| `alias`, `auth`, `median` | single bug-fix | baseline correctness |
| `overlay` | bug-fix | must deep-merge, not shallow-replace |
| `rollback` | bug-fix | must restore original state on failure |
| `cache` | feature | apply a memoize decorator per a documented convention |
| `dedupe` | refactor | extract duplicated logic into one shared helper, across two functions, without changing behaviour |
| `pipeline` | multi-bug | three independent bugs in one file — none of the tests pass until all three are fixed |

Per trajectory it records: **success** (pytest-verified, independent of anything the model
claims), wall-clock, tool calls, tool errors, and the character counts of reasoning vs. answer
content. [`scripts/reverify-h2h-expanded.sh`](./scripts/reverify-h2h-expanded.sh) re-grades a
completed run's transcripts with a corrected `PYTHONPATH`, so grading bugs don't get baked into
a result.

An earlier, smaller 5-task × 3-run fixture (the first five rows above) was used before it
stopped discriminating between candidates — several models reached a perfect 15/15 on it.
**Scores from the two fixtures are never compared directly** — every result in this repo is
tagged with which one produced it.

## What's in here

- **[`HARNESSES.md`](./HARNESSES.md)** — the other half of the question: with the model held
  fixed, how much does the *harness* driving it matter? Seven harnesses × two model slots ×
  24 trajectories. Short answer: almost nothing for correctness, a great deal for speed —
  and the ranking inverts between slots, so there is no single harness to standardise on.
- **[`STACK.md`](./STACK.md)** — the full, dated decision log. Every model tested, every
  measurement, every rejection reason, in the order it happened. This is the primary
  document; everything else supports it.
- **[`MODELS.md`](./MODELS.md)** — the same data as a scannable table: what's live, what's
  under evaluation, what was rejected and why, what's still sitting on disk unused.
- **[`fixture/`](./fixture)** — the test package the protocol runs against.
- **[`scripts/`](./scripts)** — the reusable protocol scripts. (Dozens of one-off
  benchmark/inspection scripts tied to specific now-deleted models were left out —
  these three are what actually reproduce the methodology.)
- **[`llama-swap.yaml`](./llama-swap.yaml)** — the live model-routing config, annotated
  with why each setting exists.
- **[`harnesses/`](./harnesses)** — the multi-harness setup: a machine-readable
  [`registry.json`](./harnesses/registry.json) of every wired harness (binary, config path,
  headless invocation, verification date) and a [`README`](./harnesses/README.md) of the
  traps each one hides.
- **[`harnesses/results/`](./harnesses/results)** — raw per-trajectory results for all
  336 harness trajectories, one TSV per harness/slot cell.

## Setting up the stack

Nothing below is required to *read* `STACK.md`/`MODELS.md`, only to run the protocol
yourself. Versions pinned here are what this project actually ran on 2026-09; newer
releases of each tool should work fine, but if something behaves differently, this is the
baseline to diff against.

**1. llama.cpp** (b10726, commit `85c5522`) — built from source for CUDA/Blackwell
(`sm_120`); a prebuilt release binary works too if it matches your GPU's compute
capability. From a [clone](https://github.com/ggml-org/llama.cpp):

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES=<your compute capability, e.g. 120 for Blackwell> \
  -DGGML_CUDA_FA=ON -DGGML_CUDA_GRAPHS=ON -DGGML_CUDA_NCCL=ON \
  -DGGML_CUDA_COMPRESSION_MODE=size -DGGML_NATIVE=ON -DLLAMA_CURL=ON
cmake --build build --config Release -j $(nproc) --target llama-server llama-bench
```

A model whose architecture postdates your build (this repo hit that twice — see
`STACK.md`'s K2-Horizon and Spark-X2.5 entries) needs a newer checkout. Rebuild into a
*separate* directory (`build-new`, say) rather than overwriting a binary you've already
validated — nothing here assumes the newest build is the best one.

**2. [llama-swap](https://github.com/mostlygeek/llama-swap)** (v252 here) — a single Go
binary. Download a release, point it at [`llama-swap.yaml`](./llama-swap.yaml):

```bash
llama-swap -config llama-swap.yaml -listen 127.0.0.1:8080 -watch-config
```

That config is the actual routing table this project ran, annotated with why each
`--n-cpu-moe` value was chosen — it's a starting point to edit, not a template to copy
verbatim, since that value doesn't transfer between models or hardware.

**3. [Pi](https://github.com/badlogic/pi-mono)** (0.84.4 here) — the harness the protocol
drives. Install per its own docs, then register `llama-swap` as an OpenAI-compatible
provider pointed at `http://127.0.0.1:8080/v1`. Confirm it can see your models:

```bash
pi --provider llama-swap --model <model-id> --no-session --print "say hi"
```

Zed + Pi's Agent Client Protocol integration (used for interactive daily driving, not for
the benchmark protocol itself) is one layer up from this and isn't needed just to run
`run-h2h-expanded.sh` — Pi's CLI is enough on its own.

**Running on WSL2 from Windows?** This project ran llama.cpp/llama-swap inside WSL2 Ubuntu
24.04 with mirrored networking, so `127.0.0.1:8080` is reachable identically from both
sides — no port-forwarding config needed. If you hit `wsl.exe` silently mangling a path
argument passed through Git Bash, or a shell variable collapsing to empty when nested
through `bash -c "..."`, those are both real landmines this project hit repeatedly — see
the "process lesson" entries in `STACK.md` for the exact fix.

## Reproducing a run

```bash
# 1. Set up the fixture's own venv (only needs pytest)
cd fixture && python -m venv .venv && ./.venv/Scripts/pip install pytest && cd ..

# 2. Point Pi at your own llama-swap instance, then run the protocol against a model id
#    it exposes:
./scripts/run-h2h-expanded.sh <your-model-id>

# 3. Re-grade with corrected PYTHONPATH (recommended -- fixes a real grading bug):
./scripts/reverify-h2h-expanded.sh ./results/h2h-expanded-runs-<your-model-id>
```

This assumes Pi is on `PATH` and configured with a `llama-swap` provider as above. The
protocol itself is harness-agnostic in spirit — swap the `pi --provider ...` invocation in
`run-h2h-expanded.sh` for any CLI-drivable agent harness and the fixture/grading still work.

## The headline results, if you read nothing else

| Model | Fixture | All-three | Individual | Wall/success | Notes |
|---|---|---:|---:|---:|---|
| **Tiel-Coder-35B-A3B** | 8-task ×2 | 8/8, 8/8 | 24/24, 24/24 | 59.4s / 60.5s | Only model to run the fixture perfectly, twice |
| Qwen3.6-35B-A3B APEX | 8-task | 7/8 | 23/24 | 52.29s | Fastest deep-class model; the reference challenger for everything after it |
| CalibForge-35B-A3B | 8-task | 8/8 | 24/24 | 76.90s | Perfect correctness, +22% prompt-processing benchmark, **still lost** — burned 6× the reasoning of Tiel for the same output |
| gpt-oss-20b | 5-task | 1/5 | 9/15 | 50.8s | 5/5 on an isolated screen at 101 tok/s, then repeatedly stalled re-reading context without acting under real tool use |

The CalibForge and gpt-oss rows are the two results that most directly justify the "never
judge on throughput or an isolated screen" rule above — full detail on both in `STACK.md`.

## License

MIT — see `LICENSE`. Do whatever you want with the protocol, fixture, or config; none of it
depends on anything proprietary.
