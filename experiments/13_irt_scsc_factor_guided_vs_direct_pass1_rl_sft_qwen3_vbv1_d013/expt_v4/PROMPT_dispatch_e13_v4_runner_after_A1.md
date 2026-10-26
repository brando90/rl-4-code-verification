# Dispatch 2: experiment 13 v4, Amendment V4-A1 and the end-to-end runner (CPU only, no launch)

**TLDR:** Implement [Amendment V4-A1](AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md) and the concrete v4 runner, which turns the tested components into generation, scoring, update and recovery commands. Write the launch and watchdog plans and a new admission, then verify everything with CPU tests and a GPU-free dry run. Stop with a launch-ready admission, or a precise blocker, recorded in `expt_v4/CKPT_v4_implementation.md`.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, high effort, on skampere1. The dispatcher is the experiment 13 master, on 10-20-2026. This continues the first dispatch ([prompt](PROMPT_dispatch_e13_v4_implementation.md)), whose binding limits still apply.

## Read first

- `expt_v4/PROTOCOL.md` (frozen, `d4778e25`), `AMENDMENT_V4-A1_…md` (`7877faac`), `CKPT_v4_implementation.md`, `README.md`, and your own `phase2/` and `tests/`.
- From `expt_v3/phase2/`: `pilot_run.py`, `resume_pilot_after_foreign_gpu.py`, `autoresume_watchdog.py` and the generation, score and update stage scripts it calls. Reuse their structure, but none of their retired settings: the 8,192-token cap, temperature 1, or the unfiltered objective.

## What to build

1. **Amendment V4-A1.**
   - The generator runs with `max_logprobs = 64` and records top-64 raw log-probabilities.
   - Implement the top-k and top-p certificates, including the 1e-5 boundary margin, and the trainer's tie-inclusive support.
   - Change the V4-T1 support criterion to count uncertified positions as disagreements.
   - Store full receipts for the T1 probe, G0 and the T2 refit, and reduced records during updates.
   - Test with synthetic logits: ties at the 20th place, ties at the top-p boundary, near-margin cumulative mass, the case v_64 = v_20, and a 1-token support.
   - Show on the installed source that `max_logprobs` does not change sampling. Use a CPU or synthetic check now; the real comparison happens at V4-T1.
   - If anything in V4-A1 cannot be implemented as written, record why and the smallest fix. Do not edit the amendment or the protocol.
2. **The runner.**
   - One entry point per stage: T1 probe, G0 generate and score, G0 select, T2, T3, T4 (including the maximum-length probe), B audits, the pilot update loop and the T5/extension decision.
   - Each stage is single-attempt with durable receipts, as in v3, and binds every completed stage to the admission digest.
   - Stages run strictly in protocol order. A stage refuses to start without its predecessor's PASS receipt.
   - Placebo draws are frozen before P's first response.
   - Recovery follows the v3 owner's steps, adapted, and A4's infrastructure-only cap of 3 applies.
3. **Plans.**
   - Write `/lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json` and a `launch_plan` with concrete argument vectors, device leasing through your device guard, and the tmux prefix `rl4cv-e13v4-`.
   - Do not install the cron line and do not start any session.
4. **Admission.** Write a new admission binding the protocol, V4-A1, the runner, the plans and the tests. `launch-check` should pass with the CPU-only blocker removed. The only remaining condition is a device lease and the master's go.
5. **GPU-free dry run.** Run the full stage sequence end to end with stub engines on tiny synthetic data, with `CUDA_VISIBLE_DEVICES=''`. Show the receipts, the order enforcement, a simulated crash with its recovery, and the stop-without-resampling path.
6. **Launch commands.** Record the exact master launch commands in the checkpoint: the install-watchdog command, the first stage's command, and how to check progress.

## Binding limits

All limits from dispatch 1 still apply. In particular:

- no GPU allocation, model generation or optimizer step;
- no edits to v2 or v3 paths, sessions, hooks or cron;
- the shared venv is read-only;
- $0;
- kill only processes you started;
- the frozen protocol and V4-A1 are not edited;
- commits use explicit pathspecs; rebase, then push to `main`.

## Deliverables

- Code and tests, with passed, skipped and failed counts for the v4 suite and the root suite.
- An updated `README.md`, which lists the amendments.
- An updated `CKPT_v4_implementation.md`: status (launch-ready or blocked), the dry-run evidence, the admission SHA-256, launch commands, a fresh GPU census and remaining risks.
- One copy-ready sentence for the master.
