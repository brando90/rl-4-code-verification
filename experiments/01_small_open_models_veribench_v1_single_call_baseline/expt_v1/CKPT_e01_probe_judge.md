# Checkpoint: judge experiment 01's 11 proving G = 8 probe cells

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01_probe_judge.md>

**TLDR:** Live checkpoint for the worker that judges the 11 proving G = 8 probe cells (4 in `qwen3.5-9b_g8`, 7 in `qwen3-14b_g8`) with the locked FSC design (GPT-6 Sol high and Claude Opus 5.5 max, 3 repeats each, median of 3) on the `vb103_judge` Valkyrie route, then adds the probe's `scsc` and partial `fsc_compiled` channels. Runbook: `cc_judge_probe_proving_cells.md`.

- **Created:** 10-07-2026 19:55:37 PDT
- **Last updated:** 10-07-2026 20:07:28 PDT
- **Status file:** `/lfs/skampere1/0/brando9/rl4cv_e01/STATUS_e01_probe_judge`

## Launch receipt

- **Client:** Claude Code via `clauded_tok`
- **Host:** skampere1 (SNAP)
- **Model:** `claude-fable-5-1`, effort high
- **Permission mode:** `--dangerously-skip-permissions`
- **tmux session:** `rl4cv-e01-probe-judge-worker`
- **Checkout:** `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification` on `main` at `4c1d6a2`
- **Task:** Brando (10-07-2026): "now judge the 11 proving G=8 probe cells".
- **Launched:** 10-07-2026 19:55:37 PDT; status file set to RUNNING.

## Log

- 10-07-2026 19:55:37 PDT — launched; reading INDEX_RULES, CLAUDE.md, PROTOCOL.md, results.md, REPORT.md and `judge_rl4cv_e01.py`.
- 10-07-2026 20:02:58 PDT — **§ 1–2 done (zero model calls).** `list-probe-cells` → `results/judge/probe_proving_cells.json`: verdict PASS, 11/11 cells (qwen3.5-9b 4, qwen3-14b 7, the other 6 models 0), every solution.lean SHA-256 equals its generation receipt. `build-probe` packs: qwen3.5-9b 4 items × 3 repeats = 12 cells, qwen3-14b 7 × 3 = 21 cells; both round-trip PASS, one prompt hash per item (repeats byte-identical), 0 smoke, 0 control cells. Code: `judge_rl4cv_e01.py` (+`list-probe-cells`, `build-probe`, `fsc-probe`, suite `rl4cv-e01-probe:<label>`), deploy wrapper (+`--part probe --port`), `tests/test_e01_judge_probe.py`; `make test` 119 passed, 1 skipped. Next: § 3 claim ports 9710–9711, deploy, admit both members per suite.
- 10-07-2026 20:07:28 PDT — **§ 3 deployed and admitted (first model calls of this task).**
  - **Route verification (non-secret):** Valkyrie CLI `valk`, `VALKYRIE_ENV=bench`, config = this checkout's experiment-103 `private/valkyrie.yaml` (`environment: bench`, sandbox provider `daytona`); agent `vb103_judge`; `judge_rl4cv_e01.py:env()` strips every provider key. Same route, payer (Vals gateway, D-102) and judge configs as the repeat-1 and r23 runs. Queue empty at admission (0 waiting, 0 active). Spend before admission $289.78 of $400.
  - **Port claim:** `/lfs/skampere1/0/brando9/valkyrie_port_claims/rl4cv-e01-probe_9710-9711.txt` (9710–9719 verified free with `ss -tlnp` before binding; other claims 9720–9739, 9740–9759 untouched).
  - **Services (collect-only, uvicorn + cloudflared; all health 200 with bearer / 401 without, local and tunnel):** `rl4cv-e01-probe-qwen3.5-9b` port 9710 (service PID 2661150, tunnel 2661682, 12 pack tasks); `rl4cv-e01-probe-qwen3-14b` port 9711 (service PID 2674462, tunnel 2676074, 21 pack tasks). Receipts: `external/veribench/experiments/103_…/private/deployment_rl4cv-e01-probe-<label>.json`.
  - **Admitted (concurrency 8; H2_sol_high = GPT-6 Sol high, H2_opus55_max = Claude Opus 5.5 max):**

  | State key | Run id | Cells | Benchmark |
  |---|---|---:|---|
  | `probe-qwen3.5-9b/H2_sol_high` | `491357a7-59dc-4019-a3cb-6960cf134d95` | 12 | `veribench-rl4cv-e01-probe-qwen3-5-9b` |
  | `probe-qwen3.5-9b/H2_opus55_max` | `b12aea6f-225a-45a0-8806-b726e5593837` | 12 | `veribench-rl4cv-e01-probe-qwen3-5-9b` |
  | `probe-qwen3-14b/H2_sol_high` | `6fe755ef-5266-4668-bdd2-6f4b609efec4` | 21 | `veribench-rl4cv-e01-probe-qwen3-14b` |
  | `probe-qwen3-14b/H2_opus55_max` | `a5de0dcc-2c08-49e6-a38f-d109078a64ac` | 21 | `veribench-rl4cv-e01-probe-qwen3-14b` |

  - **Transport note:** the first `valk run start` for `probe-qwen3-14b/H2_sol_high` returned `502 Bad Gateway`; `valk run list --benchmark-name veribench-rl4cv-e01-probe-qwen3-14b` showed no run had been created (no spend), so the stale `admission_failed` entry (`run_id: None`) was removed from `state.json` (recorded under `admission_failures_removed`, the deviation-11 procedure) and the member re-admitted once, succeeding.
  - **Next command:** poll until all four `probe-*` keys are terminal, then `harvest --suite rl4cv-e01-probe:<label>` per suite, `recover` only for never-served cells, `fsc-probe`, then the channel report.
