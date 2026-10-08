# Checkpoint — experiment 01 FSC repeat fix (median of 3)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01_fsc_median3.md>

**TLDR:** Resume record for completing experiment 01's locked FSC judge design (repeats 2 and 3, median of 3) without overwriting repeat-1 evidence.

**Created:** 10-07-2026 16:48 PDT
**Last updated:** 10-07-2026 18:35 PDT (worker, final)

- **Task:** `expt_v1/cc_fsc_median3_fix.md`. Requested by Brando, 10-07-2026: "fix the 01 FSC repeat deviation".
- **Master:** Claude Code (Opus 5.5) on Brando's laptop, tmux `cc-rl4cv-master-argon-qa-e02-lethan-e01-fsc`, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv. **Worker:** Claude Code `claude-fable-5-1` / effort `high` via `/lfs/skampere1/0/brando9/bin/clauded_tok` (full access) on `skampere1`, tmux `rl4cv-e01-fsc-median3-worker`.
- **Status file:** `/lfs/skampere1/0/brando9/rl4cv_e01/STATUS_e01_fsc_median3`.
- **Spend:** $106.37 of $400 before this fix; estimate was about +$204; actual +$183.41 (repeats 2–3 $174.65 + recovery $8.76); **final total $289.78 of $400**.
- **Status: DONE** (worker, see final entry below). Next command: none; the master reads the final state here and in results.md "FSC repeat correction (10-07-2026)".

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
- **10-07-2026 17:57 PDT — all 18 r23 runs terminal (watcher poll 17:32 PDT); harvesting.** Live status over all runs: 1,878 FINISHED, 114 ERROR of 1,992 cells. Every ERROR is a Daytona sandbox-provisioning failure before the agent ran ("Failed to update network settings: An operation is already in progress for this resource"), so those cells have no receipt and no model request; they are the declared single recovery pass's input. **Transport deviation:** `valk run results <run_id>` returns "tracker returned a malformed response" for every run, including the repeat-1 runs harvested on 10-01-2026, so it is a Valkyrie tracker-side regression, not these runs. `valk run output` (artifact receipts) and `valk run task <run> <task> --format json` (the same `evaluation_result.solution_b64` verdict bytes, per task) both work; `harvest` now falls back to the per-task fetch and records `results_source` in each harvest file. Same route, same bytes, no scientific setting changed.
- **10-07-2026 18:19 PDT — r23 harvested (18 runs, per-task results); recovery pass admitted.** 1,992 cells: 1,868 measured, 124 unmeasured; repeats 2–3 charges $174.65 (running total $281.02 of $400). Of the 124: **114 never served** (no receipt: Daytona sandbox provisioning error) → re-sent once as identical cells in 18 `@r23__recovery_1` runs (run ids in `state.json`); **10 served, `model_error`** (H2_opus55_max only; the same 5 items that failed for that member in repeat 1: `cs_set__dfs`, `cs_set__heapsort_build_heap`, `security_set__security_6858__safe__135_…` (qwen3.5-4b), `realcode_set__26_secrets_token` (qwen3.5-9b), `security_set__security_6858__safe__69_…` (qwen3-14b), `humaneval_set__humaneval_2_truncate_number` (qwen3.6-27b-local)) → model observations, never re-sent, stay listed as unmeasured. Watcher: tmux window `watchrec`. Next: `harvest --part r23 --recovery` per suite, then `fsc-median3`, then `fsc_median3_report.py`.
- **10-07-2026 18:35 PDT — DONE (§ 4 published, teardown verified).**
  - **Recovery:** 18 `@r23__recovery_1` runs, 114/114 never-served cells measured ($8.76). 10 `model_error` cells (Opus member, 5 items, every repeat, same as repeat 1) stay unmeasured and listed.
  - **Final FSC, single repeat → median of 3 (mean over complete items, n):** Qwen3.5-0.8B 0.011 → 0.014 (37); Qwen3.5-2B 0.073 → 0.073 (51); Qwen3.5-4B 0.328 → 0.332 (57/60); Qwen3.5-9B 0.414 → 0.419 (59/60); Qwen3-1.7B 0.096 → 0.105 (57); Qwen3-4B 0.365 → 0.362 (60); Qwen3-8B 0.372 → 0.375 (60); Qwen3-14B 0.462 → 0.455 (61); Qwen3.6-27B 0.771 → 0.775 (52). Pooled paired Δ +0.0015 [−0.0030, +0.0059] p-val=0.53 (sign-flip permutation, 491 items; task bootstrap 10,000 draws, seed 20261007); mean |Δ| 0.020; ordering unchanged; Qwen3-14B's proving cell FSC 0.8 → 0.7, SCSC 0.928 → 0.888 (mean over 896: 0.00104 → 0.00099). **No conclusion changes.** Items on < 3 repeats for one member: 4 (listed in results.md).
  - **Spend:** final total **$289.78 of $400**.
  - **Published:** results.md (TLDR, G = 1 table, footnotes, spend table, new "FSC repeat correction (10-07-2026)" section), REPORT.md deviation 17, README.md status, experiments/README.md row 01; `expt_v1/results/fsc_median3_<label>.json` × 9 and `fsc_median3_summary.json`; repeat-1 files untouched. `make test`: 116 passed, 1 skipped.
  - **Teardown:** all 9 r23 service+tunnel pairs stopped (`--stop`, PIDs in the § 3 entry), ports 9710–9718 confirmed free with `ss -tlnp`, no `cloudflared` for those ports, port-claim file removed; other sessions' claims (9720–9739, 9740–9759) untouched. Watcher windows closed; tmux session `rl4cv-e01-fsc-median3-worker` left for the master.
  - **Still open (out of scope, recorded in REPORT.md 17):** audit drew only from clean-finish cells; 11 proving G = 8 probe cells never judged; some results.md summary sources uncommitted; checkpoint vs results.md seed-split count (6 vs 8). Also: Valkyrie `run results` tracker regression affects every run on this host (harvest fallback in place).
