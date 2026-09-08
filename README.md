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

This assumes [Pi](https://github.com/badlogic/pi-mono) is on `PATH` and configured with a
`llama-swap` provider (see `llama-swap.yaml` for the reference config). The protocol itself
is harness-agnostic in spirit — swap the `pi --provider ...` invocation in
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
