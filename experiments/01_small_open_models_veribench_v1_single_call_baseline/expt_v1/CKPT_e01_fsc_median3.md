# Checkpoint — experiment 01 FSC repeat fix (median of 3)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01_fsc_median3.md>

**TLDR:** Resume record for completing experiment 01's locked FSC judge design (repeats 2 and 3, median of 3) without overwriting repeat-1 evidence.

**Created:** 10-07-2026 16:48 PDT
**Last updated:** 10-07-2026 17:07 PDT (worker)

- **Task:** `expt_v1/cc_fsc_median3_fix.md`. Requested by Brando, 10-07-2026: "fix the 01 FSC repeat deviation".
- **Master:** Claude Code (Opus 5.5) on Brando's laptop, tmux `cc-rl4cv-master-argon-qa-e02-lethan-e01-fsc`, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv. **Worker:** Claude Code `claude-fable-5-1` / effort `high` via `/lfs/skampere1/0/brando9/bin/clauded_tok` (full access) on `skampere1`, tmux `rl4cv-e01-fsc-median3-worker`.
- **Status file:** `/lfs/skampere1/0/brando9/rl4cv_e01/STATUS_e01_fsc_median3`.
- **Spend:** $106.37 of $400 before this fix; estimate about +$204.
- **Next command (worker):** runbook § 1.

## Log
- **10-07-2026 16:49 PDT — worker launch receipt.** Client Claude Code via `/lfs/skampere1/0/brando9/bin/clauded_tok`; host `skampere1`; model `claude-fable-5-1`; effort `high`; permission mode `--dangerously-skip-permissions`; tmux session `rl4cv-e01-fsc-median3-worker`; checkout `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification` on `main` (pulled `--ff-only`, clean before start). Status file set to `RUNNING`. Step: runbook § 1 done, starting § 2 (build repeat packs, zero model calls).
- **10-07-2026 16:55 PDT — § 2 done (zero model calls).** `judge_rl4cv_e01.py` gained `build-repeats`, part `r23`, `fsc-median3`; the deploy wrapper gained `--part r23` and `--stop`; offline test `tests/test_e01_judge_repeats.py` (make test: 116 passed, 1 skipped). Repeat packs built for all 9 suites, every receipt `verdict: PASS`, n_cells = 2 × repeat-1 main cells, every r2/r3 prompt_sha256 equal to the recorded and the served repeat-1 hash: qwen3.5-0.8b 74, qwen3.5-2b 102, qwen3.5-4b 120, qwen3.5-9b 120, qwen3-1.7b 114, qwen3-4b 120, qwen3-8b 120, qwen3-14b 122, qwen3.6-27b-local 104 (total 996 cells × 2 members = 1,992 judge calls). Next: § 3 deploy r23 services on ports 9710–9718 (registry order), admit both members per suite.
- **10-07-2026 17:07 PDT — § 3 deployed and admitted (first model calls of this fix).**
  - **Route verification (non-secret):** Valkyrie CLI `valk` with `VALKYRIE_ENV=bench`, config = this checkout's experiment-103 `private/valkyrie.yaml` (a merge of the saved host config plus benchmark registrations; `environment: bench`, sandbox provider `daytona`, Valkyrie-managed `api_key` present); agent `vb103_judge` (installed 09-29-2026, secrets via its own `contract.yaml` secret mapping); `judge_rl4cv_e01.py:env()` strips every provider key from the environment. Same route, payer and configs as the repeat-1 runs (D-102; payer Vals gateway). Queue was empty at admission (`valk queue status`: 0 waiting, 0 active).
  - **Services (collect-only, uvicorn + cloudflared), all health 200 with bearer / 401 without, local and tunnel:** qwen3.5-0.8b port 9710 (service 612468/tunnel 612959); qwen3.5-2b port 9711 (service 629039/tunnel 629238); qwen3.5-4b port 9712 (service 632250/tunnel 632386); qwen3.5-9b port 9713 (service 642407/tunnel 642891); qwen3-1.7b port 9714 (service 662515/tunnel 663807); qwen3-4b port 9715 (service 666462/tunnel 668614); qwen3-8b port 9716 (service 670939/tunnel 674143); qwen3-14b port 9717 (service 708948/tunnel 710268); qwen3.6-27b-local port 9718 (service 712554/tunnel 713659). Port claim file `/lfs/skampere1/0/brando9/valkyrie_port_claims/rl4cv-e01_9700-9719.txt`. Receipts: this checkout's `external/veribench/experiments/103_…/private/deployment_rl4cv-e01-<label>-r23.json`.
  - **Admitted (concurrency 8, configs unchanged: H2_sol_high = GPT-6 Sol high, H2_opus55_max = Claude Opus 5.5 max):**

  | State key | Run id | Cells | Benchmark |
  |---|---|---:|---|
  | `qwen3.5-0.8b/H2_sol_high@r23` | `7843bae4-fd7b-4d11-bf41-76c5464f51b0` | 74 | `veribench-rl4cv-e01-qwen3-5-0-8b-r23` |
  | `qwen3.5-0.8b/H2_opus55_max@r23` | `0a0d75a5-09dc-4728-bb79-7839b4d9ab90` | 74 | `veribench-rl4cv-e01-qwen3-5-0-8b-r23` |
  | `qwen3.5-2b/H2_sol_high@r23` | `303c27f3-1884-473f-a814-78547ca2c84e` | 102 | `veribench-rl4cv-e01-qwen3-5-2b-r23` |
  | `qwen3.5-2b/H2_opus55_max@r23` | `5f6d1eec-cdf4-42e5-8131-0c140a81de96` | 102 | `veribench-rl4cv-e01-qwen3-5-2b-r23` |
  | `qwen3.5-4b/H2_sol_high@r23` | `d94b587b-1c84-4408-b72c-0fd73e7f8a93` | 120 | `veribench-rl4cv-e01-qwen3-5-4b-r23` |
  | `qwen3.5-4b/H2_opus55_max@r23` | `224453b4-eeef-4521-81fc-a8d8d028d417` | 120 | `veribench-rl4cv-e01-qwen3-5-4b-r23` |
  | `qwen3.5-9b/H2_sol_high@r23` | `b931b0fc-179b-4578-a99e-3b656023a6fd` | 120 | `veribench-rl4cv-e01-qwen3-5-9b-r23` |
  | `qwen3.5-9b/H2_opus55_max@r23` | `fcd7b38c-e7ae-4034-be7d-16649feaf345` | 120 | `veribench-rl4cv-e01-qwen3-5-9b-r23` |
  | `qwen3-1.7b/H2_sol_high@r23` | `739c072d-4a26-4f7a-a93f-b4f7af492d21` | 114 | `veribench-rl4cv-e01-qwen3-1-7b-r23` |
  | `qwen3-1.7b/H2_opus55_max@r23` | `53337af9-ac4f-4474-a1a4-d61d3d0ce7a7` | 114 | `veribench-rl4cv-e01-qwen3-1-7b-r23` |
  | `qwen3-4b/H2_sol_high@r23` | `c708d3cf-f346-4b3a-9925-c126226a3576` | 120 | `veribench-rl4cv-e01-qwen3-4b-r23` |
  | `qwen3-4b/H2_opus55_max@r23` | `69340008-3fe5-4632-823f-bdd35276bf10` | 120 | `veribench-rl4cv-e01-qwen3-4b-r23` |
  | `qwen3-8b/H2_sol_high@r23` | `57263210-8020-465f-9a3c-df3f9c62a9cd` | 120 | `veribench-rl4cv-e01-qwen3-8b-r23` |
  | `qwen3-8b/H2_opus55_max@r23` | `67b08a1f-83a1-4955-965d-b6263d72bc62` | 120 | `veribench-rl4cv-e01-qwen3-8b-r23` |
  | `qwen3-14b/H2_sol_high@r23` | `749d628b-abc2-46b0-adf7-16d11ecf47b9` | 122 | `veribench-rl4cv-e01-qwen3-14b-r23` |
  | `qwen3-14b/H2_opus55_max@r23` | `ac303e3a-a2bc-4d27-8796-32bf0a26870b` | 122 | `veribench-rl4cv-e01-qwen3-14b-r23` |
  | `qwen3.6-27b-local/H2_sol_high@r23` | `bad76afa-bebc-4474-ba23-d585d870818d` | 104 | `veribench-rl4cv-e01-qwen3-6-27b-local-r23` |
  | `qwen3.6-27b-local/H2_opus55_max@r23` | `01b5c429-cdd0-4b2e-b3fc-3c31e7e31040` | 104 | `veribench-rl4cv-e01-qwen3-6-27b-local-r23` |

  - **Next command:** watcher `poll` loop until every `@r23` key is terminal, then `harvest --part r23 --suite rl4cv-e01:<label>` for each label, then `fsc-median3`. Recovery policy: re-send once, as the identical cell, only cells whose receipt shows no request served.
