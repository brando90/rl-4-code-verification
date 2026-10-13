# Experiment 13 v2 owner runbook (SNAP, skampere1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/cc.md>

**TLDR:** You are the single writer for experiment 13 version 2 on skampere1. Your job, in order:

1. Build an elaborator-backed declaration probe that measures every output, while strict always comes from the frozen historical oracle (value and status).
2. Prove the probe on fixtures (R0) and on a train-split-only diagnostic (R1).
3. Freeze the version 2 lock and forecasts (L1v2).
4. Reproduce the oracle on all 38,784 cells (R2), with test cells only inside an opaque process.
5. Run G0, Phase 1 (anchors, IRT, G1, H2) and Phase 2's matched RL comparison through one test evaluation.

Success is a published report per gate in `expt_v2/`, ending with Phase 2's test analysis, or a stop under PLAN § 4's transition table with evidence. Version 1's files stay byte-identical. Validation and test cells are never used for development, and no gate is retried until it passes.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Start

1. Read `~/agents-config/INDEX_RULES.md`, this repository's `CLAUDE.md`, then:
   - `expt_v2/PLAN.md` (binding, revision 2) and `expt_v2/REVIEW_v2.md`;
   - `../PROTOCOL.md`;
   - `../expt_v1/REVIEW.md`;
   - `../expt_v1/PHASE1_IRT_PLAN.md` and `../expt_v1/PHASE2_MATCHED_RL_PLAN.md`;
   - `../expt_v1/RESULTS_opaque_audit_terminal.md`.
2. Confirm there is no live version 1 writer:
   - `tmux ls | grep -E 'rl4cv13|e13'`;
   - `pgrep -af 'rl4cv13|deploy_16e6b761|opaque_base_audit'`.

   If one is alive, write it into the checkpoint and stop. The master coordinates.
3. Set up the work root:
   - `export WR=/lfs/skampere1/0/brando9/rl4cv_e13v2`, with your own clone of `main`.
   - Owned caches, temporary files and installs live under `$WR`.
   - Experiment 08's pinned environment is read-only: `env_e08.sh`, Lean v4.22.0 plus Mathlib, and the scorer from `external/deps.lock.json`.
4. Create `expt_v2/CKPT_e13_v2_owner.md` and `expt_v2/results.md` (header, status, declared denominators). Commit and push both before any measurement.
5. Install `expt_v2/watchdog_e13v2.sh` (PLAN § 7): shared `flock`, run-bound PID, start time and boot ID, adoption of children, and a persistent per-cell attempt ledger. Pass these self-tests before relying on it:
   - fake mailer;
   - owned unique kill-test session;
   - concurrent-recovery case;
   - orphaned-child case.

## 1. Phase 0v2: R0, R1, L1v2, R2, G0

Follow PLAN §§ 2–4 exactly, publishing each gate before the next.

- **Oracle and components.** Strict is the historical oracle's value and status. Components come from `DeclarationProbe_v2.lean` and `declaration_adapter_v2.py`: complete per-command messages (stdout and stderr), axioms after failures, unresolved obligations kept in denominators, and private raw evidence per cell.
- **R0.** Run the full fixture list in PLAN § 4. Run the suite with `E13_REQUIRE_LEAN_INTEGRATION=1`, so `tests/test_e13_declaration_adapter.py` must execute.
- **R1.** Use **train-split allowlist cells only** (cell IDs from D-013's manifest), and wrap version 1's **complete** per-cell path. The cause table's denominator is the 300 rejected cells.
- **Memory.** Measure peak memory per cell during R1, then set concurrency and limits as in PLAN § 7.
- **L1v2.** Freeze it in `expt_v2/locks/` **before** any validation or test factor is computed. It includes F0v2 and F1v2, carried from version 1 with their history recorded.
- **R2.** Train and validation cells run in the ordinary harness. Test cells run in the separate opaque process, exposing completeness, hashes and equality only. INCOMPLETE does not advance.
- **G0.** At least 21 of 135 dense-only tasks; AUC ≥ 0.65. An undefined one-class AUC fails.

## 2. Phase 1: LP-1, anchors, IRT, G1, H2

Follow PLAN § 5 in its exact order:

1. LP-1 generation admission.
2. The anchor panel: Base reused only if exactly compatible, plus `sft_4B_f0p5` and `sft_4B_f1p0` batch 1.
3. Freeze calibration and F2.
4. Independent batch 2, then H2.

Devices come only through the experiment-13-owned lease registry, after checking all processes and the other experiments' leases. Export `CUDA_VISIBLE_DEVICES` and record each device plan in the checkpoint.

Phase 1b is optional and needs its own frozen `PHASE1B_PROTOCOL.md` first.

## 3. Phase 2: matched RL and test evaluation

Follow `../expt_v1/PHASE2_MATCHED_RL_PLAN.md` and `../PROTOCOL.md` §§ 5–8, with PLAN § 4's transition table.

- **Arm C.** If G1, H2 or arm C's variance check fails, arm C is disabled and A, B and P continue.
- **Cost.** Record T4's measured cost before L2.
- **Test FSC.** Formal specification coverage (FSC) on test outputs goes through the validated Valkyrie judge only (D-102, D-108).

## 4. Throughout

- **Publishing.** Push each finished, test-passing step to `main`: `make test` first, explicit paths only. Never pipe a test command into another command inside an `&&` chain.
- **Updates.** Update `results.md` and the checkpoint at each gate and at least every 4 hours.
- **Failures.** R0 and R1 are development acceptance tests under [Amendment A1](AMENDMENT_A1_development_gates_10-13-2026.md): fix, record the numbered attempt, rerun, at most 5 attempts. From L1v2 onward, a failed gate is a published result, never a reason to retry. [Amendment A2](AMENDMENT_A2_R2_untyped_cells_and_admission_10-13-2026.md) gives untyped R2 cells exactly one identical retry, and sets R2's admission rule (equality on all measured cells; unresolved at most 0.1% per route).
- **Account limits.** On account, context or turn exhaustion, checkpoint and continue under Rule 48 with one writer.
- **Notifications.** The watchdog's deduplicated email to `brando.science@gmail.com` (no CC) goes out only on completion or on an event that needs Brando.

**TL;DR:** historical oracle for strict, elaborator-backed components → R0 fixtures → train-only R1 diagnostic → L1v2 lock → complete R2 (test opaque) → G0 → LP-1, anchors, F2, batch 2, G1/H2 → matched four-arm RL (C optional by the transition table) → one test evaluation, publishing every gate.
