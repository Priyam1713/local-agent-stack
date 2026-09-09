# Multi-harness setup

Four coding harnesses, one model backend, one source of truth.

All four drive the **same** llama-swap instance at `http://127.0.0.1:8080/v1` and see the
**same** model slots. That is the whole point: swapping harness must change only the harness,
never the models, or nothing measured across them is comparable.

```
              llama-swap  (127.0.0.1:8080/v1)
              fast / deep / deep-tiel
                          |
   +--------------+-------+-------+--------------+
   |              |               |              |
Prime Agent      dsh          OpenClaw        Hermes
   (WSL)         (WSL)          (WSL)          (WSL)
```

The goal is **not** to crown one winner. It is to know which harness is worth reaching for on
which kind of work, and on which slot -- a harness that is mediocre overall but reliably best
at one category still earns its place.

**Seven were benchmarked; three were removed on 2026-09-09.** Pi, OpenCode and Codex each
failed more than one task category or could not run a whole model slot. The full comparison,
including their results, is in [`HARNESSES.md`](../HARNESSES.md); the removal reasons are in
`registry.json` under `removed`. Their measurements stand as a record even though the
harnesses are gone.

## The one rule that keeps this from rotting

**`llama-swap.yaml` is the only place the model roster is defined.** Every harness's config is
*generated* from it by `sync-harnesses.sh` -- never hand-edited.

This is not theoretical tidiness. When this was set up, Prime Agent's config still described
`deep` as "Nemotron 3.5 Lightning" -- a model deleted days earlier and replaced by APEX -- and
still listed a `deep-lite` slot that no longer existed, while missing `fast` and `deep-tiel`
entirely. Four harnesses times a changing model roster, each maintained by hand, guarantees
that kind of drift.

**After any slot change, run:**

```bash
wsl.exe -d Ubuntu-24.04 -- bash -c "bash /mnt/d/LocalAI/config/harnesses/sync-harnesses.sh"
```

It reads the live slots, pulls each slot's display name from its own `name:` field, and
rewrites the generated provider configs. Idempotent; safe to re-run.

It also derives each slot's **context window** from that slot's own `-c` / `--ctx-size` line.
A single hardcoded number is how every harness config came to advertise 65536 tokens on slots
llama-swap only opens at 32768 -- the client then packs a request the server cannot accept.

## Verifying

"Integrated" means proven, not "the binary exists and the config looks plausible":

```bash
bash /d/LocalAI/config/harnesses/verify-harnesses.sh fast
```

Four things this caught that a config inspection would have missed:

- **Each harness must be invoked where it lives.** All four survivors run in WSL, but this
  rule cost real debugging time before the Windows-side harnesses were removed: running Pi
  from inside WSL resolved a different `HOME` and it reported
  `Unknown provider "llama-swap"` despite being correctly configured on the Windows side.
- **Git Bash mangles bare WSL paths.** Passing `/mnt/d/...` or `/home/priya/...` straight to
  `wsl.exe` from Git Bash rewrites it to `C:/Program Files/Git/mnt/d/...`, which fails with
  "No such file or directory" **and still exits 0**. Wrap it:
  `wsl.exe -d Ubuntu-24.04 -- bash -c "<literal path> ..."`.
- **"It answered" is not "it edited".** Every harness here can produce a fluent description of
  the fix while changing nothing on disk. OpenClaw went further and reported "Fixed and
  committed" for an edit it had made to a different copy of the file. Grade by running the
  tests against the resulting files, never by reading the transcript.
- **dsh has no `--model` flag.** It reads the slot from a config file, so a run that forgets
  to rewrite it silently measures the previous slot. `set-harness-model.sh` does that rewrite
  and echoes back what the file now says.

## Editor integration (ACP)

Three of the four are registered in Zed under `agent_servers` and reachable from the agent
panel. Every entry uses an **absolute path** -- Zed does not inherit the shell PATH.

| Agent | Zed command |
|---|---|
| Prime Agent | `wsl.exe -d Ubuntu-24.04 -- /home/.../bin/prime-agent --mode acp` |
| Hermes | `wsl.exe -d Ubuntu-24.04 -- /home/priya/.local/bin/hermes acp` |
| OpenClaw | `wsl.exe -d Ubuntu-24.04 -- bash /mnt/d/LocalAI/config/harnesses/zed-openclaw-acp.sh` |

dsh is benchmarked but not registered -- it exposes no ACP mode.

**OpenClaw needs a wrapper and the reason is not obvious.** `openclaw acp` is not a
self-contained agent: it is a bridge *client* of OpenClaw's WebSocket Gateway, and with
nothing listening on 127.0.0.1:18789 it exits immediately with
`ACP bridge failed: connect ECONNREFUSED`. Zed surfaces that only as an agent that will not
start. [`zed-openclaw-acp.sh`](./zed-openclaw-acp.sh) brings the gateway up lazily on first
use and then execs the bridge. It is started on demand rather than installed as a systemd
user service because the gateway holds ~383 MB RSS and WSL is capped at 14 GB on this
machine; a permanently-resident daemon for an occasionally-used harness is a poor trade.

It passes `--allow-unconfigured` because `openclaw.json` has no `gateway` block and must not
gain one: that file is generated by `sync-harnesses.sh`, so anything hand-added is erased at
the next slot change. The flag is the documented way to start without demanding
`gateway.mode=local`, and it explicitly does not rewrite the config.

**Verify a registration by handshake, not by launching it and watching.** Feed the agent an
ACP `initialize` request on stdin and keep the pipe open -- closing stdin immediately makes a
*healthy* agent exit silently, which looks exactly like a broken one:

```bash
bash /d/LocalAI/config/harnesses/test-acp-handshake.sh
```

Both currently answer with their own `agentInfo`: `hermes-agent 0.21.1` and
`openclaw-acp 2026.9.2`.

## The harnesses

| | Runs on | Slots | Role |
|---|---|---|---|
| **Prime Agent** | WSL | all | **Deep-slot default.** 24/24 on `deep-tiel` at a 35.5s median and a 137.1s ceiling -- the only harness that is both fast and bounded. Persistent IPython REPL, recursive subagents, Continual Harness (PrimeIntellect). |
| **OpenClaw** | WSL | all | **Fast-slot default.** 24/24 on `fast` at an 18.2s median, the quickest measured. Falls to a 79.1s median on `deep-tiel`, so it is a poor deep choice. |
| **Hermes** | WSL | all | The only harness perfect on **both** slots (24/24 / 24/24). Flat across model tiers -- 37.9s on `fast`, 35.5s on `deep-tiel` -- because its clock is fixed per-turn overhead, not token generation. |
| **dsh** | WSL | all | The most *predictable*: a 43.6s maximum on `fast` is the tightest ceiling measured anywhere in the campaign. DeepSeek's own agent loop; verbose interleaved reasoning on stdout. |

## Gotchas worth knowing

- **Prime Agent is PrimeIntellect's**, despite `package.json` listing author "Mario Zechner"
  and depending on `@earendil-works/pi-*`. Its `repository` field resolves to
  `github.com/PrimeIntellect-ai/prime-agent`, directory `packages/coding-agent` -- Zechner
  authors that package inside their monorepo. It is not a name collision with Pi.
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
- **`timeout` needs `-k`.** GNU `timeout` sends SIGTERM and then *waits* for the child. Against
  Pi's Windows launcher that signal never landed and one trajectory ran 9163.9s -- 18x its own
  500s bound. `timeout -k 30 500` adds a SIGKILL that maps to a real `TerminateProcess`. Kept
  here because the failure mode is not Pi-specific in principle, only in this campaign.

## A harness is not eliminated until it has been run

Hermes was recorded in this file as "deliberately not wired", with reasoning taken entirely
from its documentation: no ACP, daemon-shaped, and its persistent-memory headline already
covered by funes. That verdict was reached without ever installing it. It was overridden, and
once installed Hermes passed pre-flight on both slots on the first attempt.

The same file also asserted that OpenClaw could not run `deep-tiel` at all. That one was
measured -- but measured on a default configuration, and the harness ships its own answer to
exactly that problem, so the slot works fine.

**Those two are now the only harnesses that scored 24/24 on `fast`.** Install it, run it on
the fixture, and let the result decide -- in both directions.

## Adding a harness

1. Install it; confirm it exposes a headless/print mode (ACP is a bonus, not a requirement).
2. Pre-flight it on the fixture and confirm it **edits a file**, not merely that it replies.
3. Add a generator block to `sync-harnesses.sh` so its roster derives from `llama-swap.yaml`.
4. Add a branch to `run-h2h-harness.sh` so it can be benchmarked on the same 8 tasks.
5. Add it to `verify-harnesses.sh` -- invoked on the side it actually runs on.
6. Run the verifier. It is not integrated until it passes.
7. Record it in `registry.json`.
