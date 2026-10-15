# Argon QA via Valkyrie

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/scripts/argon_qa/README.md>

**TLDR:** `argon_qa.py` sends a read-only quality-assurance (QA) review of committed repository snapshots to Gemini 4 Argon (`google/gemini-4-argon`). The call runs through Valkyrie, the Vals agent runner, on the Vals model gateway, which Vals funds. The tool reuses the validated transport agent `vb106_rater_v2` unchanged and writes no model-calling code of its own. Each review is a single call: the reviewer has no tools, cannot run code and cannot apply fixes.

## When to use it

Use it for an extra, Vals-funded critique of an experiment's documents, code and results, alongside the Codex or Claude Code QA that agents-config Hard Rule 3 defines. It does not replace that QA: the reviewer sees only the packet, cannot run tests and returns findings that the builder must verify.

The first test, on experiment 01, is in `experiments/01_small_open_models_veribench_v1_single_call_baseline/qa/argon_valkyrie_10-07-2026/`.

## Requirements

- A hosted Valkyrie login on this host (`valkyrie login`, then `valkyrie whoami`), a default sandbox provider (`valkyrie provider list`) and the slash-free gateway secret `brandoModelGatewayApiKey`. `deploy` registers the service on the Tracker with `valkyrie benchmark service set rl4cv-argon-qa <tunnel> --auth-secret rl4cv-argon-qa-bearer`, which needs the login (an access key can't). `valkyrie.yaml` is no longer read by Valkyrie (10-14-2026).
- The `vb106_rater_v2` bundle pushed to the current organization (`valkyrie agent push <dir>`; old bundles did not migrate).
- A Python environment that provides `uvicorn` and `benchmark_service`: the Valkyrie uv tool environment at `~/.local/share/uv/tools/valkyrie` if it still has them, otherwise set `RL4CV_ARGON_QA_UVICORN` to another environment's `uvicorn`. Run the script with that interpreter.
- A VeriBench clone at `$VERIBENCH_ROOT` (default `~/veribench`). The tool runs that clone's experiment 103 service code read-only and imports experiment 106's agent source, which the self-check uses.
- `cloudflared` on `PATH`.
- Free local port 9741.

## Steps

```bash
PY=~/.local/share/uv/tools/valkyrie/bin/python
$PY scripts/argon_qa/argon_qa.py build --scope experiments/<NN_name> --packet qa__x_a=<commit>   # zero calls
$PY scripts/argon_qa/argon_qa.py selfcheck      # round-trip through the agent's parser and the service's loader
$PY scripts/argon_qa/argon_qa.py deploy         # local collect-only service + quick tunnel, bearer on every route
$PY scripts/argon_qa/argon_qa.py admit --label <label>
$PY scripts/argon_qa/argon_qa.py status
$PY scripts/argon_qa/argon_qa.py harvest --out <dir>   # writes <dir>/responses/*.md and secret-free <dir>/receipts/*.json
$PY scripts/argon_qa/argon_qa.py teardown       # stops the service and tunnel, checks the port is free
```

Private state (the pack, bearer, local service registry `services.json`, logs and raw downloads) stays in `~/.cache/rl4cv-argon-qa/` (mode 0700; override with `RL4CV_ARGON_QA_HOME`).

## How a packet is built

- Every file is read with `git show <commit>:<path>`, so uncommitted work is never sent.
- The packet holds:
  - the frozen reviewer prompt (`SYSTEM_PROMPT`);
  - the commit hash;
  - a manifest of every tracked file in scope, with byte counts;
  - the contents of each file, except raw per-cell data, which is listed but omitted (`--omit`);
  - the context files (`CLAUDE.md`, `experiments/README.md` and `docs/DECISIONS.md` by default).
- The tool refuses to build when either of these checks fails:
  - Secret scan: the Hard Rule 1 patterns and the configured credential values.
  - Transport-marker check.

## Settings

| Setting | Value | Note |
|---|---|---|
| Model | `google/gemini-4-argon` | |
| `max_tokens` | 65,536 | |
| `reasoning_effort` | high | registry default; experiment 106 records it as Argon's highest setting |
| Temperature | 1.0 | registry default |
| Requests per cell | 1 | the agent sends a second request only after an HTTP 429 or 5xx, when nothing was served |
