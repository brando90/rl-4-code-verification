# Experiment 13 v2 dispatch & continuation prompt — Gates T2–T5 and Main Qwen3-4B GRPO Pilot on skampere1 (`[p 10/10]`)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/PROMPT_dispatch_e13_v2_main_pilot.md>

**TLDR:** Carry `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` (`expt_v2`) from Technical Gate T2 attempt 3 through T3, T4, the train mutation and independent coverage audits, the T5 learning pilot, and the main Group Relative Policy Optimization (GRPO) pilot comparing Arm A (binary `pass@1`), Arm B (the frozen guarded geometric mean of declaration, test and proof factors), and Arm P (independent placebo draws from the frozen train-only Arm B reward distribution) on the validated Qwen3-4B supervised fine-tuning (SFT) warm-start checkpoint (`step_658`) using self-hosted generation. Formal specification coverage uses only the validated hosted judge, with its separately verified funding, controls and frozen allocation.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Binding authority:** [PLAN.md](PLAN.md), [PROTOCOL.md](../PROTOCOL.md), adopted amendments A1–A6 and the published locks govern this continuation. This dispatch summary cannot change a scientific setting, resource cap, failed gate or notification rule. Corrections on 10-15-2026 restore the frozen 4B warm start, independent placebo, 16-sample test outcome and single B extension to 60. The task-ID and response manifests remain private.

## 0. Single-writer & live-session check (MANDATORY BEFORE ANY WRITE)

1. The canonical work root on `skampere1` is `/lfs/skampere1/0/brando9/rl4cv_e13v2` (`WR`), with repository checkout `WR/rl-4-code-verification`.
2. Before writing any file or claiming any GPU lease, check whether the active owner session `codex-rl4cv-e13v2-owner-g0` (PID `1243923`) is still alive and working:
   ```bash
   ps -p 1243923 -o pid,etime,stat,args
   tmux capture-pane -pt codex-rl4cv-e13v2-owner-g0 -S -30
   ```
3. **Preserve one writer (Trigger Rule 48 / 55):**
   - If `codex-rl4cv-e13v2-owner-g0` is actively running, do **not** launch a competing writer or touch its leases; let it run and use this prompt only when `codex-rl4cv-e13v2-owner-g0` exits or hits a context/turn limit.
   - If `codex-rl4cv-e13v2-owner-g0` has exited or stalled at a context limit, verify all child GPU processes are exited (`nvidia-smi`), re-arm `expt_v2/watchdog_e13v2.sh` for your own tmux session and PID additively in `crontab -l`, and resume from the latest committed state in `expt_v2/results.md` and `expt_v2/CKPT_e13_v2_owner.md`.

## 1. Execution sequence (from `expt_v2/results.md` state on 10-15-2026)

1. **Completed prerequisites (do not rerun):**
   - `R0` (30/30 fixtures), `R1` (400/400 train cells), `R2` (38,784/38,784 historical cells), `G0` under A3 (**PASS**).
   - Phase 1 anchor generation: 4,312/4,312 for each of `base`, `half` and `full1`. Official scoring measured 4,311/4,312, 4,303/4,312 and 4,302/4,312 respectively; all 20 missing outcomes remain in the declared denominators. Arm C calibration is not admitted (Arm C stays disabled; independent batch 2 skipped under A6).
   - `A6` 512-response pipeline diagnostic (**SOUND**, compile 48/512, strict 48/512).
   - Technical Gate `T1` in `float16` (**PASS**, 8/8 responses, 44,844 tokens, median abs log-prob diff `3.27e-5 <= 0.01`, p99 `0.0176 <= 0.10`, 0 unsupported/truncated tokens).
2. **Technical Gate `T2` (Single-update GRPO step gate, final allowed attempt 3):**
   - Verify the owned-worker shutdown synchronization (`expt_v2/phase2/worker_shutdown.py` and `checkpoint_state_preflight.py`) passes `E13_REQUIRE_LEAN_INTEGRATION=1 make test` with direct exit code 0.
   - Publish the successor admission lock before claiming an idle GPU through the experiment-13 lease registry (`export CUDA_VISIBLE_DEVICES=<chosen_id>`).
   - Execute `T2` attempt 3 end to end: 256 train rollouts (32 tasks × 8 samples), official Lean scoring, 1-step GRPO update, weight export, and post-update refit check. Publish `RESULTS_T2_S2.md` and update `expt_v2/results.md`.
3. **Technical Gates `T3` and `T4` + Mutation Audit:**
   - Run `T3` (checkpoint round-trip / resume fidelity) and `T4` (measured resource-cost projection against the 25% reserve bound) under their locked bindings.
   - Run the frozen reward-gaming mutation audit (`phase2/audit_report.py`) and independent coverage audit, then publish their reports before the learning pilot.
4. **Learning Gate `T5` (30-update pilot) and Main GRPO Comparison (Arms A, B, P):**
   - Run the two 30-update seeds of Arm A (`pass@1` binary reward) to establish the exact realized token budget, plus Arm B (the frozen guarded declaration/test/proof-factor reward) and Arm P (independent placebo draws from the frozen train-only Arm B distribution).
   - Apply the `T5` feasibility gate on Arm B's own reward (and the single pre-registered extension to 60 updates if triggered).
   - Evaluate selected checkpoints on the 135 validation tasks × 8 samples and the 222 held-out test tasks × 16 samples under the official Lean kernel scorer (and hidden gold reference tests via `phase2/selected_hidden.py`). Formal specification coverage (FSC) uses one preselected sample per task through the validated ensemble. The prior HTTP 403 was resolved and route controls passed; verify the current route and funding before paid calls and retain any newly unavailable measurement as pending.

## 2. Uninterrupted full-set evaluation & reporting contract

- **Solver completion reminder (Trigger Rule 61):** Every declared `model × task × seed/sample` cell must be executed and accounted for in the full denominator; never drop timeouts, parse failures, or capped responses from denominators.
- **Live ledger & checkpoint (Trigger Rules 37 & 44):** Update `expt_v2/results.md` and `expt_v2/CKPT_e13_v2_owner.md` at every gate transition, run `E13_REQUIRE_LEAN_INTEGRATION=1 make test` before every `git push origin main`, and stage explicit paths only.
- **Notifications:** Follow binding PLAN §7 and the explicit experiment instruction: only the watchdog mailer, at completion or an event that needs Brando; one deduplicated message to `brando.science@gmail.com`, no CC. No separate run-start mail.
