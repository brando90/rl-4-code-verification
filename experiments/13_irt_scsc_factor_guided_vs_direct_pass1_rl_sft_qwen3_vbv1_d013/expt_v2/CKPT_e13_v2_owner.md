# Experiment 13 version 2 owner checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/CKPT_e13_v2_owner.md>

**TLDR:** Single-writer setup for `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`, version 2. The initial records were published before authored development probes; no historical cells have run.

Created: 10-13-2026 11:44 PDT
Last updated: 10-13-2026 11:58 PDT

- Status: IMPLEMENTING R0; watchdog installed and six self-tests passed. Downstream gates unadmitted.
- Owner: skampere1, tmux `codex-rl4cv-e13v2-owner`; Codex `gpt-6-astra`, effort `high` (runbook worker pin), command-line interface 0.154.0; observed full access `danger-full-access`, approvals `never`.
- Owner native process: 887384; boot `839e7dd6-64e1-4a80-9498-31d30b3cc2df`. Launch evidence: `/lfs/skampere1/0/brando9/rl4cv_e13v2/owner_launch.json`. First useful actions: read binding plans, inspect clean checkout and process inventory.
- Work root: `/lfs/skampere1/0/brando9/rl4cv_e13v2`; owned clone `rl-4-code-verification`, branch `main`, starting revision `1e0c8f85a5943997ee2124180f7e492db3ca92b8`.
- Coordination: no live version 1 session or executable found. Pattern matches in the current owner's arguments are the pasted runbook, not a version 1 writer. Master checkpoint remains separately owned.
- Version 1 preservation: complete file digest inventory at `$WR/state/v1_baseline_hashes.json`; version 1 files stay byte-identical.
- Environment: pinned Lean and scorer under `/lfs/skampere1/0/brando9/rl4cv_e08/` read-only. New virtual environment, caches and temporary files under this work root.
- Resources: no accelerator allocation or model calls; setup and fixtures use central processors. Preflight available memory 1,939 GiB; filesystem free 5.4 TiB. Cell concurrency is not chosen until train diagnostics measure memory.
- Denominators: train/validation/test tasks 539/135/222; full reproduction 38,784 unique cells; base 21,504 plus ladder 20,520 minus overlap 3,240. Parent unavailable ladder 5,400 stays separate. Diagnostic target 300 rejected plus 100 measured train cells, selected by identifier only.
- Chronology: no validation or test factors computed in version 2; lock precedes those measurements. Historical test content remains opaque.
- Authorization: verbatim Stanford Network Analysis Project pre-approval in `cc.md`; no new charges or provider-key route used.
- Published initial records: `c49d4ba` (includes own `63ccdfc` and the master's concurrent checkpoint update). Setup `make test`: 277 passed, 23 skipped. SciPy was installed in the private environment after an initial collection failure.
- Watchdog: six tests passed (fake mailer, unique tmux kill, concurrent recovery, orphan child, persistent attempts, deterministic no-retry). Full `make test`: 283 passed, 23 skipped. Shared lock `$WR/watchdog/recovery.lock`; SQLite attempt/process ledger persists across boots. Owner PID/start/boot checked. Two additive cron entries installed (15 minutes, reboot). Existing mail credential authenticated without sending; only terminal/human-needed events email.
- Recovery configuration currently monitors the registered owner and adopts registered children; automatic executor replacement is not yet configured. Do not claim unattended executor recovery until the verified handoff route is installed.
- Node health: shared filesystem percentage-free warning (3,212 GiB free) does not constrain the bounded local fixture work; local work root has 5,483 GiB free. No shared cleanup performed.
- Authored development evidence only: valid source oracle 1, components at maximum; failed proof followed by valid theorem retains proof fraction 1/2 and command fraction 2/3. These are development checks, not the frozen R0 gate. Raw evidence under `$WR/state/`.
- Exact next actions: finish independent R0 expectations, freeze fixture and implementation hashes, execute once, and run `E13_REQUIRE_LEAN_INTEGRATION=1 make test`. A failed formal gate is published and stops downstream; no gate retry.
- Blockers: none established; no gate result yet.
