# Build, run and land experiment 02A v3 (Lean warm-start data from Valkyrie teachers) on skampere1

**TLDR:** You build kernel-verified Lean 4 warm-start data for experiment 02: rewrite MBPP's 974 Python tasks into VeriBench's task layout, screen them against VeriBench, send each one once to three frontier teachers (Claude Fable 5.1, GPT-6 Astra, Gemini 4 Argon) through Vals Valkyrie single-call runs, score every returned Lean file with VeriBench's frozen scorer, and keep only fully verified files. No model call happens until Brando's exception to D-108's vendor-agent rule is recorded (PROTOCOL § 4); lock `PROTOCOL.md` after the preflight and before the first manifest call. Publish `results.md` with the verdict (SUFFICIENT / PARTIAL / INSUFFICIENT) and every denominator, push to `main` as each step lands, and tear down what you started.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Context and rules

- **Read first:** the repository `CLAUDE.md` (VeriBench held out; full declared sets; no direct provider API calls; D-108 Valkyrie rules; D-012 push small and often), then `EXP/README.md` and `EXP/PROTOCOL.md`, where `EXP=experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3`. The protocol is the contract; this runbook is how to execute it.
- **Owner:** Ethan Li (@lethan3) owns experiment 02; the master is a Claude Code session on Brando's laptop.
- **Work root:** `WORK=/lfs/skampere1/0/brando9/rl4cv_e02a_v3` (create it). Your own clone `$WORK/rl-4-code-verification` on `main`; commit with explicit pathspecs, `git pull --ff-only` (or merge) before every push, push each landed step. Never commit raw teacher outputs, Lean files, the SFT set, keys or the Valkyrie configuration.
- **Reuse, read-only:** experiment 01's work root `/lfs/skampere1/0/brando9/rl4cv_e01` and experiment 05's `/lfs/skampere1/0/brando9/rl4cv_e05` (Lean v4.22.0 grading project, scorer checkout, environments), and VeriBench's experiment 103 service and agent code. Read `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/deploy_rl4cv_e01_judge_service.py` and `judge_rl4cv_e01.py` for how experiment 01 deployed a benchmark service and drove `valk` on this host (venv, cloudflared, port claims, private config, environment scrubbing). Never modify another experiment's files, services, tmux sessions or ports.
- **Checkpoint:** `$EXP/CKPT_e02a_v3.md` (Created / Last updated from `date "+%m-%d-%Y %H:%M %Z"`; step, landed commits, sessions, ports, run ids, exact next command, blockers). Update it at every step. `$EXP/results.md` is the live result record; update it at every milestone.
- **Status file:** `$WORK/STATUS_e02a_v3` holds `RUNNING`, `BLOCKED: <reason>` or `DONE`.

## 1. Source, rewrite, screens (zero model calls)

1. Download MBPP `full` at the pinned revision (Hugging Face), record file hashes.
2. Write `$EXP/scripts/build_mbpp_tasks.py` (one-sentence TLDR docstring): the deterministic rewrite and Python gate of PROTOCOL § 1. Output the rewritten files under `$WORK/tasks/py/` and `$EXP/results/mbpp_rewrite_manifest.json` (kept and dropped, with reasons and hashes).
3. Write `$EXP/scripts/screen_mbpp_tasks.py`: PROTOCOL § 2 with `rl4cv.screens` against the pinned VeriBench checkout (`scripts/setup_external.sh` fetches it into `external/veribench`). Output `$EXP/results/screen_report.json` and the declared manifest `$EXP/results/declared_manifest.json` with its SHA-256.
4. Add tests for the rewrite (a known MBPP task round-trips; a task with no callable function is dropped) under `tests/`, and run `make test`. Commit and push.

## 2. Prompt bytes and pack (zero model calls)

1. Recover the agent-spec v6 adapter bytes experiment 103's gated pack used (find the commit from VeriBench experiment 103's `freeze_protocol.py` and the pack's `instruction.md` stamps), write `$EXP/scripts/build_pack.py`, and build `$WORK/pack/` (one task dir per manifest task: `instruction.md`, `tests/test.sh`). Record the adapter commit and file hashes.
2. Do the held-out check of PROTOCOL § 3 on the system prompt, the instruction template and `addendum_vbv1.md`. If VeriBench task text is embedded, write `BLOCKED` with the evidence and stop.
3. Round-trip every task file through the pack loader the service uses (`load_task_pack`), with zero model calls.

## 3. Scorer adapter (zero model calls)

Write `$EXP/scripts/score_teacher_files.py` around the frozen scorer bytes (PROTOCOL § 5): materialize job directories as `rl4cv.veribench.jobs` does, a placeholder `--gold-dir` of empty `mbpp/task_<id>.lean` files (PROTOCOL § 1 identity), the mapping gate passing for every declared task, run `score_scsc.py --skip-tc` in the validated grading project, and read back IC_tests, IC_proofs, theorem counts and axioms per file; then compute `kernel_binary` with `rl4cv.rewards`. Run the adapter check (3 VeriBench gold files, 3 broken files) and record it in `$EXP/results/scorer_adapter_check.json`. Commit and push.

## 4. Service, payer, exception gate, preflight, lock

1. Claim a free port block (check `ss -tlnp`; write a claim file under `/lfs/skampere1/0/brando9/valkyrie_port_claims/`), deploy experiment 103's collect-only single-call service serving `$WORK/pack/` behind a bearer-protected cloudflared tunnel, and register it in a private copy of the host Valkyrie configuration (mode 0600, under `$WORK/private/`, never committed). Health 200 with the bearer, 401 without, locally and through the tunnel; read back the per-task limit.
2. D-108 identity: record the host, Valkyrie environment and organization, the agent's gateway-key secret mapping by name, the payer, and a registry dump (zero model calls) confirming each teacher's selector and allowed settings, in the checkpoint and `results.md`.
3. **D-108 exception gate (before any model call):** `git pull` and check `docs/DECISIONS.md` for Brando's decision on the single-call teacher exception for 02A v3 (PROTOCOL § 4). If it is absent, finish every zero-call step, write `BLOCKED: awaiting D-108 exception` to the status file and the checkpoint, push, and re-check every 30 minutes for up to 24 hours; do not call any model meanwhile. If he refuses it, stop and report.
4. Preflight (PROTOCOL § 7), only after the gate passes: one live `mbpp__preflight_*` call per teacher, scored end to end. Fix infrastructure problems, never the protocol's scientific settings.
5. Lock: fill PROTOCOL's lock line (`LOCKED <UTC> at commit <hash>`), commit and push before section 5.

## 5. Run every declared cell (only after the lock)

- Admit one Valkyrie run per teacher over the whole declared manifest (`valk run start --agent vb103_single_call --benchmark <your service> --model <selector> -k …`, settings exactly as locked; concurrency as high as the service and provider limits allow; HTTP 429 is infrastructure). Record each run id.
- Supervise until every cell is terminal (check every 20–30 minutes with a background wait loop; do not end the task while work remains). Re-send a cell only when its receipts show no model request was served, within the shared two-request allowance (PROTOCOL § 4); recover artifacts of served calls from the run output; everything else stays `unmeasured` in the denominator.
- Harvest each run (`valk run results` and `valk run output`) into `$WORK/raw/<teacher>/`; write per-cell receipts without secrets to `$EXP/results/receipts/`.

## 6. Score, screen, analyze, publish

1. Score every harvested file with the adapter; write `$EXP/results/scored_cells.jsonl` (task, teacher, status, IC_tests, IC_proofs, theorem counts, axioms, `kernel_binary`, failure class, file SHA-256 and token length; no file contents).
2. Screen every kept Lean file (PROTOCOL § 2, generated-Lean screen) and record exclusions in `$EXP/results/generated_lean_screen.json`.
3. `$EXP/scripts/analyze_v3.py`: PROTOCOL § 6 tables, Wilson intervals, the verdict on post-screen counts, with missing-outcome bounds. Write `$EXP/results/analysis_v3.json` and fill `results.md` (setup sentence first, headline table with denominators, per-teacher tables, failure taxonomy, overlap, lengths, verdict, deviations, total reported charge).
4. Assemble the SFT set on the host only from kept, screen-clean pairs: `$WORK/sft/lean_warmstart_v3.jsonl` with one (prompt, kept file) pair per kept cell, plus a committed manifest of task ids, teachers and SHA-256s.
5. Update `experiments/README.md` (02A row) and the 02A README status row. Commit and push.

## 7. Tear down and finish

Stop the service and tunnel you started, remove your port claim, confirm with `ss -tlnp`, and kill only tmux sessions you created. Write `DONE` to the status file, give the checkpoint its final state, and push. Report to the master in the checkpoint: verdict, counts with denominators, charges, run ids, anything left running.

**TL;DR:** Turn screened MBPP tasks into VeriBench-format prompts, get one single-call Lean file per task from each of three Valkyrie teachers, keep only kernel-verified files, and publish the counts and verdict without touching VeriBench tasks.
