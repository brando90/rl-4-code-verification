# Run experiment 08 on SNAP: Valkyrie teacher data → matched Lean SFT of Qwen3 Base 1.7B–14B → validation ladder → one test evaluation

**TLDR:** You execute experiment 08 end to end on `skampere1`:
1. Build a 539-task train pack from VeriBench experiment 103's VBV1 pack.
2. Get 4 single-call Lean files per task from Claude Opus 5.5 and GPT-6 Astra through Vals Valkyrie (4,312 cells), keep only kernel-verified, screen-clean files, and assemble the SFT set.
3. Fine-tune Qwen3 1.7B / 4B / 8B / 14B Base with Varun's NeMo RL 0.4.0 recipe, identically at every size, with checkpoints at 12.5 / 25 / 50 / 75 / 100% of assistant tokens.
4. Run the 135-task validation ladder at G = 8, select the earliest common passing fraction, then evaluate the selected checkpoints once on the 222 test tasks with SCSC.

`PROTOCOL.md` is the contract and this runbook is how to execute it. Push every landed step to `main`, keep `results.md` and `CKPT_e08.md` live, and tear down what you start.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Context and rules (read before acting)

- **Read first:** the repository `CLAUDE.md` (D-013 split rule; full declared sets; no direct provider API calls; D-108 Valkyrie rules; D-012 push small and often), then `EXP/README.md` and `EXP/PROTOCOL.md`, where `EXP=experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`. Also read `docs/DECISIONS.md` D-013 (split) and D-015 (this experiment's single-call teacher route; D-014 is the same exception for 02A v3).
- **Owner:** Rakshit Kaushik (@rakshit-kaushik). **Master:** a Claude Code session on Brando's laptop, which reads your checkpoint and `results.md`. **Related:** experiment 02A v3 (owner Ethan Li) uses the same teacher route on MBPP. Reuse its committed scripts where they fit (`git log origin/main -- experiments/02_*/phase_a_*/expt_v3`), but never touch its work root, service, ports or tmux sessions.
- **Work root:** `WORK=/lfs/skampere1/0/brando9/rl4cv_e08`. Use your own clone `$WORK/rl-4-code-verification` on `main`. Commit with explicit pathspecs, `git pull --ff-only` (or merge) before every push, and push each landed step. Never commit raw teacher outputs, Lean files, the SFT set, checkpoints, keys, `.env` files or the Valkyrie configuration. DFS (`/dfs`) is full: write nothing there.
- **Model calls:** only through Valkyrie, with the gateway key mapped by Valkyrie (`fellows/brandoModelGatewayApiKey`). Never fetch, print or use any provider or gateway key on the host, and never write code that calls a provider API. Scrub `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` and `MODEL_GATEWAY_API_KEY` from the environment of every `valk` command, as experiment 103's controller does. Vals funds the calls and they are recorded, not capped (D-108). HTTP 429 is infrastructure.
- **Reuse, read-only:**
  - Experiment 01's work root `/lfs/skampere1/0/brando9/rl4cv_e01`, which holds the venv with vLLM 0.30.0, the frozen scorer checkout `external/veribench_scorer` at `59059a20` and the Lean v4.22.0 + Mathlib grading project.
  - Experiment 05's `env_e05.sh`, `launch_e05.sh` and `run_model_e05.sh`, which are the exact generation and scoring commands.
  - VeriBench experiment 103's private directory: pack, service code, `materialize.py` and registry dumps.
  - Experiment 01's `deploy_rl4cv_e01_judge_service.py` and `judge_rl4cv_e01.py`, for deploying a benchmark service and driving `valk` on this host.

  Never modify, restart or kill another experiment's files, services, ports, tunnels, tmux sessions or GPU processes. Kill only PIDs you started and recorded.
- **GPU discipline:** `export CUDA_VISIBLE_DEVICES=<ids>` before every GPU process. Never use a GPU with another user's process or more than 10% utilization. Check `nvidia-smi` within minutes of each launch and free GPUs as soon as a job ends. Record the per-size GPU plan (memory, expected utilization, duration) in the checkpoint before launching; the pre-approval above covers the ask.
- **Checkpoint:** `$EXP/expt_v1/CKPT_e08.md`. It holds Created / Last updated from `date "+%m-%d-%Y %H:%M %Z"`, the current step, landed commits, tmux sessions, ports, PIDs, run ids, GPU assignments, the exact next command and blockers. Update it at every step.
- **Live results (obligation):** `$EXP/results.md` is the live record and must be committed and pushed as the run proceeds, not only at the end. Every revision sets `**Status:**` (RUNNING / BLOCKED: <reason> / DONE) and `**Last updated:** <MM-DD-YYYY HH:MM TZ>`. Keep the phase table (DONE / IN PROGRESS / PENDING) current and add numbers as each phase lands, with denominators. Keep the closing `**TLDR-end:** [rl4cv: expt 08 matched Lean SFT warm start] …` line current. A progress file that lives only on the cluster does not count.
- **Status file:** `$WORK/STATUS_e08` holds `RUNNING`, `BLOCKED: <reason>` or `DONE`.
- **Persistence:** work inside tmux; long jobs run in their own named tmux sessions (`rl4cv-e08-<job>`) that you record. Do not end your turn while work remains. Wait on long jobs with a background poll, every 20–30 minutes, re-reading the checkpoint, until every phase is terminal.

## 1. Setup (zero model calls)

```bash
export WORK=/lfs/skampere1/0/brando9/rl4cv_e08 && mkdir -p $WORK && cd $WORK
git clone https://github.com/brando90/rl-4-code-verification.git && cd rl-4-code-verification
make external                       # pinned veribench + frozen scorer + rl-env-scaling under external/
python3 -m venv .venv && . .venv/bin/activate && make install
VERIBENCH_ROOT=$PWD/external/veribench make test     # must include tests/test_splits.py passing, not skipped
```

Write `RUNNING` to `$WORK/STATUS_e08` and create the checkpoint.

## 2. Served pack and prompt checks (PROTOCOL § 2)

1. Write `$EXP/expt_v1/scripts/build_train_pack.py` (one-sentence TLDR docstring). It copies `instruction.md` for each id in `$EXP/expt_v1/results/split/vbv1_train_task_ids.txt` from experiment 103's `private/packs/vbv1_896`, adds the `tests/test.sh` placeholder the service needs, and never copies `solution/` or any gold file. Output goes to `$WORK/pack_train539/`.
2. Check that each instruction's SHA-256 matches experiment 05's `instruction_sha256` for the task (`/lfs/skampere1/0/brando9/rl4cv_e05/out/raw/gen_qwen3-8b-base_g8.jsonl`). Grep the pack for any `.lean` file or `theorem` text outside `instruction.md`; there must be none.
3. Held-out check of the system prompt and addendum (PROTOCOL § 2) with `rl4cv.screens`.
4. Write `$EXP/expt_v1/results/pack_check.json` and commit.

## 3. Scorer adapter (PROTOCOL § 4)

Write `$EXP/expt_v1/scripts/score_teacher_files.py` around the frozen scorer:
- Materialize job directories as `rl4cv.veribench.jobs` does.
- Run `score_scsc.py --skip-tc` in the grading project with experiment 05's environment (`source /lfs/skampere1/0/brando9/rl4cv_e05/env_e05.sh`).
- Read back IC_tests, IC_proofs and per-theorem axioms, and compute `kernel_binary` with `rl4cv.rewards`.

Run the adapter check (3 gold, 3 broken, 5 experiment-103 Astra train files) into `$EXP/expt_v1/results/scorer_adapter_check.json`. Commit and push.

## 4. Service, registry, identity, preflight, lock 1 (PROTOCOL §§ 3, 12)

1. **Service.** Claim a free port block: check `ss -tlnp` and write a claim file under `/lfs/skampere1/0/brando9/valkyrie_port_claims/`. Deploy experiment 103's single-call benchmark service in collect-only mode (`VB_NO_COMPILER=1`, `VB_COLLECT_ONLY=1`) serving `$WORK/pack_train539/`, behind a bearer-protected cloudflared tunnel, following `deploy_rl4cv_e01_judge_service.py`. Register it as benchmark `rl4cv-e08-vbv1-train` in a private copy of the host Valkyrie configuration under `$WORK/private/` (mode 0600, never committed). Check health: 200 with the bearer and 401 without, locally and through the tunnel. Read back the per-task limit.
2. **Registry and agent bytes (zero calls).** Take a registry dump; experiment 107's `vb107_registry_probe` pattern on skampere2 is the reference, and the newest dump is from 10-07. Confirm `anthropic/claude-opus-5-5-no-fallback` (no fallbacks, `compute_effort max`) and the highest-effort GPT-6 Astra selector (expected `openai/gpt-6-astra-max`) with the exact `-k` effort values. Download the bucket's `vb103_single_call` bundle and record its file hashes; check its VBV1 prompt and extraction against PROTOCOL § 2.
3. **Identity and payer:** host, `VALKYRIE_ENV`, organization `BrandoMiranda-fellow`, bucket `fellow-brando-miranda`, the secret mapping by name, and the payer, recorded in the checkpoint and `results.md`.
4. **Live preflight (PROTOCOL § 12 item 7):** 8 calls, scored end to end, plus the independence check. Fix infrastructure only, never scientific settings.
5. **Lock 1:** write the confirmed selectors and settings into PROTOCOL § 3. Set the lock-1 line to `LOCKED <UTC> at commit <hash>`, commit and push **before** section 5.

## 5. Teacher runs (only after lock 1)

- Admit the 8 runs (2 teachers × r = 1…4). Each is `valk run start --agent vb103_single_call --benchmark rl4cv-e08-vbv1-train --dataset default --model <selector> --task-ids-file <539 ids> --concurrency <as high as the service and provider allow> --label rl4cv-e08-v1-<short>-s<r> -k addendum vbv1 -k max_tokens 128000 -k benchmark rl4cv-e08-<short>-s<r> -k <effort>`. Runs may overlap. Record each run id in the checkpoint immediately.
- Supervise until every cell is terminal. Re-send only under PROTOCOL § 3. Harvest each run with `valk run results <id> --path …` and `valk run output <id> -o …` into `$WORK/raw/<short>/s<r>/`, as experiment 103's `materialize.py` does. Write per-cell receipts without content (status, finish reason, usage, charge, hashes) to `$EXP/expt_v1/results/receipts/`. Commit and push as runs finish, and update `results.md` with cells measured / unmeasured and charges per run.

## 6. Score, keep, screen, assemble S (PROTOCOL §§ 4–7)

1. Score every harvested file into `$EXP/expt_v1/results/scored_cells.jsonl`: task, teacher, r, status, IC_tests, IC_proofs, theorem counts, axioms, `kernel_binary`, failure class, file SHA-256 and token length; no file contents.
2. Run the consistency check (PROTOCOL § 5) and the generated-Lean screen (§ 6). Write `$EXP/expt_v1/results/generated_lean_screen.json`.
3. Analysis, as `$EXP/expt_v1/scripts/analyze_teachers.py`:
   - per teacher and sample: declared, measured, unmeasured and kept counts, kept / measured with a 95% Wilson interval (unit = task);
   - union coverage over tasks and per family;
   - failure taxonomy;
   - kept-file token lengths;
   - overlap between teachers;
   - total reported charge.
4. Assemble S on the host (`$WORK/sft/s_v1.jsonl`, messages format) by the § 7 rule. Commit the manifest `$EXP/expt_v1/results/sft_set_manifest.csv` (ids, teacher, r, file and response hashes, prompt and assistant token counts) and `sft_set_stats.json`. Update `results.md` with the realized token budget against the README estimate.

## 7. NeMo RL environment, config, dry run, lock 2 (PROTOCOL §§ 8, 12)

1. Build NeMo RL 0.4.0 in `$WORK/nemo_rl` (`git clone https://github.com/NVIDIA-NeMo/RL.git`, check out the 0.4.0 release, confirm the commit matches `c751f811` or record what it is). Use `uv` per its docs, with a CUDA build that matches the driver. Varun's working build is `/lfs/skampere3/0/vmadan/vendor/nemo_rl_v040_cuda128`; read it for reference, but never write there.
2. Copy Varun's `/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1/phase1c_production_sft.yaml` (and its launcher) to `$EXP/expt_v1/configs/varun_phase1c_production_sft.yaml`, with a provenance header (path, mtime, SHA-256). Write `$EXP/expt_v1/configs/e08_sft_<size>.yaml` that differs only as PROTOCOL § 8 allows, and commit a diff report. Convert S into the dataset format the config expects with the § 7 rendering. Verify the prefix property, per-example mask counts and tokenizer identity across the four sizes. Compute the checkpoint steps for 12.5 / 25 / 50 / 75 / 100% of assistant tokens.
3. Run the dry run (PROTOCOL § 12) on one free GPU. If NeMo RL cannot pass it within 6 working hours, switch every size to the TRL fallback in a separate venv with identical settings, and record the deviation.
4. Download Qwen3-14B-Base at `0b0bd3732e2c374d483664439ea334928b65f304` to `/lfs/skampere1/0/brando9/.cache/huggingface/hub` and verify its hashes. 1.7B, 4B and 8B are already cached at experiment 05's revisions.
5. **Lock 2:** set the lock-2 line, commit and push before any SFT step.

## 8. Matched SFT (4 sizes)

- Plan GPUs from live `nvidia-smi`. Starting suggestion on 8× A100-80GB: 1.7B on 1 GPU, 4B on 2, 8B on 4, 14B on 4–8 (run 14B after the others or on free skampere3 B200s). Global batch, order, steps and schedule are identical everywhere.
- Each size runs in its own tmux session `rl4cv-e08-sft-<size>`, writing to `$WORK/ckpt/<size>/`. Export each token-fraction checkpoint to Hugging Face format and record its SHA-256 manifest. Commit the training-loss CSVs and step / token logs.
- Verify that each export loads in vLLM before deleting any intermediate distributed checkpoint.

## 9. Validation ladder and selection (PROTOCOL § 9)

- For each of the 20 checkpoints and Base 14B: generate with experiment 05's exact command (`python -m rl4cv.veribench.generate --pack <103 vbv1_896 pack> --model <local checkpoint path> --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --batch 1024 --samples 8 --task-ids $EXP/expt_v1/results/split/vbv1_validation_task_ids.txt --label <l> --out <f>`). Then run `python -m rl4cv.veribench.jobs`, score with `score_scsc.py --skip-tc`, and run `collect` and `summarize`. Use one vLLM process per GPU; free GPUs between jobs.
- Base 1.7B, 4B and 8B: restrict experiment 05's scored files to the validation ids; do not regenerate them.
- Compute gates and diagnostics with `$EXP/expt_v1/scripts/analyze_ladder.py`. Commit `$EXP/expt_v1/results/validation_ladder.json` and per-task CSVs, then commit `selection.json` (f*, checkpoint paths and hashes, gate table). **No test-split generation before the selection commit is pushed.**

## 10. Test evaluation (PROTOCOL § 10)

- Generate and kernel-score the selected checkpoints and Base 14B on the 222 test ids with the same command. Base 1.7B, 4B and 8B come from experiment 05's scored files.
- Run FSC with `vb103_judge` through Valkyrie (D-102) as a new suite `rl4cv-e08:<system>`, for every cell with IC_tests · IC_proofs > 0, following `judge_rl4cv_e01.py`. Experiment 103's existing judge runs are never modified.
- Compute `$EXP/expt_v1/scripts/analyze_test.py`: factor means, SCSC with n, all / core / IndustrySet, task-bootstrap 95% intervals with 10,000 resamples, and paired π₀(N) − Base differences. Write `$EXP/expt_v1/results/test_eval.json` and fill `results.md`:
  - setup sentence first;
  - headline table with every denominator;
  - validation ladder table;
  - tokens needed;
  - test table;
  - deviations;
  - total reported charges.

## 11. Finish

- Stop the service and tunnel you started, remove your port claim (confirm with `ss -tlnp`), stop your vLLM and training processes, and kill only tmux sessions you created. Keep checkpoints and raw data on `/lfs`.
- Update `experiments/README.md` (row 08) and the README status table. Write `DONE` to the status file, give the checkpoint its final state, push, and send one short notification to `brando.science@gmail.com` with the host's `mail` command: subject `rl4cv expt 08: <verdict>`, body with the verdict, tokens needed, the test table's SCSC per size and the `results.md` link. Send the same notification once if you end `BLOCKED` on a real blocker.
- On RL-READY, draft `$EXP/expt_v2/README.md` for the RL phase (GRPO from π₀(N) on train prompts, `kernel_binary` reward, validation monitoring, one test evaluation; trainer choice between NeMo RL and verl as in `rl-env-scaling`). Do not start RL without that version's locked protocol.

**TL;DR:** 539 train prompts × 2 Valkyrie teachers × 4 samples → kernel-verified, screened Lean SFT set → identical NeMo RL SFT at 1.7B / 4B / 8B / 14B with a 5-rung token ladder → validation gates pick the earliest common rung → one test evaluation with SCSC; push every step and keep `results.md` live.
