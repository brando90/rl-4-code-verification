# Dispatch: experiment 13 v4 implementation and tests (CPU only, no launch)

**TLDR:** Implement and test the code that the frozen [v4 protocol](PROTOCOL.md) (`d4778e25`) needs, in `expt_v4/phase2/` and `expt_v4/tests/`. Use no GPU, generation or optimizer step. Stop when the admission is ready, and report what remains for launch in `expt_v4/CKPT_v4_implementation.md`.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, high effort, on skampere1. The dispatcher is the experiment 13 master session (Claude, Mac), on 10-20-2026.

## Read first

- `~/agents-config/INDEX_RULES.md`, and this repository's `CLAUDE.md` / `AGENTS.md`.
- `expt_v4/PROTOCOL.md` (frozen) and `expt_v4/LIGHT_QA_10-20-2026.md`.
- The parent `PROTOCOL.md`, especially §§ 3, 5, 6 and 7.
- From `expt_v3/`: `phase2/` (in particular `pilot_run.py`, `device_guard.py`, `autoresume_watchdog.py` and `resume_pilot_after_foreign_gpu.py`), `tests/`, `PILOT_EXECUTION.md` and `CKPT_master_resume_10-20-2026.md`.
- From `expt_v2/`: `phase2/evaluation_contract.py`, `phase2/pilot_configuration.py`, `phase2/a6_gradient_reporting.py` and `RESULTS_A6_DIAGNOSTIC_S2.md`.

## Paths

- Fresh clone for v4: `/lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification`. Work directory: `/lfs/skampere1/0/brando9/rl4cv_e13v4`.
- Runtime: the existing NeMo RL venv at `/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv`. Use it **read-only**, as v3 does. Never install into it or modify it.

## What to build

Each item gets unit tests in `expt_v4/tests/`, written the way `expt_v3/tests/` is.

1. **Filtered-policy objective (protocol § 2.2).**
   - Compute the support exactly as the installed vLLM 0.10.0 sampler does. Read its source in the venv (`vllm/v1/sample/ops/topk_topp_sampler.py` and the order in `vllm/v1/sample/sampler.py`), including tie handling at the k-th logit and the top-p boundary token.
   - Compute log π̃ in the trainer with the support fixed at the old weights.
   - Reconstruct the generator's support and π̃ from the top-20 raw log-probabilities.
   - Wire the filtered log-probabilities into the NeMo RL 0.4.0 loss path through v4-owned code (a wrapper or hook loaded at runtime), never by editing the venv.
   - Test with synthetic logits, including ties, a boundary token and a 1-token support.
   - If the pinned engine cannot return the needed log-probabilities, or NeMo cannot take the filtered objective, record that as a blocker in the checkpoint. Do not substitute another objective.
2. **Length and context contracts (§ 2.3).**
   - The response cap is 12,288. Compute the context per engine from every prompt v4 uses (train, validation and test).
   - Check it against the model's maximum position embeddings.
   - Tests must reject 8,192 and 15,945.
3. **V4-G0 (§ 3).**
   - Task selection: `default_rng(1304001)` over the sorted train IDs.
   - The estimator q̂_G, with known-value tests: s ∈ {0, 32} gives 0; s = 1 gives G/32.
   - N_G and M_G; the paired whole-task bootstrap with seed 1304002 and 10,000 draws.
   - The rule evaluated under both missing-slot completions.
   - The deterministic V4-T2 subset.
4. **Gate statistics.**
   - V4-T1: support checks, error quantiles, truncation and discarded mass.
   - V4-T2: reward selection, the stop-without-resampling path, and the five pass criteria, including the pre-clipping gradient norm.
   - V4-T3: replay binding.
   - V4-T4: the measurement record, including a synthetic maximum-length forward/backward probe. Write the probe now and run it only at launch.
5. **Placebo (§ 2.4).**
   - The reference distribution from the G0 batch, with the ≥ 90% admission rule.
   - The SHA-256 over the sorted 17-significant-digit decimals.
   - Counter-based draws keyed by SHA-256 of `e13v4-placebo`, seed, update and slot, precomputed and bound before P's first response.
   - The per-update density and variance report.
6. **V4-T5 and T (§§ 3–4).** Conservative completion; the 30→60 extension of all six trajectories; and T from A/1301 plus A/1302, updates 1–30.
7. **A6 count reducer (§ 1).**
   - Reads the private v2 A6 scoring receipts under `/lfs/skampere1/0/brando9/rl4cv_e13v2/`, read-only.
   - Commits only aggregate counts (the per-task strict-success histogram and complete groups with mixed strict outcomes or varying B reward), with input SHA-256s and no task identities.
   - If the reducer disagrees with the protocol's unbound counts, report the difference in the checkpoint and leave the protocol unchanged.
8. **Device guard.** Generalize the v3 guard to idle GPUs on skampere1 devices 0, 5 and 7, and on skampere2 and skampere3. A GPU is idle when it has no compute process. Fail closed on probe errors, and never use a GPU another user or experiment holds.
9. **v4 auto-resume watchdog.**
   - Follow the pattern of `expt_v3/phase2/autoresume_watchdog.py`, with tmux session prefix `rl4cv-e13v4-`.
   - Write a cron installer, but **do not install it** until launch.
10. **Admission.** Write a `check_admission` like v3's. It binds the protocol hash, the implementation and test files, the A6 reducer output and the context values, and every completed update records the admission digest.
11. **Experiment 120.** Report its current GPU use (devices, owner and processes) in the checkpoint.

## Binding limits

- **No v4 GPU use:** no GPU allocation, model generation or optimizer step. Launch happens later, by the master, after v3-A7's six `result_30.json` or B_1301's `T5_30.json` FAIL.
- **Do not touch v3 or v2:**
  - v3's work directory `/lfs/skampere1/0/brando9/rl4cv_e13v3` and its checkout;
  - the `rl4cv-e13v3-*` tmux sessions and the hook `session-created[13]`;
  - the cron line tagged `# e13v3-autoresume`;
  - any `expt_v2` or `expt_v3` file, or `/lfs/skampere1/0/brando9/rl4cv_e13v2`, except for reading.
- **$0:** no Valkyrie, provider or judge calls.
- **Processes:** kill only processes you started.
- **Protocol:** `PROTOCOL.md` is frozen. If the code cannot meet it, record the problem and the smallest amendment that would fix it in the checkpoint, and leave the protocol unchanged.
- **Git:** commit with explicit pathspecs and never `git add -A`. Inspect the staged diff for secrets, then rebase on `origin/main` and push to `main`.

## Deliverables

- Code under `expt_v4/phase2/`, and tests under `expt_v4/tests/` that pass with the venv's Python. Report passed, skipped and failed counts.
- `expt_v4/README.md`: design summary and directory structure.
- `expt_v4/CKPT_v4_implementation.md`, updated as you go. When finished, it lists what is done, the test counts, blockers, the experiment 120 GPU report, and the exact launch commands for the master.
- Every file starts with a one-sentence TLDR comment or line.
