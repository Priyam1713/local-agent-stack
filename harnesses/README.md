# Multi-harness setup

Seven coding harnesses, one model backend, one source of truth.

All seven drive the **same** llama-swap instance at `http://127.0.0.1:8080/v1` and see the
**same** model slots. That is the whole point: swapping harness must change only the harness,
never the models, or nothing measured across them is comparable.

```
                          llama-swap  (127.0.0.1:8080/v1)
                          fast / deep / deep-tiel
                                     |
   +---------+---------+-------------+-------------+---------+---------+
   |         |         |             |             |         |         |
  Pi     OpenCode  Prime Agent     Codex          dsh    OpenClaw   Hermes
(Windows) (Windows)   (WSL)        (WSL)          (WSL)    (WSL)     (WSL)
```

The goal is **not** to crown one winner. It is to know which harness is worth reaching for on
which kind of work, and on which slot -- a harness that is mediocre overall but reliably best
at one category still earns its place.

## The one rule that keeps this from rotting

**`llama-swap.yaml` is the only place the model roster is defined.** Every harness's config is
*generated* from it by `sync-harnesses.sh` -- never hand-edited.

This is not theoretical tidiness. When this was set up, Prime Agent's config still described
`deep` as "Nemotron 3.5 Lightning" -- a model deleted days earlier and replaced by APEX -- and
still listed a `deep-lite` slot that no longer existed, while missing `fast` and `deep-tiel`
entirely. Seven harnesses times a changing model roster, each maintained by hand, guarantees
that kind of drift.

**After any slot change, run:**

```bash
wsl.exe -d Ubuntu-24.04 -- bash -c "bash /mnt/d/LocalAI/config/harnesses/sync-harnesses.sh"
```

It reads the live slots, pulls each slot's display name from its own `name:` field, and
rewrites the generated provider configs. Idempotent; safe to re-run.

## Verifying

"Integrated" means proven, not "the binary exists and the config looks plausible":

```bash
bash /d/LocalAI/config/harnesses/verify-harnesses.sh fast
```

Four things this caught that a config inspection would have missed:

- **Each harness must be invoked where it lives.** Running Pi from inside WSL resolved a
  different `HOME` and it reported `Unknown provider "llama-swap"` despite being correctly
  configured on the Windows side. Pi and OpenCode run on Windows; the other five run in WSL.
- **Git Bash mangles bare WSL paths.** Passing `/mnt/d/...` or `/home/priya/...` straight to
  `wsl.exe` from Git Bash rewrites it to `C:/Program Files/Git/mnt/d/...`, which fails with
  "No such file or directory" **and still exits 0**. Wrap it:
  `wsl.exe -d Ubuntu-24.04 -- bash -c "<literal path> ..."`.
- **"It answered" is not "it edited".** Every harness here can produce a fluent description of
  the fix while changing nothing on disk. OpenClaw went further and reported "Fixed and
  committed" for an edit it had made to a different copy of the file. Grade by running the
  tests against the resulting files, never by reading the transcript.
- **Three harnesses have no `--model` flag.** codex, dsh and hermes read the slot from a config
  file, so a benchmark run that forgets to rewrite it silently measures the previous slot.
  `set-harness-model.sh` does that rewrite and echoes back what the file now says.

## The harnesses

| | Runs on | Slots | Role |
|---|---|---|---|
| **Pi** | Windows | all | Default daily driver. The 8-task protocol was built around it; all 360 early trajectories ran through it. |
| **Prime Agent** | WSL | all | Capability amplification. Persistent IPython REPL, recursive subagents, Continual Harness carrying memory/skills across trajectories. The ARC-AGI-3 95.5% harness (PrimeIntellect). |
| **OpenCode** | Windows | all | Multi-provider alternative. Persistent client/server sessions (SQLite) that survive terminal disconnects. |
| **Codex** | WSL | deep only | A mainstream commercial harness pointed at local weights -- the control that shows how much of the behaviour is harness rather than model. |
| **dsh** | WSL | all | DeepSeek's own agent loop. Verbose interleaved reasoning on stdout rather than a structured event stream. |
| **OpenClaw** | WSL | all | Chat-platform-first agent with an isolated headless `agent exec` mode. |
| **Hermes** | WSL | all | Standing personal-assistant daemon with persistent cross-session memory, evaluated here purely as a coding harness. |

## Gotchas worth knowing

- **Prime Agent is PrimeIntellect's**, despite `package.json` listing author "Mario Zechner"
  and depending on `@earendil-works/pi-*`. Its `repository` field resolves to
  `github.com/PrimeIntellect-ai/prime-agent`, directory `packages/coding-agent` -- Zechner
  authors that package inside their monorepo. It is not a name collision with Pi.
- **OpenCode Desktop is not OpenCode CLI.** The Electron desktop app (`@opencode-aidesktop`)
  ships no CLI binary. ACP registration and headless runs both need the npm package
  (`npm install -g --allow-scripts=opencode-ai opencode-ai`) -- npm's script guard blocks the
  postinstall that fetches the real binary unless `--allow-scripts` is passed.
- **Codex cannot use the `fast` slot.** Qwen3.5's chat template rejects Codex's `instructions`
  field with "System message must be at the beginning". The client shows a retry storm and
  "We're currently experiencing high demand", which looks like a server problem and is not.
  Diagnosed by proxying the wire on port 8099. The Windows build is separately unusable --
  `pwsh.exe` resolves to the WindowsApps alias and is blocked by execution policy -- hence WSL.
- **dsh must come from npm, not from source.** `@deepseek-ai/cordis` declares `FiberState` as
  `export const enum`, which TypeScript erases at compile time, so tsx's isolated transpilation
  has no runtime export to import. `pnpm run build` only builds `apps/web`, `build:lib` does not
  fix it, `rescope-vendor` runs dry-only, and `node_modules/@deepseek-ai/cordis` never existed.
  The published `@deepseek-ai/dsh` build has those const enums inlined.
- **OpenClaw ignores cwd unless you use `agent exec --cwd`.** Plain `openclaw agent --local`
  edits `~/.openclaw/workspace` no matter where it is invoked. Staging into that shared
  workspace is not a workaround either: OpenClaw attests it in `state/openclaw.sqlite` and
  refuses to run once `BOOTSTRAP.md` has gone missing from an already-initialised workspace.
  Its full tool surface also builds a 33,635-token system prompt that does not fit `deep-tiel`'s
  32,768 context; `--local-model-lean`, its own reduced surface for local models, does.
- **Hermes resolves relative paths against `$HOME`,** not the process working directory and not
  `--in`, which it accepts and then ignores. Left alone it will find and edit some *other* copy
  of the file elsewhere under `$HOME`. Run it as
  `HOME=<workdir> HERMES_HOME=/home/priya/.hermes hermes -z "<prompt>" -m <slot> --yolo`.
  Without `--yolo` the approval prompts block a headless run.

## A harness is not eliminated until it has been run

Hermes was recorded in this file as "deliberately not wired", with reasoning taken entirely
from its documentation: no ACP, daemon-shaped, and its persistent-memory headline already
covered by funes. That verdict was reached without ever installing it. It was overridden, and
once installed Hermes passed pre-flight on both slots on the first attempt.

The same file also asserted that OpenClaw could not run `deep-tiel` at all. That one was
measured -- but measured on a default configuration, and the harness ships its own answer to
exactly that problem, so the slot works fine.

Install it, run it on the fixture, and let the result decide -- in both directions.

## Adding a harness

1. Install it; confirm it exposes a headless/print mode (ACP is a bonus, not a requirement).
2. Pre-flight it on the fixture and confirm it **edits a file**, not merely that it replies.
3. Add a generator block to `sync-harnesses.sh` so its roster derives from `llama-swap.yaml`.
4. Add a branch to `run-h2h-harness.sh` so it can be benchmarked on the same 8 tasks.
5. Add it to `verify-harnesses.sh` -- invoked on the side it actually runs on.
6. Run the verifier. It is not integrated until it passes.
7. Record it in `registry.json`.
