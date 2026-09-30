# Experiment 03 — coverage gating: can RL move prompts the starting policy never solves? (zero-signal bucket × reward density)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/README.md>

**Question:** Allen's coverage question (open-weight models on SNAP); numbered experiment 07 before D-007

**TLDR:** On experiment 02A's Lean pools (never VeriBench), take the prompts the warm-started policy never solves in 32 samples (`q_mixed = 0` in all four probes: the coverage-blocked bucket `Z`) and train on them under three reward arms with experiment 02B's contract: `kernel_binary` (A), `proof_fraction` (B), and B plus one compiler-feedback turn (C). This tests the claim in [notes §2](../../notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md) that outcome RL has exactly zero gradient on unsampled successes, so A cannot move `Z`, while denser reward (B) and in-rollout feedback (C) can; and whether binary reward shows the sharpening signature (pass@1 up, pass@4 not above the warm start). Designed 09-30-2026 by Claude Code for Brando to edit; `PROTOCOL.md` is written and locked once experiment 02A delivers the pools and probes.

## Goal, hypothesis and decision criterion

- **Uncertainty.** The notes argue from the policy-gradient formula that a prompt whose sampled group is all-fail contributes nothing (with a baseline, the advantage is identically zero), so the current policy's coverage of reward gates what RL can teach. Two things could still move such prompts: weight-space generalization from other prompts, and a denser reward channel that pays for partial progress. Which of these happens in Lean, and how much, is unmeasured. Brando (09-30-2026) asked for an explicit test.
- **Hypotheses.**
  - **H3 (gating).** Arm A on `Z` produces no held-out change beyond seed noise, and an endpoint re-probe of `Z` itself finds almost no prompt that moved from `K = 0` to `K > 0`. Arms B and C are the only arms that move `Z`.
  - **H4 (sharpening).** Under arm A on any cell, within-source pass@1 rises while native pass@4 at the endpoint does not exceed the warm start (the paper's 14B observation).
  - **Pre-RL corollary.** On the same probe responses, `ρ_A(Z) = 0` exactly, `ρ_B(Z) ≥ 0` (proof-fraction admits groups where a response compiles or proves part of its theorems), and `ρ_C(Z)` measured after one feedback turn is larger still. These are computed before training and frozen with `rl4cv.forecast`.
  - **FSC guard.** Endpoint VeriBench FSC under B is not below A by more than 0.05; otherwise B's reward was hacked by stating fewer or emptier theorems.
- **Decision.**
  - If arm A moves `Z` beyond the seed envelope, the notes' §2 claim is wrong for this setting: the note is rewritten, and coverage stops being treated as a gate in experiment 02D's environment selection.
  - If only B and C move `Z`, then for "solving VeriBench" (experiment 02D) the hard tail needs per-theorem credit or compiler feedback, and pools for binary channels should be built from `q_mixed > 0` prompts only. The arms' ρ and H then feed experiment 02C's channel comparison.
  - Either way the per-arm curves and the `Z` re-probe are the deliverable.
- **Rejected variant (09-30-2026).** A version that trained directly on 746 VeriBench tasks with a 150-task VeriBench held-out panel was drafted first and dropped under the *VeriBench is held out* rule in [CLAUDE.md](../../CLAUDE.md). It survives only as commit `b5e3125` on the unmerged branch `claude/admiring-heisenberg-eok3j4`; nothing from it trains on VeriBench here.

## Structure

```
03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/
├── README.md        ← this design doc
├── PROTOCOL.md      ← TODO; locked after experiment 02A's probes exist and before the first RL run
├── results.md       ← live (TODO)
├── forecasts/       ← frozen pre-RL ρ/H and outcome forecasts (rl4cv.forecast), append-only
└── expt_v1/
    ├── cc.md        ← agent prompt
    └── results/
```

## Method

1. **Inputs.** Experiment 02A's Stage A–D probes and warm starts at 1.7B and 4B (Qwen3 Base + Lean warm start, D-005), its frozen 1,000-task within-source panel, and experiment 02B's locked RL contract (NeMo RL v0.6.0, version unconfirmed against upstream's v0.7.0 audit, D-105: G = 8, unnormalized leave-one-out advantage, token-level loss, clip 0.2, no KL, overlong filtering on, dynamic sampling off, temperature 0.6 / top-p 0.95 / top-k 20, 128 steps of 4 × 8, checkpoints 16/32/48/64/96/128).
2. **Environments.**
   - `Z` (zero-signal): pool prompts with `K = 0` under `kernel_binary` in all four `G = 8` probes (32 samples), hash-capped to 256, balanced on family, split and prompt length by `rl4cv.cells`. `ρ_A(Z) = 0` by construction.
   - `N` (rare-signal, optional if compute allows): prompts with 1–2 successes in 32 samples.
   - The HH cell of experiment 02A is the reference environment; its arm comparisons come from experiment 02C and are not rerun here.
3. **Reward arms** (`src/rl4cv/rewards.py`; the verifier is never loosened):
   - **A** `kernel_binary`;
   - **B** `proof_fraction` = IC_tests × IC_proofs, 0 if any stated theorem is vacuous;
   - **C** `proof_fraction` after one feedback turn: if the first response does not typecheck, the first 40 lines of Lean diagnostics are appended and the policy samples one continuation; the reward is B on the final file; both turns' tokens count toward the generated-token budget; admission requires the final response to be uncapped. The channel (`proof_fraction_feedback1`) and its tests are added to `rl4cv.rewards` before `PROTOCOL.md` is locked. **[verify]** multi-turn environment support in the trainer used by experiment 02B.
4. **Training.** 3 seeds × 3 arms × `Z` × 2 scales = 18 trajectories (≈ 18 × 5 h ≈ 90 B200 GPU-hours, more if `N` is added). Same budget points as experiment 02B (25/50/75/100% of the largest shared generated-token budget).
5. **Outcomes at every checkpoint.** Within-source panel `kernel_binary` pass@1 (primary, eq. 1 utility); native pass@4 at endpoints; the **`Z` re-probe**: `G = 8` on the training prompts themselves at the endpoint, reporting the fraction that moved from `K = 0` to `K > 0` (the direct expansion measurement, which the panel alone cannot give). At step-128 endpoints: VeriBench V1 IC_tests, IC_proofs, FSC (`vb103_judge`, D-102) and SCSC with n, core 614 and IndustrySet 282 separately.
6. **Audits.** Experiment 02C's reward-hacking audits at every checkpoint (share of compiling files with vacuous theorems; compile-gated FSC gap); response-length and cap-hit trajectories (the paper's 1.7B LH collapse reached 86.8% capped).
7. **Analysis.** The gates below, locked in `PROTOCOL.md`; per-arm ρ and H reported alongside experiment 02C's channel table.

## Gates (proposed; numbers lock in PROTOCOL.md)

| Gate | Pass criterion |
|---|---|
| H3-A (no movement under binary) | \|ΔU_A(Z)\| within the warm start's two-seed envelope at every budget, and ≤ 2% of `Z` prompts have `K > 0` in the endpoint re-probe |
| H3-B/C (movement under denser reward) | ΔU_B(Z) or ΔU_C(Z) above the envelope at the largest budget, and ≥ 10% of `Z` prompts have `K > 0` in the endpoint re-probe |
| H4 (sharpening) | native pass@4 ≤ warm start under arm A at the largest budget |
| FSC guard | endpoint VeriBench FSC(B) ≥ FSC(A) − 0.05 |
| Pre-RL corollary | `ρ_A(Z) = 0`; `ρ_B(Z) > 0` on at least one scale; frozen before training |

If H3-A fails (arm A moves `Z`), that is the headline result, reported like a failed forecast in the paper.

## Dependencies

- Experiment 02A: pools, screens, panel, warm starts, four-stage probes (gate G2).
- Experiment 02B: the locked RL contract and NeMo RL configuration (D-105 for the paper's configs).
- `rl4cv.rewards`: the feedback channel, with tests.
- Decisions: D-102 (judge route, for endpoint FSC only), D-103 (≈ 90 B200 GPU-hours), D-105.
- Runbook for the host: [`scripts/cc_prompt_run_experiment_on_snap.md`](../../scripts/cc_prompt_run_experiment_on_snap.md).

## Status

| Step | Status |
|---|---|
| Design | Done (09-30-2026) |
| Feedback channel in `rl4cv.rewards` + tests | TODO |
| PROTOCOL.md | TODO, after experiment 02A's probes |
| Pre-RL ρ/H on `Z` per arm, frozen | TODO |
| 18 trajectories | TODO, after gate G2 and D-103 |
| Endpoint VeriBench table and gate verdicts | TODO |
